#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Classifies each arm as cluster-level (one call repeated for every cell of a
#        cluster) or cell-level, by looking for *.annotated.cluster2celltype.tsv vs
#        *.annotated.cell2celltype.tsv in the arm's output directory; prints the
#        tool x level breakdown.
# REVIEW Section 6: cluster-level arms are the correlated-evidence problem the review
#        describes.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Which arms are cluster-level (one call repeated for every cell of a cluster) vs cell-level?

Cluster-level arms are the correlated-evidence problem: `read_arm_labels` expands one cluster call to
every cell in the cluster, and `e_step` then multiplies those identical votes as if they were
independent observations. This prints the tool x level breakdown so a `--tools` subset can test it.
"""
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

HARNESS = paths.HARNESS
DS = "gse96583_fixed"
OUT = HARNESS / f"CellTypeAnnotation_{DS}-output"
meta = pl.read_csv(paths.ARTIFACTS / "gse96583-fixed-nohitype" / "resources.tsv", separator="\t")

rows = []
for r in meta.iter_rows(named=True):
    d = OUT / f"CellTypeAnnotation_{r['arm']}"
    cell = list(d.glob("*.annotated.cell2celltype.tsv"))
    clus = list(d.glob("*.annotated.cluster2celltype.tsv"))
    rows.append(dict(tool=r["tool"], arm=r["arm"], cell=len(cell), cluster=len(clus)))

df = pl.DataFrame(rows)
print("arms with a cluster table:", df.filter(pl.col("cluster") > 0).height, "of", df.height)
print()
print(f"{'tool':<18} {'arms':>5} {'cluster_tables':>15} {'level':<8}")
for tool in sorted(df["tool"].unique().to_list()):
    sub = df.filter(pl.col("tool") == tool)
    n_c = sub.filter(pl.col("cluster") > 0).height
    level = "cluster" if n_c == sub.height else ("cell" if n_c == 0 else "MIXED")
    print(f"{tool:<18} {sub.height:>5} {n_c:>15} {level:<8}")

cluster_tools = sorted(
    t for t in df["tool"].unique().to_list()
    if df.filter(pl.col("tool") == t).filter(pl.col("cluster") > 0).height
    == df.filter(pl.col("tool") == t).height
)
cell_tools = sorted(
    t for t in df["tool"].unique().to_list()
    if df.filter(pl.col("tool") == t).filter(pl.col("cluster") > 0).height == 0
)
print("\nCLUSTER_TOOLS=" + ",".join(cluster_tools))
print("CELL_TOOLS=" + ",".join(cell_tools))
