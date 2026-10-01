# --------------------------------------------------------------------------
# WHAT   Marker-resource analysis on the corrected no-hitype rosters: (1) which tool is
#        most accurate on the AutoPos resources and how the best such arm compares with the
#        fitted models; (2) which resource is most accurate per tool and pooled, and whether
#        the positive-only resources beat the mixed ones (AutoBoth = positive + negative);
#        (4) cell-level vs cluster-level arms.
#        Metric identical to the baselines scripts: acc_all over every cell, an abstention
#        or a missing vote counts as wrong, ties are not votes.
# REVIEW Section 6 marker-resource claims (and the direction-of-marker-effect observation).
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Marker-resource analysis on the corrected (no-hitype) rosters.

Answers, from votes already on disk:
  (1) which tool is most accurate on the AutoPos marker resources, and how the best such
      arm compares with the fitted models;
  (2) which marker resource is most accurate, per tool and pooled; do the positive-only
      resources beat the mixed ones (`AutoBoth` = positive + negative)?
  (4) cell-level vs cluster-level arms.

Metric identical to the other baseline scripts in the review project's analysis workspace:
acc_all over every cell, an abstention or a missing vote counts as wrong, ties are not votes.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402
from reconcile_core import Vocabulary  # noqa: E402

DATASETS = {"pbmc3k": paths.ARTIFACTS / "pbmc3k-nohitype",
            "gse96583": paths.ARTIFACTS / "gse96583-nohitype"}
# fitted models, from workspace-docs/NOHITYPE-RESULTS.md
MODELS = {"pbmc3k": {"DS": 1.0000, "AGG": 1.0000}, "gse96583": {"DS": 0.8927, "AGG": 0.8946}}


def arm_table(a: Path):
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
    rows = []
    for j, arm in enumerate(arm_cols):
        hit = (Y[:, j] == y_true) & committed[:, j]
        const = True
        for c in np.unique(cl_arr):
            sel = (cl_arr == c) & committed[:, j]
            if sel.sum() and len(np.unique(Y[sel, j])) > 1:
                const = False
                break
        tool, resource = arm.split("_", 1)
        rows.append((tool, resource, hit.mean(), committed[:, j].mean(), const))
    return rows, N, T, len(arm_cols)


for ds, path in DATASETS.items():
    rows, N, T, A = arm_table(Path(path))
    accs = np.array([r[2] for r in rows])
    print(f"\n{'=' * 78}\n{ds}: {N} cells, {A} arms, T={T}   best arm {accs.max():.4f}   "
          f"DS {MODELS[ds]['DS']:.4f}   AGG {MODELS[ds]['AGG']:.4f}")

    # ---- (1) AutoPos resources: which tool ----
    ap = [r for r in rows if r[1].startswith("AutoPos")]
    print(f"\n--- (1) AutoPos arms ({len(ap)}): tool ranking ---")
    by_tool = {}
    for t, res, acc, cov, const in ap:
        by_tool.setdefault(t, []).append((res, acc))
    for t, v in sorted(by_tool.items(), key=lambda kv: -max(x[1] for x in kv[1])):
        seeds = ", ".join(f"{r.replace('AutoPos', 's')}={a:.4f}" for r, a in sorted(v))
        print(f"  {t:10s} n={len(v)}  best {max(a for _, a in v):.4f}   {seeds}")
    t1, r1, a1, _, _ = max(ap, key=lambda r: r[2])
    print(f"  BEST AutoPos arm: {t1}_{r1}  {a1:.4f}  "
          f"(AGG {MODELS[ds]['AGG']:.4f} -> {MODELS[ds]['AGG'] - a1:+.4f})")

    # ---- (2) resource ranking, pooled; and per tool ----
    print(f"\n--- (2) marker resource, pooled over tools ---")
    by_res = {}
    for t, res, acc, cov, const in rows:
        by_res.setdefault(res, []).append((t, acc))
    for res, v in sorted(by_res.items(), key=lambda kv: -np.mean([x[1] for x in kv[1]])):
        best_t, best_a = max(v, key=lambda x: x[1])
        mark = "  (pos-only)" if ("Pos" in res or res.startswith("AutoPos")) else ""
        print(f"  {res:20s} n={len(v):2d}  mean {np.mean([x[1] for x in v]):.4f}  "
              f"best {best_a:.4f} ({best_t}){mark}")

    # ---- pos-only vs mixed, paired within tool ----
    print(f"\n--- (2b) positive-only vs mixed markers, paired by tool ---")
    pairs = [("CellMarker", "CellMarkerPos"), ("ScTypeDBFull", "ScTypeDBFullPos"),
             ("ScTypeDBShort", "ScTypeDBShortPos"), ("AutoPos8525", "AutoBoth"),
             ("AutoPos8526", "AutoBoth"), ("AutoPos8527", "AutoBoth")]
    acc_map = {(t, r): a for t, r, a, _, _ in rows}
    printed = False
    for plain, pos in pairs:
        tools = sorted({t for (t, r) in acc_map if r == plain} & {t for (t, r) in acc_map if r == pos})
        for t in tools:
            d = acc_map[(t, plain)] - acc_map[(t, pos)]
            if plain.startswith("AutoPos"):
                d = acc_map[(t, pos)] - acc_map[(t, plain)]  # AutoBoth has positives + negatives
                lab = f"{t}: AutoBoth - {plain}"
            else:
                lab = f"{t}: {plain} - {pos}"
            print(f"  {lab:44s} {d:+.4f}")
            printed = True
    if not printed:
        print("  (no tool has both variants on this roster)")

    # ---- (4) cluster vs cell level ----
    cl = [r for r in rows if r[4]]
    ce = [r for r in rows if not r[4]]
    print(f"\n--- (4) cluster-level vs cell-level ---")
    print(f"  cluster-level: n={len(cl):2d}  median {np.median([r[2] for r in cl]):.4f}  "
          f"max {max(r[2] for r in cl):.4f}")
    print(f"  cell-level:    n={len(ce):2d}  median {np.median([r[2] for r in ce]):.4f}  "
          f"max {max(r[2] for r in ce):.4f}")

    # ---- top 10 arms ----
    print(f"\n--- top 10 arms ---")
    for t, res, acc, cov, const in sorted(rows, key=lambda r: -r[2])[:10]:
        flag = "  CLUSTER-LEVEL" if const else ""
        print(f"  {t:10s} {res:20s} {acc:.4f}  cov {cov:.3f}{flag}")

print("\nMARKER_RESOURCE_ANALYSIS_DONE")
