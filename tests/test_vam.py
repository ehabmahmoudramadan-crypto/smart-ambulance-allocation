import pytest

from vam import vogel_approximation

SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COSTS = [
    [24, 45, 37, 18, 19],
    [28, 36, 37, 13, 23],
    [45, 39, 31, 42, 15],
    [26, 42, 19, 19, 18],
]


def totals(allocation):
    rows = [sum(row) for row in allocation]
    columns = [sum(row[j] for row in allocation) for j in range(len(allocation[0]))]
    return rows, columns


def test_unrestricted_problem_is_feasible_and_costs_702():
    allocation, cost, steps = vogel_approximation(SUPPLY, DEMAND, COSTS)
    assert totals(allocation) == (SUPPLY, DEMAND)
    assert cost == 702
    assert len(steps) > 0


def test_steps_describe_every_assignment():
    allocation, _, steps = vogel_approximation(SUPPLY, DEMAND, COSTS)
    assert sum(step["quantity"] for step in steps) == sum(SUPPLY)
    for step in steps:
        assert set(step) == {"row", "column", "quantity", "unit_cost"}
        assert step["unit_cost"] == COSTS[step["row"]][step["column"]]


def test_unbalanced_problem_is_rejected():
    with pytest.raises(ValueError):
        vogel_approximation([8, 6], [5, 8], [[1, 2], [3, 4]])


def test_inputs_are_not_modified():
    supply, demand = list(SUPPLY), list(DEMAND)
    vogel_approximation(supply, demand, COSTS)
    assert supply == SUPPLY
    assert demand == DEMAND


def test_closed_route_is_not_used():
    allocation, _, _ = vogel_approximation(
        SUPPLY, DEMAND, COSTS, closed_routes=[(1, 3)]
    )
    assert allocation[1][3] == 0
    assert totals(allocation) == (SUPPLY, DEMAND)


def test_route_capacity_is_respected():
    allocation, _, _ = vogel_approximation(
        SUPPLY, DEMAND, COSTS, route_capacities={(0, 3): 1}
    )
    assert allocation[0][3] <= 1
    assert totals(allocation) == (SUPPLY, DEMAND)


def test_restrictions_never_lower_the_cost():
    _, free_cost, _ = vogel_approximation(SUPPLY, DEMAND, COSTS)
    _, restricted_cost, _ = vogel_approximation(
        SUPPLY, DEMAND, COSTS,
        closed_routes=[(1, 3)], route_capacities={(3, 4): 2},
    )
    assert restricted_cost >= free_cost


def test_large_dataset_respects_both_restrictions():
    import data

    closed = [(data.STATIONS.index(s), data.AREAS.index(a))
              for s, a in data.CLOSED_ROUTES]
    capacities = {
        (data.STATIONS.index(s), data.AREAS.index(a)): limit
        for (s, a), limit in data.ROUTE_CAPACITIES.items()
    }
    allocation, cost, _ = vogel_approximation(
        data.SUPPLY, data.DEMAND, data.COST_MATRIX, closed, capacities
    )
    assert totals(allocation) == (data.SUPPLY, data.DEMAND)
    assert allocation[1][6] == 0
    assert allocation[4][8] <= 5
    assert cost >= data.REFERENCE_OPTIMAL_COST


def test_impossible_restrictions_return_none():
    allocation, cost, _ = vogel_approximation(
        [2], [2], [[1]], closed_routes=[(0, 0)]
    )
    assert allocation is None
    assert cost is None


def test_fractional_capacity_is_rejected():
    with pytest.raises(ValueError):
        vogel_approximation(
            [1], [1], [[5]],
            route_capacities={(0, 0): 0.5}
        )


def test_negative_capacity_is_rejected():
    with pytest.raises(ValueError):
        vogel_approximation(
            [1], [1], [[5]],
            route_capacities={(0, 0): -1}
        )


def test_boolean_capacity_is_rejected():
    with pytest.raises(ValueError):
        vogel_approximation(
            [1], [1], [[5]],
            route_capacities={(0, 0): True}
        )


def test_out_of_range_route_is_rejected():
    with pytest.raises(ValueError):
        vogel_approximation([1], [1], [[5]], closed_routes=[(3, 0)])


def test_closed_route_overrides_capacity():
    allocation, cost, steps = vogel_approximation(
        [1], [1], [[5]],
        closed_routes=[(0, 0)],
        route_capacities={(0, 0): 1},
    )

    assert allocation is None
