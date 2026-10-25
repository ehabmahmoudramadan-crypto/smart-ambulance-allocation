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


def vogel_approximation(supply, demand, cost_matrix,
                        closed_routes=None, route_capacities=None):
    closed_routes = closed_routes or []
    route_capacities = route_capacities or {}
    _validate_inputs(supply, demand, cost_matrix,
                     closed_routes, route_capacities)
    limits = _build_route_limits(supply, demand, closed_routes,
                                 route_capacities)

    m, n = len(supply), len(demand)
    supply_left = list(supply)
    demand_left = list(demand)
    allocation = [[0] * n for _ in range(m)]
    active_rows = {i for i, value in enumerate(supply_left) if value > 0}
    active_cols = {j for j, value in enumerate(demand_left) if value > 0}
    steps = []

    def room(i, j):
        quantity = min(supply_left[i], demand_left[j])
        if limits[i][j] is None:
            return quantity
        return min(quantity, limits[i][j] - allocation[i][j])

    def penalty(costs):
        ordered = sorted(costs)
        if len(ordered) == 1:
            return float("inf")
        return ordered[1] - ordered[0]

    while active_rows and active_cols:
        candidates = []
        for i in sorted(active_rows):
            open_cols = [j for j in active_cols if room(i, j) > 0]
            if not open_cols:
                return None, None, steps
            cheapest = min(open_cols, key=lambda j: (cost_matrix[i][j], j))
            candidates.append((
                penalty([cost_matrix[i][j] for j in open_cols]),
                -cost_matrix[i][cheapest], 1, -i, i, cheapest,
            ))
        for j in sorted(active_cols):
            open_rows = [i for i in active_rows if room(i, j) > 0]
            if not open_rows:
                return None, None, steps
            cheapest = min(open_rows, key=lambda i: (cost_matrix[i][j], i))
            candidates.append((
                penalty([cost_matrix[i][j] for i in open_rows]),
                -cost_matrix[cheapest][j], 0, -j, cheapest, j,
            ))

        _, _, _, _, i, j = max(candidates)
        quantity = room(i, j)
        allocation[i][j] += quantity
        supply_left[i] -= quantity
        demand_left[j] -= quantity
        steps.append({
            "row": i,
            "column": j,
            "quantity": quantity,
            "unit_cost": cost_matrix[i][j],
        })
        if supply_left[i] == 0:
            active_rows.discard(i)
        if demand_left[j] == 0:
            active_cols.discard(j)

    total_cost = sum(allocation[i][j] * cost_matrix[i][j]
                     for i in range(m) for j in range(n))
    return allocation, total_cost, steps


def solve_vam(supply, demand, cost_matrix,
              closed_routes=None, route_capacities=None):
    allocation, total_cost, _ = vogel_approximation(
        supply, demand, cost_matrix, closed_routes, route_capacities
    )
    return allocation, total_cost
