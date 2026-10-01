# ============================================================================
# fetch_oa_pdfs.py -- bulk-download the publisher/self-archive PDFs of the included papers
# ============================================================================
# What it does:
#   Requests each target URL directly (urllib, browser User-Agent, 60 s timeout) and saves the body
#   to the local full-text cache, choosing .pdf vs .html by sniffing the %PDF magic bytes and the
#   Content-Type header. Prints one status line per target: name, OK/FAIL, bytes, content type, final URL.
#
# Manuscript element produced:
#   Methods, "Full-text retrieval" - the provenance of every full text that the audit coded.
#   Its outputs feed the text-conversion step, then grep_fulltext_screening.py and
#   build_extraction.py (see README, "The full-text cache contract").
#
# Original path in the project: review/extract/_fetch.py
#
# Notes:
#   Caches third-party PDFs. They are NOT redistributed in this package (see .gitignore: *.pdf).
#   TLS verification is deliberately disabled (ctx.check_hostname=False) because several publisher
#   hosts failed verification on the authoring machine; keep that in mind if you re-enable it.
#   Download dir comes from $CTA_FULLTEXT (see paths.py); the target list is below.
# ============================================================================


import os, sys, urllib.request, urllib.error, ssl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

OUT = paths.FULLTEXT
os.makedirs(OUT, exist_ok=True)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0.0.0 Safari/537.36")

TARGETS = {
 "arxiv_2409.15678": "https://arxiv.org/pdf/2409.15678v1",
 "arxiv_2412.02915": "https://arxiv.org/pdf/2412.02915",
 "natcomm_45198": "https://www.nature.com/articles/s41467-024-45198-y.pdf",
 "peerj_17184": "https://peerj.com/articles/17184.pdf",
 "mdpi_a18040232": "https://www.mdpi.com/1999-4893/18/4/232/pdf",
 "rs_5754289": "https://www.researchsquare.com/article/rs-5754289/v1.pdf",
 "natcomm_64511": "https://www.nature.com/articles/s41467-025-64511-x.pdf",
}

def get(name, url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
            ct = r.headers.get("Content-Type", "")
            final = r.geturl()
    except Exception as e:
        print(f"{name}\tFAIL\t{e}")
        return
    ext = ".pdf" if (b"%PDF" in data[:1024] or "pdf" in ct) else ".html"
    p = os.path.join(OUT, name + ext)
    with open(p, "wb") as f:
        f.write(data)
    print(f"{name}\tOK\t{len(data)}\t{ct}\t{final}\t{ext}")

for n, u in TARGETS.items():
    get(n, u)
