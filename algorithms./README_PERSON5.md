# Person 5 — VAM initial solution

## Deliverable
`vam.py` implements Vogel’s Approximation Method and has no third-party dependencies.

## Function contract
```python
from vam import vogel_approximation
result = vogel_approximation(supply, demand, cost_matrix)
allocation = result["allocation"]
initial_cost = result["total_cost"]
steps = result["steps"]
```
`solve_vam(supply, demand, cost_matrix)` is also available and returns `(allocation, total_cost)`.

## Team test data (synthetic)
```python
supply = [8, 6, 7, 9]
demand = [5, 7, 6, 6, 6]
cost_matrix = [[24,45,37,18,19], [28,36,37,13,23], [45,39,31,42,15], [26,42,19,19,18]]
```
Expected initial cost: **702**. Row totals must equal supply and column totals must equal demand.

## Run
From this folder: `python -m unittest discover -s tests -v`

Costs are synthetic travel-time estimates; total cost is allocation-weighted, not average response time.
