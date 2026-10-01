# `harness/` — the annotation pipeline that runs the benchmark arms

This is the code that produced every per-arm number in the review's Section 6 demonstration, in
Figure 3 and in Supplementary Table S3. It is the arm runner, the evaluator, the marker-resource
trainers and the three scoped repair runners, plus the per-dataset configuration that binds them.

Every file carries a `WHAT / REVIEW / SOURCE` header comment naming what it does, which manuscript
element it produces and its path within this package.

## Layout

```
harness/
├── src/cell_type_annotation/          the harness package
│   ├── run-test.py                    THE ARM RUNNER — declares the full roster (201 arm classes)
│   ├── run-test-nosctype.py           the same roster as of 2026-09-26, ScType family removed
│   ├── train.py                       marker-resource training (hitype weights, Garnett classifiers)
│   ├── eval.py                        THE EVALUATOR — label mapping + metrics + report figures
│   ├── report.py                      pipeline provenance (pipelines.json)
│   ├── check_arms.py                  arm-coverage guard (declared vs finished)
│   ├── stability.py                   comparator stability / silent-zero-coverage check
│   ├── annotation.py                  the first, minimal pipeline (ancestor of run-test.py)
│   ├── clusterfix-gse96583.py         repair run #1 — the 54 cluster-level arms
│   ├── clusterfix2-gse96583.py        repair run #2 — scCATCH x13 + scSorter x13
│   ├── clusterfix3-gse96583.py        repair run #3 — ScType x13 (needs ../patches/)
│   ├── scaleout-maca-scsa.py          the 26 MACA/SCSA arms, scoped
│   └── poc-maca-scsa.py               the 2-arm ancestor of the above
└── benchmark/
    ├── pbmc3k/                        dataset 1 (10x Genomics 3k PBMC)
    └── gse96583/                      dataset 2 (GEO GSE96583)
```

## Datasets

| | `pbmc3k` | `gse96583` |
|---|---|---|
| Source | `SeuratData::pbmc3k.final` | GEO GSE96583 (ctrl/stim 10x matrices + the two label tables) |
| Truth column | `seurat_annotations` | `type` |
| Partition column used by the evaluation | `RNA_snn_res.0.5` | `RNA_snn_res.0.5` (24 clusters) |
| Cluster purity | 9 of 9 pure clusters | 0 of 24 pure clusters |
| Raw data redistributed here? | no | no |

Both datasets are public and are **not** redistributed; `data-prep.R` fetches and caches them
(see `benchmark/<ds>/data-prep.sh`). No `.qs` object, no cached API dump and no publisher PDF is in
this package.

## Run order

```bash
cd benchmark/<ds> && bash data-prep.sh          # build <ds>.qs + the 70/30 train/test split (seed 8525)
uv run src/cell_type_annotation/train.py    @benchmark/<ds>/train.toml       # marker resources
uv run src/cell_type_annotation/run-test.py @benchmark/<ds>/run-train.toml   # train-split arms
uv run src/cell_type_annotation/run-test.py @benchmark/<ds>/run-test.toml    # test-split arms
uv run src/cell_type_annotation/check_arms.py --ds <ds>                      # did every declared arm finish?
make eval DS=<ds>                                                            # evaluate + report
```

Requires the `pipen` / `biopipen` stack and, for the R-backed arms, a working R with Seurat.
The ScType arms additionally require the patch in `../patches/` — without it they abort with
`arguments imply differing number of rows: 1, 0`.

## Reproducing the *corrected* gse96583 numbers

The pre-repair run (`run-test.toml`) keyed its cluster-level arms on `seurat_clusters`, which
`benchmark/gse96583/data-prep.R` leaves aliased to the last resolution it looped over
(1.5 → 32 clusters) while `eval.toml` expands labels over `RNA_snn_res.0.5` (24 clusters). Every
cluster-level arm in that run was therefore scrambled. The repair is three scoped re-runs, each in
its own pipeline directory so nothing on disk is overwritten:

```bash
uv run src/cell_type_annotation/clusterfix-gse96583.py  @benchmark/gse96583/clusterfix.toml   # 54 arms -> 20 done
uv run src/cell_type_annotation/clusterfix2-gse96583.py @benchmark/gse96583/clusterfix2.toml  # remaining 26
uv run src/cell_type_annotation/clusterfix3-gse96583.py @benchmark/gse96583/clusterfix3.toml  # ScType x13
```

Three runs are needed because a failing arm ends the rest of the pipen schedule while the pipeline
still exits 0 and does not resume — see `check_arms.py` and the `error_strategy = "ignore"` line in
each config. The corrected per-arm accuracies (over all cells and over labelled cells only) are then
recomputed by `../analysis/score-clusterfix.py`.

## Files without an in-file header

Two files in this subtree carry no header comment, deliberately, because a leading comment line
would corrupt them:

* `benchmark/pbmc3k/mapping.tsv` and `benchmark/gse96583/mapping.tsv` — the label-mapping tables read
  positionally by `eval.py` (`tool`, `label`, `truth`, `coarse`). Their role is described here.
