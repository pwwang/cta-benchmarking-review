# --------------------------------------------------------------------------
# WHAT   Error bars for the two honest wins. Three uncertainties, reported separately
#        because they answer different questions:
#          (i)   CELL bootstrap    -- resample the 792 test cells (accuracy CI on this dataset);
#          (ii)  CLUSTER bootstrap -- resample the 9 clusters (the honest unit on pbmc3k,
#                                    where cells within a cluster share the truth);
#          (iii) ROSTER bootstrap  -- resample the ARMS with replacement and REFIT both
#                                    methods (how much the answer depends on which arms
#                                    you happen to have).
#        Plus McNemar's exact test on the paired per-cell correctness (Dawid-Skene vs AGG).
#        Deliberately reuses the reconcile script's own helpers (unit_clusters, code_matrix,
#        score) so nothing drifts from reconcile.tsv.
# REVIEW Section 5 / the uncertainty table; feeds the forest plot rebuilt by
#        rebuild-forest.py.
# RUN    python <this file> [gse96583]   (from the package root)
#        Held-out inputs come from $HELDOUT_DIR (see paths.py; default $CTA_DATA/heldout).
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Error bars for the two honest wins.

Three uncertainties, all reported separately because they answer different questions:

 (i)   CELL bootstrap      — resample the 792 test cells. CI for accuracy on this dataset.
 (ii)  CLUSTER bootstrap   — resample the 9 clusters (cells within a cluster share the truth on
                             pbmc3k, so this is the honest unit; cell bootstrap understates the CI).
 (iii) ROSTER bootstrap    — resample the ARMS with replacement and REFIT both methods. CI for the
                             method's expected performance over rosters, i.e. "how much does the
                             answer depend on which arms you happen to have".
Plus McNemar's exact test on the paired per-cell correctness (DS vs AGG).

Semantics deliberately reuse the helpers shipped beside this script in
`analysis/reconcile_helpers.py` (`unit_clusters`, `code_matrix`, `score`) so nothing drifts from the
numbers in reconcile.tsv.

Run (pbmc3k default):   python <this file>          (from the package root)
Run for another dataset: python <this file> gse96583
Held-out inputs come from $HELDOUT_DIR (see paths.py; default $CTA_DATA/heldout).
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))   # the helpers shipped beside this script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root (paths.py, reconcile_core.py)
import paths  # noqa: E402
import reconcile_helpers as R  # noqa: E402
from reconcile_core import fit  # noqa: E402
from reconcile_core import membership_matrix  # noqa: E402

TAU = 0.5
B_CELL, B_CLUSTER, B_ROSTER = 2000, 2000, 100
RNG = np.random.default_rng(20260925)


def load(ds: str, partition: str | None, axes: tuple[str, ...]):
    # $CTA_ARTIFACTS (paths.ARTIFACTS) holds the derived vote/truth/resource tables;
    # an explicit absolute path or an "artifacts/..." prefix still overrides it.
    base = Path(ds) if ds.startswith("/") else (
        paths.ARTIFACTS / ds if not ds.startswith("artifacts") else Path(ds))
    votes = pl.read_csv(base / "votes.tsv", separator="\t")
    truth = pl.read_csv(base / "truth.tsv", separator="\t")
    meta = pl.read_csv(base / "resources.tsv", separator="\t")
    units = votes["unit"].unique(maintain_order=True).to_list()
    vocab = sorted(truth["truth"].unique().to_list())
    T = len(vocab)
    tcode = {lab: i + 1 for i, lab in enumerate(vocab)}
    ut = pl.DataFrame({"unit": units}).join(
        truth.select(pl.col("cell").alias("unit"), "truth", "cluster"), on="unit", how="left")
    clusters = R.unit_clusters(ut, partition)
    true = ut["truth"].replace_strict(tcode, return_dtype=pl.Int64).to_numpy()
    arms = meta["arm"].to_list()
    y = R.code_matrix(votes.filter(pl.col("annotator").is_in(arms)), arms, units)
    members, gnames = membership_matrix(meta, axes=axes)
    return dict(base=base, units=units, clusters=clusters, true=true, y=y, members=members,
                T=T, gnames=gnames, n_arms=len(arms))


def acc_ok(res, true):
    pred, com = R.score(res.gamma, TAU)
    return (pred == true) & com


def delta_on(sel, cd, cq):
    """acc(AGG) - acc(DS) over the cells in `sel` (an index array)."""
    return float(cq[sel].mean() - cd[sel].mean())


def boot_cell(cd, cq, B):
    n = len(cd)
    idx = RNG.integers(0, n, size=(B, n))
    d = cq[idx].mean(axis=1) - cd[idx].mean(axis=1)
    a_ds = cd[idx].mean(axis=1)
    a_q = cq[idx].mean(axis=1)
    return d, a_ds, a_q


def boot_cluster(cd, cq, clusters, B):
    cs = np.unique(clusters)
    groups = {c: np.flatnonzero(clusters == c) for c in cs}
    ds_d, ds_a, ds_q = [], [], []
    for _ in range(B):
        pick = RNG.choice(len(cs), size=len(cs), replace=True)
        sel = np.concatenate([groups[cs[i]] for i in pick])
        ds_d.append(delta_on(sel, cd, cq))
        ds_a.append(float(cd[sel].mean()))
        ds_q.append(float(cq[sel].mean()))
    return np.array(ds_d), np.array(ds_a), np.array(ds_q)


