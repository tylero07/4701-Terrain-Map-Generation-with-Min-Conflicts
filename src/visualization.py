# visualization.py
# Map images, per-trial CSVs, per-condition convergence graphs, overall summary.

import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from pathlib import Path

from terrain import TERRAIN_CHARS, TERRAIN_NAMES, TERRAIN_COLORS, N_TERRAINS

# ── Colormap ─────────────────────────────────────────────────────────────────

_CMAP = mcolors.ListedColormap(TERRAIN_COLORS)
_NORM = mcolors.BoundaryNorm(np.arange(-0.5, N_TERRAINS), N_TERRAINS)

_LEGEND_PATCHES = [
    mpatches.Patch(
        facecolor=TERRAIN_COLORS[i], edgecolor='#444', linewidth=0.5,
        label=f'{TERRAIN_CHARS[i]}  {TERRAIN_NAMES[i]}'
    )
    for i in range(N_TERRAINS)
]


def _render_grid(ax, grid: np.ndarray, title: str):
    ax.imshow(grid, cmap=_CMAP, norm=_NORM, interpolation='nearest', aspect='equal')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=6)
    ax.axis('off')
    ax.legend(handles=_LEGEND_PATCHES, fontsize=7.5, framealpha=0.88,
              loc='lower right', borderpad=0.7)


# ── Map images ───────────────────────────────────────────────────────────────

def save_terrain_map(grid: np.ndarray, path, title: str = 'Terrain Map'):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7))
    _render_grid(ax, grid, title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {path}')


def save_before_after(before: np.ndarray, after: np.ndarray, output_dir, tag: str = ''):
    output_dir = Path(output_dir)
    prefix = f'{tag}_' if tag else ''
    save_terrain_map(before, output_dir / f'{prefix}before_map.png',
                     title=f'Before – Random Init {("(" + tag + ")") if tag else ""}')
    save_terrain_map(after,  output_dir / f'{prefix}after_map.png',
                     title=f'After – Min-Conflicts {("(" + tag + ")") if tag else ""}')

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    _render_grid(axes[0], before, 'Before (Random)')
    _render_grid(axes[1], after,  'After (Min-Conflicts)')
    if tag:
        fig.suptitle(tag, fontsize=13, fontweight='bold')
    fig.tight_layout()
    combined = output_dir / f'{prefix}before_after.png'
    fig.savefig(combined, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {combined}')


# ── Per-trial CSV (conflicts over iterations) ─────────────────────────────────

def save_trial_csv(log: list, path, converged: bool, n_iters: int):
    """
    Save a single trial's conflict log to CSV.

    Each row: iteration, n_conflicted_cells
    log is a list of (iteration, n_conflicted) checkpoints from TerrainGrid.solve().
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['iteration', 'n_conflicted_cells', 'converged', 'total_iterations'])
        for row in log:
            w.writerow([row[0], row[1], converged, n_iters])
    print(f'  Saved: {path}')


# ── Per-condition trial overlay graph ────────────────────────────────────────

def save_trials_graph(
    all_logs: list,          # list of logs, one per trial
    converged_flags: list,   # list of bool, one per trial
    output_path,
    title: str = 'Conflicts Over Iterations',
):
    """
    Plot all trials' conflict curves on one graph.
    Converged trials drawn solid, failed trials drawn dashed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = plt.cm.tab10.colors
    for t, (log, converged) in enumerate(zip(all_logs, converged_flags)):
        if not log:
            continue
        xs = [pt[0] for pt in log]
        ys = [pt[1] for pt in log]
        style   = '-'   if converged else '--'
        label   = f'Trial {t+1} {"✓" if converged else "✗"}'
        ax.plot(xs, ys, linestyle=style, color=colors[t % 10],
                linewidth=1.4, label=label, alpha=0.85)

    ax.set_xlabel('Iteration (cell reassignments)', fontsize=11)
    ax.set_ylabel('Conflicted Cells', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, ncol=2, loc='upper right')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {output_path}')


# ── Overall summary CSV and convergence graph ─────────────────────────────────

def save_results_csv(summary: list, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ['map_size', 'diagonals', 'avg_iterations', 'failures',
              'n_trials', 'stopping_criterion']
    with open(output_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in summary:
            w.writerow({
                'map_size':           f"{d['size']}x{d['size']}",
                'diagonals':          'On' if d['diagonals'] else 'Off',
                'avg_iterations':     f"{d['avg_iterations']:.1f}" if d['avg_iterations'] is not None else 'N/A',
                'failures':           d['failures'],
                'n_trials':           d['n_trials'],
                'stopping_criterion': d.get('stopping_criterion', ''),
            })
    print(f'  Saved: {output_path}')


def save_convergence_graph(summary: list, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    for diagonals, marker, color, label in [
        (True,  'o', 'steelblue',  'Diagonals On'),
        (False, 's', 'darkorange', 'Diagonals Off'),
    ]:
        rows = sorted([d for d in summary if d['diagonals'] == diagonals],
                      key=lambda d: d['size'])
        xs = [d['size'] for d in rows if d['avg_iterations'] is not None]
        ys = [d['avg_iterations'] for d in rows if d['avg_iterations'] is not None]
        if xs:
            ax.plot(xs, ys, marker=marker, color=color, label=label,
                    linewidth=2, markersize=8)
        for d in rows:
            if d['failures'] > 0 and d['avg_iterations'] is not None:
                ax.annotate(f"{d['failures']}/{d['n_trials']} failed",
                            xy=(d['size'], d['avg_iterations']),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, color='red')
            elif d['avg_iterations'] is None:
                ax.axvline(x=d['size'], color=color, linestyle=':', alpha=0.4)

    ax.set_xlabel('Map Size (N×N)', fontsize=12)
    ax.set_ylabel('Avg. Iterations to Convergence (successes only)', fontsize=12)
    ax.set_title('Min-Conflicts Convergence by Map Size', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {output_path}')
