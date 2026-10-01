# FACTS.md — canonical numbers for the review

**Every number in the manuscript must come from this file. Do not compute, round, or infer new numbers.
Sections D and E are FINAL (Section E was corrected 2026-09-30 - see the RETRACTED note there).
If a claim needs a number that is not here, write `[NEEDS-NUMBER: description]` and stop.**

---

## A. What the manuscript is

Critical review of **how cell-type annotation benchmarks are designed**. Target: *Nucleic Acids Research*,
Survey and Summary (8,000–12,000 words, 200-word unstructured abstract). Not a tool comparison. Not a
methods paper.

**Thesis:** benchmarks of cell-type annotation routinely fail to report the design properties that determine
their own conclusions. Four such properties are measurable, common, and — in our re-analysis — large enough
to invert results.

---

## B. Audit corpus (FINAL — do not restate differently)

| Quantity | Value |
|---|---|
| Records retrieved (two overlapping shards) | 800 |
| — shard 1: merged PubMed + Europe PMC search | 486 |
| — shard 2: preprint citation chaining | 314 |
| Distinct papers across both shards | 681 |
| Duplicate records merged | 180 |
| Unique records screened | 620 |
| **Included** (benchmark ≥3 annotation methods, quantitative, scRNA-seq) | **40** |
| MAYBE | 29 |
| Excluded | 551 |
| — excluded as EXCL-notbenchmark | 269 |
| — excluded as EXCL-notannotation | 139 |
| — excluded as EXCL-modality | 91 |
| — excluded as EXCL-dup | 34 |
| — excluded as EXCL-review | 17 |
| — excluded as EXCL-1tool | 1 |
| (these sum to 551 — one primary reason per excluded record, per Table S2) | |
| Full text obtained | **32 / 40** |
| Closed-access / blocked (all fields NO-FULL-TEXT, never inferred from abstract) | 8 / 40 |
| Publication years | 2019–2026 |
| Extraction fields per paper | 23 |
| Verbatim quotes machine-verified against retrieved text | 115 + 23 groups, 0 failures |

Exclusion codes are not perfectly disjoint across the two search shards (a paper could be counted under two
codes before dedup); report the primary reason only and do not sum them as a partition.

## C. Audit results over the 38 full-text benchmarks (FINAL)

| Field | Result | Report as |
|---|---|---|
| `cluster_purity_reported` | no = 36, yes = 2 | "36 of 38 report no check of the purity of the partition they annotate" |
| `n_configurations` | NOT-STATED = 25, else scattered | "25 of 38 never state how many distinct configurations were run" |
| `redundancy_checked` | NOT-STATED = 23, yes = 6, no = 9 | "23 of 38 do not address duplicate or equivalent configurations at all" |
| `metric_is_ontology_aware` | no = 31, yes = 7 | "31 of 38 score by exact label match with no ontology structure" |
| `ontology_id` | none = 30, CL = 8 | (one further paper, christensen2022, names CL without using it in scoring) |
| `exact_match_required` | yes = 19, partly = 10, NOT-STATED = 8, no = 1 | "19 of 38 require exact agreement; 8 never describe how granularity mismatches are scored" |
| `trivial_baseline_present` | no = 27, yes = 11 | "27 of 38 include no trivial (majority-class or single-best-tool) baseline" |
| `uncertainty_reported` | no = 26, yes = 12 | "26 of 38 report no confidence interval, bootstrap, or significance test" |
| `partition_independent_of_gt` | NOT-STATED = 17, no = 8, yes = 6, n/a = 7 | "only 6 of 38 assert that the partition is independent of the ground truth" |
| `n_cells_total` | NOT-STATED = 27 | "27 of 38 never state a pooled cell count" |
| `limitation_acknowledged` | yes = 37, no = 1 | "37 of 38 discuss limitations — but none of the limitations above" |
| `resource_policy` | shared-one-table = 20, mixed = 8, per-tool-defaults = 8, NOT-STATED = 2 | "Sixteen do not run the methods on a common marker resource: eight give each method its own defaults and eight mix the two." (16 of 38 = 42%) |
| `gt_source` | author-annotation = 17, mixed = 8, NOT-STATED = 8, expert-annotation = 3, computed-by-tool = 2 | provenance of ground truth. 17 of 38 (44.7%) score against the authors' own annotation; 27 of 38 (71.1%) use no independent expert standard. AUDIT-ONLY, no demonstration — do not give it a pillar. |

