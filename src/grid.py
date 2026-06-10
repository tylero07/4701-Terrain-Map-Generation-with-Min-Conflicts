# grid.py
# Grid initialization and conflict detection

import random
import numpy as np
from terrain import TERRAINS, ELEVATION, COMPATIBLE, NUM_TERRAINS

# Neighbor offsets
NEIGHBORS_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
NEIGHBORS_8 = [(-1, 0), (1, 0), (0, -1), (0, 1),
               (-1, -1), (-1, 1), (1, -1), (1, 1)]


def random_grid(rows: int, cols: int) -> np.ndarray:
    """Create a grid with uniformly random terrain assignments (as elevation indices)."""
    return np.random.randint(0, NUM_TERRAINS, size=(rows, cols), dtype=np.int8)


def get_neighbors(r: int, c: int, rows: int, cols: int, diagonals: bool) -> list:
    """Return valid (row, col) neighbor positions for a cell."""
    offsets = NEIGHBORS_8 if diagonals else NEIGHBORS_4
    neighbors = []
    for dr, dc in offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            neighbors.append((nr, nc))
    return neighbors


def cell_conflicts(grid: np.ndarray, r: int, c: int,
                   rows: int, cols: int, diagonals: bool) -> int:
    """Count the number of neighbors that conflict with cell (r, c)."""
    val = grid[r, c]
    count = 0
    for nr, nc in get_neighbors(r, c, rows, cols, diagonals):
        if not COMPATIBLE[val][grid[nr, nc]]:
            count += 1
    return count


def cell_conflicts_if(grid: np.ndarray, r: int, c: int,
                      rows: int, cols: int, diagonals: bool, value: int) -> int:
    """Count conflicts cell (r, c) would have if assigned `value`."""
    count = 0
    for nr, nc in get_neighbors(r, c, rows, cols, diagonals):
        if not COMPATIBLE[value][grid[nr, nc]]:
            count += 1
    return count


def find_conflicted_cells(grid: np.ndarray, rows: int, cols: int,
                          diagonals: bool) -> list:
    """Return list of (r, c) for all cells with at least one conflict."""
    conflicted = []
    for r in range(rows):
        for c in range(cols):
            if cell_conflicts(grid, r, c, rows, cols, diagonals) > 0:
                conflicted.append((r, c))
    return conflicted


def total_conflicts(grid: np.ndarray, rows: int, cols: int, diagonals: bool) -> int:
    """Count total conflicting edges (each edge counted once)."""
    count = 0
    # Only check right and down neighbors to avoid double-counting
    for r in range(rows):
        for c in range(cols):
            val = grid[r, c]
            if c + 1 < cols and not COMPATIBLE[val][grid[r, c + 1]]:
                count += 1
            if r + 1 < rows and not COMPATIBLE[val][grid[r + 1, c]]:
                count += 1
            if diagonals:
                if r + 1 < rows and c + 1 < cols and not COMPATIBLE[val][grid[r + 1, c + 1]]:
                    count += 1
                if r + 1 < rows and c - 1 >= 0 and not COMPATIBLE[val][grid[r + 1, c - 1]]:
                    count += 1
    return count
