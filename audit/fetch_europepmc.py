# ============================================================================
# fetch_europepmc.py -- Europe PMC search by DOI: is a full text available, and under which ID?
# ============================================================================
# What it does:
#   For each candidate DOI, runs a Europe PMC REST search (resultType=core) and prints the record id,
#   pmcid, isOpenAccess, inEPMC, inPMC and the openAccess block. This decided which papers could be
#   obtained as PMC full text rather than a publisher PDF.
#
# Manuscript element produced:
#   Methods, "Full-text retrieval" - retrieval routing per included paper.
#
# Original path in the project: review/extract/_epmc.py
#
# Notes:
#   stdout only; no arguments. The DOI list is below.
# ============================================================================



import json, urllib.request, urllib.parse, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
dois = ["10.7717/peerj.17184","10.3390/a18040232","10.1007/s12539-023-00601-y",
        "10.1016/j.compbiolchem.2024.108332","10.1093/bib/bbaf677",
        "10.1038/s41467-024-45198-y","10.1038/s41467-025-64511-x"]
for d in dois:
    q = urllib.parse.quote(f'DOI:"{d}"')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&resultType=core&format=json&pageSize=1"
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"research/1.0"}), timeout=45, context=ctx)
        j = json.load(r)
        res = j.get("resultList",{}).get("result",[])
        if not res:
            print(d, "NO-RESULT"); continue
        x = res[0]
        print(d, "|", x.get("id"), "|pmcid=", x.get("pmcid"), "|isOpen=", x.get("isOpenAccess"),
              "|inEPMC=", x.get("inEPMC"), "|inPMC=", x.get("inPMC"), "|OA=", (x.get("openAccess") or {}), "|", x.get("title","")[:70])
    except Exception as e:
        print(d, "ERR", e)
