# ============================================================================
# build_extraction.py -- final 23-column extraction table, with verbatim quote verification
# ============================================================================
# What it does:
#   Contains the curated coding for the eight included papers that could be coded from full text, with
#   the supporting verbatim quotes inline. Every quote is checked twice against the fetched text: first
#   NFKC-normalised exact substring, then a whitespace/dash-stripped fallback. Papers that could not be
#   reached are emitted as NO-FULL-TEXT rows rather than guessed. Writes the TSV and prints the count of
#   VERBATIM FAILURES (expected: 0) plus each failure if any.
#
# Manuscript element produced:
#   Results - the primary coded data for the audit: prevalence of purity reporting, redundancy, ontology
#   scoring, baselines, uncertainty, abstention handling and partition independence.
#   Column order matches audit/EXTRACTION-SCHEMA.md exactly (23 columns incl. paper_id and quotes).
#
# Original path in the project: review/extract/_build2.py
#
# Notes:
#   Because the curated values live in this file, running it re-emits the table - the data and the code
#   are the same artefact. Re-running requires the full-text cache at $CTA_FULLTEXT (see paths.py).
#   Output is TAB-separated UTF-8 with LF row endings, no tabs or newlines inside fields.
# ============================================================================


# -*- coding: utf-8 -*-
"""Build extracted-3.tsv (23-col schema) with verbatim-quote verification."""
import os, re, unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

RAW = paths.FULLTEXT                                   # the converted full texts
OUT = paths.OUTPUT / "extracted-3.tsv"                 # the coded table this script writes

SRC = {
    "lic": "arxiv_2409.15678.txt",
    "soar": "arxiv_2412.02915.txt",
    "leader": "natcomm_45198.txt",
    "scannox": "pmc_PMC10981883.txt",
    "mdpi": "mdpi_a18040232.txt",
    "rs": "rs_5754289.txt",
    "anndict": "natcomm_64511.txt",
    "bib": "pmc_PMC12704438.txt",
}

def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"===PAGE\s+\d+===", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def tight(s):
    return re.sub(r"[\s\-]+", "", s)

TEXT, TIGHT = {}, {}
for k, v in SRC.items():
    raw = open(os.path.join(RAW, v), encoding="utf-8", errors="replace").read()
    TEXT[k] = norm(raw)
    TIGHT[k] = tight(TEXT[k])

def check(src, q):
    n = norm(q)
    if n in TEXT[src]:
        return "A"
    if tight(n) in TIGHT[src]:
        return "B"
    return None

HEADER = ["paper_id","n_tools_compared","n_configurations","redundancy_checked","resource_policy",
          "n_datasets","n_cells_total","gt_source","partition_used","partition_independent_of_gt",
          "cluster_purity_reported","metric_primary","metric_is_ontology_aware","ontology_id",
          "exact_match_required","trivial_baseline_present","uncertainty_reported","abstention_handled",
          "code_available","data_available","limitation_acknowledged","design_risk_quotes","evidence_quotes"]

R = []

def add(pid, src, vals, risk, quotes):
    assert len(vals) == 20, (pid, len(vals))
    R.append(dict(pid=pid, src=src, vals=vals, risk=risk, quotes=quotes))

