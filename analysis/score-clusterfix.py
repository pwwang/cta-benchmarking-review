#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   PER-ARM SCORER for the corrected gse96583 partition. Walks the two repair runs'
#        output directories, reads each arm's *cluster2celltype.tsv, expands the
#        cluster-level table to cells through the SAME cluster column the evaluator uses
#        (truth.tsv$cluster, keyed 0..23), and writes two accuracies per arm:
#          acc_n        -- correct / ALL cells (unlabelled and unknown counted wrong,
#                          i.e. exactly what the evaluator's expansion yields)
#          acc_labelled -- correct / cells the arm actually labelled
#        plus coverage columns (labelled, unknown, no_row, clusters in table).
# REVIEW This is the script behind Supplementary Table S3 and the Section 6 per-arm
#        summaries (median, maximum, count >= 0.85) and the corrected end of Figure 3.
# RUN    python <this file>   (from the package root)
# NOTE   The harness and artifacts locations come from paths.py (see README, "Configuration").
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Re-score every gse96583 cluster-level arm on the CORRECTED 24-cluster partition.

Before the fix, the cluster-level arms clustered on `seurat_clusters`, which `data-prep.R` leaves
aliased to the LAST resolution it ran (1.5 -> 32 clusters), while `eval.toml` expands the labels over
`RNA_snn_res.0.5` (24 clusters). `eval.py` matches cluster IDs as strings, so those labels landed on
the wrong cells and the recorded accuracies (ScType 0.1485, scSorter 0.1482, scCATCH 0.0050, cluster
median 0.0262) are the scrambled ones.

This script reproduces the eval's own expansion -- cluster table -> cluster column -> cells -- on the
re-run tables, which are keyed 0..23, and reports per-arm accuracy. It reports coverage too, because
scCATCH annotates only a subset of clusters and a label it never emits must not silently count as a
correct answer.
"""
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

H = paths.HARNESS
Q = paths.ARTIFACTS
DS = "gse96583"

# The two runs that together hold all 45 cluster-level arms.
RUNDIRS = [
    "CellTypeAnnotation_gse96583_clusterfix-output",   # SCSA x13, ScInfeR x2, ScType x4
    "CellTypeAnnotation_gse96583_clusterfix2-output",  # scCATCH x13, scSorter x13
]

truth = pl.read_csv(Q / f"{DS}-nohitype" / "truth.tsv", separator="\t")
print(f"truth.tsv columns: {truth.columns}")
cells = truth["cell"].to_list()
tmap = dict(zip(cells, truth["truth"].to_list()))
clust_of = {c: str(k) for c, k in zip(cells, truth["cluster"].to_list())}
N = len(cells)
print(f"cells={N}  truth types={truth['truth'].n_unique()}  eval clusters={truth['cluster'].n_unique()}")

rows = []
for rundir in RUNDIRS:
    base = H / rundir
    if not base.is_dir():
        print(f"!! missing {rundir}")
        continue
    for d in sorted(base.glob("CellTypeAnnotation_*")):
        tbl = next(iter(d.glob("*cluster2celltype.tsv")), None)
        if tbl is None:
            print(f"   (no cluster table) {d.name}")
            continue
        ct = pl.read_csv(tbl, separator="\t")
        lab_col = [c for c in ct.columns if c not in ("Cluster", "Size", "cluster", "size")]
        if not lab_col:
            print(f"   (no label column) {d.name}")
            continue
        lab_col = lab_col[0]
        c2l = {}
        for cl, lab in zip(ct["Cluster"].to_list(), ct[lab_col].to_list()):
            c2l[str(cl)] = None if lab is None else str(lab)

        n_correct = n_labelled = n_unknown = n_missing_cluster = 0
        for c in cells:
            cl = clust_of.get(c)
            if cl not in c2l:
                n_missing_cluster += 1          # cluster absent from the arm's table
                continue
            lab = c2l[cl]
            if lab is None or lab.strip() == "" or lab.strip().lower() in ("na", "nan", "unknown",
                                                                           "unassigned", "none"):
                n_unknown += 1
                continue
            n_labelled += 1
            if lab.strip() == tmap[c].strip():
                n_correct += 1

        # acc_n: unlabelled / unknown counted wrong (what the eval's expansion yields).
        rows.append({
            "arm": d.name.replace("CellTypeAnnotation_", ""),
            "run": rundir.split("_")[-1].replace("-output", ""),
            "in_table": ct.height,
            "acc_n": round(n_correct / N, 4),
            "acc_labelled": round(n_correct / n_labelled, 4) if n_labelled else 0.0,
            "labelled": n_labelled,
            "unknown": n_unknown,
            "no_row": n_missing_cluster,
        })

out = pl.DataFrame(rows).sort("acc_n", descending=True)
print(f"\n=== {len(rows)} cluster-level arms on the corrected partition ===")
print(out)

print("\n=== the specific numbers that were scrambled ===")
for want in ["ScType_AutoBoth", "scSorter_AutoPos8527", "scCATCH_CellMarker",
             "scCATCH_scCATCH", "SCSA_CellMarker", "ScType_AutoPos8525"]:
    m = out.filter(pl.col("arm") == want)
    if m.height:
        r = m.row(0, named=True)
        print(f"  {want:<22} acc={r['acc_n']:.4f}  labelled={r['labelled']}/{N}  "
              f"unknown={r['unknown']}  no-row={r['no_row']}  clusters_in_table={r['in_table']}")
    else:
        print(f"  {want:<22} (not found)")

print(f"\ncluster-level arms: n={out.height}  median acc_n={out['acc_n'].median():.4f}  "
      f"min={out['acc_n'].min():.4f}  max={out['acc_n'].max():.4f}")
chance = 1.0 / truth["truth"].n_unique()
print(f"chance (1/{truth['truth'].n_unique()} types) = {chance:.4f}   "
      f"arms below chance: {out.filter(pl.col('acc_n') < chance).height}")
paths.OUTPUT.mkdir(parents=True, exist_ok=True)
out.write_csv(paths.OUTPUT / "clusterfix-rescore.tsv", separator="\t")
print(f"\nwrote {paths.OUTPUT / 'clusterfix-rescore.tsv'}")
