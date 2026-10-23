"""MODI (u-v) transportation optimizer with degeneracy handling."""
from collections import deque
from typing import Dict, Any


def _validate(supply, demand, cost_matrix, allocation):
    m, n = len(supply), len(demand)
    if not m or not n or len(cost_matrix) != m or len(allocation) != m:
        raise ValueError("Invalid matrix dimensions.")
    if any(len(row) != n for row in cost_matrix) or any(len(row) != n for row in allocation):
        raise ValueError("Cost and allocation matrices must match supply/demand dimensions.")
    if sum(supply) != sum(demand):
        raise ValueError("Problem is unbalanced: total supply must equal total demand.")
    if any(v < 0 for v in supply + demand):
        raise ValueError("Supply and demand must be non-negative.")
    if any(v < 0 for row in cost_matrix for v in row):
        raise ValueError("Costs must be non-negative.")
    if any(v < 0 for row in allocation for v in row):
        raise ValueError("Allocations must be non-negative.")
    if [sum(row) for row in allocation] != list(supply):
        raise ValueError("Initial allocation row totals do not match supply.")
    if [sum(allocation[i][j] for i in range(m)) for j in range(n)] != list(demand):
        raise ValueError("Initial allocation column totals do not match demand.")


def _find_cycle(basis, start, m, n):
    """Find a rectangular +/- cycle through start and basis cells."""
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

    # Start horizontally, then vertically; cycle alternates row/column moves.
    return dfs(start, True, [start]) or dfs(start, False, [start])


def modi_optimize(supply, demand, cost_matrix, initial_allocation, max_iterations=1000) -> Dict[str, Any]:
    """Optimize allocation; returns allocation, total_cost, iterations, is_optimal, potentials, reduced_costs.

    Zero allocations are added to the basis as epsilon cells when needed.
    For this project's small matrices, cycle search is exhaustive and deterministic.
    """
    _validate(supply, demand, cost_matrix, initial_allocation)
    m, n = len(supply), len(demand)
    x = [list(map(float, row)) for row in initial_allocation]
    costs = [list(map(float, row)) for row in cost_matrix]
    basis = {(i, j) for i in range(m) for j in range(n) if x[i][j] > 0}

    # Complete a spanning-tree basis with zero (epsilon) cells, avoiding cycles.
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
    for i, j in sorted(basis):
        union(i, m + j)
    for i in range(m):
        for j in range(n):
            if len(basis) >= m + n - 1:
                break
            if (i, j) not in basis and union(i, m + j):
                basis.add((i, j))

    iterations = 0
    while iterations < max_iterations:
        # Solve u_i + v_j = c_ij for basic cells.
        u, v = [None] * m, [None] * n
        u[0] = 0.0
        changed = True
        while changed:
            changed = False
            for i, j in basis:
                if u[i] is not None and v[j] is None:
                    v[j] = costs[i][j] - u[i]; changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = costs[i][j] - v[j]; changed = True
        # Normally connected after basis completion; safeguard disconnected components.
        for i in range(m):
            if u[i] is None:
                u[i] = 0.0
                changed = True
                while changed:
                    changed = False
                    for r, c in basis:
                        if u[r] is not None and v[c] is None:
                            v[c] = costs[r][c] - u[r]; changed = True
                        elif v[c] is not None and u[r] is None:
                            u[r] = costs[r][c] - v[c]; changed = True
        reduced = [[costs[i][j] - u[i] - v[j] for j in range(n)] for i in range(m)]
        entering = [(reduced[i][j], i, j) for i in range(m) for j in range(n) if (i, j) not in basis and reduced[i][j] < -1e-9]
        if not entering:
            total = sum(x[i][j] * costs[i][j] for i in range(m) for j in range(n))
            out = [[int(round(val)) if abs(val-round(val)) < 1e-9 else val for val in row] for row in x]
            return {"allocation": out, "total_cost": total, "iterations": iterations, "is_optimal": True,
                    "potentials_u": u, "potentials_v": v, "reduced_costs": reduced}
        _, ei, ej = min(entering)  # most negative reduced cost
        cycle = _find_cycle(basis, (ei, ej), m, n)
        if not cycle:
            raise RuntimeError("Could not construct a MODI improvement loop; basis may be invalid.")
        # Cycle returned includes start at end. Signs + - + - ...
        cycle_cells = cycle[:-1]
        minus_cells = cycle_cells[1::2]
        theta = min(x[i][j] for i, j in minus_cells)
        for k, (i, j) in enumerate(cycle_cells):
            x[i][j] += theta if k % 2 == 0 else -theta
            if abs(x[i][j]) < 1e-9:
                x[i][j] = 0.0
        basis.add((ei, ej))
        # Remove one zero minus cell to keep a tree basis (deterministic tie break).
        zero_minus = sorted((i, j) for i, j in minus_cells if abs(x[i][j]) < 1e-9)
        if zero_minus:
            basis.remove(zero_minus[0])
        iterations += 1
    raise RuntimeError(f"MODI reached max_iterations={max_iterations} before proving optimality.")


def solve_modi(supply, demand, cost_matrix, initial_allocation):
    result = modi_optimize(supply, demand, cost_matrix, initial_allocation)
    return result["allocation"], result["total_cost"]

