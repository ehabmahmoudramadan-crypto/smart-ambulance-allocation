"""QA suite - Part 15 (testing & quality assurance).

Covers:
  TC-01..05  allocation totals and cost
  TC-06..09  VAM / MODI against the manual solution (and an exact LP)
  TC-10..14  excess demand, station / vehicle failure, extra constraints
  TC-20..23  no ambulance is booked twice at the same time
  TC-30..32  API behaviour on bad / impossible input

Tests marked xfail document a BUG found during QA (see the bug log). When a bug
is fixed, remove its xfail marker so the test guards against regressions.
"""
import random

import pytest

from algorithms.model import check_plan, load_dataset, plan_cost, solve
from algorithms.modi import modi_optimize
from algorithms.vam import vogel_approximation
from simulation.ambulance_agent import IDLE
from simulation.dispatcher import GreedyDispatcher, PlanDispatcher
from simulation.engine import (Simulation, fleet_from_plan, fleet_greedy,
                               generate_incidents, simulate_once)

#   manual data
# Same data as VAM_Manual_Solution_steps.md / MODI_Manual_Solution_steps.md
SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COSTS = [
    [24, 45, 37, 18, 19],
    [28, 36, 37, 13, 23],
    [45, 39, 31, 42, 15],
    [26, 42, 19, 19, 18],
]
MANUAL_VAM = [
    [5, 3, 0, 0, 0],
    [0, 0, 0, 6, 0],
    [0, 1, 0, 0, 6],
    [0, 3, 6, 0, 0],
]
MANUAL_VAM_COST = 702
MANUAL_MODI_COST = 690


#   helpers
def is_feasible(x, supply, demand):
    """Integers, non-negative, row sums = supply, column sums = demand."""
    return (all(v == int(v) and v >= 0 for row in x for v in row)
            and [sum(r) for r in x] == list(supply)
            and [sum(c) for c in zip(*x)] == list(demand))


def lp_cost(supply, demand, cost):
    """Exact optimum from scipy (independent check of MODI)."""
    from scipy.optimize import linprog
    m, n = len(supply), len(demand)
    a_eq, b_eq = [], []
    for i in range(m):
        row = [0] * (m * n)
        for j in range(n):
            row[i * n + j] = 1
        a_eq.append(row)
        b_eq.append(supply[i])
    for j in range(n):
        row = [0] * (m * n)
        for i in range(m):
            row[i * n + j] = 1
        a_eq.append(row)
        b_eq.append(demand[j])
    res = linprog([cost[i][j] for i in range(m) for j in range(n)],
                  A_eq=a_eq, b_eq=b_eq, bounds=(0, None), method="highs")
    assert res.success
    return round(res.fun)


def random_problem(rng):
    m, n = rng.randint(2, 6), rng.randint(2, 6)
    total = rng.randint(max(m, n), 30)

    def split(k):
        parts = [1] * k
        for _ in range(total - k):
            parts[rng.randrange(k)] += 1
        return parts

    cost = [[rng.randint(1, 40) for _ in range(n)] for _ in range(m)]
    return split(m), split(n), cost


@pytest.fixture(scope="module")
def world():
    ds, closed, caps = load_dataset()
    plan = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, caps)["optimal"]["allocation"]
    return ds, closed, caps, plan


# ======================================================================
# 1. Totals and cost
# ======================================================================
def test_tc01_vam_manual_allocation_is_feasible():
    x = vogel_approximation(SUPPLY, DEMAND, COSTS)["allocation"]
    assert is_feasible(x, SUPPLY, DEMAND)


def test_tc02_plan_cost_helper_matches_hand_calculation():
    # 5*24 + 3*45 + 6*13 + 1*39 + 6*15 + 3*42 + 6*19 = 702
    assert plan_cost(MANUAL_VAM, COSTS) == MANUAL_VAM_COST


def test_tc03_default_dataset_reference_costs(world):
    ds, closed, caps, _ = world
    with_c = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, caps)
    without = solve(ds["supply"], ds["demand"], ds["cost_matrix"])
    assert with_c["initial"]["cost"] == 1261
    assert with_c["optimal"]["cost"] == ds["reference_optimum_with_constraints"] == 1111
    assert without["optimal"]["cost"] == ds["reference_optimum_without_constraints"] == 1016


def test_tc04_default_plan_totals_and_constraints(world):
    ds, closed, caps, plan = world
    assert is_feasible(plan, ds["supply"], ds["demand"])
    check_plan(plan, ds["supply"], ds["demand"], closed, caps)
    assert plan_cost(plan, ds["cost_matrix"]) == 1111          # no Big-M leaks into the cost
    assert plan[1][6] == 0                                      # S2 -> A7 closed
    assert plan[4][8] <= 5                                      # S5 -> A9 capacity


