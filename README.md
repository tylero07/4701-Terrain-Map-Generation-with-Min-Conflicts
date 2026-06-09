# Terrain Map Generation with Min-Conflicts

## Overview

This project uses the **min-conflicts local search algorithm** to generate valid terrain maps as a **constraint satisfaction problem (CSP)**.

A terrain map is represented as a grid. Each cell in the grid must be assigned one of six terrain types. The goal is to assign terrain values so that every neighboring pair of cells satisfies the terrain adjacency rules.

Unlike pathfinding projects, this project does **not** require finding a path or calculating movement costs. The objective is simply to produce a valid terrain map where all adjacency constraints are satisfied.

---

## Terrain Types

The six terrain types are ordered from lowest to highest elevation:

| Symbol | Terrain | Description |
|---|---|---|
| `W` | Water | Open water; lowest elevation |
| `B` | Beach | Coastal sand; transition between water and land |
| `L` | Lowland | Flat open terrain; fields and plains |
| `F` | Forest | Forested terrain; moderate elevation |
| `H` | Hills | Rolling hills; elevated terrain |
| `M` | Mountains | High peaks; highest elevation |

---

## Adjacency Rules

Two terrain types may be placed next to each other only if their positions in the terrain ordering differ by at most `1`.

For example:

- Beach may be adjacent to Water, Beach, or Lowland.
- Beach may **not** be adjacent to Forest, Hills, or Mountains.
- Mountains may be adjacent to Hills or Mountains.

### Allowed Adjacency Table

| Terrain | Water | Beach | Lowland | Forest | Hills | Mountains |
|---|---:|---:|---:|---:|---:|---:|
| Water | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Beach | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Lowland | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Forest | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ |
| Hills | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Mountains | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |

---

## Min-Conflicts Algorithm

The project requires implementing the min-conflicts algorithm manually.

The algorithm works by starting with a complete random assignment and repeatedly repairing conflicts.

### Algorithm Steps

1. Randomly assign a terrain type to every cell in the grid.
2. Identify all cells that violate at least one adjacency constraint.
3. Randomly select one conflicted cell.
4. Reassign that cell to the terrain type that produces the fewest conflicts with its neighbors.
5. Break ties randomly.
6. Repeat until either:
   - the map has zero conflicts, or
   - the stopping criterion is reached.

### Important Note

Min-conflicts is a local search algorithm. It is not guaranteed to find a solution every time, even when a solution exists. Because of this, the program must track both successful runs and failures to converge.

---

## Neighbor Conditions

Experiments must be run using two different neighbor configurations.

### Diagonals Off

Each cell checks up to 4 neighbors:

- Up
- Down
- Left
- Right

### Diagonals On

Each cell checks up to 8 neighbors:

- Up
- Down
- Left
- Right
- Up-left
- Up-right
- Down-left
- Down-right

The grid does **not** wrap around. Edge and corner cells have fewer neighbors.

---

## Experimental Design

The program must test multiple map sizes and both diagonal conditions.

### Required Map Sizes

| Map Size |
|---|
| `50 × 50` |
| `75 × 75` |
| `100 × 100` |
| `150 × 150` |
| `200 × 200` |

### Required Conditions

Each map size must be tested with:

- Diagonals on
- Diagonals off

### Trials

Each condition must be run at least **10 times** using different random initializations.

For each trial, record:

- Number of iterations needed to reach zero conflicts, if successful
- Whether the run failed to converge
- The stopping criterion used

---

## Stopping Criterion

A stopping criterion must be defined and justified in the write-up.

Possible stopping criteria include:

- Maximum number of iterations
- Maximum number of iterations without improvement
- Time limit
- A combination of multiple limits

Failure counts must be reported relative to the chosen stopping criterion.

---

## Required Program Outputs

The program must produce the following outputs.

### 1. Colored Map Visualizations

For at least one map size, generate:

- A **before** image showing the initial random terrain assignment
- An **after** image showing the final constraint-satisfying map

Each terrain type should have a distinct color and a legend.

Suggested colors:

| Terrain | Suggested Color |
|---|---|
| Water | Blue |
| Beach | Tan or yellow |
| Lowland | Light green |
| Forest | Dark green |
| Hills | Brown |
| Mountains | Gray or white |

