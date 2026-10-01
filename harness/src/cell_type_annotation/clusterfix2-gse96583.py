# --------------------------------------------------------------------------
# WHAT   Scoped runner #2 of the repair: the 26 cluster-level arms the first repair run
#        never reached (scCATCH x13, scSorter x13). A second run is needed because pipen
#        breaks out of its proc loop at the first failing arm while still exiting 0 and
#        does not resume, so the first run stopped at the failing ScType arm.
# REVIEW Section 6 keying repair / Figure 3. Config: benchmark/gse96583/clusterfix2.toml
# SOURCE harness/src/cell_type_annotation/clusterfix2-gse96583.py
# --------------------------------------------------------------------------
"""Scoped runner #2: re-run the REMAINING gse96583 cluster-level arms with the fixed `ident`.

Fix for workspace-docs/CLUSTER-MAPPING-DEFECT.md. An arm is "cluster-level" exactly when it
declares an `ident`: ScType x13, scCATCH x13, scSorter x13, ScInfeR x2 and SCSA x13 -- 54 arms.
They used to cluster on `seurat_clusters`, which data-prep.R leaves aliased to the LAST
resolution it ran (1.5 -> 32 clusters), while benchmark/gse96583/eval.toml expands the labels
over `RNA_snn_res.0.5` (24 clusters). Here they run against `ident = "RNA_snn_res.0.5"`
(declared in benchmark/gse96583/clusterfix2.toml) and land in a NEW pipeline directory, so the
pre-fix artifacts are left untouched.

Why a SECOND scoped runner: the first one (clusterfix-gse96583.py @ clusterfix.toml) declared
all 54 cluster-level arms, but ScType has only 4 arms in the gse96583 roster, and
`CellTypeAnnotation_ScType_CellMarker` fails on gse96583 (`Error in data.frame(...) : arguments
imply differing number of rows: 1, 0`). With `error_strategy = "ignore"` pipen breaks out of its
proc loop at the FIRST failure while still exiting 0, and it does not resume, so that run
stopped after the 19 good arms (13 SCSA + ScType_AutoBoth/AutoPos8525-27 + 2 ScInfeR) and never
reached scCATCH/scSorter. This runner schedules only the 26 arms that still need it:
scCATCH x13 and scSorter x13.

Why a scoped runner at all: pipen builds its schedule from `starts` plus everything reachable
downstream of it, and *every* arm class in run-test.py requires the same `InputData`. So
`uv run src/cell_type_annotation/run-test.py @benchmark/gse96583/clusterfix2.toml` would
schedule the whole ~200-arm roster -- the first arm without a binding fails and pipen breaks
out of its proc loop. Giving the imported arm classes a private input process keeps the
schedule to InputData + the 26 scCATCH/scSorter arms, and runs no ScType/SCSA/ScInfeR/cell-level
arm.

Usage:
    uv run src/cell_type_annotation/clusterfix2-gse96583.py @benchmark/gse96583/clusterfix2.toml

The arms themselves are the classes from run-test.py (imported, never copied); only their
`requires` is repointed at this file's InputData. The pipeline name comes from the `@<config>`
file, so the rerun lands in `CellTypeAnnotation_gse96583_clusterfix2-output/`.
"""
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from biopipen.ns.misc import File2Proc
from pipen import run

SOURCES = [
    "ScTypeDBShort",
    "ScTypeDBFull",
    "scCATCH",
    "CellMarker",
    "AutoPos8525",
    "AutoPos8526",
    "AutoPos8527",
    "AutoBoth",
    "ScTypeDBShortPos",
    "ScTypeDBFullPos",
    "scCATCHPos",
    "CellMarkerPos",
    "PanglaoDB",
]

# The cluster-level arms still missing after the first clusterfix run: exactly the
# scCATCH and scSorter (tool, resource) pairs. No ScType arm here -- ScType has only
# 4 arms in the gse96583 roster and they are already done.
CLUSTER_ARMS = {
    "scCATCH": SOURCES,
    "scSorter": SOURCES,
}

# run-test.py holds the arms; its name has a dash, so it is loaded by path
_spec = spec_from_file_location(
    "cell_type_annotation_run_test", Path(__file__).with_name("run-test.py")
)
_run_test = module_from_spec(_spec)
_spec.loader.exec_module(_run_test)  # __name__ != "__main__", so nothing runs


class InputData(File2Proc):
    """Input data for the pipeline"""


# The 26 arms, imported from run-test.py (never copied), one per (tool, resource)
ARMS = [
    (
        f"CellTypeAnnotation_{tool}_{m}",
        getattr(_run_test, f"CellTypeAnnotation_{tool}_{m}"),
    )
    for tool, sources in CLUSTER_ARMS.items()
    for m in sources
]

for _name, _arm in ARMS:
    globals()[_name] = _arm  # keep the standard names visible in this module
    # Repointing `requires` re-registers the arm downstream of THIS InputData
    _arm.requires = InputData


def pipeline_name() -> str:
    """Pipeline name from the `@<config>` argument."""
    for arg in sys.argv[1:]:
        if arg.startswith("@"):
            text = Path(arg[1:]).read_text()
            match = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.M)
            if match:
                return match.group(1)
            raise SystemExit(f"no `name` in config file: {arg[1:]}")
    raise SystemExit(f"usage: {Path(__file__).name} @<config.toml>")


if __name__ == "__main__":
    run(pipeline_name(), starts=InputData, plugins=["-report"])