def test_tc05_modi_total_cost_equals_recomputed_cost():
    x0 = vogel_approximation(SUPPLY, DEMAND, COSTS)["allocation"]
    o = modi_optimize(SUPPLY, DEMAND, COSTS, x0)
    assert o["total_cost"] == plan_cost(o["allocation"], COSTS)


  
# 2. VAM / MODI against the manual solution

def test_tc06_vam_matches_manual_cost_702():
    x = vogel_approximation(SUPPLY, DEMAND, COSTS)["allocation"]
    assert plan_cost(x, COSTS) == MANUAL_VAM_COST


def test_tc07_vam_matches_manual_allocation_cell_by_cell():
    x = vogel_approximation(SUPPLY, DEMAND, COSTS)["allocation"]
    assert [list(r) for r in x] == MANUAL_VAM


def test_tc08_modi_matches_manual_cost_690():
    x0 = vogel_approximation(SUPPLY, DEMAND, COSTS)["allocation"]
    o = modi_optimize(SUPPLY, DEMAND, COSTS, x0)
    assert is_feasible(o["allocation"], SUPPLY, DEMAND)
    assert o["total_cost"] == MANUAL_MODI_COST
    assert MANUAL_VAM_COST - o["total_cost"] == 12              # improvement in the manual


def test_tc09_vam_feasible_and_modi_equals_exact_lp_on_random_problems():
    rng = random.Random(11)
    for _ in range(150):
        s, d, c = random_problem(rng)
        x0 = vogel_approximation(s, d, c)["allocation"]
        assert is_feasible(x0, s, d)
        o = modi_optimize(s, d, c, x0)
        assert is_feasible(o["allocation"], s, d)
        assert o["total_cost"] <= plan_cost(x0, c)               # MODI never worse than VAM
        assert o["total_cost"] == lp_cost(s, d, c)               # and it is optimal


#  
# 3. Excess demand, station / vehicle failure, extra constraints
#  
def test_tc10_excess_demand_handled_with_dummy_station():
    demand = [5, 7, 6, 6, 11]                                   # 35 needed, 30 available
    supply = SUPPLY + [5]                                       # dummy station (cost 0)
    costs = COSTS + [[0] * 5]
    x = solve(supply, demand, costs)["optimal"]["allocation"]
    assert is_feasible(x, supply, demand)
    assert sum(x[4]) == 5                                       # exactly the 5 missing units
    assert all(sum(x[i]) == SUPPLY[i] for i in range(4))        # real ambulances all used


def test_tc11_unbalanced_input_is_rejected_or_balanced_by_solve():
    # BUG-03 was closed: solve() (via vam) correctly raises ValueError for unbalanced input.
    with pytest.raises(ValueError):
        solve(SUPPLY, [5, 7, 6, 6, 11], COSTS)


@pytest.mark.parametrize("station,lost", [(0, 8), (2, 7), (3, 3)])
def test_tc12_station_or_vehicle_failure(station, lost):
    """Station/vehicle failure: 'lost' ambulances at 'station' are unavailable.

    FIX (BUG-01): the original test subtracted from supply[station] without
    adjusting demand -> unbalanced problem -> ValueError from VAM.

    Correct balanced model: reduce supply[station] by 'lost', then add a dummy
    SUPPLY row of size 'lost' with BIG_M costs to all areas so it cannot serve
    any real area.  sum(supply+dummy) == sum(demand) is restored.
    The dummy row absorbs the 'lost' unavailable units.
    """
    BIG_M = 99999
    supply = SUPPLY[:]
    supply[station] -= lost                                     # remove failed ambulances
    supply_with_dummy = supply + [lost]                         # dummy row restores balance
    costs_with_dummy = COSTS + [[BIG_M] * len(DEMAND)]          # dummy row can't serve
    x = solve(supply_with_dummy, DEMAND, costs_with_dummy)["optimal"]["allocation"]
    assert is_feasible(x, supply_with_dummy, DEMAND)
    # The real station sends at most what it still has
    assert sum(x[station]) == supply[station]
    # The dummy row absorbs exactly 'lost' units spread across any columns
    assert sum(x[-1]) == lost