### 2. Results Table

The results table should summarize average successful convergence time and failures for every condition.

| Map Size | Diagonals | Avg. Iterations (Successes Only) | Failures (out of N trials) | Stopping Criterion |
|---|---|---:|---:|---|
| 50×50 | On |  |  |  |
| 50×50 | Off |  |  |  |
| 75×75 | On |  |  |  |
| 75×75 | Off |  |  |  |
| 100×100 | On |  |  |  |
| 100×100 | Off |  |  |  |
| 150×150 | On |  |  |  |
| 150×150 | Off |  |  |  |
| 200×200 | On |  |  |  |
| 200×200 | Off |  |  |  |

If a condition never fails, enter `0` in the failures column.

If a condition never succeeds, enter `N/A` in the average iterations column.

### 3. Convergence Graph

Create a graph showing:

- X-axis: map size
- Y-axis: average number of iterations to convergence
- One series for diagonals on
- One series for diagonals off

If any condition has frequent failures, note that near the graph or in the discussion.

---

## Required Write-Up Structure

The final report should be written as a structured lab report.

### 1. Introduction

Explain:

- What the project does
- What min-conflicts is being used for
- General results from the experiments

### 2. Algorithm Description

Explain the min-conflicts algorithm in your own words.

Include:

- How the algorithm chooses which cell to change
- How the algorithm chooses the new terrain value
- Why random complete assignment is different from incremental construction
- Whether min-conflicts is complete
- The stopping criterion used
- Any tricky or non-standard implementation details

### 3. Results

#### 3.1 Map Visualizations

Include before and after terrain maps.

Briefly explain how the after map differs from the before map.

#### 3.2 Results Table

Include the completed results table.

Report averages over at least 10 trials per condition.

#### 3.3 Convergence Graph

Include the convergence graph with labeled axes and separate diagonal conditions.

### 4. Discussion

Discuss the experimental results using specific numbers from the table and graph.

Address:

- How convergence time scaled with map size
- Whether the relationship appeared linear, faster than linear, or slower than linear
- How diagonal neighbors affected convergence and failure rates
- Whether any runs got stuck
- What the before and after maps show about the algorithm
- Whether the final maps look geographically plausible
- How min-conflicts compares to the search algorithms from Project 1

### 5. Use of AI

Describe whether AI tools were used.

Include:

- Which tools were used
- How they were used for coding
- What worked well or did not work well
- Whether AI was used for writing or revision
- How the final work still reflects personal understanding

If no AI tools were used, write `N/A`.

### 6. Code

Submit the complete source code separately on Canvas or through a repository link.

Do not paste the full source code into the report body.

The code should include:

- Random map initializer
- Min-conflicts implementation
- Conflict detection and counting
- Colored map visualization
- Data collection
- Graph generation

---

## Suggested Repository Structure

```text
terrain-map-min-conflicts/
├── README.md
├── src/
│   └── main.py
├── output/
│   ├── before_map.png
│   ├── after_map.png
│   ├── results.csv
│   └── convergence_graph.png
└── report/
    └── lab_report.pdf
```

This structure is optional, but it keeps code, outputs, and the final report organized.

---

## Extra Credit: Custom Terrain Rules

For extra credit, design a custom terrain rule set that produces more realistic or visually interesting maps.

The extra credit section must include:

1. Custom terrain types
2. Custom adjacency table
3. Justification for the rule design
4. Example output from the custom rules
5. Comparison against the provided rules
6. Discussion of convergence behavior under the custom rules

---

## Submission Checklist

Before submitting, confirm that the project includes:

- [ ] Random terrain map initializer
- [ ] Min-conflicts algorithm implementation
- [ ] Conflict detection and counting
- [ ] Support for diagonals on and off
- [ ] Experiments for all required map sizes
- [ ] At least 10 trials per condition
- [ ] Stopping criterion defined and justified
- [ ] Before and after map visualizations
- [ ] Results table
- [ ] Convergence graph
- [ ] Structured write-up
- [ ] AI-use section
- [ ] Source code submitted separately or linked
- [ ] Optional extra credit section, if attempted
