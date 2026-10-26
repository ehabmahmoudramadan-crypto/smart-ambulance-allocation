"""MODI (u-v method) - optimises a basic feasible solution.

The basis is kept as a spanning tree of the bipartite graph (m + n - 1 cells,
zero-flow cells allowed), so degenerate solutions need no special-casing.
"""
from collections import deque


def _complete_basis(x, cost):
    """Add zero-flow cells until the basic cells form a spanning tree."""
    m, n = len(x), len(x[0])
    parent = list(range(m + n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    basis = set()
    for i in range(m):
        for j in range(n):
            if x[i][j] > 0:
                basis.add((i, j))
                parent[find(i)] = find(m + j)
    extra = sorted(((cost[i][j], i, j) for i in range(m) for j in range(n)
                    if (i, j) not in basis))
    for _, i, j in extra:
        if len(basis) == m + n - 1:
            break
        if find(i) != find(m + j):
            basis.add((i, j))
            parent[find(i)] = find(m + j)
    return basis


def _potentials(basis, cost, m, n):
    adj = {k: [] for k in range(m + n)}
    for i, j in basis:
        adj[i].append(m + j)
        adj[m + j].append(i)
    u, v = [None] * m, [None] * n
    u[0] = 0
    q = deque([0])
    while q:
        a = q.popleft()
        for b in adj[a]:
            if a < m and v[b - m] is None:
                v[b - m] = cost[a][b - m] - u[a]
                q.append(b)
            elif a >= m and u[b] is None:
                u[b] = cost[b][a - m] - v[a - m]
                q.append(b)
    return u, v, adj


def _tree_path(adj, start, goal):
    prev = {start: None}
    q = deque([start])
    while q:
        a = q.popleft()
        if a == goal:
            break
        for b in adj[a]:
            if b not in prev:
                prev[b] = a
                q.append(b)
    path, a = [], goal
    while a is not None:
        path.append(a)
        a = prev[a]
    return path[::-1]


def modi_optimize(supply, demand, cost, allocation, max_iterations=10000):
    m, n = len(supply), len(demand)
    x = [row[:] for row in allocation]
    basis = _complete_basis(x, cost)
    iterations = 0

    while True:
        u, v, adj = _potentials(basis, cost, m, n)
        entering, best = None, 0
        for i in range(m):
            for j in range(n):
                if (i, j) in basis:
                    continue
                r = cost[i][j] - u[i] - v[j]
                if r < best:
                    best, entering = r, (i, j)
        if entering is None:
            break
        if iterations >= max_iterations:
            raise RuntimeError("MODI exceeded max_iterations")

        i0, j0 = entering
        path = _tree_path(adj, i0, m + j0)      # row i0 ... column j0
        edges = []
        for a, b in zip(path, path[1:]):
            edges.append((a, b - m) if a < m else (b, a - m))
        minus = edges[0::2]                      # edges next to i0 lose flow
        plus = edges[1::2]
        theta = min(x[i][j] for i, j in minus)
        for i, j in minus:
            x[i][j] -= theta
        for i, j in plus:
            x[i][j] += theta
        x[i0][j0] += theta
        leaving = min((e for e in minus if x[e[0]][e[1]] == 0),
                      key=lambda e: (cost[e[0]][e[1]], e))
        basis.discard(leaving)
        basis.add(entering)
        iterations += 1

    total = sum(x[i][j] * cost[i][j] for i in range(m) for j in range(n))
    return {"allocation": x, "total_cost": total, "iterations": iterations}
