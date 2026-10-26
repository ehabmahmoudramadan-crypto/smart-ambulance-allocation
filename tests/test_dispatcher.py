"""Task 14 - dispatcher tests: selection rules, constraints, no double booking."""
import pytest

from optimization.model import load_dataset, solve
from simulation.ambulance import Ambulance, IDLE, TO_SCENE
from simulation.dispatcher import GreedyDispatcher, PlanDispatcher
from simulation.engine import (Simulation, fleet_from_plan, fleet_greedy,
                               generate_incidents)
from simulation.incident import Incident

# 3 stations x 2 areas (minutes)
COST = [[5, 20],
        [9, 4],
        [14, 8]]


def call(area=0):
    return Incident(id=0, area=area, time=0.0, priority=2, service=25.0)


def fleet(*stations, designated=None):
    designated = designated or [None] * len(stations)
    return [Ambulance(id=k, station=s, designated_area=d)
            for k, (s, d) in enumerate(zip(stations, designated))]


# ----------------------------------------------------------- greedy rule
def test_greedy_picks_nearest_idle():
    amb, fallback = GreedyDispatcher(COST).select(call(0), fleet(0, 1, 2))
    assert amb.station == 0 and fallback is False


def test_busy_ambulance_is_never_chosen():
    cars = fleet(0, 1)
    cars[0].state = TO_SCENE                      # nearest one is busy
    amb, _ = GreedyDispatcher(COST).select(call(0), cars)
    assert amb.id == 1


def test_no_idle_ambulance_returns_none():
    cars = fleet(0, 1)
    for c in cars:
        c.state = TO_SCENE
    assert GreedyDispatcher(COST).select(call(0), cars) is None


def test_tie_goes_to_lowest_id():
    amb, _ = GreedyDispatcher(COST).select(call(0), fleet(1, 1, 1))
    assert amb.id == 0


# ----------------------------------------------------------- constraints
def test_closed_road_is_skipped():
    d = GreedyDispatcher(COST, closed=[(0, 0)])
    amb, _ = d.select(call(0), fleet(0, 1))
    assert amb.station == 1 and d.closed_uses == 0


def test_only_closed_road_available_means_waiting():
    d = GreedyDispatcher(COST, closed=[(0, 0)])
    assert d.select(call(0), fleet(0)) is None


def test_capacity_blocks_then_releases():
    d = GreedyDispatcher(COST, caps=[(0, 0, 1)])
    cars = fleet(0, 0, 1)
    first, _ = d.select(call(0), cars)
    first.state = TO_SCENE
    d.reserve(first, 0)
    second, _ = d.select(call(0), cars)           # station 0 is full -> station 1
    assert second.station == 1
    first.state = IDLE
    d.release(first, 0)
    third, _ = d.select(call(0), [first, cars[1]])
    assert third.station == 0                     # capacity is free again


# ----------------------------------------------------------- plan rule
def test_plan_prefers_designated_even_if_farther():
    cars = fleet(0, 2, designated=[1, 0])         # car 1 is designated to area 0
    amb, fallback = PlanDispatcher(COST).select(call(0), cars)
    assert amb.id == 1 and fallback is False


def test_plan_falls_back_to_nearest_idle():
    cars = fleet(0, 1, designated=[1, 1])         # nobody designated to area 0
    amb, fallback = PlanDispatcher(COST).select(call(0), cars)
    assert amb.station == 0 and fallback is True


# ----------------------------------------------------------- double booking
def test_reserving_a_busy_ambulance_twice_raises():
    d = GreedyDispatcher(COST)
    car = fleet(0)[0]
    d.reserve(car, 0)
    with pytest.raises(RuntimeError):
        d.reserve(car, 1)


# ----------------------------------------------------------- full simulation audit
@pytest.fixture(scope="module")
def world():
    ds, closed, caps = load_dataset()
    plan = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, caps)["optimal"]["allocation"]
    return ds, closed, caps, plan


def _run(world, strategy, rate, hours=8, seed=7):
    ds, closed, caps, plan = world
    incidents = generate_incidents(ds["demand"], rate, hours, seed)
    if strategy == "greedy":
        sim = Simulation(fleet_greedy(ds["supply"]),
                         GreedyDispatcher(ds["cost_matrix"], closed, caps), incidents)
    else:
        sim = Simulation(fleet_from_plan(plan),
                         PlanDispatcher(ds["cost_matrix"], closed, caps), incidents)
    return sim.run(), ds, caps


@pytest.mark.parametrize("strategy", ["greedy", "plan"])
@pytest.mark.parametrize("rate", [10, 48, 90])
def test_simulation_respects_constraints_and_never_double_books(world, strategy, rate):
    sim, ds, caps = _run(world, strategy, rate)
    d = sim.dispatcher

    assert d.closed_uses == 0                                     # closed road never used
    for i, j, k in caps:                                          # capacity never exceeded
        assert d.max_load.get((i, j), 0) <= k
    assert all(a.state == IDLE for a in sim.ambulances)           # everyone ends at home
    assert not d.active                                           # nobody left reserved

    by_amb = {}
    for inc in sim.incidents:
        assert inc.response is not None                           # every call is served
        travel = ds["cost_matrix"][next(a.station for a in sim.ambulances
                                        if a.id == inc.ambulance_id)][inc.area]
        assert inc.response >= travel - 1e-9                      # never faster than driving
        home = inc.arrived_at + inc.service + travel
        by_amb.setdefault(inc.ambulance_id, []).append((inc.dispatched_at, home))

    for spans in by_amb.values():                                 # no overlapping missions
        spans.sort()
        for (_, end), (start, _) in zip(spans, spans[1:]):
            assert start >= end - 1e-9
