"""Problem definition: constraints + conversion to a plain transportation problem.

Constraints (single source of truth - the simulation must import these too):
  * closed road  (i -> j):      x[i][j] = 0   -> cost = BIG_M on that cell
  * route capacity (i -> j) <= k: split station i into two rows
        row "a": supply = k,        normal costs
        row "b": supply = s_i - k,  cost to j = BIG_M
    VAM and MODI then run unchanged, and the optimum is exact.
"""
import json
from pathlib import Path

from algorithms.vam import vogel_approximation
from algorithms.modi import modi_optimize

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "data.json"


def load_dataset(path=DEFAULT_DATA):
    with open(path, encoding="utf-8") as f:
        ds = json.load(f)
    idx_s = {n: k for k, n in enumerate(ds["stations"])}
    idx_a = {n: k for k, n in enumerate(ds["areas"])}
    cons = ds["constraints"]
    closed = [(idx_s[c["from"]], idx_a[c["to"]]) for c in cons.get("closed_roads", [])]
    caps = [(idx_s[c["from"]], idx_a[c["to"]], c["max"]) for c in cons.get("route_capacities", [])]
    return ds, closed, caps


def build_problem(supply, demand, cost, closed=(), caps=()):
    """Return (supply2, cost2, row_owner, big_m) for the expanded problem."""
    big_m = (max(max(r) for r in cost) + 1) * sum(supply) + 1
    cost2 = [r[:] for r in cost]
    for i, j in closed:
        cost2[i][j] = big_m

    cap_of = {}
    for i, j, k in caps:
        if i in cap_of:
            raise ValueError("Only one capacity constraint per station is supported.")
        cap_of[i] = (j, k)

    supply2, rows, owner = [], [], []
    for i, s in enumerate(supply):
        if i in cap_of and cap_of[i][1] < s:
            j, k = cap_of[i]
            supply2 += [k, s - k]
            rows += [cost2[i][:], cost2[i][:]]
            rows[-1][j] = big_m
            owner += [i, i]
        else:
            supply2.append(s)
            rows.append(cost2[i][:])
            owner.append(i)
    return supply2, rows, owner, big_m


def merge_rows(x2, owner, m, n):
    x = [[0] * n for _ in range(m)]
    for r, i in enumerate(owner):
        for j in range(n):
            x[i][j] += x2[r][j]
    return x


def plan_cost(x, cost):
    return sum(x[i][j] * cost[i][j] for i in range(len(x)) for j in range(len(x[0])))


def check_plan(x, supply, demand, closed=(), caps=()):
    """Raise if the plan breaks supply, demand or either constraint."""
    m, n = len(supply), len(demand)
    assert all(sum(x[i]) == supply[i] for i in range(m)), "supply violated"
    assert all(sum(x[i][j] for i in range(m)) == demand[j] for j in range(n)), "demand violated"
    for i, j in closed:
        assert x[i][j] == 0, f"closed road {i}->{j} used"
    for i, j, k in caps:
        assert x[i][j] <= k, f"capacity {i}->{j} exceeded"


def solve(supply, demand, cost, closed=(), caps=()):
    m, n = len(supply), len(demand)
    s2, c2, owner, big_m = build_problem(supply, demand, cost, closed, caps)

    v = vogel_approximation(s2, demand, c2)
    o = modi_optimize(s2, demand, c2, v["allocation"])

    x_init = merge_rows(v["allocation"], owner, m, n)
    x_opt = merge_rows(o["allocation"], owner, m, n)
    check_plan(x_opt, supply, demand, closed, caps)   # real, original constraints

    return {
        "initial": {"allocation": x_init, "cost": plan_cost(x_init, cost)},
        "optimal": {"allocation": x_opt, "cost": plan_cost(x_opt, cost),
                    "iterations": o["iterations"]},
    }


if __name__ == "__main__":          # python -m optimization.model
    ds, closed, caps = load_dataset()
    r = solve(ds["supply"], ds["demand"], ds["cost_matrix"], closed, caps)
    cur = plan_cost(ds["current_allocation"], ds["cost_matrix"])
    opt = r["optimal"]["cost"]
    print("VAM cost     :", r["initial"]["cost"])
    print("MODI cost    :", opt, f"({r['optimal']['iterations']} iterations)")
    print("current cost :", cur)
    print("saving       :", cur - opt, f"({100 * (cur - opt) / cur:.1f}%)")
