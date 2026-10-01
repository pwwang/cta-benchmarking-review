# ============================================================================
# grep_fulltext_screening.py -- the screening pass that turned full texts into codable design facts
# ============================================================================
# What it does:
#   Scans every converted .txt full text with eleven named keyword families - uncertainty reporting,
#   trivial baselines, cluster purity, abstention handling, code availability, data availability,
#   stated limitations, partitioning, ground truth, ontology use, marker resources - and prints, per file
#   and per family, the hit count plus de-duplicated context windows.
#
# Manuscript element produced:
#   Results - each TERMS group maps onto one extraction column, so this is the machine-readable
#   version of the screening step; the numbers it surfaced are the prevalence figures in the manuscript.
#
# Original path in the project: review/extract/_grep.py
#
# Notes:
#   Optional argv: pass family names to restrict the scan (e.g. `python grep_fulltext_screening.py UNCERT BASE`).
#   Reads the full-text cache directory at $CTA_FULLTEXT (see paths.py).
# ============================================================================


import re, os, glob, sys
import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

RAW = paths.FULLTEXT

TERMS = {
 "UNCERT": r"bootstrap|confidence interval|\bCI\b|significan|p-value|p value|Wilcoxon|permutation test|standard deviation|standard error|error bar",
 "BASE": r"majority|random baseline|na[iï]ve baseline|baseline|best.?.?single|single best|trivial",
 "PURITY": r"purity|silhouette|cluster quality|adjusted Rand|ARI\b|NMI\b|modularity",
 "ABSTAIN": r"unassign|unknown|not assigned|unannotat|abstain|reject|'NA'|\bNA\b|unlabeled|unlabelled",
 "CODE": r"github|zenodo|gitlab|code is avail|source code|bitbucket|figshare|osf\.io",
 "DATA": r"GEO|GSE\d|zenodo|figshare|data availab|download|cellxgene|10x|datasets are",
 "LIMIT": r"limitation|caveat|however, our|we acknowledge|bias|shortcoming|future work|not without",
 "PART": r"cluster|Louvain|Leiden|Seurat|k-means|partition|resolution|granularity",
 "GT": r"ground truth|ground-truth|reference annotation|manual annotation|expert annotation|gold standard|cell ontology|CL:|Cell Ontology",
 "ONT": r"ontology|Cell Ontology|\bCL\b|GO term|Gene Ontology|semantic similarity|hierarch",
 "RES": r"marker gene|top \d+ genes|differentially expressed|FindAllMarkers|rank_genes|input genes",
}

files = sorted(glob.glob(os.path.join(RAW, "*.txt")))
want = sys.argv[1:] if len(sys.argv) > 1 else list(TERMS)
for f in files:
    if os.path.basename(f).startswith(("jina", "wb_", "pmc_PMC1098")):
        pass
    t = open(f, encoding="utf-8", errors="replace").read()
    t2 = re.sub(r"\s+", " ", t)
    print("#" * 90)
    print("FILE:", os.path.basename(f), "chars:", len(t2))
    for k in want:
        pat = TERMS[k]
        hits = [m.start() for m in re.finditer(pat, t2, flags=re.I)]
        print(f"  --{k}-- {len(hits)} hits")
        seen = set()
        for h in hits[:14]:
            s = t2[max(0, h - 130):h + 170]
            if s[:60] in seen: continue
            seen.add(s[:60])
            print("      ...", s.strip())
