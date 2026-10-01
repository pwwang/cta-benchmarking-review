"""paths.py -- the single place where this package resolves a location.

Nothing in this package hardcodes a machine path.  Every location is read from an
environment variable and falls back to a RELATIVE default computed from this file's own
location (``PACKAGE_ROOT`` below), so a fresh clone runs as-is and a reader who keeps data
elsewhere only has to export a variable.  ``paths.describe()`` prints what resolved, and
from where.

Environment variables (all optional)
------------------------------------
===========================  ====================================================  ======================================
variable                     what it is                                            default
===========================  ====================================================  ======================================
``CTA_DATA``                 root for every downloaded / generated data file       ``<package root>/data``  (git-ignored)
``CTA_HARNESS``              the annotation-harness checkout whose ``*-output``     ``<package root>/harness``
                             directories hold the per-arm results
``CTA_ARTIFACTS``            vote / truth / resource tables built from the          ``$CTA_DATA/artifacts``
                             harness output (``truth.tsv``, ``votes.tsv``, ...)
``CTA_FULLTEXT``             the audit's full-text cache: retrieved and converted   ``$CTA_DATA/fulltext``
                             full texts that the screening and coding steps read
``CTA_OUTPUT``               generated tables the audit writes                      ``$CTA_DATA/output``
``CTA_LOGS``                 logs the analysis scripts read                         ``$CTA_DATA/logs``
``CTA_GEO_RAW``              the raw GSE96583 GEO download (not redistributed)      ``$CTA_DATA/geo/gse96583/raw``
``HELDOUT_DIR``              held-out inputs for ``analysis/uncertainty.py``        ``$CTA_DATA/heldout``
``CTA_FACTS``                the canonical facts file the figure scripts check      ``<package root>/FACTS.md``
===========================  ====================================================  ======================================

Anything not overridden is derived from ``PACKAGE_ROOT = Path(__file__).resolve().parent``,
so the whole package is relocatable: move the directory and every default moves with it.

Usage
-----
Scripts in ``analysis/``, ``audit/`` and ``figures/`` live one directory below the package
root, so they begin with::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
    import paths

    raw = paths.FULLTEXT / "arxiv_2409.15678.txt"

Standalone files that must stay standalone (``reconcile_core.py``, the R
scripts, the TOML configs under ``harness/``) read the same variable names directly from
the environment, with the same relative defaults; see the README, "Configuration".
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "PACKAGE_ROOT",
    "DATA",
    "HARNESS",
    "ARTIFACTS",
    "FULLTEXT",
    "OUTPUT",
    "LOGS",
    "GEO_RAW",
    "HELDOUT",
    "FACTS",
    "FIGURES",
    "describe",
]

# --- the one fixed anchor: this file sits at the package root ----------------
PACKAGE_ROOT = Path(__file__).resolve().parent

# --- data roots --------------------------------------------------------------
DATA = Path(os.environ.get("CTA_DATA", PACKAGE_ROOT / "data"))

# --- the annotation harness that produced the arm results -------------------
#    (its *-output/ directories are what `analysis/*.py` reads)
HARNESS = Path(os.environ.get("CTA_HARNESS", PACKAGE_ROOT / "harness"))

# --- tables derived from the harness output ---------------------------------
ARTIFACTS = Path(os.environ.get("CTA_ARTIFACTS", DATA / "artifacts"))

# --- the audit's retrieval cache and generated tables -----------------------
FULLTEXT = Path(os.environ.get("CTA_FULLTEXT", DATA / "fulltext"))
OUTPUT = Path(os.environ.get("CTA_OUTPUT", DATA / "output"))

# --- logs and other working inputs ------------------------------------------
LOGS = Path(os.environ.get("CTA_LOGS", DATA / "logs"))
GEO_RAW = Path(os.environ.get("CTA_GEO_RAW", DATA / "geo" / "gse96583" / "raw"))
HELDOUT = Path(os.environ.get("HELDOUT_DIR", DATA / "heldout"))

# --- files that ship with the package ---------------------------------------
FACTS = Path(os.environ.get("CTA_FACTS", PACKAGE_ROOT / "FACTS.md"))
FIGURES = PACKAGE_ROOT / "figures"


def describe() -> str:
    """One line per resolved location, with the variable that can override it."""
    rows = [
        ("CTA_DATA", DATA),
        ("CTA_HARNESS", HARNESS),
        ("CTA_ARTIFACTS", ARTIFACTS),
        ("CTA_FULLTEXT", FULLTEXT),
        ("CTA_OUTPUT", OUTPUT),
        ("CTA_LOGS", LOGS),
        ("CTA_GEO_RAW", GEO_RAW),
        ("HELDOUT_DIR", HELDOUT),
        ("CTA_FACTS", FACTS),
    ]
    width = max(len(name) for name, _ in rows)
    out = ["package root: %s" % PACKAGE_ROOT]
    for name, path in rows:
        mark = " (set)" if os.environ.get(name) else ""
        out.append("%-*s = %s%s" % (width, name, path, mark))
    return "\n".join(out)


if __name__ == "__main__":
    print(describe())
