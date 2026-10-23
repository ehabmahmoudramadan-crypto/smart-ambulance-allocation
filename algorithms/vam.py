"""Vogel's Approximation Method (VAM) for an initial transportation solution."""
from typing import List, Dict, Any


def _validate(supply, demand, cost_matrix):
    if not supply or not demand:
        raise ValueError("Supply and demand must not be empty.")
    if len(cost_matrix) != len(supply) or any(len(row) != len(demand) for row in cost_matrix):
        raise ValueError("Cost matrix dimensions must match supply and demand.")
    values = list(supply) + list(demand) + [v for row in cost_matrix for v in row]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in values):
        raise ValueError("Supply, demand, and costs must be non-negative numbers.")
    if sum(supply) != sum(demand):
        raise ValueError("Problem is unbalanced: total supply must equal total demand.")


def vogel_approximation(supply, demand, cost_matrix) -> Dict[str, Any]:
    """Return {'allocation': matrix, 'total_cost': number, 'steps': [...]}.

    This implementation expects a balanced problem. Ties are resolved
    deterministically by choosing the lowest-index eligible row/column.
    """
    _validate(supply, demand, cost_matrix)
    supply_left = list(supply)
    demand_left = list(demand)
    costs = [list(row) for row in cost_matrix]
    m, n = len(supply_left), len(demand_left)
    allocation = [[0 for _ in range(n)] for _ in range(m)]
    active_rows = {i for i, value in enumerate(supply_left) if value > 0}
    active_cols = {j for j, value in enumerate(demand_left) if value > 0}
    steps = []

    def penalty(values):
        ordered = sorted(values)
        return ordered[1] - ordered[0] if len(ordered) >= 2 else ordered[0] if ordered else -1

    while active_rows and active_cols:
        candidates = []
        for i in sorted(active_rows):
            p = penalty([costs[i][j] for j in active_cols])
            cheapest = min(active_cols, key=lambda j: (costs[i][j], j))
            candidates.append((p, -costs[i][cheapest], 1, -i, i, cheapest))
        for j in sorted(active_cols):
            p = penalty([costs[i][j] for i in active_rows])
            cheapest = min(active_rows, key=lambda i: (costs[i][j], i))
            candidates.append((p, -costs[cheapest][j], 0, -j, cheapest, j))
        _, _, _, _, i, j = max(candidates)
        quantity = min(supply_left[i], demand_left[j])
        allocation[i][j] += quantity
        supply_left[i] -= quantity
        demand_left[j] -= quantity
        steps.append({"row": i, "column": j, "quantity": quantity, "unit_cost": costs[i][j]})
        if supply_left[i] == 0:
            active_rows.discard(i)
        if demand_left[j] == 0:
            active_cols.discard(j)

    total_cost = sum(allocation[i][j] * costs[i][j] for i in range(m) for j in range(n))
    return {"allocation": allocation, "total_cost": total_cost, "steps": steps}


# Friendly alias for integration with existing naming conventions.
def solve_vam(supply, demand, cost_matrix):
    result = vogel_approximation(supply, demand, cost_matrix)
    return result["allocation"], result["total_cost"]
