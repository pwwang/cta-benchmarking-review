#!/usr/bin/env python
# --------------------------------------------------------------------------
# WHAT   The same decomposition on the CORRECTED gse96583 artifacts; the only change from
#        vote-decomposition.py is the DATASETS dict, which adds the repaired dataset and
#        keeps the pre-repair one as the read-only "was" control. Metric code identical.
# REVIEW Section 6 / Figure 3: the corrected all-arm plurality (0.8738) and
#        cell-level-only plurality (0.8711, unchanged), and the evidence that the
#        pre-repair collapse was the defect and not a property of ensembling.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Vote decomposition on the CORRECTED gse96583 artifacts (fork of vote-decomposition.py).

Only the DATASETS dict differs: the corrected dataset is scored, plus the pre-fix
gse96583-nohitype artifacts as the "was" control (read-only).  Metric code identical.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402
from reconcile_core import Vocabulary  # noqa: E402

DATASETS = {
    "gse96583-fixed (corrected)": paths.ARTIFACTS / "gse96583-fixed-nohitype",
    "gse96583-nohitype (pre-fix, scrambled)": paths.ARTIFACTS / "gse96583-nohitype",
}


def plurality(Y, committed, y_true, sel):
    sub, n_commit = Y[:, sel], committed[:, sel]
    T = int(max(y_true.max(), 1))
    counts = np.zeros((Y.shape[0], T), dtype=int)
    for t in range(1, T + 1):
        counts[:, t - 1] = ((sub == t) & n_commit).sum(axis=1)
    top = counts.max(axis=1)
    tied = (counts == top[:, None]).sum(axis=1) > 1
    pred = np.where(top > 0, counts.argmax(axis=1) + 1, 0)
    answered = (top > 0) & (~tied)
    return (((pred == y_true) & answered).mean(), answered.mean(), tied.mean())


for ds, a in DATASETS.items():
    votes = pl.read_csv(a / "votes.tsv", separator="\t")
    truth = pl.read_csv(a / "truth.tsv", separator="\t")
    vocab = Vocabulary(sorted(truth["truth"].unique().to_list()))
    T = vocab.T
    code = {t: vocab.code(t) for t in truth["truth"].unique().to_list()}

    units = truth["cell"].to_list()
    cl_arr = truth["cluster"].to_numpy()
    y_true = np.array([code[t] for t in truth["truth"].to_list()])
    N = len(units)

    wide = votes.pivot(on="annotator", index="unit", values="code", aggregate_function="first")
    uindex = pl.DataFrame({"unit": units, "i": np.arange(N)})
    wide = uindex.join(wide, on="unit", how="left").sort("i")
    arm_cols = [c for c in wide.columns if c not in ("unit", "i")]
    Y = wide.select(arm_cols).fill_null(0).to_numpy().astype(int)
    committed = (Y >= 1) & (Y <= T)

    const = []
    for j in range(len(arm_cols)):
        ok = True
        for c in np.unique(cl_arr):
            sel = (cl_arr == c) & committed[:, j]
            if sel.sum() and len(np.unique(Y[sel, j])) > 1:
                ok = False
                break
        const.append(ok)
    const = np.array(const)
    cell_idx, clus_idx = np.where(~const)[0], np.where(const)[0]

    print(f"\n{'=' * 74}\n{ds}: {N} cells, {len(arm_cols)} arms  "
          f"({len(cell_idx)} cell-level, {len(clus_idx)} cluster-level)")
    nv = committed.sum()
    print(f"  committed votes: total {nv}  from cell-level {committed[:, cell_idx].sum():.0f} "
          f"({committed[:, cell_idx].sum() / nv:.1%})  from cluster-level "
          f"{committed[:, clus_idx].sum():.0f} ({committed[:, clus_idx].sum() / nv:.1%})")
    for label, sel in (("all arms", np.arange(len(arm_cols))), ("cell-level only", cell_idx),
                       ("cluster-level only", clus_idx)):
        acc, cov, tie = plurality(Y, committed, y_true, sel)
        print(f"  plurality over {label:20s} acc_all {acc:.4f}   coverage {cov:.3f}  ties {tie:.3f}")

    # median per-arm accuracy (abstain/missing wrong) over each class, for the report
    for label, sel in (("cell-level", cell_idx), ("cluster-level", clus_idx)):
        accs = [float(((Y[:, j] == y_true) & committed[:, j]).mean()) for j in sel]
        print(f"  per-arm acc over {label:14s} arms: n={len(accs)}  median {np.median(accs):.4f}  "
              f"min {min(accs):.4f}  max {max(accs):.4f}")

print("\nVOTE_DECOMPOSITION_DONE")
