"""Vogel's Approximation Method (VAM) - initial basic feasible solution.

Works on a balanced transportation problem. Big-M costs are treated like any
other cost (the large penalty naturally makes VAM avoid those cells); the
reported cost is always computed from the real cost matrix.
"""


def vogel_approximation(supply, demand, cost):
    m, n = len(supply), len(demand)
    if sum(supply) != sum(demand):
        raise ValueError("Problem must be balanced (sum(supply) == sum(demand)).")

    s, d = list(supply), list(demand)
    x = [[0] * n for _ in range(m)]
    rows, cols = set(range(m)), set(range(n))
    steps = []

    def penalty(costs):
        c = sorted(costs)
        return (c[1] - c[0]) if len(c) > 1 else c[0]

    while rows and cols:
        row_pen = {i: penalty([cost[i][j] for j in cols]) for i in rows}
        col_pen = {j: penalty([cost[i][j] for i in rows]) for j in cols}
        best_r = max(row_pen.items(), key=lambda kv: (kv[1], -kv[0]))
        best_c = max(col_pen.items(), key=lambda kv: (kv[1], -kv[0]))

        if best_r[1] >= best_c[1]:
            i = best_r[0]
            j = min(cols, key=lambda j: (cost[i][j], j))
        else:
            j = best_c[0]
            i = min(rows, key=lambda i: (cost[i][j], i))

        q = min(s[i], d[j])
        x[i][j] += q
        s[i] -= q
        d[j] -= q
        steps.append({"cell": (i, j), "qty": q})

        # remove exactly one line per step so degenerate cases keep going
        if s[i] == 0 and (d[j] > 0 or len(rows) > 1):
            rows.discard(i)
        else:
            cols.discard(j)

    total = sum(x[i][j] * cost[i][j] for i in range(m) for j in range(n))
    return {"allocation": x, "total_cost": total, "steps": steps}
