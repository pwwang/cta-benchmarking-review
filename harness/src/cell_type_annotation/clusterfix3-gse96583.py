# --------------------------------------------------------------------------
# WHAT   Scoped runner #3 of the repair: the 13 gse96583 ScType cluster-level arms,
#        recomputed against the GUARDED biopipen.utils::sctype_score(). ScType is the only
#        tool in the roster that calls sctype_score(), which is where the zero-variance
#        z-scaling NaN defect lived.
# REVIEW Section 6 keying repair / Figure 3. REQUIRES the patch in ../patches/
#        (biopipen.utils 0.4.9 + the sctype guard) -- without it these arms abort with
#        "arguments imply differing number of rows: 1, 0".
# CONFIG benchmark/gse96583/clusterfix3.toml
# SOURCE harness/src/cell_type_annotation/clusterfix3-gse96583.py
# --------------------------------------------------------------------------
"""Scoped runner: the 13 gse96583 ScType cluster-level arms, against the guarded sctype_score.

Same construction as src/cell_type_annotation/clusterfix-gse96583.py (the previous attempt's
runner), narrowed to the ScType family.  ScType is the only tool that calls
biopipen.utils::sctype_score(), which is where the z-scaling NaN bug lived, so these 13 arms are
recomputed as one consistently-guarded set into CellTypeAnnotation_gse96583_clusterfix3-output/.

The arms themselves are the classes from run-test.py (imported, never copied); only their
`requires` is repointed at this file's InputData, and their `ident` comes from
benchmark/gse96583/clusterfix3.toml at ARM level (envs.ident = "RNA_snn_res.0.5").

Usage:
    uv run src/cell_type_annotation/clusterfix3-gse96583.py @benchmark/gse96583/clusterfix3.toml
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

# Only the ScType family: the one tool family that calls sctype_score().
CLUSTER_ARMS = {
    "ScType": SOURCES,
}

# run-test.py holds the arms; its name has a dash, so it is loaded by path
_spec = spec_from_file_location(
    "cell_type_annotation_run_test", Path(__file__).with_name("run-test.py")
)
_run_test = module_from_spec(_spec)
_spec.loader.exec_module(_run_test)  # __name__ != "__main__", so nothing runs


class InputData(File2Proc):
    """Input data for the pipeline"""


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
