# core/rules.py
from __future__ import annotations
from typing import List, Tuple
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


def in_power_scan(viewer: Pos, target: Pos, radius: int) -> bool:
    """Power scan in 8 directions (orthogonal + diagonal), ignores walls."""
    vr, vc = viewer
    tr, tc = target
    same_row = vr == tr and abs(vc - tc) <= radius
    same_col = vc == tc and abs(vr - tr) <= radius
    same_diag = abs(vr - tr) == abs(vc - tc) and abs(vr - tr) <= radius
    return same_row or same_col or same_diag


def power_scan_cells(grid: Grid, viewer: Pos, radius: int) -> List[Pos]:
    """Cells highlighted by power scan: orthogonal + diagonal rays."""
    vr, vc = viewer
    cells: List[Pos] = [(vr, vc)]
    for step in range(1, radius + 1):
        for dr, dc in (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ):
            nr, nc = vr + dr * step, vc + dc * step
            if grid.in_bounds(nr, nc):
                cells.append((nr, nc))
    return cells


def in_orthogonal_range(viewer: Pos, target: Pos, rng: int) -> bool:
    """Orthogonal range check that ignores walls."""
    vr, vc = viewer
    tr, tc = target
    if vr == tr:
        return abs(vc - tc) <= rng
    if vc == tc:
        return abs(vr - tr) <= rng
    return False


def in_directional_sight(grid: Grid, viewer: Pos, target: Pos, facing: Tuple[int, int], rng: int) -> bool:
    """
    Check if target is visible in the direction the viewer is facing.
    facing is (dr, dc) like (-1, 0) for up, (1, 0) for down, (0, -1) for left, (0, 1) for right.
    Sight stops at WALL.
    """
    if facing == (0, 0):  # Not facing any direction
        return False
    
    vr, vc = viewer
    tr, tc = target
    dr, dc = facing
    
    # Check if target is in the correct direction
    if dr != 0:  # Facing up or down
        if vc != tc:  # Target must be in same column
            return False
        if dr > 0 and tr <= vr:  # Facing down but target is above/same
            return False
        if dr < 0 and tr >= vr:  # Facing up but target is below/same
            return False
        dist = abs(tr - vr)
    elif dc != 0:  # Facing left or right
        if vr != tr:  # Target must be in same row
            return False
        if dc > 0 and tc <= vc:  # Facing right but target is left/same
            return False
        if dc < 0 and tc >= vc:  # Facing left but target is right/same
            return False
        dist = abs(tc - vc)
    else:
        return False
    
    if dist == 0 or dist > rng:
        return False
    
    # Check for walls blocking the view
    step_r = dr if dr != 0 else 0
    step_c = dc if dc != 0 else 0
    
    for step in range(1, dist + 1):
        check_r = vr + step_r * step
        check_c = vc + step_c * step
        if not grid.in_bounds(check_r, check_c):
            return False
        if grid.get(check_r, check_c) == WALL:
            return False
    
    return True
