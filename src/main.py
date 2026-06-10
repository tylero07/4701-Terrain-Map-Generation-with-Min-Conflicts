# main.py
# Experiment runner for terrain map min-conflicts

import sys
import time
import py_compile
from pathlib import Path

# Force-recompile all src modules so stale .pyc files never shadow edits
_SRC = Path(__file__).parent
for _f in _SRC.glob("*.py"):
    if _f.name != "__init__.py":
        try:
            py_compile.compile(
                str(_f),
                invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
            )
        except Exception:
            pass

sys.path.insert(0, str(_SRC))

from terrain import TerrainGrid
from visualization import (
    save_before_after, save_trial_csv, save_trials_graph,
    save_results_csv, save_convergence_graph,
)

# ── Configuration ─────────────────────────────────────────────────────────────

MAP_SIZES  = [50, 75, 100, 150, 200]
N_TRIALS   = 10
MAX_ITER   = 1_000_000    # hard iteration cap
PATIENCE   = 10_000       # stop if no improvement for this many iters
LOG_EVERY  = 250          # checkpoint interval passed to solve()

VIZ_SIZE   = 50
OUTPUT_DIR = Path(__file__).parent.parent / "output"

STOPPING_CRITERION = (
    f"max_iterations={MAX_ITER:,} OR "
    f"{PATIENCE:,} consecutive iterations without any reduction in conflict score"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def banner(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def condition_dir(size: int, diagonals: bool) -> Path:
    """Return (and create) the output folder for a given size + diagonal condition."""
    d = OUTPUT_DIR / f"{size}x{size}" / ("diag_on" if diagonals else "diag_off")
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_trials(size: int, diagonals: bool) -> dict:
    """Run N_TRIALS, save per-trial CSVs and a combined trial graph."""
    cdir = condition_dir(size, diagonals)
    iters_list, failures, all_logs, conv_flags = [], 0, [], []

    for i in range(N_TRIALS):
        tg = TerrainGrid(size, size, use_diagonals=diagonals)
        tg.initialize_random()
        n_iters, converged, log = tg.solve(
            max_iterations=MAX_ITER,
            patience=PATIENCE,
            log_every=LOG_EVERY,
            verbose=False,
        )
        status = "OK" if converged else "FAIL"
        print(f"    Trial {i+1:2d}: {status}  iters={n_iters:>9,}  "
              f"final_conflicts={log[-1][1] if log else '?'}")

        # Save per-trial CSV
        save_trial_csv(log, cdir / f"trial_{i+1:02d}.csv", converged, n_iters)

        all_logs.append(log)
        conv_flags.append(converged)
        if converged:
            iters_list.append(n_iters)
        else:
            failures += 1

    # Save combined trial graph for this condition
    diag_label = "On" if diagonals else "Off"
    save_trials_graph(
        all_logs, conv_flags,
        output_path=cdir / "trials_convergence.png",
        title=f"Conflicts Over Iterations — {size}×{size}, Diagonals {diag_label}",
    )

    avg = sum(iters_list) / len(iters_list) if iters_list else None
    return {
        'successes':      N_TRIALS - failures,
        'failures':       failures,
        'avg_iterations': avg,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    # Before/after visualizations (saved inside each condition folder)
    banner(f"Generating before/after visualizations ({VIZ_SIZE}x{VIZ_SIZE})")
    for diagonals in [False, True]:
        tag  = f"{VIZ_SIZE}x{VIZ_SIZE}_{'diag_on' if diagonals else 'diag_off'}"
        cdir = condition_dir(VIZ_SIZE, diagonals)
        tg   = TerrainGrid(VIZ_SIZE, VIZ_SIZE, use_diagonals=diagonals)
        tg.initialize_random()
        before = tg.copy_grid()
        tg.solve(max_iterations=MAX_ITER, patience=PATIENCE,
                 log_every=LOG_EVERY, verbose=True, label=tag)
        after = tg.copy_grid()
        save_before_after(before, after, cdir, tag=tag)

    # Main experiments
    for size in MAP_SIZES:
        for diagonals in [True, False]:
            diag_label = "On" if diagonals else "Off"
            banner(f"Size {size}x{size} | Diagonals {diag_label} | {N_TRIALS} trials")

            t0  = time.time()
            agg = run_trials(size, diagonals)
            elapsed = time.time() - t0

            avg = agg['avg_iterations']
            print(f"  Successes : {agg['successes']}/{N_TRIALS}")
            print(f"  Failures  : {agg['failures']}/{N_TRIALS}")
            print(f"  Avg iters : {avg:.1f}" if avg is not None else "  Avg iters : N/A")
            print(f"  Wall time : {elapsed:.1f}s")

            summary.append({
                'size':              size,
                'diagonals':         diagonals,
                'avg_iterations':    avg,
                'failures':          agg['failures'],
                'n_trials':          N_TRIALS,
                'stopping_criterion': STOPPING_CRITERION,
            })

    # Save top-level summary outputs
    banner("Saving summary outputs")
    save_results_csv(summary, OUTPUT_DIR / "results.csv")
    save_convergence_graph(summary, OUTPUT_DIR / "convergence_graph.png")

    print("\nResults Table:")
    print(f"{'Size':<10} {'Diag':<8} {'Avg Iters':>12} {'Failures':>10}")
    print("-" * 44)
    for d in summary:
        avg_str  = f"{d['avg_iterations']:.1f}" if d['avg_iterations'] is not None else "N/A"
        diag_str = "On" if d['diagonals'] else "Off"
        print(f"{d['size']}x{d['size']:<6} {diag_str:<8} {avg_str:>12} {d['failures']:>5}/{N_TRIALS}")

    banner("Done -- outputs saved to: " + str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
