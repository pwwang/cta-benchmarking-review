# --------------------------------------------------------------------------
# WHAT   Two-arm proof-of-concept runner for the MACA/SCSA arms; superseded by
#        scaleout-maca-scsa.py. Kept because it is the experiment that established the
#        pipen scheduling behaviour the scoped runners exist to avoid (running run-test.py
#        with a small config still schedules the whole roster; the run stops at the first
#        unconfigured arm with "aucell.db is not set" and still exits 0).
# REVIEW Background for Section 6's silent-truncation finding. Its two arms were
#        superseded by the 26-arm scale-out.
# CONFIG benchmark/pbmc3k/poc-maca-scsa.toml
# SOURCE harness/src/cell_type_annotation/poc-maca-scsa.py
# --------------------------------------------------------------------------
"""POC runner: run ONLY the two new MACA/SCSA arms declared in run-test.py.

pipen builds its schedule from the `starts` procs plus everything reachable
downstream of them (`Pipen.build_proc_relationships`), and *every* arm class in
run-test.py requires the same `InputData`. So running run-test.py with a
two-arm config still schedules the whole ~175-arm roster: the first
unconfigured arm fails and `error_strategy = "ignore"` ends the pipeline
(measured: the run stops at `CellTypeAnnotation_AUCell_AutoPos8525` with
"`aucell.db` is not set" and the two new arms never start). This entry point
gives the two imported arm classes a private input process, so the schedule is
exactly InputData + MACA + SCSA.

Usage:
    uv run src/cell_type_annotation/poc-maca-scsa.py @benchmark/pbmc3k/poc-maca-scsa.toml

The arms themselves are the classes from run-test.py (imported, not copied);
only their `requires` is repointed at this file's InputData.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from biopipen.ns.misc import File2Proc
from pipen import run

# run-test.py holds the arms; its name has a dash, so it is loaded by path
_spec = spec_from_file_location(
    "cell_type_annotation_run_test", Path(__file__).with_name("run-test.py")
)
_run_test = module_from_spec(_spec)
_spec.loader.exec_module(_run_test)  # __name__ != "__main__", so nothing runs


class InputData(File2Proc):
    """Input data for the pipeline"""


CellTypeAnnotation_MACA_AutoPos8525 = _run_test.CellTypeAnnotation_MACA_AutoPos8525
CellTypeAnnotation_SCSA_AutoPos8525 = _run_test.CellTypeAnnotation_SCSA_AutoPos8525

# Repointing `requires` re-registers the arms downstream of THIS InputData
for _arm in (
    CellTypeAnnotation_MACA_AutoPos8525,
    CellTypeAnnotation_SCSA_AutoPos8525,
):
    _arm.requires = InputData


if __name__ == "__main__":
    run(
        "CellTypeAnnotation_pbmc3k_maca_scsa_poc",
        starts=InputData,
        plugins=["-report"],
    )
