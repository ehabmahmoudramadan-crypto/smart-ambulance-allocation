"""algorithms/vam.py and algorithms/modi.py — unit tests against the real API.

The old version of this file imported functions that do not exist in the actual
source code (calculate_cost, modi_method, validate_allocation,
solve_constrained_transport).  This rewrite tests the real public interface:

  - vogel_approximation(supply, demand, cost) -> dict
  - modi_optimize(supply, demand, cost, allocation) -> dict
  - algorithms.model.solve / plan_cost / check_plan
"""
import random

import pytest

from algorithms.model import check_plan, plan_cost, solve
from algorithms.modi import modi_optimize
from algorithms.vam import vogel_approximation

# ------------------------------------------------------------------ fixtures
SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COSTS = [
    [24, 45, 37, 18, 19],
    [28, 36, 37, 13, 23],
    [45, 39, 31, 42, 15],
    [26, 42, 19, 19, 18],
]
# Reference VAM solution (manual)
INITIAL = [
    [5, 3, 0, 0, 0],
    [0, 0, 0, 6, 0],
    [0, 1, 0, 0, 6],
    [0, 3, 6, 0, 0],
]
VAM_COST   = 702
MODI_COST  = 690


def is_feasible(x, supply, demand):
    return (
        [sum(r) for r in x] == list(supply)
        and [sum(c) for c in zip(*x)] == list(demand)
        and all(v >= 0 for r in x for v in r)
    )


# ------------------------------------------------------------------ VAM tests
def test_vam_output_is_feasible():
    result = vogel_approximation(SUPPLY, DEMAND, COSTS)
    assert "allocation" in result and "total_cost" in result and "steps" in result
    assert is_feasible(result["allocation"], SUPPLY, DEMAND)


def test_vam_matches_known_cost():
    result = vogel_approximation(SUPPLY, DEMAND, COSTS)
    assert result["total_cost"] == VAM_COST


def test_vam_matches_known_allocation():
    result = vogel_approximation(SUPPLY, DEMAND, COSTS)
    assert [list(r) for r in result["allocation"]] == INITIAL


def test_vam_rejects_unbalanced():
    with pytest.raises(ValueError, match="balanced"):
        vogel_approximation([5], [3, 4], [[1, 2]])


def test_vam_simple_diagonal():
    """2×2 problem: optimal = diagonal."""
    s, d, c = [5, 5], [5, 5], [[1, 10], [10, 1]]
    x = vogel_approximation(s, d, c)["allocation"]
    assert is_feasible(x, s, d)
    assert plan_cost(x, c) == 10


# ------------------------------------------------------------------ MODI tests
def test_modi_output_keys():
    o = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert "allocation" in o and "total_cost" in o and "iterations" in o


def test_modi_reaches_known_optimum():
    o = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert o["total_cost"] == MODI_COST
    assert is_feasible(o["allocation"], SUPPLY, DEMAND)


def test_modi_improvement_equals_12():
    o = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert VAM_COST - o["total_cost"] == 12


def test_modi_internal_cost_matches_plan_cost():
    """total_cost reported by MODI must equal plan_cost() on its own allocation."""
    o = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert o["total_cost"] == plan_cost(o["allocation"], COSTS)


def test_modi_never_worsens_vam():
    rng = random.Random(42)
    for _ in range(50):
        m, n = rng.randint(2, 5), rng.randint(2, 5)
        total = rng.randint(max(m, n), 20)
        parts = lambda k: (lambda p: p)([1] * k) or [
            1 + rng.randint(0, total - k) for _ in range(k)
        ]
        # build balanced random problem
        s = [1] * m
        d = [1] * n
        extra = total - m
        for _ in range(extra):
            s[rng.randrange(m)] += 1
        extra2 = sum(s) - n
        for _ in range(extra2):
            d[rng.randrange(n)] += 1
        c = [[rng.randint(1, 30) for _ in range(n)] for _ in range(m)]
        if sum(s) != sum(d):
            continue
        x0 = vogel_approximation(s, d, c)["allocation"]
        o  = modi_optimize(s, d, c, x0)
        assert o["total_cost"] <= plan_cost(x0, c)
        assert is_feasible(o["allocation"], s, d)


# ------------------------------------------------------------------ plan_cost / check_plan
def test_plan_cost_manual():
    # 5*24+3*45+6*13+1*39+6*15+3*42+6*19 = 702
    assert plan_cost(INITIAL, COSTS) == VAM_COST


def test_check_plan_passes_valid():
    check_plan(INITIAL, SUPPLY, DEMAND)   # must not raise


def test_check_plan_fails_closed_road_violation():
    bad = [r[:] for r in INITIAL]
    bad[0][0] += 1; bad[1][0] -= 1        # violate supply/demand to trigger assertion
    with pytest.raises(AssertionError):
        check_plan(bad, SUPPLY, DEMAND)


# ------------------------------------------------------------------ solve() integration
def test_solve_returns_initial_and_optimal():
    r = solve(SUPPLY, DEMAND, COSTS)
    assert "initial" in r and "optimal" in r
    assert r["optimal"]["cost"] <= r["initial"]["cost"]


def test_solve_honours_closed_road():
    closed = [(0, 0)]
    r = solve(SUPPLY, DEMAND, COSTS, closed=closed)
    assert r["optimal"]["allocation"][0][0] == 0


def test_solve_honours_capacity():
    caps = [(3, 2, 2)]          # station 3, area 2, max 2
    r = solve(SUPPLY, DEMAND, COSTS, caps=caps)
    assert r["optimal"]["allocation"][3][2] <= 2


def test_solve_rejects_unbalanced():
    with pytest.raises(ValueError):
        solve(SUPPLY, [5, 7, 6, 6, 11], COSTS)
