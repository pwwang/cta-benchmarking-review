# Single-Cell RNA-seq Cell Type Annotation Benchmarking Review

Code that produced the **results** of this review: the benchmark-design audit (corpus search,
screening, full-text retrieval, and the extraction -- "coding" -- of design properties), the
annotation-harness runs behind the demonstration datasets, the re-analysis of the aggregation
methods.

---

## Layout

```
audit/        corpus search, full-text retrieval, screening, extraction ("coding")
  SEARCH-PROTOCOL.md          the search protocol, verbatim from the project
  EXTRACTION-SCHEMA.md        the 23-column extraction schema, verbatim from the project
  search_core_europepmc.py    title search (CORE v3 / Europe PMC) for the last unresolved records
  fetch_europepmc.py          Europe PMC lookup per DOI: is a full text there, under which ID?
  fetch_oa_pdfs.py            download the included papers' PDFs/HTML into the full-text cache
  fetch_europepmc_xml.py      download Europe PMC fullTextXML + publisher fallbacks
  grep_fulltext_screening.py  keyword-family screening over the full texts
  build_extraction.py         the coded table (23 columns) + verbatim quote verification

harness/      the annotation pipeline that ran the benchmark arms
  src/cell_type_annotation/   arm runner, evaluator, marker-resource trainers, the scoped repairs
  benchmark/<ds>/             per-dataset configuration (TOML) and the data-prep scripts

analysis/     the analysis scripts behind the re-analysis numbers (Figure 3, Table S3, Section 6)
patches/      the one third-party patch the reported ScType numbers depend on
reconcile_core.py  the agreement-based aggregator evaluated in the review's re-analysis: the
              minimal core (Vocabulary, fit, membership_matrix) that analysis/*.py imports
paths.py      every location, resolved from the environment (see Configuration)
LICENSE       MIT (copyright holder line is a placeholder to fill in)
requirements.txt   what the audit needs (stdlib + curl) and what the demonstration side needs
```

Each subtree documents itself: `harness/README.md`, `patches/README.md`.

---

## Configuration:

`paths.py` is the single place where this package resolves a location. Every value is read from an
environment variable and falls back to a **relative default computed from `paths.py`'s own
location**, so a fresh clone runs as-is, and a reader whose data lives elsewhere only has to export
a variable. Nothing in the package needs editing to run it.

| Variable | Default | What it points at |
|---|---|---|
| `CTA_DATA` | `<package>/data` (git-ignored) | root for everything downloaded or generated |
| `CTA_HARNESS` | `<package>/harness` | the harness checkout whose `*-output/` dirs hold the arm results |
| `CTA_ARTIFACTS` | `$CTA_DATA/artifacts` | `truth.tsv` / `votes.tsv` / `resources.tsv` built from that output |
| `CTA_FULLTEXT` | `$CTA_DATA/fulltext` | the audit's full-text cache (retrieved and converted full texts) |
| `CTA_OUTPUT` | `$CTA_DATA/output` | tables the audit writes (e.g. `extracted-3.tsv`) |
| `CTA_LOGS` | `$CTA_DATA/logs` | logs the analysis scripts read (`uncertainty.log`, `robustness.log`) |
| `CTA_GEO_RAW` | `$CTA_DATA/geo/gse96583/raw` | the raw GSE96583 GEO download (not redistributed) |
| `HELDOUT_DIR` | `$CTA_DATA/heldout` | held-out inputs for `analysis/uncertainty.py` |
| `CTA_FACTS` | `<package>/FACTS.md` | the canonical facts file the figure script verifies against |

Print the resolved configuration at any time:

```bash
python paths.py            # or: python -c "import paths; print(paths.describe())"
```

### The two things that are not Python

* **`harness/benchmark/*/*.toml` -- interpreter for the MACA/SCSA arms.** The `python = "python3"`
  lines are **configurable**: they name the interpreter the wrapper scripts run with, and it must
  carry `scanpy`/`anndata` plus the MACA and SCSA tool code -- the harness's own virtualenv does
  not. Each such line is marked `# CONFIGURE`. Point it at whatever interpreter you have (a name on
  `PATH`, or an absolute path you supply in your own checkout). The value recorded here is the
  generic one; no interpreter path from the authoring machine is kept.
* **The R library the patch is installed into.** `patches/README.md` gives the install command in
  the generic form `R CMD INSTALL --library="$(Rscript -e 'cat(.libPaths()[1])')" <checkout>` --
  i.e. the first entry of the `Rscript` that runs the arms, not any fixed library.
  `harness/benchmark/gse96583/data-prep.R` reads its raw GEO directory from `CTA_GEO_RAW`, with the
  same relative default as `paths.py`.

### The full-text cache contract

`audit/build_extraction.py` re-verifies every quote against the converted full texts, so the cache
must satisfy one contract: a `.txt` beside each download in `$CTA_FULLTEXT`, named as in the `SRC`
map at the top of `build_extraction.py` (e.g. `natcomm_45198.txt`), with PDF pages introduced by
`===PAGE n===` markers so a quote traces back to a page (the script strips those markers before
matching). The conversion step itself is not shipped -- any PDF/XML/HTML-to-text tool will do; the
markers and the filenames are all that matter.

---

## Pipeline, in the order it ran

```
                     SEARCH-PROTOCOL.md        (what was searched, and the screen codes)
                             |
  corpus records ------------+-----------------> screened set  (620 records -> 40 INCLUDE)
                             |
  search_core_europepmc.py / fetch_europepmc.py   <- resolve the last records; route retrieval
                             |
  fetch_oa_pdfs.py / fetch_europepmc_xml.py       <- download the full texts
                             |
  <your PDF/XML/HTML -> text step>                <- make them quotable (see the contract above)
                             |
  grep_fulltext_screening.py                      <- find the passages that answer each schema column
                             |
  build_extraction.py  (EXTRACTION-SCHEMA.md)     <- code it, verifying every quote verbatim
                             |
  analysis/*.py                                   <- the re-analysis numbers
```