**Abstention handling** (over the 38): scored = 12, dropped = 7, not-reported = 8, not-applicable = 11.
Describe as "four mutually incompatible treatments; no convention".

**Ontology-aware scoring by year** (the 7 ontology-aware papers):
2019 = 0, 2020 = 0, 2021 = 0, 2022 = 0, 2023 = 0, 2024 = 3, 2025 = 2, 2026 = 2.
**Not one benchmark before 2024 used ontology-aware scoring.** The 7 are: popV (Ergen 2024), Single-Cell Omics
Arena (Liu, arXiv 2024), Ye 2024 (the LICT paper, arXiv 2409.15678), Benchmarking LLMs for cell typing (Xiao, BIB 2025),
Single-cell omics arena (Liu, BIB 2025), Cell-type separability factorial benchmark (Wardhana, bioRxiv 2026),
Cross-tissue generalization of rare cell-type representations (Cheng, 2026).
All 7 use the Cell Ontology. NOTE: CohortHijack is a MAYBE row and was NOT audited — it must not be named
as one of the six.

**Paradigm split (the key interpretive claim):** ontology-aware scoring has been adopted by LLM-based
benchmarks, whose labels are free text; marker- and reference-based benchmarks keep exact match, because
their labels come from a shared table. Cross-paradigm comparisons therefore mix incommensurable metrics.

## D. Our re-analysis — FINAL numbers (pbmc3k)

| Quantity | Value |
|---|---|
| Arms before curation | 97 |
| Arms casting **byte-identical** vote vectors | **63 of 97** |
| Arms after redundancy curation | 51 |
| Clusters, and clusters that are pure | **9 of 9 pure** |
| Plurality vote, all arms | 0.9444 |
| Plurality vote, curated roster | 0.8535 |
| Dawid–Skene, curated roster | 0.8535 |
| Best single cell-level arm | 0.8838 |
| Dawid–Skene, 97-arm roster | 1.0000 |

**pbmc3k structural point:** the unsupervised partition equals the ground-truth annotation — all 9 clusters
are pure. A cluster-level arm therefore only has to name nine already-pure groups; its 1.0000 is not a
measure of cell-level annotation accuracy.

**pbmc3k direction finding (FINAL):** arms differing only in whether the negative (direction = negative)
marker entries were included produced **byte-identical label vectors** for several independent tools
(ScType, scSorter, scCATCH, and the MACA/SCSA additions). The marker tables differed between the two
conditions; the outputs did not. This is an observation about our experiments, not a general claim about the
tools. No audited benchmark reports testing this ablation.

## E. Our re-analysis — FINAL numbers (gse96583), CORRECTED 2026-09-30

The gse96583 cluster-level arms were originally scored against a **scrambled** label-to-cell
correspondence: arms emitted their own clustering keyed 0..31, the loader joined on the raw integer against
the evaluation partition keyed 0..23, and ids 0..23 matched silently. All 54 cluster-level arms have now
been re-run keyed 0..23 and re-scored. In the normalized roster (below), 36 completed with full 24-row
tables and 11 scCATCH arms annotated only 15-20 clusters (their per-cell labels are complete; the tool
simply does not name every cluster).

**The demonstration roster is NORMALIZED before any summary is taken (2026-10-01).** Two changes, and
both are corrections to the roster rather than to any method:

- **One `AutoPos` seed.** `AutoPos8525`, `AutoPos8526` and `AutoPos8527` return **byte-identical
  accuracies for all four tools that run them** (SCSA 0.8706, ScType 0.8550, scCATCH 0.5516, scSorter
  0.8527). The three seeds are one piece of evidence, not three. 8526 and 8527 are dropped; 8525 is kept.