add("NA", "lic",
 ["5","NOT-STATED","NOT-STATED","shared-one-table","4","NOT-STATED",
  "author-annotation","NOT-STATED","NOT-STATED","no",
  "weighted-agreement","yes","CL","partly","yes",
  "no","not-reported",
  "https://github.com/Glowworm-cell/LICT",
  "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164378",
  "yes"],
 "Without a universally objective standard for evaluation, assessing the credibility of annotations remains challenging; "
 "Manual annotations can vary and be biased, particularly in low-heterogeneity datasets where cell clusters may be ambiguous",
 ["we conducted an initial evaluation of 87 different LLMs",
  "Based on accessibility and annotation accuracy, we selected five top-performing LLMs",
  "Each model was tested with standardized prompts to ensure consistency in the evaluation process",
  "For each dataset, we selected the top 10 differentially expressed genes and applied a basic prompting strategy to generate cell type annotations.",
  "The four scRNA-seq datasets used in this study represented diverse biological contexts",
  "Manually annotated cell type labels from each dataset were also collected for validation purposes.",
  "Cell type annotations provided by the LLMs were compared directly to the manual annotations from the original studies.",
  "we performed data processing steps such as quality control, dimensionality reduction, and clustering, following the protocols outlined in the respective original articles",
  "We assigned agreement scores of 1, 0.5, and 0 for 'fully match', 'partially match', and 'mismatch', respectively.",
  "To enhance objectivity, we introduced cell ontology (CL) names to each manually or automatically identified cell type annotation.",
  "'partially match' if they shared a broad cell type name or subordinate relationship (e.g., fibroblast and stromal cell), but had different annotations and CL names",
  "they still outperformed single models like GPT-4, demonstrating the effectiveness of our strategy",
  "The LICT package (v0.1.0) is provided as an open-source software package with a detailed user manual available in the GitHub repository at https://github.com/Glowworm-cell/LICT.",
  "Four datasets used in this study: human peripheral blood mononuclear cells (PBMCs, GSE164378",
  "it is important to recognize that discrepancies between LLM and manual annotations do not necessarily indicate lower reliability of LLM results. Manual annotations can vary and be biased, particularly in low-heterogeneity datasets where cell clusters may be ambiguous"])

add("10.48550/arxiv.2412.02915", "soar",
 ["8","NOT-STATED","NOT-STATED","shared-one-table","11","NOT-STATED",
  "author-annotation","cell-type groups from the source publications (no clustering performed; the annotation units ARE the published ground-truth labels)","no","no",
  "other","yes","CL","partly","no",
  "no","not-reported",
  "no",
  "no",
  "yes"],
 "Additionally, due to data constraints, the majority of multiomics benchmarks in this study are limited to RNA-seq and ATAC-seq data.",
 ["we assess the performance of 8 instruction-tuned LLMs across 11 datasets, spanning multiple cell types and species",
  "Our comprehensive analysis spans 11 diverse datasets and evaluates 8 instruction-tuned LLMs across 1226 cell-type annotation-related tasks.",
  "For each scRNA-seq, manually annotated cell types (y) and gene expression matrices (x) were obtained directly from the corresponding publications.",
  "Welch's t-test was then performed to identify differentially expressed genes (DEGs) by comparing each cell type against all others.",
  "The top 10 DEGs were selected to construct the gene list X.",
  "we normalized cell type annotations to their unambiguous cell ontology (CL) names",
  "All synonyms for a cell type name returned by the API were included as ground truth annotation candidates (y).",
  "To fairly assess the free-format responses for cell type annotation, we propose using the BLEU score",
  "we also employ EM and F1, metrics commonly used to assess the quality of responses in question-answering tasks",
  "Our code is available in the Supplementary Materials.",
  "we curated cell type annotation samples from the following single-cell RNA sequencing datasets: Azimuth (HuBMAP, 2019), Human Cell Landscape (HCL) (Han et al., 2020), Mouse Cell Atlas (MCA) (Han et al., 2018), GTEx (Eraslan et al., 2022), B-cell lymphoma (BCL) (Liu et al., 2023), Literature (Eraslan et al., 2022), Colon Cancer (Lee et al., 2020), Lung Cancer (Kim et al., 2020), Tabula Sapiens (TS) (The Tabula Sapiens et al., 2022), and Non-model Mammal (Chen et al., 2021)."])

