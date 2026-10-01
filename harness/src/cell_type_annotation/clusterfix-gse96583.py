# --------------------------------------------------------------------------
# WHAT   Scoped runner #1 of the cluster-keying repair: re-runs the 54 gse96583
#        CLUSTER-LEVEL arms (exactly those that declare an `ident`) with
#        ident = "RNA_snn_res.0.5" -- the column the evaluation actually uses -- into a NEW
#        pipeline directory, leaving the pre-repair artifacts untouched.
# REVIEW Section 6 keying repair / Figure 3 (the "after correction" end). The defect:
#        benchmark/gse96583/data-prep.R loops FindClusters over 7 resolutions, so
#        `seurat_clusters` is an alias for the LAST one (1.5 -> 32 clusters), while
#        benchmark/gse96583/eval.toml expands labels over RNA_snn_res.0.5 (24 clusters).
# CONFIG benchmark/gse96583/clusterfix.toml
# RUN    uv run src/cell_type_annotation/clusterfix-gse96583.py @benchmark/gse96583/clusterfix.toml
# SOURCE harness/src/cell_type_annotation/clusterfix-gse96583.py
# --------------------------------------------------------------------------
"""Scoped runner: re-run ONLY the gse96583 cluster-level arms with the fixed `ident`.

Fix for workspace-docs/CLUSTER-MAPPING-DEFECT.md. An arm is "cluster-level" exactly when it
declares an `ident`: ScType x13, scCATCH x13, scSorter x13, ScInfeR x2 and SCSA x13 -- 54 arms.
They used to cluster on `seurat_clusters`, which data-prep.R leaves aliased to the LAST
resolution it ran (1.5 -> 32 clusters), while benchmark/gse96583/eval.toml expands the labels
over `RNA_snn_res.0.5` (24 clusters). Here they run against `ident = "RNA_snn_res.0.5"`
(declared in benchmark/gse96583/clusterfix.toml) and land in a NEW pipeline directory, so the
pre-fix artifacts are left untouched.

Why a scoped runner: pipen builds its schedule from `starts` plus everything reachable
downstream of it, and *every* arm class in run-test.py requires the same `InputData`. So
`uv run src/cell_type_annotation/run-test.py @benchmark/gse96583/clusterfix.toml` would
schedule the whole ~200-arm roster -- the first arm without a binding fails and pipen breaks
out of its proc loop (measured in the MACA/SCSA POC: it stopped at
`CellTypeAnnotation_AUCell_AutoPos8525`, exit code still 0, and the configured arms never
started). Giving the imported arm classes a private input process keeps the schedule to
InputData + the 54 cluster-level arms, and runs no cell-level arm.

Usage:
    uv run src/cell_type_annotation/clusterfix-gse96583.py @benchmark/gse96583/clusterfix.toml

The arms themselves are the classes from run-test.py (imported, never copied); only their
`requires` is repointed at this file's InputData. The pipeline name comes from the `@<config>`
file, so the rerun lands in `CellTypeAnnotation_gse96583_clusterfix-output/`.
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

# The cluster-level arms: exactly the (tool, resource) pairs that carry an `ident`.
CLUSTER_ARMS = {
    "ScType": SOURCES,
    "scCATCH": SOURCES,
    "scSorter": SOURCES,
    "ScInfeR": ["ScTypeDBFull", "CellMarker"],
    "SCSA": SOURCES,
}

# run-test.py holds the arms; its name has a dash, so it is loaded by path
_spec = spec_from_file_location(
    "cell_type_annotation_run_test", Path(__file__).with_name("run-test.py")
)
_run_test = module_from_spec(_spec)
_spec.loader.exec_module(_run_test)  # __name__ != "__main__", so nothing runs


class InputData(File2Proc):
    """Input data for the pipeline"""


# The 54 arms, imported from run-test.py (never copied), one per (tool, resource)
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
