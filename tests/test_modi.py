
import pytest

import random

from modi import (
    calculate_cost,
    modi_method,
    modi_optimize,
    validate_allocation,
    solve_constrained_transport,
)
from vam import vogel_approximation


def test_simple_transport_problem():
    supply = [5, 5]
    demand = [5, 5]
    costs = [
        [1, 10],
        [10, 1],
    ]

    result = solve_constrained_transport(
        supply, demand, costs
    )

    assert result["success"] is True
    assert result["cost"] == 10


def test_closed_route_is_respected():
    supply = [1, 1]
    demand = [1, 1]
    costs = [
        [1, 2],
        [2, 1],
    ]

    result = solve_constrained_transport(
        supply, demand, costs,
        closed_routes=[(0, 0)],
    )

    assert result["allocation"][0][0] == 0
    assert result["cost"] == 4


def test_route_capacity_is_respected():
    supply = [3, 2]
    demand = [2, 3]
    costs = [
        [1, 5],
        [4, 1],
    ]

    result = solve_constrained_transport(
        supply, demand, costs,
        route_capacities={(0, 0): 1},
    )

    assert result["allocation"][0][0] <= 1
    assert result["cost"] == 16


def test_infeasible_problem_raises_error():
    with pytest.raises(RuntimeError):
        solve_constrained_transport(
            [2], [2], [[1]],
            closed_routes=[(0, 0)],
        )


def test_invalid_allocation_fails_validation():
    valid, message = validate_allocation(
        [[2, 0], [0, 2]],
        [1, 3],
        [2, 2],
    )

    assert valid is False


def test_cost_calculation():
    allocation = [
        [2, 1],
        [0, 3],
    ]
    costs = [
        [4, 5],
        [7, 2],
    ]

    assert calculate_cost(allocation, costs) == 19


SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COSTS = [
    [24, 45, 37, 18, 19],
    [28, 36, 37, 13, 23],
    [45, 39, 31, 42, 15],
    [26, 42, 19, 19, 18],
]
INITIAL = [
    [5, 3, 0, 0, 0],
    [0, 0, 0, 6, 0],
    [0, 1, 0, 0, 6],
    [0, 3, 6, 0, 0],
]


def test_modi_reaches_known_optimum():
    result = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert result["cost"] == 690
    assert result["is_optimal"] is True
    assert result["iterations"] >= 1
    assert len(result["potentials_u"]) == 4
    assert len(result["potentials_v"]) == 5


def test_reduced_costs_are_non_negative_at_optimum():
    result = modi_optimize(SUPPLY, DEMAND, COSTS, INITIAL)
    assert all(value >= -1e-9 for row in result["reduced_costs"] for value in row)


def test_modi_method_reports_improvement():
    result = modi_method(INITIAL, SUPPLY, DEMAND, COSTS)
    assert result["initial_cost"] == 702
    assert result["cost"] == 690
    assert result["improvement"] == 12
    assert result["initial_feasible"] is True
    assert result["method"] == "MODI (u-v method)"


def test_modi_respects_closed_route_and_capacity_together():
    start, _, _ = vogel_approximation(
        SUPPLY, DEMAND, COSTS, [(0, 0)], {(3, 2): 2}
    )
    result = modi_method(
        start, SUPPLY, DEMAND, COSTS, [(0, 0)], {(3, 2): 2}
    )
    expected = solve_constrained_transport(
        SUPPLY, DEMAND, COSTS, [(0, 0)], {(3, 2): 2}
    )
    assert result["allocation"][0][0] == 0
    assert result["allocation"][3][2] <= 2
    assert result["cost"] == expected["cost"]


def test_invalid_start_falls_back_to_linear_programming():
    result = modi_method([[0, 0], [0, 0]], [1, 1], [1, 1], [[1, 2], [2, 1]])
    assert result["initial_feasible"] is False
    assert result["cost"] == 2
    assert result["method"] == "Linear Programming (HiGHS)"


def test_modi_matches_linear_programming_on_random_problems():
    rng = random.Random(5)
    checked = 0
    while checked < 150:
        m, n = rng.randint(2, 5), rng.randint(2, 5)
        total = rng.randint(3, 25)

        def split(parts):
            cuts = sorted(rng.randint(0, total) for _ in range(parts - 1))
            return [b - a for a, b in zip([0] + cuts, cuts + [total])]

        supply, demand = split(m), split(n)
        costs = [[rng.randint(0, 30) for _ in range(n)] for _ in range(m)]
        cells = [(i, j) for i in range(m) for j in range(n)]
        closed = [c for c in cells if rng.random() < 0.15]
        capacities = {
            c: rng.randint(0, 5)
            for c in cells if c not in closed and rng.random() < 0.2
        }
        start, _, _ = vogel_approximation(supply, demand, costs, closed, capacities)
        if start is None:
            continue
        result = modi_method(start, supply, demand, costs, closed, capacities)
        expected = solve_constrained_transport(
            supply, demand, costs, closed, capacities
        )
        valid, _ = validate_allocation(
            result["allocation"], supply, demand, closed, capacities
        )
        assert valid
        assert result["cost"] == pytest.approx(expected["cost"])
        checked += 1
