import pytest


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


def test_closed_route_overrides_capacity():
    allocation, cost, steps = vogel_approximation(
        [1], [1], [[5]],
        closed_routes=[(0, 0)],
        route_capacities={(0, 0): 1},
    )

    # No feasible allocation exists on a closed route.
    # The algorithm should report infeasibility.
    assert allocation is None
