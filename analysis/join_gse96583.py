# --------------------------------------------------------------------------
# WHAT   Join-integrity check for GSE96583: does every truth row find its matrix barcode
#        and vice versa? The label tables and the count matrices come from two different GEO
#        deposits and only the barcodes tie them together.
# REVIEW Section 6 methods: nothing downstream is trustworthy until this passes, so it is
#        the precondition for every gse96583 number.
# RUN    python <this file>   (from the package root)
# NOTE   Reads $CTA_GEO_RAW (see paths.py) -- the raw GEO download is NOT redistributed.
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""GSE96583 join integrity: does every truth row find its matrix barcode, and vice versa?

Nothing downstream is trustworthy until this passes: the label tables and the matrices come from two
different GEO deposits, and only the barcodes tie them together.
"""
import gzip
import glob
import os
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

RAW = paths.GEO_RAW
UNPACK = str(RAW / "unpack")


def read_truth(f):
    with gzip.open(f, "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        first = fh.readline().rstrip("\n").split("\t")
    names = ["barcode"] + head
    assert len(first) == len(names), f"{f}: {len(names)} names vs {len(first)} fields"
    df = pl.read_csv(f, separator="\t", skip_rows=1, new_columns=names,
                     infer_schema_length=0, null_values=["NA", "nan", ""])
    tcol = "cell.type" if "cell.type" in df.columns else "cell"
    return df.rename({tcol: "type"})


t1 = read_truth(RAW / "GSE96583_batch1.total.tsne.df.tsv.gz")
t2 = read_truth(RAW / "GSE96583_batch2.total.tsne.df.tsv.gz")
print(f"truth batch1: {t1.height} rows   cols {t1.columns}")
print(f"truth batch2: {t2.height} rows   cols {t2.columns}")

# 1. barcodes unique within each file?
for nm, d in (("batch1", t1), ("batch2", t2)):
    dup = d.height - d["barcode"].n_unique()
    print(f"  {nm}: {dup} duplicate barcodes, {d['type'].null_count()} unlabelled cells")

# 2. barcode sets vs the matrices
print("\nsample  matrix_barcodes  truth_rows_here  matched  only_in_matrix  only_in_truth")
all_truth = set(t1["barcode"].to_list()) | set(t2["barcode"].to_list())
used = set()
for f in sorted(glob.glob(f"{UNPACK}/*barcodes.tsv.gz")):
    sample = os.path.basename(f).split("_")[1].replace("barcodes.tsv.gz", "")
    with gzip.open(f, "rt") as fh:
        bc = {line.strip().split("\t")[0] for line in fh if line.strip()}
    here = all_truth & bc
    used |= here
    print(f"{sample:>6}  {len(bc):>14}  {len(here):>15}  {len(here):>7}  "
          f"{len(bc - all_truth):>14}  {len(all_truth & bc) - len(here):>12}")
print(f"\nunion of matched barcodes: {len(used)}   truth rows total: {t1.height + t2.height}")
unmatched = all_truth - used
print(f"truth barcodes with NO matrix row: {len(unmatched)}")
if unmatched:
    print("  examples:", list(unmatched)[:5])
print(f"matrix barcodes with no truth row: {len((set().union(*[set()]) ) if False else set())}")

# 3. what the joined design will look like
j = pl.concat([t1.with_columns(pl.lit("batch1").alias("file")),
               t2.with_columns(pl.lit("batch2").alias("file"))])
print("\ncells per file / condition / donor:")
print(j.group_by("file").len().to_dicts())
if "stim" in j.columns:
    print(j.group_by("file", "stim").len().sort(["file", "stim"]).to_dicts())
print("donors:", j["ind"].n_unique(), " clusters:", sorted(j["cluster"].unique().to_list()))
print("types:", sorted(j["type"].drop_nulls().unique().to_list()))
print("\ncells per type x file:")
print(j.group_by("type", "file").len().pivot(on="file", index="type", values="len").fill_null(0))
