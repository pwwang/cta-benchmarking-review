# --------------------------------------------------------------------------
# WHAT   Independent recomputation of the gse96583 no-hitype plurality vote with a
#        different implementation (polars group-by counts instead of a numpy count matrix),
#        plus forensics on whether ties, abstentions or label concentration drive it.
# REVIEW Section 6: was written because the forked baselines script reported an all-arm
#        majority vote far below the best single arm -- a number that would have gone into
#        the manuscript, so it was recomputed independently. That collapse was later shown
#        to be the aliasing defect (see FACTS.md section E).
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Independent recomputation of the gse96583 no-hitype plurality vote, plus forensics.

Why: the forked baselines script reports majority-vote acc_all 0.6933 on 10,947 cells, far below the
best single arm (0.8913). That number would go in the manuscript, so recompute it with a different
implementation (polars group-by counts rather than a numpy count matrix) and find out whether ties,
abstentions, or label concentration drive the collapse.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402
from reconcile_core import Vocabulary  # noqa: E402

A = Path(sys.argv[1]) if len(sys.argv) > 1 else paths.ARTIFACTS / "gse96583-nohitype"
votes = pl.read_csv(A / "votes.tsv", separator="\t")
truth = pl.read_csv(A / "truth.tsv", separator="\t")
vocab = Vocabulary(sorted(truth["truth"].unique().to_list()))
T = vocab.T

code = {t: vocab.code(t) for t in truth["truth"].unique().to_list()}
inv = {v: k for k, v in code.items()}
truth_df = truth.with_columns(
    pl.col("truth").replace_strict(code, return_dtype=pl.Int64).alias("y")
).select("cell", "y")

v = votes.filter((pl.col("code") >= 1) & (pl.col("code") <= T))  # committed only

c = v.group_by(["unit", "code"]).len()
top = c.group_by("unit").agg(pl.col("len").max().alias("n_max")).join(c, on="unit")
top = top.filter(pl.col("len") == pl.col("n_max"))
w = top.group_by("unit").agg(
    pl.col("n_max").first().alias("n_max"),
    pl.len().alias("n_tied"),
    pl.col("code").min().alias("pred_min"),
)
df = truth_df.join(w, left_on="cell", right_on="unit", how="left")
n = df.height
answered = df["pred_min"].is_not_null()
tied = df["n_tied"] > 1

acc_all = ((df["pred_min"] == df["y"]) & answered & ~tied).sum() / n
acc_tb = ((df["pred_min"] == df["y"]) & answered).sum() / n
print(f"units {n}  answered {answered.sum()}  ties {tied.sum()} ({tied.sum() / n:.3f})")
print(f"plurality acc_all (ties wrong)       {acc_all:.4f}")
print(f"plurality acc_all (ties -> min code) {acc_tb:.4f}")

print("\npredicted label distribution (top 5):")
for r in df.filter(answered & ~tied).group_by("pred_min").len().sort("len", descending=True).head(5).iter_rows():
    print(f"  {inv[r[0]]:20s} {r[1]:6d}  {r[1] / n:.3f}")
print("truth label distribution:")
for r in truth_df.group_by("y").len().sort("len", descending=True).iter_rows():
    print(f"  {inv[r[0]]:20s} {r[1]:6d}  {r[1] / n:.3f}")

wide = v.pivot(on="annotator", index="unit", values="code", aggregate_function="first")
per = []
for a in wide.columns[1:]:
    s = wide.select("unit", a).drop_nulls().rename({a: "pred"})
    j = truth_df.join(s, left_on="cell", right_on="unit", how="left")
    per.append((a, ((j["pred"] == j["y"]).fill_null(False)).sum() / n))
per.sort(key=lambda r: -r[1])
accs = np.array([p[1] for p in per])
print(f"\nper-arm accuracy: mean {accs.mean():.4f}  median {np.median(accs):.4f}  "
      f"max {accs.max():.4f}  min {accs.min():.4f}")
print(f"arms >= 0.85: {(accs >= 0.85).sum()}   arms < 0.60: {(accs < 0.60).sum()}   of {len(accs)}")
print("worst 5:", [(a, round(x, 4)) for a, x in per[-5:]])
print("VERIFY_VOTE_DONE")
