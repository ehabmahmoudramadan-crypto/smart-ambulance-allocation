
"""MODI and constrained transportation optimizer.

MODI improves an initial basic feasible transportation solution and
supports closed routes and route capacities. SciPy LP provides the exact
constrained optimum when no feasible starting solution is available.
"""

from collections import deque
from copy import deepcopy

EPS = 1e-9


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


class NotBasicSolution(Exception):
    pass


def _upper_bounds(m, n, closed_routes, route_capacities):
    upper = [[None] * n for _ in range(m)]
    for (i, j), cap in (route_capacities or {}).items():
        upper[i][j] = cap
    for i, j in closed_routes:
        upper[i][j] = 0
    return upper


def _find_cycle(basis, start, m, n):
    cells = set(basis)
    cells.add(start)
    row_cells = {i: [c for c in cells if c[0] == i] for i in range(m)}
    col_cells = {j: [c for c in cells if c[1] == j] for j in range(n)}

    def dfs(cell, move_row, path):
        i, j = cell
        neighbors = row_cells[i] if move_row else col_cells[j]
        for nxt in sorted(neighbors):
            if nxt == cell:
                continue
            if nxt == start and len(path) >= 4 and not move_row:
                return path + [start]
            if nxt in path:
                continue
            found = dfs(nxt, not move_row, path + [nxt])
            if found:
                return found
        return None

    return dfs(start, True, [start]) or dfs(start, False, [start])


def _potentials(basis, costs, m, n):
    row_cells = {i: [] for i in range(m)}
    col_cells = {j: [] for j in range(n)}
    for i, j in basis:
        row_cells[i].append(j)
        col_cells[j].append(i)

    u = [None] * m
    v = [None] * n
    u[0] = 0.0
    queue = deque([("row", 0)])
    while queue:
        kind, k = queue.popleft()
        if kind == "row":
            for j in row_cells[k]:
                if v[j] is None:
                    v[j] = costs[k][j] - u[k]
                    queue.append(("col", j))
        else:
            for i in col_cells[k]:
                if u[i] is None:
                    u[i] = costs[i][k] - v[k]
                    queue.append(("row", i))

    if any(value is None for value in u + v):
        raise RuntimeError("The basis does not connect all stations and areas.")
    return u, v


def _room(value, upper, sign):
    if sign > 0:
        return float("inf") if upper is None else upper - value
    return value


def modi_optimize(supply, demand, cost_matrix, initial_allocation,
                  closed_routes=(), route_capacities=None,
                  max_iterations=1000):
    m, n = len(supply), len(demand)
    upper = _upper_bounds(m, n, closed_routes, route_capacities)
    x = [list(row) for row in initial_allocation]
    costs = [list(map(float, row)) for row in cost_matrix]

    parent = list(range(m + n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[rb] = ra
        return True

    basis = set()
    for i in range(m):
        for j in range(n):
            inside = x[i][j] > 0 and (upper[i][j] is None or x[i][j] < upper[i][j])
            if inside:
                if not union(i, m + j):
                    raise NotBasicSolution("The starting solution contains a cycle.")
                basis.add((i, j))

    spare = sorted(
        (upper[i][j] == 0, costs[i][j], i, j)
        for i in range(m) for j in range(n)
        if (i, j) not in basis
    )
    for _, _, i, j in spare:
        if len(basis) == m + n - 1:
            break
        if union(i, m + j):
            basis.add((i, j))

    for iteration in range(max_iterations + 1):
        u, v = _potentials(basis, costs, m, n)
        reduced = [
            [0.0 if (i, j) in basis else costs[i][j] - u[i] - v[j] for j in range(n)]
            for i in range(m)
        ]

        entering = None
        best_gain = EPS
        for i in range(m):
            for j in range(n):
                if (i, j) in basis or upper[i][j] == 0:
                    continue
                at_upper = upper[i][j] is not None and x[i][j] == upper[i][j]
                if not at_upper and reduced[i][j] < -best_gain:
                    entering, direction, best_gain = (i, j), 1, -reduced[i][j]
                elif at_upper and reduced[i][j] > best_gain:
                    entering, direction, best_gain = (i, j), -1, reduced[i][j]

        if entering is None:
            allocation = [[int(value) if float(value).is_integer() else value
                           for value in row] for row in x]
            return {
                "allocation": allocation,
                "cost": calculate_cost(allocation, cost_matrix),
                "success": True,
                "message": "Optimal: all reduced costs satisfy the optimality conditions.",
                "method": "MODI (u-v method)",
                "iterations": iteration,
                "is_optimal": True,
                "potentials_u": u,
                "potentials_v": v,
                "reduced_costs": reduced,
            }

        cycle = _find_cycle(basis, entering, m, n)
        if not cycle:
            raise RuntimeError("Could not construct a MODI improvement loop.")
        cells = cycle[:-1]
        signs = [direction if k % 2 == 0 else -direction for k in range(len(cells))]
        rooms = [_room(x[i][j], upper[i][j], s) for (i, j), s in zip(cells, signs)]
        theta = min(rooms)
        leaving = rooms.index(theta)

        for (i, j), s in zip(cells, signs):
            x[i][j] += s * theta
        if leaving != 0:
            basis.remove(cells[leaving])
            basis.add(entering)

    raise RuntimeError(f"MODI reached max_iterations={max_iterations} before proving optimality.")


def modi_method(
    initial_allocation, supply, demand, cost_matrix,
    closed_routes=(), route_capacities=None
):
    """Validate the VAM initial solution, then optimize with route restrictions."""
    initial = deepcopy(initial_allocation)

    valid, message = validate_allocation(
        initial, supply, demand, closed_routes, route_capacities
    )

    initial_cost = calculate_cost(initial, cost_matrix)

    result = None
    if valid:
        try:
            result = modi_optimize(
                supply, demand, cost_matrix, initial,
                closed_routes, route_capacities
            )
        except NotBasicSolution:
            result = None

    if result is None:
        result = solve_constrained_transport(
            supply, demand, cost_matrix,
            closed_routes, route_capacities
        )

    result["initial_cost"] = initial_cost
    result["improvement"] = initial_cost - result["cost"]
    result["initial_feasible"] = valid
    result["initial_validation_message"] = message

    return result
