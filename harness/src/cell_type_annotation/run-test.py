# --------------------------------------------------------------------------
# WHAT   THE ARM RUNNER. Declares the full test-split roster -- 201 arm classes across
#        ScType, scCATCH, scSorter, SCSA, ScInfeR, MACA, SCINA, CelliD, Garnett, Hitype,
#        UCell, singscore, GSVA and AUCell -- driven by benchmark/<ds>/run-test.toml.
# REVIEW The demonstration roster behind Section 6 and Supplementary Table S3.
# RUN    uv run src/cell_type_annotation/run-test.py @benchmark/<ds>/run-test.toml
# SOURCE harness/src/cell_type_annotation/run-test.py
# --------------------------------------------------------------------------
from pipen import run
from biopipen.ns.misc import File2Proc
from biopipen.ns.scrna import CellTypeAnnotation as CellTypeAnnotation_

# Marker-based tools that consume hitype's trained weight tables (the universal marker format)
# as their input, so that only the tool differs -- see docs/TOOLS.md and docs/ARMS.md.
#
# `cellassign` needs its R package (and a TensorFlow-backed Python) installed first; flip
# INCLUDE_CELLASSIGN to True then, and add the matching env block to run-test.toml.
INCLUDE_CELLASSIGN = False

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


class InputData(File2Proc):
    """Input data for the pipeline"""


class CellTypeAnnotation_Garnett_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Garnett_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}

class CellTypeAnnotation_Hitype_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

class CellTypeAnnotation_Hitype_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "Hitype"}

# cell-level
class CellTypeAnnotation_SCINA_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

class CellTypeAnnotation_SCINA_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "SCINA"}

# cell-level
class CellTypeAnnotation_CelliD_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

class CellTypeAnnotation_CelliD_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "cellid"}

# cluster-level: needs an unsupervised cluster column
class CellTypeAnnotation_ScType_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

class CellTypeAnnotation_ScType_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sctype"}

# cluster-level: needs an unsupervised cluster column
class CellTypeAnnotation_scCATCH_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

class CellTypeAnnotation_scCATCH_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "sccatch"}

# cluster-level: needs an unsupervised cluster column
class CellTypeAnnotation_scSorter_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

class CellTypeAnnotation_scSorter_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsorter"}

# cell-level: equal-weight marker scorers (the weight column is deliberately ignored)
class CellTypeAnnotation_UCell_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "ucell"}

class CellTypeAnnotation_UCell_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "ucell"}

class CellTypeAnnotation_UCell_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "ucell"}

# cell-level
class CellTypeAnnotation_AUCell_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "aucell"}

class CellTypeAnnotation_AUCell_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "aucell"}

class CellTypeAnnotation_AUCell_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "aucell"}

# cell-level
class CellTypeAnnotation_GSVA_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "gsva"}

class CellTypeAnnotation_GSVA_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "gsva"}

class CellTypeAnnotation_GSVA_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "gsva"}

# cell-level
class CellTypeAnnotation_singscore_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "singscore"}

class CellTypeAnnotation_singscore_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "singscore"}

class CellTypeAnnotation_singscore_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "singscore"}

# cluster-level: needs an unsupervised cluster column
class CellTypeAnnotation_ScInfeR_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scinfer"}

class CellTypeAnnotation_ScInfeR_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scinfer"}



# Training-method axis: annotation arms fed by the matching trained table

class CellTypeAnnotation_Hitype_ScTypeDBShort_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShort_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShort_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShort_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShort_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFull_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFull_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFull_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFull_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFull_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCH_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCH_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCH_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCH_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCH_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarker_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarker_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarker_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarker_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarker_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8525_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8525_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8525_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8525_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8525_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8526_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8526_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8526_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8526_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8526_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8527_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8527_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8527_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8527_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoPos8527_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoBoth_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoBoth_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoBoth_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoBoth_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_AutoBoth_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShortPos_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShortPos_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShortPos_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShortPos_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBShortPos_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFullPos_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFullPos_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFullPos_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFullPos_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_ScTypeDBFullPos_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCHPos_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCHPos_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCHPos_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCHPos_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_scCATCHPos_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarkerPos_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarkerPos_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarkerPos_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarkerPos_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_CellMarkerPos_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_PanglaoDB_UNIFORM(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_PanglaoDB_CORRELATION(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_PanglaoDB_LR(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_PanglaoDB_RF(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}


class CellTypeAnnotation_Hitype_PanglaoDB_XGB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "hitype"}




# Garnett documented-configuration annotations (fed by the _Documented classifiers)

class CellTypeAnnotation_Garnett_ScTypeDBShort_Documented(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}


class CellTypeAnnotation_Garnett_ScTypeDBFull_Documented(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}


class CellTypeAnnotation_Garnett_scCATCH_Documented(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}


class CellTypeAnnotation_Garnett_PanglaoDB_Documented(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}


class CellTypeAnnotation_Garnett_AutoBoth_Documented(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "garnett"}


# Two more marker-based tools of biopipen's CellTypeAnnotation namespace; the POC
# added the AutoPos8525 pair first (benchmark/pbmc3k/poc-maca-scsa.toml), the rest of
# the 13-resource roster follows below.
class CellTypeAnnotation_MACA_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_SCSA_AutoPos8525(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

# MACA (cell-level) and SCSA (cluster-level) across every marker resource. The marker
# table (`db`), the interpreter (`python`) and, for the cluster-level SCSA,
# `ident = "seurat_clusters"` are bound per arm in benchmark/<ds>/run-test.toml.
class CellTypeAnnotation_MACA_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_MACA_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "maca"}

class CellTypeAnnotation_SCSA_ScTypeDBShort(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_ScTypeDBFull(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_scCATCH(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_CellMarker(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_AutoPos8526(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_AutoPos8527(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_AutoBoth(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_ScTypeDBShortPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_ScTypeDBFullPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_scCATCHPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_CellMarkerPos(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}

class CellTypeAnnotation_SCSA_PanglaoDB(CellTypeAnnotation_):
    requires = InputData
    envs = {"tool": "scsa"}


if INCLUDE_CELLASSIGN:
    class CellTypeAnnotation_cellassign_ScTypeDBShort(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_ScTypeDBFull(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_scCATCH(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_CellMarker(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_AutoPos8525(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_AutoPos8526(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_AutoPos8527(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_AutoBoth(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_ScTypeDBShortPos(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_ScTypeDBFullPos(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_scCATCHPos(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_CellMarkerPos(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

    class CellTypeAnnotation_cellassign_PanglaoDB(CellTypeAnnotation_):
        requires = InputData
        envs = {"tool": "cellassign"}

if __name__ == "__main__":
    run("CellTypeAnnotationTrained", starts=InputData, plugins=["-report"])