- **`ScInfeR` on its cohort's full three sources.** It was declared for two (`ScTypeDBFull`,
  `CellMarker`) when the Roster P+ loop was written; its control cohort is three, so `AutoPos8525` was
  run and added. This is the ONE number that had to be computed rather than counted: the arm was run
  under `RNA_snn_res.0.5` and its table carries all 24 clusters.

Net: 54 - 8 + 1 = **47 arms**. The normalization moves the *counts* and the *median*, and leaves every
*aggregate* untouched.

| Quantity | Pre-fix (scrambled) | CORRECTED |
|---|---|---|
| Cluster-level arms scored | 30 | 47 |
| Median per-arm accuracy (30-arm roster pre-fix -> 47-arm normalized roster) | 0.1482 | **0.7422** |
| Max per-arm accuracy | 0.1764 | **0.8729** |
| *pairing note* | the median and the "21 of 47" count describe the **47** normalized arms; the pre-fix median 0.1482 describes the **30** arms then present. Never quote the corrected median beside a pre-fix denominator of 30. | |
| Arms >= 0.85 | 0 of 30 | **21 of 47** |
| Cluster-level plurality | 0.1486 | **0.8726** (identical over 54 and over 47 — verified both ways) |
| Plurality, all arms | 0.6933 | **0.8738** |
| Plurality, cell-level only | 0.8711 | 0.8711 (unchanged) |

**The normalization is itself the roster argument in miniature:** dropping 8 redundant arms moves the
median by 0.08 and the count of arms at or above 0.85 by 5, while the plurality is unmoved at 0.8726.
A redundant arm inflates a count without moving an aggregate.

**RETRACTED — never repeat this claim:** "the plurality vote over all arms collapses on the larger dataset
(0.6933) because cluster-level arms cast correlated votes." That collapse was **an artefact of the aliasing
defect**. With corrected cluster-level arms the all-arm plurality is 0.8738, slightly ABOVE cell-level-only
(0.8711). Correlation among cluster-level arms is a genuine design property, but it did NOT cause this
collapse and the number must not be used as evidence that it does.

The scrambling cost roughly 0.72 in aggregate accuracy (0.1486 -> 0.8726), and the pre-fix values
reproduced the recorded numbers exactly (0.1486, 0.1482) - which is how the defect was found in the first
place.