add("10.1038/s41467-024-45198-y", "leader",
 ["6","24","NOT-STATED","shared-one-table","6","NOT-STATED",
  "mixed","cell-level labels; Seurat clustering used only for cell selection","NOT-STATED","no",
  "accuracy","no","none","yes","yes",
  "no","dropped",
  "https://github.com/camlab-bioml/leader",
  "https://doi.org/10.5281/zenodo.10403475",
  "yes"],
 "While doublets were removed by the dataset authors, the approaches used for this task are generally imperfect and doublets or mislabeled cells may still exist in the ground truth dataset",
 ["SingleR, scmap, CyTOF-LDA, a random forest model, singleCellNet, and a support vector machine is then trained using ground truth labels",
  "we address these questions by performing a comprehensive benchmarking of active learning across 6 datasets, 3 technologies, 6 cell annotation methods, 24 active learning approaches and trained over 1600 active learning models",
  "These subsets were then used to train six cell type assignment methods using ground truth cell type labels.",
  "we collated six single cell datasets comprising different modalities and existing ground truth labels",
  "This covers cell type labels previously designated as gold (cell lines) and silver (gating) standards as ground truth",
  "we cluster with Seurat",
  "Datasets of size 100, 250 and 500 cells are then sampled from the training dataset using active learning, adaptive reweighting and a random sampling (baseline).",
  "While we focused our analysis on balanced accuracy and sensitivity for the sake of clarity, all five metrics are highly correlated",
  "Each model was then evaluated using a total of five metrics: sensitivity, F1-score, Matthew's correlation coefficient, Cohen's kappa and balanced accuracy.",
  "No statistical method was used to predetermine sample size.",
  "Any cells predicted as 'unassigned' were removed prior to calculating these metrics.",
  "An R package implementing the heuristic approaches introduced in this work may be found at https://github.com/camlab-bioml/leader.",
  "Source data are provided on zenodo: https://doi.org/10.5281/zenodo.10403475.",
  "While doublets were removed by the dataset authors, the approaches used for this task are generally imperfect and doublets or mislabeled cells may still exist in the ground truth dataset"])

add("10.7717/peerj.17184", "scannox",
 ["10","NOT-STATED","NOT-STATED","shared-one-table","4","NOT-STATED",
  "author-annotation","NOT-STATED","NOT-STATED","no",
  "accuracy","no","none","yes","no",
  "no","not-reported",
  "https://github.com/XQ-hub/scAnnoX",
  "no",
  "yes"],
 "Due to the intricate nature of the cell types and the potential confounding effects of batch processing, the validation results were not satisfactory.; "
 "A closer examination revealed that the challenges in distinguishing these cell types could be attributed to their relatively low cell counts, especially the scarcity of pancreatic polypeptide-secreting cells within the islet dataset",
 ["Ten single-cell annotation algorithms were selected based on the classification of either reference dataset-dependent or marker gene-dependent approaches. These algorithms included SingleR, Seurat, sciBet, scmap, CHETAH, scSorter, sc.type, cellID, scCATCH, and SCINA.",
  "we conducted a comprehensive algorithmic performance evaluation using the scAnnoX software package on four distinct single-cell omics datasets",
  "The use of marker gene-based tools enables the identification of marker genes from the reference expression profiles. This can be achieved using the \"FindAllMarkers\" function within the \"Seurat\" package.",
  "We compared the annotation accuracies of the ten annotation algorithms embedded within the scAnnoX package",
  "we calculated the root mean square error between the prediction results and the actual cell types",
  "Interested parties can access the scAnnoX package at https://github.com/XQ-hub/scAnnoX .",
  "the validation results were not satisfactory",
  "The accuracies of most intrinsic methods tended to converge within the range of 45% to 66%",
  "Given the high cell types heterogeneity and the limited sample sizes within certain cell type categories, we comprehensively reclassified and aggregated the cell types within the dataset."])

add("10.3390/a18040232", "mdpi",
 ["8","NOT-STATED","NOT-STATED","shared-one-table","4","NOT-STATED",
  "author-annotation","Leiden","NOT-STATED","no",
  "accuracy","no","none","yes","no",
  "no","not-reported",
  "https://drive.google.com/drive/folders/1CZTtak88WXkvqTlAsJwdZHGkMkbPze_",
  "https://www.ebi.ac.uk/gxa/sc/experiments/E-HCAD-35/results/tsne",
  "yes"],
 "differences in cell type representation, particularly imbalances or rare subpopulations, can skew classification; "
 "batch effects introduce confounding biases. Without appropriate correction, models may learn batch-specific patterns rather than true biological signals, leading to poor generalization.",
 ["We conducted a comprehensive evaluation of seven traditional machine learning models for cell type annotation using single-cell gene expression data.",
  "We also implemented a Transformer-based model comprising an embedding layer that projected the input gene expression data into a 512-dimensional feature space",
  "Cells were then clustered using the Leiden algorithm, a graph-based community detection method that captures local cell-cell similarity in expression space.",
  "cell type annotation was performed using reference-based methods, where clusters were assigned biological labels by comparing their expression profiles to curated reference datasets containing well-defined marker genes",
  "The provided cell type labels from the original publication were used as ground truth labels for evaluation.",
  "we evaluated these techniques by comparing their F1 scores and accuracy to validate their performance",
  "Each model was trained on the training set and used to predict cell types in the test set.",
  "The code used to generate the results presented in this study is available at: https://drive.google.com/drive/folders/1CZTtak88WXkvqTlAsJwdZHGkMkbPze_",
  "The Multiple sclerosis (MS) dataset has been accessed (https://www.ebi.ac.uk/gxa/sc/experiments/E-HCAD-35/results/tsne)",
  "batch effects introduce confounding biases. Without appropriate correction, models may learn batch-specific patterns rather than true biological signals, leading to poor generalization."])

