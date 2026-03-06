# core/rules.py
from __future__ import annotations
from typing import Tuple
from core.grid import Grid, WALL

Pos = Tuple[int, int]


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def in_straight_sight(grid: Grid, viewer: Pos, target: Pos, rng: int) -> bool:
    """
    Viewer sees in 4 directions up/down/left/right up to rng cells.
    Sight stops at WALL.
    """
    vr, vc = viewer
    tr, tc = target

    # same row -> check left/right
    if vr == tr:
        step = 1 if tc > vc else -1
        dist = abs(tc - vc)
        if dist == 0 or dist > rng:
            return False
        for c in range(vc + step, tc + step, step):
            if not grid.in_bounds(vr, c):
                return False
            if grid.get(vr, c) == WALL:
                return False
        return True

    # same col -> check up/down
    if vc == tc:
        step = 1 if tr > vr else -1
        dist = abs(tr - vr)
        if dist == 0 or dist > rng:
            return False
        for r in range(vr + step, tr + step, step):
            if not grid.in_bounds(r, vc):
                return False
            if grid.get(r, vc) == WALL:
                return False
        return True

    return False


def heard_noise(listener: Pos, source: Pos, radius: int) -> bool:
    return manhattan(listener, source) <= radius
