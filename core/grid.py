# core/grid.py
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple

FLOOR = 0
WALL = 1
EXIT = 2

Tile = int
Pos = Tuple[int, int]


@dataclass
class Grid:
    tiles: List[List[Tile]]

    @property
    def rows(self) -> int:
        return len(self.tiles)

    @property
    def cols(self) -> int:
        return len(self.tiles[0]) if self.tiles else 0

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get(self, r: int, c: int) -> Tile:
        return self.tiles[r][c]

    def set(self, r: int, c: int, t: Tile) -> None:
        self.tiles[r][c] = t

    def is_walkable(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.get(r, c) != WALL

    def all_cells_of_type(self, t: Tile) -> List[Pos]:
        out: List[Pos] = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.tiles[r][c] == t:
                    out.append((r, c))
        return out

    def place_random_exits(self, n: int = 2, seed: int | None = None) -> None:
        """Place N exits on random FLOOR cells (for now: no distance constraints)."""
        rng = random.Random(seed)
        floors = self.all_cells_of_type(FLOOR)
        rng.shuffle(floors)

        # remove existing exits first (optional)
        for (r, c) in self.all_cells_of_type(EXIT):
            self.set(r, c, FLOOR)

        for i in range(min(n, len(floors))):
            r, c = floors[i]
            self.set(r, c, EXIT)

    @classmethod
    def from_ascii(cls, rows: List[str]) -> "Grid":
        """
        Map format (8 chars each row):
        '.' = FLOOR
        '#' = WALL
        'E' = EXIT (optional)
        """
        tiles: List[List[Tile]] = []
        for line in rows:
            line = line.strip()
            row_tiles: List[Tile] = []
            for ch in line:
                if ch == '#':
                    row_tiles.append(WALL)
                elif ch == 'E':
                    row_tiles.append(EXIT)
                else:
                    row_tiles.append(FLOOR)
            tiles.append(row_tiles)
        return cls(tiles)
