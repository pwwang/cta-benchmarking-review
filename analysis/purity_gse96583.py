# --------------------------------------------------------------------------
# WHAT   Measures cluster purity in the two GSE96583 GEO label tables (cross-tab of source
#        cluster id against expert cell type, per cluster and overall) and recounts the
#        pancreas human1 CSV.
# REVIEW Section 4: the dataset-selection justification. GSE96583 has 0 of 24 pure
#        clusters against pbmc3k's 9 of 9, which is why it can expose what pbmc3k cannot.
# RUN    python <this file>   (from the package root; downloads two GEO .tsv.gz files)
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Is GSE96583 actually a good test bed? Measure the thing the pick depends on: cluster purity.

Reads the two GEO label tables (the source truth), cross-tabs the source cluster id against the
expert cell type, and reports purity per cluster + overall. Also recounts the pancreas human1 CSV
(the scoping report said 2,012 cells; my wc -l said 1,937).
"""
import gzip
import subprocess
from collections import Counter

import polars as pl

URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96583/suppl/"
FILES = ["GSE96583_batch1.total.tsne.df.tsv.gz", "GSE96583_batch2.total.tsne.df.tsv.gz"]

for f in FILES:
    subprocess.run(["curl", "-s", "--max-time", "180", "-o", f, URL + f], check=True)

frames = []
for f in FILES:
    with gzip.open(f, "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        first = fh.readline().rstrip("\n").split("\t")
    # the header omits a name for the barcode column: 7 names, 8 fields
    names = ["barcode"] + head
    assert len(first) == len(names), f"{f}: header {len(names)} names vs {len(first)} fields"
    print(f"{f}: {len(names)} columns -> {names[1:]}")
    df = pl.read_csv(f, separator="\t", skip_rows=1, new_columns=names,
                     infer_schema_length=0, null_values=["NA", "nan", ""])
    # batch1 names the type column `cell.type`, batch2 names it `cell`; column ORDER differs too
    tcol = "cell.type" if "cell.type" in df.columns else "cell"
    df = df.rename({tcol: "type"}).select(["barcode", "type", "cluster", "ind"])
    df = df.with_columns(pl.lit(f.split(".")[0]).alias("batch"))
    frames.append(df)

d = pl.concat(frames)
d = d.filter(pl.col("type").is_not_null() & (pl.col("type") != ""))
print(f"\nall cells: {d.height}   distinct types: {d['type'].n_unique()}   "
      f"distinct source clusters: {d['cluster'].n_unique()}   donors: {d['ind'].n_unique()}")
print("types:", sorted(d["type"].unique().to_list()))

# cluster -> majority type, purity = majority share (the definition used throughout this project)
tab = d.group_by(["cluster", "type"]).len(name="n")
tot = tab.group_by("cluster").agg(pl.col("n").sum().alias("cluster_n"))
maj = tab.sort("n", descending=True).group_by("cluster").first()
pur = maj.join(tot, on="cluster").with_columns(
    (pl.col("n") / pl.col("cluster_n")).alias("purity")).sort("cluster")
print("\ncluster  n   purity  majority type")
for r in pur.iter_rows(named=True):
    print(f"  {r['cluster']:>4}  {r['cluster_n']:>5}  {r['purity']:.4f}  {r['type']}")
w = d.height
overall = sum(r["purity"] * r["cluster_n"] for r in pur.iter_rows(named=True)) / w
impure = pur.filter(pl.col("purity") < 0.9999)
print(f"\noverall cluster->type purity: {overall:.4f}   (pbmc3k = 1.0000)")
print(f"impure clusters: {impure.height} of {pur.height}")
print(f"cells in impure clusters: {impure['cluster_n'].sum()} of {w}")

# donor/condition structure
print("\ncells per donor:", d.group_by("ind").len().sort("ind").to_dicts()[:12])

# pancreas recount
try:
    n = 0
    labels = Counter()
    with gzip.open("GSM2230757_human1_umifm_counts.csv.gz", "rt") as fh:
        fh.readline()
        for line in fh:
            n += 1
            labels[line.split(",")[2]] += 1
    print(f"\npancreas human1: {n} data rows, {len(labels)} labels")
    print("  ", dict(labels.most_common()))
except FileNotFoundError:
    print("\n(pancreas csv not extracted here)")
