"""The three scoring helpers ``analysis/uncertainty.py`` needs, shipped with the deposit.

These are `unit_clusters`, `code_matrix` and `score`, copied verbatim from the authors'
reconciliation script -- the script that writes `reconcile.tsv` -- so the uncertainty numbers cannot
drift from that table. They are the only three functions the re-analysis takes from it; the deposit
therefore carries no `scripts/` tree.

  unit_clusters(ut, path)  per-unit cluster ids the fit runs on: the truth column, or the ids in a
                           `--partition` TSV (relabelled dense 0..C-1), joined on cell
  code_matrix(votes, arms, units)  (N, K) code matrix, -1 (MISSING) where an arm has no row
  score(gamma, tau)        (predicted type code, committed mask) from the reconciled posteriors

Nothing else is imported from them, and nothing here is modified: only the module they live in
changed.
"""

from __future__ import annotations

import numpy as np
import polars as pl


def unit_clusters(ut: pl.DataFrame, path: str | None) -> np.ndarray:
    """Per-unit cluster ids the fit runs on: truth's own column, or `--partition`'s, joined on cell.

    Partition ids are relabelled dense 0..C-1 (sorted order) because `e_step` sizes `q` by
    `clusters.max()+1`: an id vocabulary with a hole would allocate a phantom empty cluster. With
    no `--partition` the truth column is returned untouched, so every default number is unchanged.
    """
    if path is None:
        return ut["cluster"].to_numpy()
    part = pl.read_csv(path, separator="\t")
    ids = ut.select("unit").join(
        part.select(pl.col("cell").alias("unit"), pl.col("cluster")), on="unit", how="left"
    )["cluster"]
    if ids.null_count():
        raise SystemExit(f"{path}: {ids.null_count()}/{ut.height} units have no cluster row")
    return np.unique(ids.to_numpy(), return_inverse=True)[1]


def code_matrix(votes: pl.DataFrame, arms: list[str], units: list[str]) -> np.ndarray:
    """(N, K) code matrix, -1 (MISSING) where an arm has no row for a unit."""
    ui = {u: i for i, u in enumerate(units)}
    ai = {a: i for i, a in enumerate(arms)}
    y = np.full((len(units), len(arms)), -1, dtype=np.int64)
    y[
        votes["unit"].replace_strict(ui, return_dtype=pl.Int64).to_numpy(),
        votes["annotator"].replace_strict(ai, return_dtype=pl.Int64).to_numpy(),
    ] = votes["code"].to_numpy()
    return y


def score(gamma: np.ndarray, tau: float) -> tuple[np.ndarray, np.ndarray]:
    """(predicted type code, committed mask) from the reconciled per-unit posteriors."""
    return gamma.argmax(axis=1) + 1, gamma.max(axis=1) >= tau