def test_tc13_extra_constraints_never_lower_the_cost(world):
    ds, closed, caps, _ = world
    base = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, caps)["optimal"]
    more_closed = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed + [(0, 0)], caps)["optimal"]
    assert more_closed["allocation"][0][0] == 0
    assert more_closed["cost"] >= base["cost"]
    tighter = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, [(4, 8, 3)])["optimal"]
    assert tighter["allocation"][4][8] <= 3
    assert tighter["cost"] >= base["cost"]


def test_tc14_impossible_problem_is_not_returned_as_a_valid_plan(world):
    ds, _, _, _ = world
    all_closed = [(i, 0) for i in range(len(ds["supply"]))]     # nobody can reach A1
    with pytest.raises(Exception):
        solve(ds["supply"], ds["demand"], ds["cost_matrix"], all_closed, [])



# 4. No ambulance is booked twice at the same time

def _run(world, strategy, rate, hours=8, seed=7):
    ds, closed, caps, plan = world
    incidents = generate_incidents(ds["demand"], rate, hours, seed)
    if strategy == "greedy":
        sim = Simulation(fleet_greedy(ds["supply"]),
                         GreedyDispatcher(ds["cost_matrix"], closed, caps), incidents)
    else:
        sim = Simulation(fleet_from_plan(plan),
                         PlanDispatcher(ds["cost_matrix"], closed, caps), incidents)
    return sim.run()


@pytest.mark.parametrize("strategy", ["greedy", "plan"])
@pytest.mark.parametrize("rate", [10, 48, 90])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_tc20_no_overlapping_missions_per_ambulance(world, strategy, rate, seed):
    ds = world[0]
    sim = _run(world, strategy, rate, seed=seed)
    station_of = {a.id: a.station for a in sim.ambulances}
    spans = {}
    for inc in sim.incidents:
        assert inc.ambulance_id is not None, "call never served"
        assert inc.dispatched_at >= inc.time - 1e-9             # nobody leaves before the call
        travel = ds["cost_matrix"][station_of[inc.ambulance_id]][inc.area]
        home = inc.arrived_at + inc.service + travel
        spans.setdefault(inc.ambulance_id, []).append((inc.dispatched_at, home))
    for amb_id, s in spans.items():
        s.sort()
        for (_, end), (start, _) in zip(s, s[1:]):
            assert start >= end - 1e-9, f"ambulance {amb_id} booked while still on a mission"
    assert sum(a.missions for a in sim.ambulances) == len(sim.incidents)
    assert all(a.state == IDLE for a in sim.ambulances)
    assert not sim.dispatcher.active


def test_tc21_each_vehicle_has_one_station_and_one_area(world):
    ds, _, _, plan = world
    fleet = fleet_from_plan(plan)
    assert len({a.id for a in fleet}) == len(fleet) == sum(ds["supply"])
    for i, s in enumerate(ds["supply"]):
        assert sum(a.station == i for a in fleet) == s
    for j, d in enumerate(ds["demand"]):
        assert sum(a.designated_area == j for a in fleet) == d
    greedy = fleet_greedy(ds["supply"])
    assert len({a.id for a in greedy}) == len(greedy) == sum(ds["supply"])


def test_tc22_same_seed_gives_same_result(world):
    a = _run(world, "plan", 48, seed=5)
    b = _run(world, "plan", 48, seed=5)
    key = lambda s: [(i.id, i.ambulance_id, round(i.dispatched_at, 6)) for i in s.incidents]
    assert key(a) == key(b)


@pytest.mark.xfail(strict=False, reason="BUG-02: summarize() crashes when a run has no incidents "
                                        "(possible at 1 call/hour for 1 hour)")
def test_tc23_run_with_zero_incidents_does_not_crash(world):
    ds, closed, caps, plan = world
    simulate_once("greedy", ds, closed, caps, plan, [], 1)


  
# 5. API

@pytest.fixture(scope="module")
def client():
    from Backend.app import app
    return app.test_client()


def test_tc30_api_rejects_unbalanced_problem(client):
    r = client.post("/api/solve", json={"demand": [5, 7, 6, 6, 11, 1, 1, 1, 1, 1, 1, 1]})
    assert r.status_code == 400


@pytest.mark.xfail(strict=False, reason="BUG-04: an impossible problem returns HTTP 500 instead of a clear 4xx")
def test_tc31_api_impossible_problem_returns_4xx(client):
    r = client.post("/api/solve", json={"closed": [[i, 0] for i in range(8)]})
    assert r.status_code in (400, 422)


def test_tc32_api_default_solution_has_no_bigm_in_cost(client):
    j = client.post("/api/solve", json={}).json
    assert j["optimal"]["cost"] == 1111
    assert j["optimal"]["allocation"][1][6] == 0