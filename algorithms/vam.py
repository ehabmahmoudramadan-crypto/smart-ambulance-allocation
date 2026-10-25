def _validate_inputs(supply, demand, cost_matrix,
                     closed_routes, route_capacities):
    """Validate transportation problem inputs."""

    if not supply or not demand:
        raise ValueError("Supply and demand must not be empty.")

    if len(cost_matrix) != len(supply):
        raise ValueError("Cost matrix rows must match supply.")

    if any(len(row) != len(demand) for row in cost_matrix):
        raise ValueError("Cost matrix columns must match demand.")

    for name, values in (("supply", supply), ("demand", demand)):
        for value in values:
            if (isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0):
                raise ValueError(
                    f"{name} values must be non-negative integers."
                )

    for row in cost_matrix:
        for cost in row:
            if (isinstance(cost, bool)
                    or not isinstance(cost, (int, float))
                    or cost < 0):
                raise ValueError(
                    "Costs must be non-negative numbers."
                )

    if sum(supply) != sum(demand):
        raise ValueError("Total supply must equal total demand.")

    for route in closed_routes:
        if (not isinstance(route, (tuple, list))
                or len(route) != 2):
            raise ValueError("Each closed route must be (row, col).")

        i, j = route
        if (not isinstance(i, int) or isinstance(i, bool)
                or not isinstance(j, int) or isinstance(j, bool)
                or not (0 <= i < len(supply))
                or not (0 <= j < len(demand))):
            raise ValueError("Closed route index out of range.")

    for route, cap in route_capacities.items():
        if (not isinstance(route, (tuple, list))
                or len(route) != 2):
            raise ValueError("Each capacity route must be (row, col).")

        i, j = route
        if (not isinstance(i, int) or isinstance(i, bool)
                or not isinstance(j, int) or isinstance(j, bool)
                or not (0 <= i < len(supply))
                or not (0 <= j < len(demand))):
            raise ValueError("Capacity route index out of range.")

        if (isinstance(cap, bool)
                or not isinstance(cap, int)
                or cap < 0):
            raise ValueError(
                "Route capacities must be non-negative integers."
            )


def _build_route_limits(supply, demand, closed_routes,
                        route_capacities):
    """Build route limits; None means unlimited."""

    limits = [
        [None for _ in demand]
        for _ in supply
    ]

    for (i, j), cap in route_capacities.items():
        limits[i][j] = cap

    for i, j in closed_routes:
        limits[i][j] = 0

    return limits