**The curated data lives in the code.** `build_extraction.py` holds the coded field values and
their supporting verbatim quotes inline, and re-verifies every quote against the retrieved full
text each time it runs (it prints a `VERBATIM FAILURES` count; the expected value is 0). So
re-running it -- given the same full texts in the cache -- re-emits the audit table. That is why the
table itself is not shipped as a data file.

---

## Curation rule -- what is deliberately NOT here

| Excluded | Why |
|---|---|
| Superseded pass `audit/build_extraction_pass1.py` | the first coding pass (20 fields); `build_extraction.py` writes the final 23-column table. |
| Retrieval adapters: Unpaywall / OpenAlex / fatcat / Wayback-CDX / text-mirror lookups | one-off helpers for locating a copy of a paper; they produce no reported number. |
| `_raw/` and `raw/` directories | cached API responses. **They contain harvested third-party e-mail addresses** (published corresponding-author contacts from Crossref/publisher records). Never publish them. |
| Downloaded `*.pdf` / `*.xml` full texts | publisher material -- copyrighted, not ours to redistribute. The fetch scripts re-download what is open access. |
| Large data outputs: `*.qs`, `*.tsv` result dumps | data, not code; regenerable by the scripts here. |

---

## How to run it

```bash
python -m pip install -r requirements.txt        # the audit itself needs only the stdlib + curl

# 1. fetch full texts into the cache ($CTA_FULLTEXT; default <package>/data/fulltext)
python audit/fetch_oa_pdfs.py
python audit/fetch_europepmc_xml.py
#    then convert them to .txt (any converter; see "The full-text cache contract")

# 2. screen, then code
python audit/grep_fulltext_screening.py
python audit/build_extraction.py                 # writes $CTA_OUTPUT/extracted-3.tsv

# 3. the demonstration side (see harness/README.md for the arm runs)
cd harness/benchmark/<ds> && bash data-prep.sh   # build the .qs objects + the 70/30 split
python analysis/score-clusterfix.py              # and the other analysis/*.py scripts
#    analysis/uncertainty.py additionally reads $HELDOUT_DIR (see Configuration) and takes the
#    crossed-roster artifacts directory as an optional first argument; with no argument it looks
#    for ./artifacts/<ds> relative to the current directory.
```

The published scripts are packaged **as they ran**, with deliberate exceptions, all of them noted
above: the hardcoded paths now come from `paths.py`, and the manuscript-only tooling and the
one-off retrieval adapters listed under "Curation rule" are gone. TLS verification is still disabled
in the fetchers exactly as it ran (several publisher hosts failed verification, so re-enabling it
may break retrieval -- that is the recorded behaviour, not an oversight), and the HTTP
`User-Agent` strings still mimic a browser because several publishers return 403 to anything else.

`analysis/uncertainty.py` scores with the three helpers shipped beside it in
`analysis/reconcile_helpers.py` (`unit_clusters`, `code_matrix`, `score`), copied verbatim from the
reconciliation script that writes `reconcile.tsv`, so the deposit runs without the authoring
workspace's `scripts/` tree.

---

## Provenance map (package path <- original path in the review project)

| Package | Original |
|---|---|
| `audit/fetch_oa_pdfs.py` | `review/extract/_fetch.py` |
| `audit/fetch_europepmc_xml.py` | `review/extract/_fetch2.py` |
| `audit/fetch_europepmc.py` | `review/extract/_epmc.py` |
| `audit/search_core_europepmc.py` | `review/extract/_last.py` |
| `audit/grep_fulltext_screening.py` | `review/extract/_grep.py` |
| `audit/build_extraction.py` | `review/extract/_build2.py` |
| `audit/SEARCH-PROTOCOL.md` | `review/SEARCH-PROTOCOL.md` |
| `audit/EXTRACTION-SCHEMA.md` | `review/extract/EXTRACTION-SCHEMA.md` |
| `analysis/*.py` | the same file name in the review project's analysis workspace |
| `analysis/reconcile_helpers.py` | `unit_clusters`, `code_matrix` and `score` from the authors' reconciliation script; the rest of that script is not shipped |
| `harness/**`, `patches/**` | the same relative path in the review project |
| `reconcile_core.py` | the aggregator the re-analysis evaluates: `Vocabulary`, `fit` and `membership_matrix`, extracted from the authors' aggregation implementation and merged into one module |

Not carried over, and therefore named here rather than mapped to a file:
`review/extract/_unpaywall.py`, `_oa.py`, `_cdx.py`, `_fetch3.py`, `_build.py`, `_topdf.py`,
`html2txt.py`, `xml2txt.py` (the retrieval adapters, the superseded coding pass and the
converters), plus `review/build/` and `review/references/` (the manuscript toolchain).

Only these changes were made while packaging: a header comment added to each file, line endings
normalised to LF, the absolute paths replaced by `paths.py`, three scripts renamed, the aggregator
reduced to the single module `reconcile_core.py` the analysis actually calls, and its printed method
label changed to the neutral `AGG` (numbers untouched; see Verification).

---

## Notes on the extraction building script

**`audit/build_extraction.py`** -- the audit's numbers are only as good as the verbatim quote
check. Each cached full text is normalised twice (NFKC; then whitespace and dashes stripped) and
every quote must be found in one of them, otherwise the run prints the offending quote and its
paper. A paper whose full text could not be obtained is written out as `NO-FULL-TEXT` with no
field inferred from the abstract; that is the honest state of the record, not a gap to fill in.

---

## Licence

MIT -- see `LICENSE`.
