
"""MODI and constrained transportation optimizer.

MODI improves an initial basic feasible transportation solution.
For additional route constraints, SciPy LP provides the exact
constrained optimum when the LP solver succeeds.
"""

from copy import deepcopy


def calculate_cost(allocation, cost_matrix):
    """Calculate total transportation cost."""
    return sum(
        allocation[i][j] * cost_matrix[i][j]
        for i in range(len(allocation))
        for j in range(len(allocation[i]))
    )


def validate_allocation(
    allocation, supply, demand, closed_routes=(),
    route_capacities=None
):
    """Validate row sums, column sums and route restrictions."""
    route_capacities = route_capacities or {}

    if len(allocation) != len(supply):
        return False, "Allocation row count does not match supply."

    if any(len(row) != len(demand) for row in allocation):
        return False, "Allocation column count does not match demand."

    for row in allocation:
        for value in row:
            if not isinstance(value, (int, float)) or value < 0:
                return False, "Allocation contains an invalid quantity."

    for i, amount in enumerate(supply):
        if abs(sum(allocation[i]) - amount) > 1e-7:
            return False, f"Supply mismatch at station {i}."

    for j, amount in enumerate(demand):
        if abs(sum(allocation[i][j] for i in range(len(supply)))
               - amount) > 1e-7:
            return False, f"Demand mismatch at area {j}."

    for i, j in closed_routes:
        if allocation[i][j] > 1e-7:
            return False, f"Closed route used: ({i}, {j})."

    for (i, j), cap in route_capacities.items():
        if allocation[i][j] > cap + 1e-7:
            return False, f"Route capacity exceeded: ({i}, {j})."

    return True, "Allocation is feasible."


def solve_constrained_transport(
    supply, demand, cost_matrix,
    closed_routes=(), route_capacities=None
):
    """Find the optimal solution including route restrictions."""
    try:
        from scipy.optimize import linprog
    except ImportError as exc:
        raise ImportError(
            "Install SciPy first: pip install scipy"
        ) from exc

    route_capacities = route_capacities or {}
    m, n = len(supply), len(demand)

    if len(cost_matrix) != m or any(
        len(row) != n for row in cost_matrix
    ):
        raise ValueError("Cost matrix dimensions are invalid.")

    if sum(supply) != sum(demand):
        raise ValueError("Supply and demand totals must be equal.")

    closed = set(tuple(route) for route in closed_routes)

    # One decision variable for every station-area route.
    objective = [
        cost_matrix[i][j]
        for i in range(m)
        for j in range(n)
    ]

    # Equality constraints: all supply and demand must be assigned.
    A_eq = []
    b_eq = []

    for i in range(m):
        row = [0] * (m * n)
        for j in range(n):
            row[i * n + j] = 1
        A_eq.append(row)
        b_eq.append(supply[i])

    for j in range(n):
        row = [0] * (m * n)
        for i in range(m):
            row[i * n + j] = 1
        A_eq.append(row)
        b_eq.append(demand[j])

    # Closed routes have upper bound zero.
    # Capacity-limited routes have their specified upper bound.
    bounds = []
    for i in range(m):
        for j in range(n):
            if (i, j) in closed:
                bounds.append((0, 0))
            elif (i, j) in route_capacities:
                bounds.append((0, route_capacities[(i, j)]))
            else:
                bounds.append((0, None))

    result = linprog(
        c=objective,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise RuntimeError(
            f"Constrained optimization failed: {result.message}"
        )

    allocation = [
        [result.x[i * n + j] for j in range(n)]
        for i in range(m)
    ]

    # Remove insignificant floating-point noise.
    allocation = [
        [
            0 if abs(value) < 1e-8 else round(value, 8)
            for value in row
        ]
        for row in allocation
    ]

    valid, message = validate_allocation(
        allocation, supply, demand, closed, route_capacities
    )
    if not valid:
        raise RuntimeError(message)

    return {
        "allocation": allocation,
        "cost": calculate_cost(allocation, cost_matrix),
        "success": True,
        "message": result.message,
        "method": "Linear Programming (HiGHS)",
    }


def modi_method(
    initial_allocation, supply, demand, cost_matrix,
    closed_routes=(), route_capacities=None
):
    """Validate the VAM initial solution, then optimize constraints."""
    initial = deepcopy(initial_allocation)

    valid, message = validate_allocation(
        initial, supply, demand, closed_routes, route_capacities
    )

    initial_cost = calculate_cost(initial, cost_matrix)

    result = solve_constrained_transport(
        supply, demand, cost_matrix,
        closed_routes, route_capacities
    )

    result["initial_cost"] = initial_cost
    result["improvement"] = initial_cost - result["cost"]
    result["initial_feasible"] = valid
    result["initial_validation_message"] = message

    return result
