# core/spawn.py
from __future__ import annotations
import random
from typing import List, Tuple, Optional, Dict

from core.grid import Grid, FLOOR, WALL, EXIT

Pos = Tuple[int, int]


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def spawn_match(
    grid: Grid,
    seed: Optional[int] = None,
    exits_n: int = 2,
    min_rg: int = 4,            # BirSreshtha-Rajakar distance
    min_thief_exit: int = 4,    # thief to each exit
    min_birsreshtha_exit: int = 8,    # BirSreshtha to each exit (your constraint)
    min_exit_exit: int = 8,     # exit-exit distance
    attempts: int = 8000,
) -> Dict[str, object]:
    """
    Returns:
      {
        "rajakar": (r,c),
                "birsreshtha": (r,c),
        "exits": [(r,c), (r,c)]
      }
    Tries hard with strict constraints. Raises ValueError if impossible.
    """
    rng = random.Random(seed)

    floors: List[Pos] = []
    for r in range(grid.rows):
        for c in range(grid.cols):
            if grid.get(r, c) == FLOOR:
                floors.append((r, c))

    if len(floors) < 10:
        raise ValueError("Maze has too few FLOOR cells to spawn fairly.")

    for _ in range(attempts):
        # --- pick Rajakar + BirSreshtha ---
        raj = rng.choice(floors)
        birsreshtha = rng.choice(floors)
        if birsreshtha == raj:
            continue
        if manhattan(birsreshtha, raj) < min_rg:
            continue

        # --- pick exits ---
        # candidates must be FLOOR and not on players
        candidates = [p for p in floors if p != raj and p != birsreshtha]

        # filter by thief-exit and BirSreshtha-exit distances
        candidates = [
            p for p in candidates
            if manhattan(p, raj) >= min_thief_exit and manhattan(p, birsreshtha) >= min_birsreshtha_exit
        ]
        if len(candidates) < exits_n:
            continue

        rng.shuffle(candidates)

        exits: List[Pos] = []
        for p in candidates:
            if not exits:
                exits.append(p)
            else:
                # keep far from existing exits
                if all(manhattan(p, e) >= min_exit_exit for e in exits):
                    exits.append(p)
            if len(exits) == exits_n:
                break

        if len(exits) != exits_n:
            continue

        return {"rajakar": raj, "birsreshtha": birsreshtha, "exits": exits}

    raise ValueError(
        "Failed to spawn with constraints. Try a more open maze or reduce min distances.")
