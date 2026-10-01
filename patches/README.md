# Third-party patch: `biopipen.utils` — ScType zero-variance / empty-score guard

`biopipen-sctype-zerovariance-and-empty-scores.patch` is the **only** change to third-party code
that the review's numbers depend on. It fixes a crash in `sctype_score()` that killed every ScType
arm of the gse96583 run. The corrected ScType numbers in Section 6, in Figure 3 and in
Supplementary Table S3 were produced with this patch applied.

The patch is a minimal, **additive** change to the authors' own `biopipen.utils` R package:
57 insertions, 19 deletions, one file (`R/scrna-celltype-annotation.R`), both guards inside code
that only executes where the unpatched code raised. No behaviour changes for finite input.

---

## The crash

```
Error in data.frame(cluster = cl, type = names(es.max.cl), scores = es.max.cl) :
  arguments imply differing number of rows: 1, 0
```

The pipeline run stopped there. Because the harness runs with `error_strategy = "ignore"`, the
pipeline still exited 0 and every later arm silently never ran (see
`../harness/src/cell_type_annotation/check_arms.py`).

## Root cause

1. The benchmark fits marker tables on the **train** split and scores the **test** split, so genes
   that are all-zero (zero variance) in the test cells are plentiful.
2. `sctype_score()` z-scales the scoring matrix: `Z <- t(scale(t(scRNAseqData)))`. R's `scale()`
   returns **`NaN`** for a zero-variance gene, because it divides by a standard deviation of 0.
3. A single such gene inside a cell type's marker set turns that cell type's **whole** score vector
   into `NaN` — not just that gene's entry.
4. The all-`NA` cell-type rows are then dropped, and `es.max` can end up with **zero rows**.
5. `rowSums()` over a 0-column matrix returns `numeric(0)`, so `es.max.cl` is length 0.
6. `data.frame(cluster = cl, type = names(es.max.cl), scores = es.max.cl)` therefore mixes a
   length-1 column with a length-0 column: `arguments imply differing number of rows: 1, 0`.

## The fix — two additive guards

**Guard 1 — in `sctype_score()`, immediately after the z-scaling step:**

```r
if(!scaled) Z <- t(scale(t(scRNAseqData))) else Z <- scRNAseqData
Z[!is.finite(Z)] <- 0                       # <-- added
```

A zero-variance gene cannot discriminate anything, so its z-score contribution is taken to be 0
instead of propagating `NaN` into a whole cell type's score vector. This removes the cause.

**Guard 2 — in `.run_celltypeannotation_sctype()`, at the cluster-score merge:**

* a cluster whose score vector is empty (`length(es.max.cl) == 0`) returns `NULL` instead of a
  malformed `data.frame()`, and the `lapply()` results are wrapped in `Filter(Negate(is.null), ...)`.
  That cluster is later labelled `"Unknown"`, i.e. the arm degrades instead of aborting;
* the `rowSums(...)` call also gains `drop = FALSE`, so a single-cell cluster cannot collapse the
  score matrix to a vector;
* if **nothing** scored at this level (`cl_resutls` is `NULL` or has 0 rows), every cluster is
  labelled `"Unknown"` and the loop moves on rather than letting `data.frame()` / `dplyr` crash
  the job.

Guard 2 keeps a partially-usable result instead of an exception; it does not mask the defect,
because the `"Unknown"` labels are visible in the arm's own output and in the evaluator's
`ABSTAIN` / `Unmapped` handling.

## How to apply

From the root of a `biopipen.utils` checkout:

```bash
git apply biopipen-sctype-zerovariance-and-empty-scores.patch
# or, without git:
patch -p1 < biopipen-sctype-zerovariance-and-empty-scores.patch
```

## How it was built and installed

```bash
# 1. patch the checkout (BIOPIPEN_UTILS = your biopipen.utils source checkout)
cd "$BIOPIPEN_UTILS"
git apply biopipen-sctype-zerovariance-and-empty-scores.patch

# 2. install into the R library the harness uses -- by default the first entry of
#    .libPaths() of the R that runs the arms
R CMD INSTALL --library="$(Rscript -e 'cat(.libPaths()[1])')" "$BIOPIPEN_UTILS"
```

The same command with the library made explicit (it is what the reported run used, with the paths
substituted for the placeholders):

```bash
R CMD INSTALL \
    --library="$(Rscript -e 'cat(.libPaths()[1])')" \
    "$BIOPIPEN_UTILS"
```

`--library` matters: the harness's Rscript must resolve the *patched* build, so install into the
library that R actually searches (`Rscript -e '.libPaths()'`), not into another R installation's
tree.

## Provenance

| Item | Value |
|---|---|
| Upstream repository | `biopipen.utils` (R package, author's own) |
| Checkout used | a `biopipen.utils` source checkout (set `$BIOPIPEN_UTILS`) |
| Package version | `0.4.9` |
| Patching commit | `5c4507d` — *fix(sctype_score): add guards for zero-variance genes and empty score matrices* |
| File patched | `R/scrna-celltype-annotation.R` |
| Diff extracted with | `git show --format= 5c4507d -- R/scrna-celltype-annotation.R` |

The `--format=` is deliberate: it emits a bare unified diff with no commit-metadata preamble, so the
`.patch` carries no author identity and stays a plain, portable diff.

## Verification

The patch was round-tripped against the upstream blobs before being deposited:

1. `git show 5c4507d^:R/scrna-celltype-annotation.R` → the pre-patch source, md5 `fc54ded8aaf84470a4abffb3066bcb50`;
2. `git show 5c4507d:R/scrna-celltype-annotation.R`  → the post-patch source, md5 `33fac18645eb506e274253f7d10bf85a`
   (this is also the md5 of the working-tree file that was actually installed);
3. `git -c core.autocrlf=false apply --check` on the pre-patch source passed;
4. applying it reproduced the post-patch source **bit-identically** (md5 `33fac186…`).

`core.autocrlf=false` is needed on Windows only; without it the working tree gains CRLF endings.

## Note on scope

Nothing else in the review's results depends on a third-party modification. The rest of the
demonstration runs against released packages; the cluster-identifier keying repair is a
*configuration* change (`benchmark/gse96583/clusterfix*.toml`), not a code patch.
