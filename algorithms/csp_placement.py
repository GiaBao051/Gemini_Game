# algorithms/csp_placement.py
from __future__ import annotations
from collections import deque
import random
from typing import List, Tuple, Dict, Optional

Vec = Tuple[int, int]
INF = 10**9
T_WALL = 1

def bfs_dist(grid: List[List[int]], start: Vec) -> List[List[int]]:
    H, W = len(grid), len(grid[0])
    dist = [[INF]*W for _ in range(H)]
    q = deque([start])
    dist[start[1]][start[0]] = 0
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] != T_WALL and dist[ny][nx] == INF:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
    return dist

def manhattan(a: Vec, b: Vec) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def solve_csp_placement(
    grid: List[List[int]],
    floor_cells: List[Vec],
    start1: Vec,
    start2: Vec,
    quiz_count: int = 10,
    k_apart: int = 6,
    balance_tol: int = 6,
    seed: int = 1,
) -> Optional[Dict[str, Vec]]:
    """
    Returns dict with keys: S1, S2, T, Q0..Q{quiz_count-1}
    """
    rnd = random.Random(seed)

    d1 = bfs_dist(grid, start1)
    d2 = bfs_dist(grid, start2)

    # Candidate treasure cells: reachable & balanced
    treasure_domain = [
        p for p in floor_cells
        if d1[p[1]][p[0]] < INF and d2[p[1]][p[0]] < INF and abs(d1[p[1]][p[0]] - d2[p[1]][p[0]]) <= balance_tol
        and p != start1 and p != start2
    ]
    if not treasure_domain:
        return None

    # Quiz candidates: reachable from both starts, not start cells
    quiz_domain_base = [
        p for p in floor_cells
        if d1[p[1]][p[0]] < INF and d2[p[1]][p[0]] < INF and p != start1 and p != start2
    ]
    if len(quiz_domain_base) < quiz_count + 1:
        return None

    assignment: Dict[str, Vec] = {"S1": start1, "S2": start2}

    # Choose Treasure first
    rnd.shuffle(treasure_domain)

    def backtrack_quiz(i: int, quiz_positions: List[Vec]) -> bool:
        if i == quiz_count:
            for idx, pos in enumerate(quiz_positions):
                assignment[f"Q{idx}"] = pos
            return True

        # MRV-ish: filter candidates dynamically
        candidates = []
        for p in quiz_domain_base:
            if p == assignment["T"]:
                continue
            if p in quiz_positions:
                continue
            if manhattan(p, assignment["T"]) == 0:
                continue
            ok = True
            for qpos in quiz_positions:
                if manhattan(p, qpos) < k_apart:
                    ok = False
                    break
            if ok:
                candidates.append(p)

        rnd.shuffle(candidates)
        for p in candidates:
            quiz_positions.append(p)
            if backtrack_quiz(i+1, quiz_positions):
                return True
            quiz_positions.pop()
        return False

    for tpos in treasure_domain:
        assignment["T"] = tpos
        if backtrack_quiz(0, []):
            return assignment

    return None
