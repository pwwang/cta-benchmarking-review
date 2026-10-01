# ============================================================================
# fetch_europepmc_xml.py -- download Europe PMC fullTextXML and publisher HTML fallbacks
# ============================================================================
# What it does:
#   Pulls the Europe PMC REST fullTextXML record for the PMC-deposited included papers, plus
#   fallback URLs (MDPI PDF and landing page, PeerJ article HTML) for the ones Europe PMC does not hold.
#   The .pdf/.xml/.html extension is decided from the Content-Type header and the body's magic bytes.
#
# Manuscript element produced:
#   Methods, "Full-text retrieval" - supplies the XML that the text-conversion step turns into
#   quotable text before coding (see README, "The full-text cache contract").
#
# Original path in the project: review/extract/_fetch2.py
#
# Notes:
#   The downloaded XML/HTML is third-party material and is NOT redistributed in this package.
#   Cache dir comes from $CTA_FULLTEXT (see paths.py); the target list is below.
# ============================================================================


import os, sys, urllib.request, ssl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

OUT = paths.FULLTEXT
os.makedirs(OUT, exist_ok=True)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0.0.0 Safari/537.36")

TARGETS = {
 "pmc_PMC10981883": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10981883/fullTextXML",
 "pmc_PMC12704438": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12704438/fullTextXML",
 "mdpi_a18040232b": "https://www.mdpi.com/1999-4893/18/4/232/pdf?version=1744352043",
 "mdpi_a18040232c": "https://www.mdpi.com/1999-4893/18/4/232",
 "peerj_17184b": "https://peerj.com/articles/17184/",
}

def get(name, url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/pdf,application/xml,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read(); ct = r.headers.get("Content-Type", ""); final = r.geturl()
    except Exception as e:
        print(f"{name}\tFAIL\t{e}"); return
    ext = ".pdf" if (b"%PDF" in data[:1024] or "pdf" in ct) else (".xml" if "xml" in ct else ".html")
    p = os.path.join(OUT, name + ext)
    open(p, "wb").write(data)
    print(f"{name}\tOK\t{len(data)}\t{ct}\t{final}\t{ext}")

for n, u in TARGETS.items():
    get(n, u)
