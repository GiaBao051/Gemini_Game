# maze.py
from __future__ import annotations
import random
from typing import List, Tuple, Set, Optional

Grid = List[List[int]]

# Tile codes
T_WALL = 1
T_FLOOR = 0
T_QUIZ = 2


def generate_maze(w: int, h: int, seed: int) -> Grid:
    """Randomized DFS maze on odd-dimension grid. Walls=1, Floors=0."""
    rnd = random.Random(seed)
    grid: Grid = [[T_WALL for _ in range(w)] for _ in range(h)]

    def carve(x: int, y: int):
        grid[y][x] = T_FLOOR
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        rnd.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < w - 1 and 1 <= ny < h - 1 and grid[ny][nx] == T_WALL:
                grid[y + dy // 2][x + dx // 2] = T_FLOOR
                carve(nx, ny)

    carve(1, 1)
    return grid


def mutate_maze_for_return(grid: Grid, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Grid:
    """Carve a Manhattan corridor from from_pos to to_pos + small random toggles. Keeps QUIZ tiles."""
    new = [row[:] for row in grid]
    fx, fy = from_pos
    tx, ty = to_pos

    x, y = fx, fy
    while x != tx:
        if new[y][x] != T_QUIZ:
            new[y][x] = T_FLOOR
        x += 1 if tx > x else -1
        if new[y][x] != T_QUIZ:
            new[y][x] = T_FLOOR

    while y != ty:
        if new[y][x] != T_QUIZ:
            new[y][x] = T_FLOOR
        y += 1 if ty > y else -1
        if new[y][x] != T_QUIZ:
            new[y][x] = T_FLOOR

    rnd = random.Random()
    h = len(new)
    w = len(new[0])
    for _ in range(60):
        rx = rnd.randint(1, w - 2)
        ry = rnd.randint(1, h - 2)
        if (rx, ry) in [(fx, fy), (tx, ty)]:
            continue
        if new[ry][rx] == T_QUIZ:
            continue
        if new[ry][rx] == T_WALL:
            new[ry][rx] = T_FLOOR
        elif new[ry][rx] == T_FLOOR and rnd.random() < 0.15:
            new[ry][rx] = T_WALL

    return new


def mutate_obstacles_dynamic(
    grid: Grid,
    protected: Set[Tuple[int, int]],
    flips: int = 18,
    seed: Optional[int] = None,
) -> Grid:
    """
    Continuously-changing obstacles:
    - Randomly flip some floor<->wall tiles (never QUIZ, never border, never protected).
    - Caller should validate connectivity before accepting.
    """
    rnd = random.Random(seed)
    new = [row[:] for row in grid]
    h = len(new)
    w = len(new[0])

    floors = []
    walls = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if (x, y) in protected:
                continue
            if new[y][x] == T_QUIZ:
                continue
            if new[y][x] == T_FLOOR:
                floors.append((x, y))
            elif new[y][x] == T_WALL:
                walls.append((x, y))

    rnd.shuffle(floors)
    rnd.shuffle(walls)

    open_n = min(len(walls), flips // 2)
    close_n = min(len(floors), flips - open_n)

    for i in range(open_n):
        x, y = walls[i]
        new[y][x] = T_FLOOR

    for i in range(close_n):
        x, y = floors[i]
        new[y][x] = T_WALL

    return new
