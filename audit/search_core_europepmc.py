# ============================================================================
# search_core_europepmc.py -- last-resort title search against CORE v3 and Europe PMC
# ============================================================================
# What it does:
#   Exact-title searches for two records whose DOI could not be matched to a record, run against the
#   CORE v3 works search and the Europe PMC REST search; prints the raw response (truncated) and the
#   parsed EPMC fields id / pmcid / isOpenAccess / inEPMC / title.
#
# Manuscript element produced:
#   Screening - the resolution step that decided whether a candidate title was a real, retrievable record.
#
# Original path in the project: review/extract/_last.py
#
# Notes:
#   CORE v3 requires an API key; the unauthenticated call returns an error string which the script
#   prints verbatim rather than hiding - that is intentional, not a bug.
#   The query list is below; nothing is read from or written to disk.
# ============================================================================


import json, urllib.request, urllib.parse, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
def get(url, acc="application/json"):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":UA,"Accept":acc}), timeout=60, context=ctx)
        return r.read().decode("utf-8","replace")
    except Exception as e:
        return "ERR " + str(e)

for q in ['"scEM: A New Ensemble Framework for Predicting Cell Type Composition"',
          '"Application of bioinformatic tools in cell type classification for single-cell RNA-seq data"']:
    u = "https://api.core.ac.uk/v3/search/works?q=" + urllib.parse.quote(q) + "&limit=3"
    print("====", q)
    print(get(u)[:900])
    u2 = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" + urllib.parse.quote(q) + "&resultType=core&format=json&pageSize=3"
    t = get(u2)
    try:
        j = json.loads(t)
        for r in j.get("resultList",{}).get("result",[]):
            print("  EPMC:", r.get("id"), r.get("pmcid"), r.get("isOpenAccess"), r.get("inEPMC"), (r.get("title") or "")[:60])
    except Exception as e:
        print("  EPMC parse", e, t[:200])
