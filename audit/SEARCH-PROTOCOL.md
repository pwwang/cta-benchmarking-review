<!--
  SEARCH-PROTOCOL.md -- documentation, copied verbatim from the review project.
  Original path in the project: review/SEARCH-PROTOCOL.md
  Kept with the audit scripts because they implement exactly this protocol/schema.
-->

# Search protocol — systematic audit of cell-type annotation benchmark design

Version 1.0, 2026-09-29. Both search agents follow this identically so their outputs merge cleanly.

## Objective

Find every paper that **benchmarks / systematically compares** automated cell-type annotation methods on
scRNA-seq data. These are the *objects of study* for the review: we audit how they were designed.

We are NOT looking for: new annotation methods, single-tool papers, or reviews without a primary comparison.

## Sources

Peer-reviewed and preprint, in this order of priority:
1. **PubMed** — `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=...`
   then `efetch`/`esummary` for titles, years, journals, DOIs.
2. **Europe PMC** — `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=...&format=json&pageSize=100`
3. **Semantic Scholar** — `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,year,venue,externalIds,abstract`
4. **arXiv** — `http://export.arxiv.org/api/query?search_query=...&max_results=100`
5. **bioRxiv / medRxiv** — via the Europe PMC `SRC:PPR` filter, or the bioRxiv API
   `https://api.biorxiv.org/details/biorxiv/{from}/{to}` (paged by month; filter locally).

Use `terminal` with `curl` for the APIs (they are all keyless and rate-limit tolerant if you sleep 1s
between calls). If a call fails, retry once, then fall back to `web_search` for that slice and say so.

## Query term families

Combine with AND. Run each family separately as well as combined, so nothing hides behind a bad combination.

```
A: "cell type annotation" OR "cell-type annotation" OR "cell type identification"
   OR "cell-type identification" OR "cell annotation" OR "automated annotation"
B: benchmark OR benchmarking OR comparison OR "systematic evaluation" OR "comparative evaluation"
   OR "performance evaluation" OR "evaluation of"
C: "single-cell" OR "single cell" OR scRNA-seq OR "single-cell RNA sequencing" OR transcriptomics
```

Suggested concrete queries (run these, then variants):
- `A AND B AND C`
- `"cell type annotation" AND (benchmark OR comparison)`
- `"automatic cell identification" AND (benchmark OR comparison)`
- `"annotation methods" AND "single-cell" AND comparison`
- `"marker-based" AND "cell type annotation" AND benchmark`
- `"reference-based" AND "cell type annotation" AND comparison`

## Window

2018-01-01 → today. Rationale: pre-2018 tools are era artefacts and the comparison practice we audit
post-dates the modern toolkit (SingleR 2019, ScType 2022, etc.). Log anything important found earlier
as a `MAYBE` with a note rather than dropping it.

## Inclusion criteria (abstract level)

- Peer-reviewed **or** preprint
- Compares **≥ 3** automated cell-type annotation methods
- Reports a **quantitative** comparison on scRNA-seq data

## Exclusion criteria — record the reason with the exact code

| Code | Meaning |
|---|---|
| `EXCL-1tool` | single-tool paper, no head-to-head comparison |
| `EXCL-review` | review/opinion with no primary quantitative comparison |
| `EXCL-notannotation` | benchmarks clustering, normalisation, integration, DE, or trajectory instead |
| `EXCL-modality` | not scRNA-seq (e.g. scATAC-seq, spatial-only, proteomics-only, bulk) |
| `EXCL-notbenchmark` | method-development paper that reports its own accuracy but compares nothing |
| `EXCL-dup` | duplicate record of one already listed |

Ambiguous → `MAYBE`, with a one-line note on what would resolve it.

## Mandatory honesty rules

1. **Only report records you actually retrieved from a database or page.** Never reconstruct a citation
   from memory, never guess a DOI, never invent a title. If you cannot confirm a record exists, it does
   not go in the file.
2. Every row must carry a `url` you actually fetched.
3. If a source failed, say which one failed in your summary; do not silently narrow the search.
4. Deduplicate by DOI (fall back to normalised title) — one row per paper.

## Output

Write a tab-separated file, one row per paper, **with a header row**, at the path given in your task.
Columns, in this exact order:

```
key	title	year	venue	type	url	source_db	screen	reason	notes
```

- `key` — DOI if known, else PMID, else `bioRxiv:<doi>`, else `NA`
- `type` — `peer-reviewed` | `preprint`
- `screen` — `INCLUDE` | `MAYBE` | `EXCLUDE`
- `reason` — the exclusion code above, or `ok` for INCLUDE, or a one-line ambiguity for MAYBE
- `notes` — <= 200 chars: what it benchmarks, and the claimed n_tools / n_datasets if the abstract states it
- Tabs inside fields are forbidden; use `;` instead. No newlines inside fields.

Also write a short sibling markdown file with: the exact queries you ran, how many raw hits each returned,
the counts by screen verdict, and which sources failed.

Report back: the file path, the total row count, the INCLUDE/MAYBE/EXCLUDE counts, and the distinct
queries used. Do not summarise individual papers at length — the file is the deliverable.