add("10.21203/rs.3.rs-5754289/v1", "rs",
 ["8","NOT-STATED","NOT-STATED","shared-one-table","4","NOT-STATED",
  "computed-by-tool","Seurat clustering (shared nearest neighbour graph)","NOT-STATED","no",
  "accuracy","no","none","yes","no",
  "no","dropped",
  "https://github.com/TorteloteLab/ML-models-for-scRNA-analysis",
  "no",
  "yes"],
 "One limitation of this study is the use of relatively small datasets for training machine ML models.; "
 "Another limitation lies in the use of default hyperparameters for all ML models, that may need fine adjustments to increase performance of the trained model; "
 "the clusters identified as 'Alternative lineage 1 and 2' were removed from the training and test datasets",
 ["In this study, we systematically assess the performance of eight machine learning models (Support Vector Machine (SVM), Logistic Regression, Decision Tree, Random Forest, Elastic Net Regularization, Gradient Boosting (XGBoost), k-Nearest Neighbors (k-NN), and Naive Bayes), in learning and transferring cell labels.",
  "We analyzed two Peripheral Blood Mononuclear Cells (PBMC) datasets freely available from 10X Genomics (PBMC3K and PBMC10K).",
  "For cell annotation, the SingleR tool was utilized following its tutorial. This approach enabled the automatic identification of cell types within the processed datasets",
  "The CellDex human primary cell atlas was used as a reference atlas",
  "clustering based on shared nearest neighbor (SNN) graphs",
  "The 4,000 most variable genes were used for the training and test datasets.",
  "we chose not to adjust them in this study. This decision was made to ensure consistency and simplicity in the comparative analysis",
  "the clusters identified as 'Alternative lineage 1 and 2' were removed from the training and test datasets.",
  "Accuracy measures the proportion of correctly classified cells out of the total number of cells.",
  "The codes used for the generation and training of the machine-learning algorithms are freely available at https://github.com/TorteloteLab/ML-models-for-scRNA-analysis",
  "One limitation of this study is the use of relatively small datasets for training machine ML models."])

add("10.1038/s41467-025-64511-x", "anndict",
 ["15","NOT-STATED","NOT-STATED","shared-one-table","1","1136218",
  "author-annotation","Leiden","yes","no",
  "accuracy","no","none","partly","yes",
  "yes","not-reported",
  "https://github.com/ggit12/benchmark_llms",
  "https://doi.org/10.6084/m9.figshare.27921984.v1",
  "yes"],
 "The apparent shortfall of LLM annotation for cell types such as basal cells and mononuclear phagocytes may actually represent an artifact of dichotomizing continuous expressional gradients in transcriptomic data, and not speak to the performance of LLMs themselves.; "
 "the case of stromal cell sub-cluster annotation by LLMs could be an artefact of potential over-clustering in the preprocessing pipeline used in the present study, or limitations of the marker gene selection method.; "
 "there is a standard ontology for cells. However, the first step of annotation typically uses free text labels, and most dataset annotations are not mapped to terms in the standard ontology.",
 ["enables AnnDictionary to be used to annotate Tabula Sapiens v2 with 15 different LLMs",
  "We then used LLMs to annotate each cluster with a cell type label based on its top differentially expressed genes",
  "The dataset contains n = 61,806 genes and n = 1,136,218 cells annotated by the Tabula Sapiens Consortium",
  "there has not yet been an assessment of LLMs at de novo cell type annotation, meaning annotation of gene lists derived directly from unsupervised clustering",
  "clustered with the Leiden algorithm",
  "We assessed cell type annotation agreement with manual annotation using direct string comparison, Cohen's kappa",
  "Claude 3.5 Sonnet had the highest binary agreement with manual annotations at 84.0",
  "we asked the LLM to rate the quality of the label match as perfect, partial, or non-matching",
  "The code to run the LLM benchmarking pipeline and reproduce all figures and tables presented in this study is publicly available in the benchmark_llms repository",
  "The gene expression data used in this study have been deposited in Figshare under accession code",
  "The apparent shortfall of LLM annotation for cell types such as basal cells and mononuclear phagocytes may actually represent an artifact of dichotomizing continuous expressional gradients in transcriptomic data, and not speak to the performance of LLMs themselves."])

