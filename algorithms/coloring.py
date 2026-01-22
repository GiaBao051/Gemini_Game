# algorithms/coloring.py
from __future__ import annotations
from typing import Dict, List, Tuple, Set
from .csp_placement import bfs_dist, INF

Vec = Tuple[int, int]

def build_quiz_graph(grid: List[List[int]], quiz_positions: List[Vec], radius: int = 7) -> Dict[int, Set[int]]:
    """
    Node i corresponds to quiz_positions[i]
    Edge if BFS distance <= radius
    """
    adj: Dict[int, Set[int]] = {i: set() for i in range(len(quiz_positions))}
    # Precompute BFS dist from each quiz position (q small => acceptable)
    dists = []
    for pos in quiz_positions:
        dists.append(bfs_dist(grid, pos))

    for i in range(len(quiz_positions)):
        for j in range(i+1, len(quiz_positions)):
            pj = quiz_positions[j]
            dij = dists[i][pj[1]][pj[0]]
            if dij < INF and dij <= radius:
                adj[i].add(j)
                adj[j].add(i)
    return adj

def greedy_coloring(adj: Dict[int, Set[int]]) -> Dict[int, int]:
    color: Dict[int, int] = {}
    nodes = sorted(adj.keys(), key=lambda x: len(adj[x]), reverse=True)
    for u in nodes:
        used = {color[v] for v in adj[u] if v in color}
        c = 0
        while c in used:
            c += 1
        color[u] = c
    return color
