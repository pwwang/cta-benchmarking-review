#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Re-derives the marker-resource claims on the corrected partition.
#          Q1: fix the resource, vary the tool     -> spread across tools    (tool choice)
#          Q2: fix the tool,     vary the resource -> spread across resources (resource choice)
#        Comparing the two spreads is what the "tool choice dominates resource choice" claim
#        means.
# REVIEW Section 6: both spreads were originally derived from the SCRAMBLED cluster-level
#        labels, so this script is what makes the claim citable after the repair.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Re-derive the marker-resource claims on the CORRECTED gse96583 partition.

The manuscript's Q1/Q2 claims -- the per-tool ranking on a fixed marker resource, and "tool choice
dominates resource choice ~3-4x" -- were derived from the scrambled cluster-level labels (ScType
0.1485, scSorter 0.1482, scCATCH 0.0050). This recomputes both spreads from the rebuilt artifact.

Q1: fix the resource, vary the tool  -> spread across tools   (tool choice)
Q2: fix the tool,     vary the resource -> spread across resources (resource choice)
Comparing the two is what the "dominates" claim means.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

FIX = paths.ARTIFACTS / "gse96583-fixed-nohitype"

RESOURCES = ["ScTypeDBShort", "ScTypeDBFull", "scCATCH", "CellMarker", "AutoPos8525",
             "AutoPos8526", "AutoPos8527", "AutoBoth", "ScTypeDBShortPos", "ScTypeDBFullPos",
             "scCATCHPos", "CellMarkerPos", "PanglaoDB"]

truth = pl.read_csv(FIX / "truth.tsv", separator="\t")
types = sorted(truth["truth"].unique().to_list())
T = len(types)
code = {t: i + 1 for i, t in enumerate(types)}
cells = truth["cell"].to_list()
y = np.array([code[t] for t in truth["truth"].to_list()])

votes = pl.read_csv(FIX / "votes.tsv", separator="\t")
wide = votes.pivot(on="annotator", index="unit", values="code", aggregate_function="first")
uindex = pl.DataFrame({"unit": cells, "i": np.arange(len(cells))})
wide = uindex.join(wide, on="unit", how="left").sort("i")
arms = [c for c in wide.columns if c not in ("unit", "i")]
M = wide.select(arms).fill_null(0).to_numpy().astype(np.int16)
acc = {a: float(((M[:, j] == y) & (M[:, j] >= 1) & (M[:, j] <= T)).mean())
       for j, a in enumerate(arms)}

# tool -> resource -> accuracy, for every arm that parses as <tool>_<resource>
grid: dict[str, dict[str, float]] = {}
for a in arms:
    tool, _, res = a.partition("_")
    if res in RESOURCES:
        grid.setdefault(tool, {})[res] = acc[a]

tools = sorted(grid)
print("=== per-tool accuracy across the 13 resources (corrected) ===")
print(f"{'tool':<12} {'n':>3} {'min':>7} {'median':>7} {'max':>7} {'spread':>7}   worst resource")
for t in tools:
    v = grid[t]
    vals = np.array(list(v.values()))
    worst = min(v, key=v.get)
    print(f"{t:<12} {len(v):>3} {vals.min():>7.4f} {np.median(vals):>7.4f} {vals.max():>7.4f} "
          f"{vals.max()-vals.min():>7.4f}   {worst} ({v[worst]:.4f})")

print("\n=== per-resource spread across tools (Q1: fix the resource, vary the tool) ===")
print(f"{'resource':<18} {'n':>3} {'min':>7} {'max':>7} {'spread':>7}")
spreads_fixed_res = []
for r in RESOURCES:
    vals = {t: grid[t][r] for t in tools if r in grid[t]}
    if len(vals) < 2:
        continue
    a = np.array(list(vals.values()))
    spreads_fixed_res.append(a.max() - a.min())
    print(f"{r:<18} {len(vals):>3} {a.min():>7.4f} {a.max():>7.4f} {a.max()-a.min():>7.4f}")

print("\n=== the two spreads, compared ===")
per_tool_spread = [max(grid[t].values()) - min(grid[t].values()) for t in tools if len(grid[t]) > 1]
print(f"  resource choice (median within-tool spread)  : {np.median(per_tool_spread):.4f}")
print(f"  tool choice     (median across-tool spread)  : {np.median(spreads_fixed_res):.4f}")
ratio = np.median(spreads_fixed_res) / np.median(per_tool_spread)
print(f"  ratio tool:resource = {ratio:.2f}x")

# --- the RECORDED definitions, so the comparison is like-for-like -------------------------
# MARKER-RESOURCE-RESULTS.md lines 39-41 recorded, for gse96583:
#   resource choice (mean within-tool spread) = 0.2535
#   tool choice (best-arm-per-tool spread)    = 0.8651
#   "Tool choice dominates resource choice by roughly 3-4x"
# Recomputing with THOSE definitions is the only valid way to say what changed.
print("\n=== like-for-like with the recorded definitions ===")
mean_within = float(np.mean(per_tool_spread))
mean_within_nost = float(np.mean([max(grid[t].values()) - min(grid[t].values())
                                  for t in tools if len(grid[t]) > 1 and t != "ScType"]))
best_per_tool = np.array([max(grid[t].values()) for t in tools])
tool_spread = float(best_per_tool.max() - best_per_tool.min())
print(f"  resource choice (MEAN within-tool spread)   : {mean_within:.4f}   (recorded 0.2535)")
print(f"    ... excluding the degenerate ScType       : {mean_within_nost:.4f}")
print(f"  tool choice (best-arm-per-tool spread)      : {tool_spread:.4f}   (recorded 0.8651)")
print(f"  ratio = {tool_spread / mean_within:.2f}x   (recorded '3-4x')")
print(f"    ... with ScType excluded from the resource mean: {tool_spread / mean_within_nost:.2f}x")
print(f"  best per tool: max {best_per_tool.max():.4f} ({tools[int(best_per_tool.argmax())]})  "
      f"min {best_per_tool.min():.4f} ({tools[int(best_per_tool.argmin())]})")

print("\n=== resource-blindness check (does a tool ignore the resource?) ===")
for t in tools:
    if len(grid[t]) >= 8:
        vals = list(grid[t].values())
        print(f"  {t:<12} distinct accuracies across {len(vals)} resources: {len(set(np.round(vals,4)))}")

print("\n=== best arm per tool ===")
for t in sorted(tools, key=lambda t: -max(grid[t].values())):
    r = max(grid[t], key=grid[t].get)
    print(f"  {t:<12} {grid[t][r]:.4f}  ({r})")
