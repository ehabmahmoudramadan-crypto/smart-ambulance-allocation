from typing import List, Dict, Any, Tuple

CLOSED_ROADS = [("S1", "A2")]
WEIGHT_LIMITS = {("S2", "A1"): 2.0}
AMBULANCE_WEIGHT = 2.5
BIG_M = 999999


def get_constrained_cost_matrix(cost_matrix: List[List[float]]) -> List[List[float]]:
    stations = ["S1", "S2", "S3", "S4"]
    destinations = ["A1", "A2", "A3", "A4", "A5"]
    constrained_matrix = [row[:] for row in cost_matrix]
    
    for st, dest in CLOSED_ROADS:
        i = stations.index(st)
        j = destinations.index(dest)
        constrained_matrix[i][j] = BIG_M
        
    for (st, dest), max_w in WEIGHT_LIMITS.items():
        if AMBULANCE_WEIGHT > max_w:
            i = stations.index(st)
            j = destinations.index(dest)
            constrained_matrix[i][j] = BIG_M
            
    return constrained_matrix


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
    constrained_costs = get_constrained_cost_matrix(cost_matrix)
    _validate(supply, demand, constrained_costs)
    supply_left = list(supply)
    demand_left = list(demand)
    costs = [list(row) for row in constrained_costs]
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


def solve_vam(supply, demand, cost_matrix):
    result = vogel_approximation(supply, demand, cost_matrix)
    return result["allocation"], result["total_cost"]


if __name__ == "__main__":
    SUPPLY = [8, 6, 7, 9]
    DEMAND = [5, 7, 6, 6, 6]
    
    COST_MATRIX = [
        [24, 45, 37, 18, 19],
        [28, 36, 37, 13, 23],
        [45, 39, 31, 42, 15],
        [26, 42, 19, 19, 18]
    ]

    allocation, total_cost = solve_vam(SUPPLY, DEMAND, COST_MATRIX)
    
    print("Constrained Cost Matrix:")
    for row in get_constrained_cost_matrix(COST_MATRIX):
        print(row)
        
    print("\nOptimal Allocation:")
    stations = ["S1", "S2", "S3", "S4"]
    destinations = ["A1", "A2", "A3", "A4", "A5"]
    
    print(f"{'':<6}" + "".join([f"{d:>6}" for d in destinations]))
    for idx, row in enumerate(allocation):
        print(f"{stations[idx]:<6}" + "".join([f"{val:>6}" for val in row]))
        
    print(f"\nTotal Cost: {total_cost}")
