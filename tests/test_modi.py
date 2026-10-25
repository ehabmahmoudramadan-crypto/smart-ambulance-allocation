
import pytest

from modi import (
    calculate_cost,
    validate_allocation,
    solve_constrained_transport,
)


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
    assert result["cost"] == 11


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
