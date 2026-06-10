# solver.py
# Min-conflicts algorithm -- numpy-vectorized for speed

import random
import numpy as np
from dataclasses import dataclass
from terrain import NUM_TERRAINS, COMPATIBLE
from grid import random_grid, total_conflicts

COMPAT_NP = np.array(COMPATIBLE, dtype=bool)


@dataclass
class SolveResult:
    success: bool
    iterations: int
    initial_conflicts: int
    final_conflicts: int
    grid: np.ndarray


def _build_neighbor_cache(rows, cols, diagonals):
    offsets = [(-1,0),(1,0),(0,-1),(0,1)]
    if diagonals:
        offsets += [(-1,-1),(-1,1),(1,-1),(1,1)]
    cache = []
    for r in range(rows):
        for c in range(cols):
            nbrs = []
            for dr, dc in offsets:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    nbrs.append(nr * cols + nc)
            cache.append(np.array(nbrs, dtype=np.int32))
    return cache


def min_conflicts(rows, cols, diagonals,
                  max_iterations=100_000, max_no_improve=5_000):
    """
    Run min-conflicts on a rows x cols terrain grid.
    Stopping criteria (first to trigger):
      1. Zero conflicts -> success
      2. max_iterations reached -> failure
      3. max_no_improve consecutive iterations without improvement -> failure
    """
    grid = random_grid(rows, cols)
    flat = grid.ravel()
    n = rows * cols

    nbr_cache = _build_neighbor_cache(rows, cols, diagonals)
    init_conflicts = total_conflicts(grid, rows, cols, diagonals)

    conflicted = set()
    for idx in range(n):
        nbrs = nbr_cache[idx]
        if nbrs.size and np.any(~COMPAT_NP[flat[idx], flat[nbrs]]):
            conflicted.add(idx)

    best_size = len(conflicted)
    no_improve_cnt = 0
    conf_list = list(conflicted)

    for iteration in range(1, max_iterations + 1):
        if not conflicted:
            return SolveResult(
                success=True,
                iterations=iteration - 1,
                initial_conflicts=init_conflicts,
                final_conflicts=0,
                grid=grid,
            )

        idx = random.choice(conf_list)
        nbrs = nbr_cache[idx]
        nbr_vals = flat[nbrs]
        conf_counts = np.sum(~COMPAT_NP[:, nbr_vals], axis=1)
        min_c = conf_counts.min()
        best_vals = np.where(conf_counts == min_c)[0]
        flat[idx] = int(np.random.choice(best_vals))

        for cidx in [idx] + nbr_cache[idx].tolist():
            cn = nbr_cache[cidx]
            if cn.size and np.any(~COMPAT_NP[flat[cidx], flat[cn]]):
                conflicted.add(cidx)
            else:
                conflicted.discard(cidx)

        new_size = len(conflicted)
        if new_size != best_size or iteration % 200 == 0:
            conf_list = list(conflicted)

        if new_size < best_size:
            best_size = new_size
            no_improve_cnt = 0
        else:
            no_improve_cnt += 1

        if no_improve_cnt >= max_no_improve:
            break

    final = total_conflicts(grid, rows, cols, diagonals)
    return SolveResult(
        success=False,
        iterations=max_iterations,
        initial_conflicts=init_conflicts,
        final_conflicts=final,
        grid=grid,
    )


def run_trials(rows, cols, diagonals, n_trials=10,
               max_iterations=100_000, max_no_improve=5_000):
    results = []
    for i in range(n_trials):
        r = min_conflicts(rows, cols, diagonals, max_iterations, max_no_improve)
        status = "OK" if r.success else "FAIL"
        print(f"    Trial {i+1:2d}: {status}  iters={r.iterations:>7,}")
        results.append(r)

    successes = [r for r in results if r.success]
    avg_iter = (
        sum(r.iterations for r in successes) / len(successes)
        if successes else None
    )
    return {
        'results': results,
        'successes': len(successes),
        'failures': len(results) - len(successes),
        'avg_iterations': avg_iter,
    }