add("10.1093/bib/bbaf677", "bib",
 ["14","NOT-STATED","NOT-STATED","shared-one-table","34","1800000",
  "expert-annotation","the pre-annotated cell types provided in the source datasets (used directly as the clusters)","no","no",
  "weighted-agreement","yes","CL","partly","yes",
  "yes","not-reported",
  "https://deepcellseek.kiz.ac.cn/",
  "no",
  "yes"],
 "We acknowledge that because our benchmark relies on public datasets, some of these data may have been part of the models' training corpora, a potential source of performance overestimation.",
 ["Here, we systematically benchmarked seven leading LLM models and three traditional bioinformatics tools across 34 diverse human and mouse datasets.",
  "This study evaluated a total of 11 specific model endpoints from seven prominent large language model families",
  "evaluating their performance on >1.8 million cells across 34 diverse human and mouse datasets",
  "For marker gene identification, each pre-annotated cell type provided in the original datasets was treated as a distinct cluster.",
  "All selected datasets contained expert-provided annotations at the cell type level",
  "manual annotation by experts, serving as the gold standard",
  "we developed an ontology-aware scoring system based on the CL",
  "the dark segments represent \"Perfect matches\" (score = 1.0), the light segments represent \"Partial matches\" (score = 0.5), and the unfilled segments represent \"No matches\" (score = 0.0)",
  "Partial Match (Score = 0.5): Awarded in three distinct scenarios: (1) the prediction is an ancestor (a broader parent category) of the ground-truth term in the ontology hierarchy",
  "Statistical comparisons (Wilcoxon rank-sum test) are made against the top-performing model, Kimi-k2",
  "To ensure a fair comparison, the exact same sets of substituted gene lists were used as input for all evaluated models.",
  "This integrated solution is provided as both a user-friendly interactive web platform (available at https://deepcellseek.kiz.ac.cn/ ) and an open-source R package",
  "We acknowledge that because our benchmark relies on public datasets, some of these data may have been part of the models' training corpora, a potential source of performance overestimation."])

for pid in ["10.1007/s12539-023-00601-y", "10.1016/j.compbiolchem.2024.108332"]:
    add(pid, None, ["NO-FULL-TEXT"] * 20, "NO-FULL-TEXT", [])

fails = []
for r in R:
    if r["src"] is None:
        continue
    for q in r["quotes"]:
        if check(r["src"], q) is None:
            fails.append((r["pid"], q))
    for q in [x for x in r["risk"].split("; ") if x]:
        if check(r["src"], q) is None:
            fails.append((r["pid"], "[risk] " + q))

print("=== VERBATIM FAILURES:", len(fails))
for pid, q in fails:
    print("  ", pid, "::", q[:170])

lines = ["\t".join(HEADER)]
for r in R:
    if r["src"] is None:
        vals = [r["pid"]] + r["vals"] + ["NO-FULL-TEXT", "NO-FULL-TEXT"]
    else:
        vals = [r["pid"]] + r["vals"] + [r["risk"], "; ".join(r["quotes"])]
    cells = [re.sub(r"[\t\r\n]+", " ", v) for v in vals]
    assert len(cells) == 23, (r["pid"], len(cells))
    lines.append("\t".join(cells))

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(lines) + "\n")
print("wrote", OUT, "rows:", len(R))