def mcnemar(cd, cq):
    b = int((~cd & cq).sum())   # DS wrong, AGG right
    c = int((cd & ~cq).sum())   # DS right, AGG wrong
    n = b + c
    if n == 0:
        return b, c, 1.0
    # exact two-sided binomial test (p = 0.5), no scipy needed
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return b, c, min(1.0, p)


def roster_boot(d, B):
    K = d["y"].shape[1]
    out = []
    t0 = time.time()
    for i in range(B):
        idx = RNG.integers(0, K, size=K)
        yb = d["y"][:, idx]
        mb = d["members"][idx]
        ds = fit(yb, d["clusters"], mb[:, :0], d["T"], max_iter=300)
        q = fit(yb, d["clusters"], mb, d["T"], max_iter=300)
        cd, cq = acc_ok(ds, d["true"]), acc_ok(q, d["true"])
        out.append((float(cd.mean()), float(cq.mean())))
        if (i + 1) % 25 == 0:
            print(f"    roster bootstrap {i+1}/{B}  ({time.time()-t0:.0f}s)", flush=True)
    a = np.array(out)
    return a[:, 1] - a[:, 0], a[:, 0], a[:, 1]


def analyse(name, ds, partition, axes, b_roster):
    print(f"\n================ {name} ================", flush=True)
    d = load(ds, partition, axes)
    print(f"  {d['n_arms']} arms, G={d['members'].shape[1]}, C={int(d['clusters'].max())+1}, "
          f"{len(d['units'])} cells, T={d['T']}", flush=True)
    rds = fit(d["y"], d["clusters"], d["members"][:, :0], d["T"], max_iter=300)
    rq = fit(d["y"], d["clusters"], d["members"], d["T"], max_iter=300)
    cd, cq = acc_ok(rds, d["true"]), acc_ok(rq, d["true"])
    acc_ds, acc_q = float(cd.mean()), float(cq.mean())
    print(f"  DS     acc_all {acc_ds:.4f}  loglik {rds.loglik[-1]:.3f}  iters {rds.n_iter}")
    print(f"  AGG acc_all {acc_q:.4f}  loglik {rq.loglik[-1]:.3f}  iters {rq.n_iter}"
          f"  no_failure_states {rq.no_failure_states}")
    print(f"  delta  {acc_q - acc_ds:+.4f}")

    b, c, p = mcnemar(cd, cq)
    print(f"  McNemar exact: DS-wrong/AGG-right {b}, DS-right/AGG-wrong {c}, two-sided p = {p:.4g}")

    for label, (dd, ad, aq) in (("cell", boot_cell(cd, cq, B_CELL)),
                                ("cluster", boot_cluster(cd, cq, d["clusters"], B_CLUSTER))):
        print(f"  {label:7s} bootstrap ({len(dd)}): delta {dd.mean():+.4f} "
              f"[{np.percentile(dd,2.5):+.4f}, {np.percentile(dd,97.5):+.4f}]  "
              f"DS [{np.percentile(ad,2.5):.4f}, {np.percentile(ad,97.5):.4f}]  "
              f"Q [{np.percentile(aq,2.5):.4f}, {np.percentile(aq,97.5):.4f}]  "
              f"P(delta>0) {float((dd>0).mean()):.3f}", flush=True)

    print(f"  roster bootstrap ({b_roster} refits) ...", flush=True)
    dd, ad, aq = roster_boot(d, b_roster)
    print(f"  roster  bootstrap ({len(dd)}): delta {dd.mean():+.4f} "
          f"[{np.percentile(dd,2.5):+.4f}, {np.percentile(dd,97.5):+.4f}]  "
          f"DS [{np.percentile(ad,2.5):.4f}, {np.percentile(ad,97.5):.4f}]  "
          f"Q [{np.percentile(aq,2.5):.4f}, {np.percentile(aq,97.5):.4f}]  "
          f"P(delta>0) {float((dd>0).mean()):.3f}")
    return dict(name=name, acc_ds=acc_ds, acc_q=acc_q, delta=acc_q - acc_ds, mcnemar=(b, c, p),
                cell=(float(boot_cell(cd, cq, 400)[0].mean()), None),
                roster_mean=float(dd.mean()))


HELDOUT = paths.HELDOUT
DS = sys.argv[1] if len(sys.argv) > 1 else "pbmc3k"


if __name__ == "__main__":
    print(f"B_CELL {B_CELL}  B_CLUSTER {B_CLUSTER}  B_ROSTER {B_ROSTER}  seed 20260925  ds={DS}")
    analyse(f"crossed roster G=21 ({DS}, canonical partition)", DS, None,
            ("base_source", "family"), B_ROSTER)
    # Held-out inputs live at $HELDOUT_DIR (see paths.py); they once sat in a scratch directory
    # that did not survive a reboot. If the dir is missing, say so loudly instead of degrading
    # silently.
    if (HELDOUT / "s0").exists():
        analyse("held-out seed 0 (partition from 140 arms, measured on 35)", str(HELDOUT / "s0"),
                str(HELDOUT / "s0" / "partition.tsv"), ("base_source",), 200)
    else:
        print(f"\nWARNING: held-out inputs missing at {HELDOUT} — the held-out uncertainty block "
              f"was NOT computed. Restore the held-out tree under $HELDOUT_DIR before quoting any "
              f"held-out numbers.")
