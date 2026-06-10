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
    save_results_csv, save_convergence_graph, save_conflict_region,
)

"""Create globals for test total parameters"""

MAP_SIZES  = [50, 75, 100, 150, 200]
N_TRIALS   = 10
MAX_ITER   = 1_000_000    # hard iteration cap
PATIENCE   = 10_000       # stop if no improvement for this many iters
LOG_EVERY  = 250          # checkpoint interval passed to solve()

VIZ_SIZE   = 50
OUTPUT_DIR = Path(__file__).parent.parent / "output" # path for saving results

STOPPING_CRITERION = (
    f"max_iterations={MAX_ITER:,} OR "
    f"{PATIENCE:,} consecutive iterations without any reduction in conflict score"
)

def banner(msg: str):
    """Terminal Logging"""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def condition_dir(size: int, diagonals: bool) -> Path:
    """Return (and create) the output folder for a given size + diagonal condition."""
    d = OUTPUT_DIR / f"{size}x{size}" / ("diag_on" if diagonals else "diag_off")
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_trials(size: int, diagonals: bool) -> dict:
    """Run N_TRIALS, save per-trial CSVs and a combined trial graph to output file"""
    cdir = condition_dir(size, diagonals) # size of the grid and are we running diagnals
    iters_list, failures, all_logs, conv_flags = [], 0, [], [] # initialize all if the needed trackers

    # run the N_Trials (up to 10 hardcoded)
    for i in range(N_TRIALS):
        tg = TerrainGrid(size, size, use_diagonals=diagonals) # create new grid
        tg.initialize_random() # initialize the values randomly using Enumed Values

        # Capture the before grid on trial 1 for before/after visualization
        if i == 0:
            before_grid = tg.copy_grid()

        n_iters, converged, log = tg.solve(
            max_iterations=MAX_ITER, # max iterations is 1M
            patience=PATIENCE, # Patience = a max of 10k changes with no conflict improvement before we stop
            log_every=LOG_EVERY, # log every change (shown on graph)
            verbose=False, # I toggled this for debugging
        )
        status = "OK" if converged else "FAIL" # result status
        print(f"    Trial {i+1:2d}: {status}  iters={n_iters:>9,}  " # terminal printing
              f"final_conflicts={log[-1][1] if log else '?'}")

        # Save before/after maps from trial 1
        if i == 0:
            save_before_after(before_grid, tg.copy_grid(), cdir,
                              tag=f"{size}x{size}_{'diag_on' if diagonals else 'diag_off'}")

        # Save per-trial CSV results
        save_trial_csv(log, cdir / f"trial_{i+1:02d}.csv", converged, n_iters)

        # On failure, save an image of the conflict region
        if not converged:
            save_conflict_region(
                tg.grid, tg.conflicted,
                path=cdir / f"trial_{i+1:02d}_fail.png",
                trial_label=f"trial {i+1} {size}x{size} {'diag_on' if diagonals else 'diag_off'}",
            )

        # more logging 
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
    # avg checking with a div by 0 guard if the list is empty
    avg = sum(iters_list) / len(iters_list) if iters_list else None
    return {
        'successes':      N_TRIALS - failures,
        'failures':       failures,
        'avg_iterations': avg,
    }


def main():
    """Call workhorse functions for main logic initialization and running, filing, printing etc"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    # Main experiments (before/after maps saved per-condition inside run_trials)
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
            print(f"  Timer     : {elapsed:.1f}s")

            summary.append({
                'size':              size,
                'diagonals':         diagonals,
                'avg_iterations':    avg,
                'successes':         agg['successes'],
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
