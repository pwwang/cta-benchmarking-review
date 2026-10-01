#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Re-checks the redundancy finding on the CORRECTED artifacts rather than assuming
#        it survived the repair. Groups arms by byte-identical per-cell vote vectors over
#        all 10,947 cells (exact, no tolerance).
# REVIEW Section 3 / Section 6: the claim that distinct marker resources routinely produce
#        byte-identical vote vectors (negative markers a no-op, ScTypeDBShort/Full aliased,
#        learned AutoPos variants indistinguishable).
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Does the redundancy finding survive the fix?

The paper claims that distinct marker resources routinely produce BYTE-IDENTICAL vote vectors
(negative markers a no-op, ScTypeDBShort/Full aliased, learned AutoPos variants indistinguishable).
That was established on the scrambled artifacts. Now that the cluster-level labels were rebuilt on
the corrected 24-cluster partition, the claim has to be re-checked, not assumed -- the whole point of
the finding is that the tools ignore information, and a repair that changed the tables could in
principle have broken the ties.

Groups arms by identical per-cell vote vectors over all 10,947 cells, exactly (no tolerance).
"""
import collections
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

FIX = paths.ARTIFACTS / "gse96583-fixed-nohitype"

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

groups: dict[bytes, list[str]] = {}
for j, a in enumerate(arms):
    groups.setdefault(M[:, j].tobytes(), []).append(a)

dupes = {k: v for k, v in groups.items() if len(v) > 1}
n_dup_arms = sum(len(v) for v in dupes.values())
print(f"=== exact duplicate vote vectors, corrected gse96583 ({len(arms)} arms) ===")
print(f"  arms in a duplicate group : {n_dup_arms} / {len(arms)}  ({100*n_dup_arms/len(arms):.0f}%)")
print(f"  distinct vote vectors     : {len(groups)}")
print(f"  groups of size > 1        : {len(dupes)}")

print("\n=== the groups (size >= 2), with accuracy ===")
for _, members in sorted(dupes.items(), key=lambda kv: -len(kv[1])):
    j = arms.index(members[0])
    acc = float(((M[:, j] == y) & (M[:, j] >= 1) & (M[:, j] <= T)).mean())
    print(f"  x{len(members)}  acc={acc:.4f}  {' == '.join(sorted(members))}")

print("\n=== does a tool's *Pos variant ever differ from its non-Pos twin? ===")
for a in sorted(arms):
    if a.endswith("Pos"):
        base = a[:-3]
        if base in arms:
            same = M[:, arms.index(a)].tobytes() == M[:, arms.index(base)].tobytes()
            print(f"  {a:<26} identical to {base:<22} {same}")

print("\n=== which tools are entirely resource-blind (one vector fits all resources)? ===")
grid = collections.defaultdict(dict)
for a in arms:
    tool, _, res = a.partition("_")
    grid[tool][res] = M[:, arms.index(a)].tobytes()
for tool, d in sorted(grid.items()):
    if len(d) >= 4:
        print(f"  {tool:<10} {len(set(d.values()))} distinct vectors for {len(d)} resources")
