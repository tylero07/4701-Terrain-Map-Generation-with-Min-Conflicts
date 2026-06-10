"""
terrain_csp.py — Min-Conflicts CSP for terrain map generation
CS 4701, Assignment 3
"""

import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

"""Terrain Definitions"""

TERRAIN_CHARS  = ['W',       'B',      'L',        'F',      'H',      'M',         'V'      ]
TERRAIN_NAMES  = ['Water',   'Beach',  'Lowland',  'Forest', 'Hills',  'Mountains', 'Volcano']
TERRAIN_COLORS = ['#2166ac', '#f7e08a','#a6d96a',  '#1a9641','#8c510a','#d9d9d9',   '#d73027']
N_TERRAINS = 7

"""Precomputed 7X7 adjacency table — every lookup is O(1).
ADJACENT[i, j] = True  iff terrain i and j may be neighbours.
Uses abs(i-j) <= 1 across the elevation chain:
  W(0)-B(1)-L(2)-F(3)-H(4)-M(5)-V(6)
Volcano(6) is adjacent only to Mountains(5) and other Volcanoes(6).
"""
ADJACENT = np.array(
    [[abs(i - j) <= 1 for j in range(N_TERRAINS)] for i in range(N_TERRAINS)],
    dtype=bool,
)


class TerrainGrid:
    """
    Rectangular grid of terrain cells.

    Public state
    ------------
    grid[r, c]           np.int8    terrain index 0–5
    conflict_count[r, c] np.int16   number of this cell's neighbours it conflicts with
    conflicted           set        {(r, c)} for all cells where conflict_count > 0
    """
    def __init__(self, rows: int, cols: int, use_diagonals: bool = False):
        """Initializes the grid objects"""
        self.rows = rows 
        self.cols = cols
        self.use_diagonals = use_diagonals # 8 directions vs 5

        self.grid           = np.zeros((rows, cols), dtype=np.int8)
        self.conflict_count = np.zeros((rows, cols), dtype=np.int16)
        self.conflicted: set[tuple[int, int]] = set()

        # Precompute neighbour lists once; avoids repeated bounds-checking in the
        # inner loop.  Stored as nbrs[r][c] = [(nr0,nc0), (nr1,nc1), ...]
        self._nbrs = self._build_neighbor_lists()


    def _build_neighbor_lists(self) -> list:
        """Return nbrs[r][c] — list of valid (row, col) neighbours of each cell."""
        if self.use_diagonals:
            offsets = [(diagonal_row, diagonal_col) for diagonal_row in (-1, 0, 1) for diagonal_col in (-1, 0, 1)
                       if (diagonal_row, diagonal_col) != (0, 0)]           # 8 directions
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4 directions

        nbrs = [[[] for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                for diagonal_row, diagonal_col in offsets:
                    neighbor_row, neighbor_col = r + diagonal_row, c + diagonal_col
                    if 0 <= neighbor_row < self.rows and 0 <= neighbor_col < self.cols:
                        nbrs[r][c].append((neighbor_row, neighbor_col))
        return nbrs

    def initialize_random(self):
        """Assign a uniformly random terrain type to every cell, then compute conflicts."""
        self.grid = np.random.randint(0, N_TERRAINS, (self.rows, self.cols), dtype=np.int8)
        self._recompute_all_conflicts()

    def _recompute_all_conflicts(self):
        """Recompute conflict_count and conflicted from scratch. Used after initialization."""
        self.conflicted = set()
        for r in range(self.rows):
            for c in range(self.cols):
                t = int(self.grid[r, c])
                cc = sum(0 if ADJACENT[t, self.grid[neighbor_row, neighbor_col]] else 1
                         for neighbor_row, neighbor_col in self._nbrs[r][c])
                self.conflict_count[r, c] = cc
                if cc > 0:
                    self.conflicted.add((r, c))


    def _min_conflict_value(self, r: int, c: int) -> int:
        """
        Return the terrain index that results in the fewest constraint violations
        for cell (r, c) given its current neighbours.
        Ties are broken uniformly at random.
        """
        nbr_ts = [int(self.grid[neighbor_row, neighbor_col]) for neighbor_row, neighbor_col in self._nbrs[r][c]]

        if not nbr_ts:                         # isolated cell — any terrain is fine
            return random.randrange(N_TERRAINS)

        min_cc, best = len(nbr_ts) + 1, []
        for t in range(N_TERRAINS):
            cc = sum(1 for nt in nbr_ts if abs(nt - t) > 1)
            if cc < min_cc:
                min_cc, best = cc, [t]
            elif cc == min_cc:
                best.append(t)
        return random.choice(best)

    def _assign(self, r: int, c: int, new_t: int):
        """
        Assign terrain new_t to cell (r, c) and update conflict_count and
        self.conflicted incrementally — O(|neighbours|) per call.

        Key insight: only edges incident to (r, c) change when we reassign it.
        So we update each neighbour's conflict count by ±1 if that edge's
        conflict status flipped, then recount (r, c)'s own conflicts from scratch.
        """
        old_t = int(self.grid[r, c])
        if old_t == new_t:
            return

        self.grid[r, c] = new_t

        # Update each neighbour: only the edge connecting it to (r,c) changed.
        for neighbor_row, neighbor_col in self._nbrs[r][c]:
            nt = int(self.grid[neighbor_row, neighbor_col])
            was_conflict = not ADJACENT[old_t, nt]
            now_conflict = not ADJACENT[new_t, nt]
            if was_conflict != now_conflict:
                self.conflict_count[neighbor_row, neighbor_col] += 1 if now_conflict else -1
                if self.conflict_count[neighbor_row, neighbor_col] > 0:
                    self.conflicted.add((neighbor_row, neighbor_col))
                else:
                    self.conflicted.discard((neighbor_row, neighbor_col))

        # Recount (r, c) itself — its terrain changed, so all its edges need checking.
        self.conflict_count[r, c] = sum(
            0 if ADJACENT[new_t, self.grid[neighbor_row, neighbor_col]] else 1
            for neighbor_row, neighbor_col in self._nbrs[r][c]
        )
        if self.conflict_count[r, c] > 0:
            self.conflicted.add((r, c))
        else:
            self.conflicted.discard((r, c))


    def solve(
        self,
        max_iterations: int | None = None,
        patience: int | None = None,
        log_every: int = 500,
        label: str = '',
        verbose: bool = True,
    ) -> tuple[int, bool, list[tuple[int, int]]]:
        """
        Run the min-conflicts algorithm.

        Stopping criteria (first one triggered wins)
        -------------------------------------------
        1. Zero conflicts remaining              → success
        2. max_iterations reached                → failure (hard cap)
        3. No drop in total conflict score for
           `patience` consecutive iterations     → failure (stuck / local minimum)

        Parameters
        ----------
        max_iterations  Hard iteration cap.
                        Default: min(5 × rows × cols, 100_000)
        patience        Give up after this many iterations without any reduction
                        in total conflict score.
                        Default: max(2_000, rows × cols // 2)
        log_every       Record a checkpoint and optionally print every N iters.
        label           String prefix shown on every progress line (e.g. '50×50 On t=01').
        verbose         Print progress lines to stdout.

        Returns
        -------
        (n_iterations, converged, log)
            n_iterations : actual assignment steps taken
            converged    : True iff zero conflicts remain at return
            log          : list of (iteration, n_conflicted_cells) checkpoints,
                           starting with (0, initial_count) and ending with the
                           final state — suitable for writing directly to CSV.

        Performance note
        ----------------
        Instead of converting self.conflicted to a list on every iteration
        (O(k) each time), we build a shuffled candidate batch and work through
        it, rebuilding only when exhausted or too many stale entries appear.
        This is the main speedup over the naive loop for large conflict sets.
        """
        if max_iterations is None: # max iterations 1,000,000
            max_iterations = min(5 * self.rows * self.cols, 100_000)
        if patience is None: # 10,000 with no increase to prevent sticking at local optima
            patience = max(2_000, self.rows * self.cols // 2)

        n_start = len(self.conflicted)
        log: list[tuple[int, int]] = [(0, n_start)]
        best_score = int(np.sum(self.conflict_count))   # tracks total edge-conflict score
        stagnant   = 0

        pfx = f'[{label}]' if label else '[solve]'
        if verbose:
            print(f'  {pfx} start  conflicts={n_start:,}')

        # Build a shuffled list from the conflicted set once, then walk through
        # it sequentially.  Cells fixed mid-batch are skipped (stale check).
        # Rebuild when the batch is exhausted or too many stale hits pile up.
        candidates: list[tuple[int, int]] = list(self.conflicted)
        random.shuffle(candidates)
        ptr         = 0
        stale_run   = 0   # consecutive stale picks; triggers early rebuild
        STALE_LIMIT = max(32, len(candidates))

        i = 0  # counts actual assignments (not loop steps)

        while i < max_iterations:

            if not self.conflicted:
                log.append((i, 0))
                if verbose:
                    print(f'  {pfx} ✓ converged  iters={i:,}')
                return i, True, log

            
            if ptr >= len(candidates) or stale_run >= STALE_LIMIT:
                candidates  = list(self.conflicted)
                random.shuffle(candidates)
                ptr         = 0
                stale_run   = 0
                STALE_LIMIT = max(32, len(candidates))

            r, c = candidates[ptr]
            ptr += 1

            # Skip if this cell was already fixed by an earlier assignment
            if self.conflict_count[r, c] == 0:
                stale_run += 1
                continue   # don't count as an iteration

            stale_run = 0
            self._assign(r, c, self._min_conflict_value(r, c))
            i += 1

            
            if i % log_every == 0:
                n = len(self.conflicted)
                log.append((i, n))
                if verbose:
                    print(f'  {pfx}  iter={i:,}  conflicts={n:,}')

                score = int(np.sum(self.conflict_count))
                if score < best_score:
                    best_score = score
                    stagnant   = 0
                else:
                    stagnant  += log_every

                if stagnant >= patience:
                    if verbose:
                        print(f'  {pfx} ✗ stuck  iters={i:,}  conflicts={n:,}'
                              f'  (no improvement in {stagnant:,} iters)')
                    return i, False, log

        n = len(self.conflicted)
        log.append((i, n))
        if verbose:
            print(f'  {pfx} ✗ limit  iters={i:,}  conflicts={n:,}')
        return i, False, log


    def copy_grid(self) -> np.ndarray:
        """Snapshot the current grid array (call before solve() for before/after viz)."""
        return self.grid.copy()

    def load_grid(self, arr: np.ndarray):
        """Load a saved grid snapshot for display.  Does not update conflict_count."""
        self.grid = arr.copy()

    def visualize(self, title: str = '', ax=None):
        """Render the terrain grid as a colour-coded image with a legend."""
        cmap = mcolors.ListedColormap(TERRAIN_COLORS)
        norm = mcolors.BoundaryNorm(np.arange(-0.5, N_TERRAINS), N_TERRAINS)

        standalone = (ax is None)
        if standalone:
            _, ax = plt.subplots(figsize=(6, 6))

        ax.imshow(self.grid, cmap=cmap, norm=norm, interpolation='nearest')
        ax.set_title(title, fontsize=10, pad=7)
        ax.axis('off')

        patches = [
            mpatches.Patch(facecolor=TERRAIN_COLORS[i],
                           edgecolor='#444', linewidth=0.5,
                           label=f'{TERRAIN_CHARS[i]}  {TERRAIN_NAMES[i]}')
            for i in range(N_TERRAINS)
        ]
        ax.legend(handles=patches, fontsize=7.5, framealpha=0.88,
                  loc='lower right', borderpad=0.7)

        if standalone:
            plt.tight_layout()
            plt.show()