Still VALID (cell-level or dataset properties, unaffected by the defect):
- 24 clusters, **0 of 24 pure** (against pbmc3k's 9 of 9). This is the Section 4 contrast and it stands.
- 88-arm roster: 52 of 88 arms cast byte-identical vote vectors (arm redundancy is partition-independent).
- SCSA abstains with the literal label `unassigned`: 0-6 cells on pbmc3k, 29-1,638 on gse96583 (worst
  AutoBoth). In the corrected vote table these fall through to OTHER, not ABSTAIN.
- scCATCH completes but names only 15-20 of 24 clusters - a quantified instance of the Section 6.2 finding.

**NOT YET CITABLE:** the gse96583 Dawid-Skene figures (pre-fix 0.8927, delta +0.0019)
were fitted on vote tables that contained the scrambled cluster-level arms. They must be re-fitted before
use. The review does not depend on them.

## F. Standing caveats that must appear in the manuscript

1. `NOT-STATED` describes **reporting**, not conduct. An unreported purity check may still have been done.
2. Screening was abstract-level; full-text re-screening may move some MAYBE rows.
3. 2 of 40 papers were unreachable — excluded from prevalence, never scored as NOT-STATED.
4. Semantic Scholar's topic-search endpoint was rate-limited throughout; substituted with OpenAlex and
   citation chaining. A real coverage gap.
5. Two `n_datasets` values are the extractor's arithmetic from reported components, not verbatim.
6. One author developed one of the aggregation methods evaluated in the underlying re-analysis. It did
    not outperform a standard baseline. Disclose this in the conflict-of-interest statement — it is a
    neutrality credential, not a weakness to hide.

## G. Prohibited claims

- Do not claim the field is unaware of these issues; DOME (*Nature Methods* 2021) and REFORMS
  (*Science Advances* 2024) already request simpler baselines and confidence intervals. The finding is
  **non-compliance with existing guidance**, not absence of guidance.
- Do not claim a tool is "best" or "state of the art".
- Do not generalise the two-dataset re-analysis to the whole field; the audit carries the prevalence claims,
  the re-analysis carries the mechanism.
- Section E numbers are FINAL and citable EXCEPT the Dawid-Skene gse96583 figures, which
  require a re-fit (see Section E).
- Never state or imply that ensembling collapses on gse96583; that was the defect, not a property.

## H. Full-text retrieval re-attempt (8 previously unreachable papers)

All 8 NO-FULL-TEXT DOIs were re-attempted via open-access aggregators, publisher archives, preprint
servers and web archives, and the authors later supplied publisher PDFs directly. Outcome: **8 full texts
obtained, 0 failed.**

- `10.1093/bib/bbab035` — FULL TEXT obtained by retrieval (70,874 chars, 12,393 words; Oxford Academic, article flagged Free).
- Five more were obtained from publisher PDFs supplied by the authors: 10.1145/3512452.3512456 (chen2021),
  10.1145/3498731.3498735 (zhang2021), 10.1016/j.ymeth.2024.05.007 (xia2024),
  10.1016/j.compbiolchem.2024.108332 (sujana2025), 10.14293/pr2199.003456.v1 (cheng2026).
- Two papers remain unreachable and stay NO-FULL-TEXT: `10.1007/978-3-031-07802-6_28` (Vasighizaker 2022, Springer LNCS)
  and `10.1007/s12539-023-00601-y` (Cai 2024, Springer). Both were verified closed-access with no OA copy from
  Unpaywall, OpenAlex, Europe PMC, OpenAIRE or CORE; a Springer PDF obtained by retrieval proved to be a
  1,523-word paywall preview and was rejected by the coding rule.

**Denominators are 38** (of 40 audited). Five of the recovered papers were coded from full text against the
same schema as the original 32, blind to the existing rows; the audit's prevalences held and mostly tightened.
The other two cannot be coded: an abstract does not report design properties, so coding one would violate the
NOT-STATED-vs-excluded rule and inflate the audit's apparent finding.

**No wrong citation was found.** A DOI/title mismatch was raised during retrieval against `10.1016/j.compbiolchem.2024.108332`; investigation showed the corpus DOI is CORRECT and the mismatch
came from a truncated DOI in the retrieval request, not from the audit. The corpus entry is right.

Retrieved texts: `review/retrieval/` (9 files + RETRIEVAL-REPORT.md). Nothing in the manuscript was
coded from an abstract.


## I. Identifier-assertion check over the 37 readable full texts (FINAL — 2026-09-30)

Question asked of every paper: does the evaluation expand cluster-level labels onto cells — a tool assigns
one label per cluster and the evaluation applies it to every cell in that cluster by joining on the cluster
identifier — and if so, does the paper state or assert that the labelling partition and the scoring partition
share an identifier space?

**10 of 37 expand cluster-level labels onto cells.** The other 27 never perform the expansion.

| id_assertion | n | refs |
|---|---|---|
| ASSERTED | **0** | — |
| IMPLIED (one clustering serves both steps, never asserted) | 3 | 41, 42, 54 |
| NOT-MENTIONED (join keying never described) | 7 | 43, 52, 56, 57, 61, 63, 68 |
| N-A (no expansion) | 27 | — |

Source: `review/extract/idassert/batch-{1..5}.tsv` (37 rows, 5 columns). Every evidence_quote was verified
as a verbatim substring of its declared source file; 0 fabrications. Input mapping:
`review/extract/ID-ASSERTION-INPUT.tsv`.

Coverage: 37 of 40. Excluded — `vasighizaker2022` and `cai2024` (no full text, both Springer) and
`hu2026` (full text not retrievable).

**Prohibited restatements:** do not write that any benchmark asserts the correspondence; do not generalise
the 10 to the whole corpus; do not call the 3 IMPLIED papers "asserted". The 27 non-expanding papers are
not evidence of anything and must not be counted as compliance.
