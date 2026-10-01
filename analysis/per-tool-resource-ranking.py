# --------------------------------------------------------------------------
# WHAT   Marker-resource ranking WITHIN each tool. The pooled per-resource means are
#        confounded (tools do not use the same resources, so a resource's mean accuracy is
#        partly a statement about which tools happen to use it); the fair comparison holds
#        the tool fixed and varies only the resource.
# REVIEW Section 6 marker-resource ranking.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Marker-resource ranking WITHIN each tool.

The pooled-per-resource means are confounded: tools do not use the same resources, so a
resource's mean accuracy is partly a statement about which tools happen to use it. The fair
comparison is within a tool, where the only thing that changes is the marker resource.
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

for ds, a in DATASETS.items():
    votes = pl.read_csv(a / "votes.tsv", separator="\t")
    truth = pl.read_csv(a / "truth.tsv", separator="\t")
    vocab = Vocabulary(sorted(truth["truth"].unique().to_list()))
    T = vocab.T
    code = {t: vocab.code(t) for t in truth["truth"].unique().to_list()}
    units = truth["cell"].to_list()
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
        tool, resource = arm.split("_", 1)
        rows.append((tool, resource, (((Y[:, j] == y_true) & committed[:, j]).mean())))

    print(f"\n{'=' * 74}\n{ds}  ({N} cells)  resource ranking within each tool")
    tools = sorted({r[0] for r in rows})
    for t in tools:
        rs = sorted([r for r in rows if r[0] == t], key=lambda r: -r[2])
        if len(rs) < 2:
            print(f"  {t:10s} (single arm: {rs[0][1]} {rs[0][2]:.4f})")
            continue
        best, worst = rs[0], rs[-1]
        print(f"  {t:10s} best {best[1]:20s} {best[2]:.4f} | worst {worst[1]:20s} {worst[2]:.4f} "
              f"| spread {best[2] - worst[2]:.4f}")
        print(f"  {'':10s} all: " + "  ".join(f"{r[1]}={r[2]:.3f}" for r in rs))

    # spread of accuracy contributed by resource choice vs by tool choice
    per_res = {r for _, r, _ in rows}
    within = []
    for t in tools:
        v = [r[2] for r in rows if r[0] == t]
        if len(v) > 1:
            within.append(max(v) - min(v))
    per_tool = {}
    for t in tools:
        per_tool[t] = [x[2] for x in rows if x[0] == t]
    print(f"\n  resource choice (within-tool spread): mean {np.mean(within):.4f}  max {np.max(within):.4f}")
    print(f"  tool choice (best-arm-per-tool spread): "
          f"{max(max(v) for v in per_tool.values()) - min(max(v) for v in per_tool.values()):.4f}")

print("\nPER_TOOL_RESOURCE_DONE")
