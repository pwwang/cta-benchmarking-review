#!/usr/bin/env python
# --------------------------------------------------------------------------
# WHAT   Tests the corroboration hypothesis for why family-axis groups are unidentifiable.
#        For each injected group and unit it computes the group's committed plurality label,
#        the same for non-members, and the modal label over all arms; reports
#        corroboration, max_impostor and the group's culprit-identification hit rate.
# REVIEW Section 3 (arm redundancy / blame): why a corrupted group can only be blamed to
#        the extent its members are NOT echoed by the rest of the roster.
# RUN    python <this file>   (from the package root)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Why are family-axis groups unidentifiable? Test the corroboration hypothesis.

Hypothesis: a corrupted group can be blamed only to the extent that its members are *not* echoed by the
other arms. If the rest of the roster says the same thing the group says, the failure is not separable
(blame is symmetric between the group and its corroborators), so `argmax_g q[c,g]` lands elsewhere.

For each group in the injection set, per unit:
  * the group's committed plurality label (modal code in 1..T over its members),
  * the same for the non-members,
  * the modal label over ALL arms.
Reported per group:
  corroboration = fraction of units where the group's plurality equals the non-members' plurality
  max_impostor  = the best agreement achieved by any OTHER group's plurality (a near-duplicate group)
  hit_rate      = the group's culprit-identification rate from the injection matrix (for comparison)

Usage: python <this>                   (from the package root)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

ART = paths.ARTIFACTS / "pbmc3k"
TAU = 0.5  # unused here but kept for parity with the model's vocabulary

votes = pl.read_csv(ART / "votes.tsv", separator="\t")
meta = pl.read_csv(ART / "resources.tsv", separator="\t")
inj = pl.read_csv(ART / "injections.tsv", separator="\t")

T = int(votes["code"].max()) - 1  # codes 1..T committed, T+1 OTHER, 0 ABSTAIN
units = sorted(votes["unit"].unique().to_list())
arms = meta["arm"].to_list()

ui = {u: i for i, u in enumerate(units)}
ai = {a: i for i, a in enumerate(arms)}
y = np.full((len(units), len(arms)), -1, dtype=np.int64)
y[
    votes["unit"].replace_strict(ui, return_dtype=pl.Int64).to_numpy(),
    votes["annotator"].replace_strict(ai, return_dtype=pl.Int64).to_numpy(),
] = votes["code"].to_numpy()


def committed_plurality(mask: np.ndarray) -> np.ndarray:
    """(N,) modal committed code (1..T) per unit over the arms selected by `mask`; 0 if none."""
    sub = y[:, mask]
    out = np.zeros(sub.shape[0], dtype=np.int64)
    for i in range(sub.shape[0]):
        row = sub[i]
        row = row[(row >= 1) & (row <= T)]
        if row.size:
            vals, counts = np.unique(row, return_counts=True)
            out[i] = int(vals[np.argmax(counts)])
    return out


GROUPS = [
    ("base_source", "CellMarker"),
    ("base_source", "ScTypeDBFull"),
    ("base_source", "AutoBoth"),
    ("base_source", "scCATCH"),
    ("family", "scorer"),
    ("family", "model"),
]

masks = {}
for axis, name in GROUPS:
    m = (meta[axis] == name).to_numpy()
    masks[(axis, name)] = m

hit = (
    inj.filter(pl.col("method") == "quorum")
    .group_by("group")
    .agg(pl.col("hit").fill_null(0).mean().round(3).alias("hit_rate"))
)
hit_rate = dict(zip(hit["group"].to_list(), hit["hit_rate"].to_list()))

all_masks = {k: v for k, v in masks.items()}
rows = []
for key, m in all_masks.items():
    g = committed_plurality(m)
    others = committed_plurality(~m)
    use = (g > 0) & (others > 0)
    corrob = float((g[use] == others[use]).mean()) if use.any() else float("nan")
    impr = []
    for other_key, om in all_masks.items():
        if other_key == key:
            continue
        o = committed_plurality(om)
        u = (g > 0) & (o > 0)
        if u.any():
            impr.append((other_key[1], float((g[u] == o[u]).mean())))
    best = max(impr, key=lambda t: t[1]) if impr else ("-", float("nan"))
    rows.append(
        {
            "axis": key[0],
            "group": key[1],
            "members": int(m.sum()),
            "corroboration_by_others": round(corrob, 3),
            "max_impostor": best[0],
            "max_impostor_agree": round(best[1], 3),
            "hit_rate": hit_rate.get(key[1], float("nan")),
        }
    )

print(f"units={len(units)} arms={len(arms)} T={T} (codes 0=ABSTAIN, 1..{T}=committed, {T + 1}=OTHER)")
print()
print(
    pl.DataFrame(rows)
    .sort("hit_rate")
)
print()
print("rows sorted by hit_rate: if the hypothesis holds, low hit_rate goes with high corroboration")
print("(REFUTED above: corroboration is 0.75-0.92 for every group, identifiable or not.)")

# --- the actual mechanism: is the corruption expressed at the granularity the lattice blames? -------
# A group is identifiable when some lattice group (a base source) is almost entirely corrupted, so the
# failure shows up as one failed column of q. A family injects across several sources, so each source is
# only partly corrupted -> the evidence for any single column is diluted.
print()
print("=== lattice dilution: max fraction of a base-source group that the injection corrupts ===")
lattice = sorted(meta["base_source"].unique().to_list())
rows2 = []
for key, m in all_masks.items():
    per_source = {s: float((( meta["base_source"] == s).to_numpy() & m).sum()) / float((meta["base_source"] == s).sum()) for s in lattice}
    worst = max(per_source.values())
    best_src = max(per_source, key=lambda s: per_source[s])
    rows2.append(
        {
            "axis": key[0],
            "group": key[1],
            "max_source_corrupted": round(worst, 3),
            "at_source": best_src,
            "n_sources_touched": sum(1 for v in per_source.values() if v > 0),
            "hit_rate": hit_rate.get(key[1], float("nan")),
        }
    )
print(pl.DataFrame(rows2).sort("max_source_corrupted"))
