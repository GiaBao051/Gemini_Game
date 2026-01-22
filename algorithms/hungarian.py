# algorithms/hungarian.py
from __future__ import annotations
from typing import List, Tuple

def hungarian(cost: List[List[int]]) -> Tuple[int, List[int]]:
    """
    Solve min-cost assignment for a square matrix cost (n x n).
    Returns (min_cost, assignment) where assignment[i] = j.
    """
    n = len(cost)
    u = [0]*(n+1)
    v = [0]*(n+1)
    p = [0]*(n+1)
    way = [0]*(n+1)

    for i in range(1, n+1):
        p[0] = i
        j0 = 0
        minv = [10**18]*(n+1)
        used = [False]*(n+1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = 10**18
            j1 = 0
            for j in range(1, n+1):
                if not used[j]:
                    cur = cost[i0-1][j-1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, n+1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignment = [-1]*n
    for j in range(1, n+1):
        assignment[p[j]-1] = j-1
    min_cost = -v[0]
    return min_cost, assignment

def pad_to_square(cost: List[List[int]], pad_value: int = 10**6) -> List[List[int]]:
    r = len(cost)
    c = len(cost[0]) if r else 0
    n = max(r, c)
    out = [[pad_value]*n for _ in range(n)]
    for i in range(r):
        for j in range(c):
            out[i][j] = cost[i][j]
    return out
