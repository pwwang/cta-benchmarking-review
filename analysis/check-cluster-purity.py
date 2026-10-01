#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Is the pbmc3k cluster partition identical to the truth partition? Groups truth.tsv
#        by cluster and counts distinct truth types per cluster (1 == pure).
# REVIEW Section 4: the structural contrast with gse96583 -- pbmc3k has 9 of 9 pure
#        clusters, so a cluster-level arm there only has to name nine already-pure groups
#        and its 1.0000 is not a cell-level accuracy.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Is the pbmc3k cluster partition identical to the truth partition? Check purity."""
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

TRUTH = paths.ARTIFACTS / "pbmc3k-nohitype" / "truth.tsv"
t = pl.read_csv(TRUTH, separator="\t")

per_cluster = (
    t.group_by("cluster")
    .agg(
        pl.len().alias("n_cells"),
        pl.col("truth").n_unique().alias("n_truth_types"),
        pl.col("truth").first().alias("label"),
    )
    .sort("cluster")
)
print("=== cluster purity (n_truth_types == 1 means a pure cluster) ===")
print(per_cluster)

pure = per_cluster.filter(pl.col("n_truth_types") == 1).height
print(f"\nclusters: {per_cluster.height}, pure: {pure}")
print(f"partition == truth partition: {pure == per_cluster.height}")

print("\n=== same question on gse96583 (the second dataset) ===")
g = pl.read_csv(paths.ARTIFACTS / "gse96583-nohitype" / "truth.tsv", separator="\t")
gc = (
    g.group_by("cluster")
    .agg(pl.len().alias("n_cells"), pl.col("truth").n_unique().alias("n_truth_types"))
    .sort("cluster")
)
pure_g = gc.filter(pl.col("n_truth_types") == 1).height
print(f"clusters: {gc.height}, pure: {pure_g}  ({pure_g / gc.height:.1%})")
print(gc.head(30))
