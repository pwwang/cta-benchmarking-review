# --------------------------------------------------------------------------
# WHAT   Scale-out runner: runs ONLY the 26 MACA/SCSA arms declared in run-test.py. It
#        re-imports the arm classes from run-test.py and repoints their `requires` at a
#        private InputData, so the schedule is exactly InputData + 26 arms instead of the
#        whole ~200-arm roster.
# REVIEW Section 6: adds the MACA/SCSA arms to the demonstration roster (they are the
#        arms named in the direction-of-marker-effect observation).
# CONFIG benchmark/pbmc3k/scaleout-maca-scsa.toml, benchmark/gse96583/scaleout-maca-scsa.toml
# SOURCE harness/src/cell_type_annotation/scaleout-maca-scsa.py
# --------------------------------------------------------------------------
"""Scoped runner: run ONLY the MACA/SCSA arms declared in run-test.py.

pipen builds its schedule from the `starts` procs plus everything reachable
downstream of them (`Pipen.build_proc_relationships`), and *every* arm class in
run-test.py requires the same `InputData`. So running run-test.py with a
26-arm config still schedules the whole ~200-arm roster: the first unconfigured
arm fails and pipen breaks out of its proc loop (measured in the POC: the run
stopped at `CellTypeAnnotation_AUCell_AutoPos8525` with "`aucell.db` is not
set", exit code still 0, and the new arms never started). This entry point
gives the imported arm classes a private input process, so the schedule is
exactly InputData + the 26 MACA/SCSA arms.

Usage:
    uv run src/cell_type_annotation/scaleout-maca-scsa.py @benchmark/pbmc3k/scaleout-maca-scsa.toml
    uv run src/cell_type_annotation/scaleout-maca-scsa.py @benchmark/gse96583/scaleout-maca-scsa.toml

The arms themselves are the classes from run-test.py (imported, not copied);
only their `requires` is repointed at this file's InputData. The pipeline name
comes from the `@<config>` file, so the two datasets land in distinct output
directories and keep the standard per-arm process names.
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

# run-test.py holds the arms; its name has a dash, so it is loaded by path
_spec = spec_from_file_location(
    "cell_type_annotation_run_test", Path(__file__).with_name("run-test.py")
)
_run_test = module_from_spec(_spec)
_spec.loader.exec_module(_run_test)  # __name__ != "__main__", so nothing runs


class InputData(File2Proc):
    """Input data for the pipeline"""


# The 26 arms, imported from run-test.py (never copied), one per (tool, source)
ARMS = [
    (
        f"CellTypeAnnotation_{tool}_{m}",
        getattr(_run_test, f"CellTypeAnnotation_{tool}_{m}"),
    )
    for tool in ("MACA", "SCSA")
    for m in SOURCES
]

for _name, _arm in ARMS:
    globals()[_name] = _arm  # keep the standard names visible in this module
    # Repointing `requires` re-registers the arm downstream of THIS InputData
    _arm.requires = InputData


def pipeline_name() -> str:
    """Pipeline name from the `@<config>` argument (keeps the two datasets apart)."""
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
