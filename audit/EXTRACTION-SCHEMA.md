<!--
  EXTRACTION-SCHEMA.md -- documentation, copied verbatim from the review project.
  Original path in the project: review/extract/EXTRACTION-SCHEMA.md
  Kept with the audit scripts because they implement exactly this protocol/schema.
-->

# Extraction schema — benchmark design audit (Phase 2)

One row per benchmark paper. Every field needs an `evidence_quote` (verbatim from the paper's full text or
supplementary) OR the literal value `NOT-STATED`. Never infer a design choice the authors did not describe.

| # | Field | Allowed values / format | Why it is extracted |
|---|---|---|---|
| 1 | paper_id | DOI or key from corpus-master.tsv | join key |
| 2 | n_tools_compared | integer | roster size as reported |
| 3 | n_configurations | integer or NOT-STATED | distinct runs; differs from n_tools when variants exist |
| 4 | redundancy_checked | yes / no / NOT-STATED | do they declare duplicate or equivalent configurations? |
| 5 | resource_policy | shared-one-table / per-tool-defaults / mixed / NOT-STATED | was the marker resource held constant across tools? |
| 6 | n_datasets | integer | breadth |
| 7 | n_cells_total | integer or NOT-STATED | scale |
| 8 | gt_source | author-annotation / expert-annotation / experimental / computed-by-tool / mixed / NOT-STATED | ground-truth provenance |
| 9 | partition_used | string as named in the paper, or NOT-STATED | which clustering the arms annotated |
| 10 | partition_independent_of_gt | yes / no / NOT-STATED | **the F2 validity test** |
| 11 | cluster_purity_reported | yes / no | do they report how pure their clusters are? |
| 12 | metric_primary | accuracy / ARI / F1 / kappa / ontology-semantic-similarity / weighted-agreement / other / NOT-STATED | the headline metric |
| 13 | metric_is_ontology_aware | yes / no | does scoring use an ontology (CL/GO) structure at all? |
| 14 | ontology_id | CL / GO / other / none | which ontology, if any |
| 15 | exact_match_required | yes / no / partly | is a parent/child label counted as wrong? |
| 16 | trivial_baseline_present | yes / no | majority-class or best-single-tool baseline |
| 17 | uncertainty_reported | yes / no | CI, bootstrap, or significance test |
| 18 | abstention_handled | scored / dropped / not-reported / not-applicable | what happens to unassigned/unknown labels |
| 19 | code_available | url or no | reproducibility |
| 20 | data_available | url or no | reproducibility |
| 21 | limitation_acknowledged | yes / no | do the authors name their own design risks? |
| 22 | design_risk_quotes | verbatim, `;`-separated | the money quotes for the review |
| 23 | evidence_quotes | verbatim supporting fields 2-21 | grounding; one quote per contested field |

## Hard rules

1. **`NOT-STATED` is a finding, not a failure.** A design choice absent from the paper is exactly what this
   review measures. Never fill it in by inference.
2. **Verbatim only.** Quote the paper, do not paraphrase. If you cannot reach the full text, say so and mark
   every field `NO-FULL-TEXT` rather than guessing from the abstract.
3. **One row per paper.** If a paper benchmarks both scRNA-seq and another modality, extract the scRNA-seq part.
4. Output TSV, header row, `\t`-separated, no tabs or newlines inside fields (use `;`).
