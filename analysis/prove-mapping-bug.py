#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Proves the cross-resolution mapping defect for named arms by computing BOTH
#        numbers from data already on disk: the arm's own per-cell labels, and the
#        evaluator's cluster-ID-matched expansion of the arm's cluster table.
# REVIEW Section 6 / Figure 3: the mechanism demonstration. If an arm clustered at a
#        different resolution than the benchmark's cluster column, the string IDs refer to
#        different cell groups and the expansion is scrambled.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Prove the cross-resolution mapping bug: an arm's own per-cell labels vs the eval's ID-matched expansion.

For a cluster-level arm the eval reads the arm's cluster2celltype table and expands it over the
benchmark's cluster column, matching by cluster ID *string*. If the arm clustered at a different
resolution than the benchmark's column, the IDs refer to different cell groups and the expansion is
scrambled. This script computes both numbers from data already on disk.
"""
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

H = paths.HARNESS
Q = paths.ARTIFACTS

CASES = [
    ("gse96583", "CellTypeAnnotation_gse96583_test-output", "CellTypeAnnotation_ScType_AutoBoth", "ScType_AutoBoth"),
    ("gse96583", "CellTypeAnnotation_gse96583_test-output", "CellTypeAnnotation_scSorter_AutoPos8527", "scSorter_AutoPos8527"),
    ("gse96583", "CellTypeAnnotation_gse96583_test-output", "CellTypeAnnotation_scCATCH_CellMarker", "scCATCH_CellMarker"),
    ("pbmc3k", "CellTypeAnnotation_pbmc3k_test-output", "CellTypeAnnotation_ScType_CellMarker", "ScType_CellMarker"),
    ("pbmc3k", "CellTypeAnnotation_pbmc3k_test-output", "CellTypeAnnotation_scSorter_AutoPos8525", "scSorter_AutoPos8525"),
]

for ds, outdir, armdir, label in CASES:
    truth = pl.read_csv(Q / f"{ds}-nohitype" / "truth.tsv", separator="\t")
    tmap = dict(zip(truth["cell"].to_list(), truth["truth"].to_list()))
    cmap = dict(zip(truth["cell"].to_list(), truth["cluster"].to_list()))
    n_eval_clusters = truth["cluster"].n_unique()

    d = H / outdir / armdir
    cell_f = d / f"{ds}_test.annotated.cell2celltype.tsv"
    clus_f = d / f"{ds}_test.annotated.cluster2celltype.tsv"

    print(f"\n=== {ds} / {label} ===")
    if not clus_f.exists():
        print("   no cluster table"); continue
    ct = pl.read_csv(clus_f, separator="\t")
    lab_col = [c for c in ct.columns if c not in ("Cluster", "Size")][0]
    c2l = dict(zip((str(x) for x in ct["Cluster"].to_list()), ct[lab_col].to_list()))
    print(f"   arm clusters: {ct.height}   eval clusters: {n_eval_clusters}")

    # (A) the arm's own per-cell labels — self-consistent with its own clustering
    if cell_f.exists():
        cf = pl.read_csv(cell_f, separator="\t")
        ccol = [c for c in cf.columns if c != "Cell"][0]
        own = dict(zip(cf["Cell"].to_list(), cf[ccol].to_list()))
        common = set(tmap) & set(own)
        a = sum(1 for c in common if own[c] == tmap[c]) / len(common)
        print(f"   (A) own per-cell labels:        {a:.4f}  ({len(common)} cells)")
    else:
        print("   (A) no cell table")

    # (B) what the eval's ID-matched expansion produces
    matched = 0
    hit = 0
    missing_ids = set()
    for cell, lab in tmap.items():
        key = str(cmap[cell])
        if key in c2l:
            matched += 1
            if c2l[key] == lab:
                hit += 1
        else:
            missing_ids.add(key)
    print(f"   (B) eval ID-matched expansion:  {hit/matched:.4f}  ({matched} matched)")
    if missing_ids:
        print(f"   eval cluster ids absent from the arm's table: {sorted(missing_ids, key=int)[:10]}")
