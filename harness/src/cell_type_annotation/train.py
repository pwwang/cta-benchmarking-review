# --------------------------------------------------------------------------
# WHAT   Marker-resource training pipeline: HitypeWeightTrainer and GarnettClassifierTrainer
#        per marker resource, fitted on the TRAIN split only.
# REVIEW Section 6: produces the learned marker tables that the Hitype/Garnett arms (and
#        the marker-resource comparison) consume. The hitype cv_folds = 1 disclosure that
#        must accompany those tables is declared in benchmark/<ds>/eval.toml.
# SOURCE harness/src/cell_type_annotation/train.py
# --------------------------------------------------------------------------
from pipen import run
from biopipen.core.proc import Proc
from biopipen.core.config import config
from biopipen.ns.misc import File2Proc
from biopipen.ns.scrna import (
    HitypeWeightTrainer as HitypeWeightTrainer_,
    GarnettClassifierTrainer as GarnettClassifierTrainer_,
)


class InputData(File2Proc):
    """Input data for the pipeline"""


# M1
class HitypeWeightTrainer_ScTypeDBShort(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
    }


class GarnettClassifierTrainer_ScTypeDBShort(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
    }


# M2
class HitypeWeightTrainer_ScTypeDBFull(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
    }


class GarnettClassifierTrainer_ScTypeDBFull(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
    }


# M3
class HitypeWeightTrainer_scCATCH(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
    }


class GarnettClassifierTrainer_scCATCH(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
    }


# M4
class HitypeWeightTrainer_CellMarker(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
    }


class GarnettClassifierTrainer_CellMarker(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
    }


# M5_8525
class HitypeWeightTrainer_AutoPos8525(HitypeWeightTrainer_):
    requires = InputData
    export = True
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525},
    }


class GarnettClassifierTrainer_AutoPos8525(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_AutoPos8525


# M5_8526
class HitypeWeightTrainer_AutoPos8526(HitypeWeightTrainer_):
    requires = InputData
    export = True
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526},
    }


class GarnettClassifierTrainer_AutoPos8526(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_AutoPos8526


# M5_8527
class HitypeWeightTrainer_AutoPos8527(HitypeWeightTrainer_):
    requires = InputData
    export = True
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527},
    }


class GarnettClassifierTrainer_AutoPos8527(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_AutoPos8527


# M6
class HitypeWeightTrainer_AutoBoth(HitypeWeightTrainer_):
    requires = InputData
    export = True
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False},
    }


class GarnettClassifierTrainer_AutoBoth(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_AutoBoth


# M9_M1_pos
class HitypeWeightTrainer_ScTypeDBShortPos(HitypeWeightTrainer_):
    requires = InputData
    export = True
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True},
    }


class GarnettClassifierTrainer_ScTypeDBShortPos(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_ScTypeDBShortPos


# M9_M2_pos
class HitypeWeightTrainer_ScTypeDBFullPos(HitypeWeightTrainer_):
    requires = InputData
    export = True
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True},
    }


class GarnettClassifierTrainer_ScTypeDBFullPos(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_ScTypeDBFullPos


# M9_M3_pos
class HitypeWeightTrainer_scCATCHPos(HitypeWeightTrainer_):
    requires = InputData
    export = True
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True},
    }


class GarnettClassifierTrainer_scCATCHPos(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_scCATCHPos


# M9_M4_pos
class HitypeWeightTrainer_CellMarkerPos(HitypeWeightTrainer_):
    requires = InputData
    export = True
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True},
    }


class GarnettClassifierTrainer_CellMarkerPos(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_CellMarkerPos


# M12
class HitypeWeightTrainer_PanglaoDB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
    }


class GarnettClassifierTrainer_PanglaoDB(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
    }




# ---------------------------------------------------------------
# Training-method axis: 5 methods x 13 sources (glmnet remains the
# unnamed default arm). `method` is an argument of hitype::train_weights();
# biopipen forwards envs.train_weights verbatim and validates it against
# formalArgs(train_weights), so it needs no biopipen env declaration.
# Each arm keeps its source's own marker file / tissue / cancer / seed / pos_only.
# ---------------------------------------------------------------

class HitypeWeightTrainer_ScTypeDBShort_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "uniform"},
    }


class HitypeWeightTrainer_ScTypeDBShort_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "correlation"},
    }


class HitypeWeightTrainer_ScTypeDBShort_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "lr"},
    }


class HitypeWeightTrainer_ScTypeDBShort_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "rf"},
    }


class HitypeWeightTrainer_ScTypeDBShort_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "xgb"},
    }


class HitypeWeightTrainer_ScTypeDBFull_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "uniform"},
    }


class HitypeWeightTrainer_ScTypeDBFull_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "correlation"},
    }


class HitypeWeightTrainer_ScTypeDBFull_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "lr"},
    }


class HitypeWeightTrainer_ScTypeDBFull_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "rf"},
    }


class HitypeWeightTrainer_ScTypeDBFull_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "xgb"},
    }


class HitypeWeightTrainer_scCATCH_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"method": "uniform"},
    }


class HitypeWeightTrainer_scCATCH_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"method": "correlation"},
    }


class HitypeWeightTrainer_scCATCH_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"method": "lr"},
    }


class HitypeWeightTrainer_scCATCH_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"method": "rf"},
    }


class HitypeWeightTrainer_scCATCH_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"method": "xgb"},
    }


class HitypeWeightTrainer_CellMarker_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"method": "uniform"},
    }


class HitypeWeightTrainer_CellMarker_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"method": "correlation"},
    }


class HitypeWeightTrainer_CellMarker_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"method": "lr"},
    }


class HitypeWeightTrainer_CellMarker_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"method": "rf"},
    }


class HitypeWeightTrainer_CellMarker_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"method": "xgb"},
    }


class HitypeWeightTrainer_AutoPos8525_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525, "method": "uniform"},
    }


class HitypeWeightTrainer_AutoPos8525_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525, "method": "correlation"},
    }


class HitypeWeightTrainer_AutoPos8525_LR(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525, "method": "lr"},
    }


class HitypeWeightTrainer_AutoPos8525_RF(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525, "method": "rf"},
    }


class HitypeWeightTrainer_AutoPos8525_XGB(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8525, "method": "xgb"},
    }


class HitypeWeightTrainer_AutoPos8526_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526, "method": "uniform"},
    }


class HitypeWeightTrainer_AutoPos8526_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526, "method": "correlation"},
    }


class HitypeWeightTrainer_AutoPos8526_LR(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526, "method": "lr"},
    }


class HitypeWeightTrainer_AutoPos8526_RF(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526, "method": "rf"},
    }


class HitypeWeightTrainer_AutoPos8526_XGB(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8526, "method": "xgb"},
    }


class HitypeWeightTrainer_AutoPos8527_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527, "method": "uniform"},
    }


class HitypeWeightTrainer_AutoPos8527_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527, "method": "correlation"},
    }


class HitypeWeightTrainer_AutoPos8527_LR(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527, "method": "lr"},
    }


class HitypeWeightTrainer_AutoPos8527_RF(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527, "method": "rf"},
    }


class HitypeWeightTrainer_AutoPos8527_XGB(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": True},
        "train_weights": {"seed": 8527, "method": "xgb"},
    }


class HitypeWeightTrainer_AutoBoth_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False, "method": "uniform"},
    }


class HitypeWeightTrainer_AutoBoth_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False, "method": "correlation"},
    }


class HitypeWeightTrainer_AutoBoth_LR(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False, "method": "lr"},
    }


class HitypeWeightTrainer_AutoBoth_RF(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False, "method": "rf"},
    }


class HitypeWeightTrainer_AutoBoth_XGB(HitypeWeightTrainer_):
    requires = InputData
    envs = {
        "find_markers": {"pos_only": False},
        "train_weights": {"pos_only": False, "method": "xgb"},
    }


class HitypeWeightTrainer_ScTypeDBShortPos_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "uniform"},
    }


class HitypeWeightTrainer_ScTypeDBShortPos_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "correlation"},
    }


class HitypeWeightTrainer_ScTypeDBShortPos_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "lr"},
    }


class HitypeWeightTrainer_ScTypeDBShortPos_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "rf"},
    }


class HitypeWeightTrainer_ScTypeDBShortPos_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "xgb"},
    }


class HitypeWeightTrainer_ScTypeDBFullPos_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "uniform"},
    }


class HitypeWeightTrainer_ScTypeDBFullPos_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "correlation"},
    }


class HitypeWeightTrainer_ScTypeDBFullPos_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "lr"},
    }


class HitypeWeightTrainer_ScTypeDBFullPos_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "rf"},
    }


class HitypeWeightTrainer_ScTypeDBFullPos_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"pos_only": True, "method": "xgb"},
    }


class HitypeWeightTrainer_scCATCHPos_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True, "method": "uniform"},
    }


class HitypeWeightTrainer_scCATCHPos_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True, "method": "correlation"},
    }


class HitypeWeightTrainer_scCATCHPos_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True, "method": "lr"},
    }


class HitypeWeightTrainer_scCATCHPos_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True, "method": "rf"},
    }


class HitypeWeightTrainer_scCATCHPos_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "train_weights": {"pos_only": True, "method": "xgb"},
    }


class HitypeWeightTrainer_CellMarkerPos_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True, "method": "uniform"},
    }


class HitypeWeightTrainer_CellMarkerPos_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True, "method": "correlation"},
    }


class HitypeWeightTrainer_CellMarkerPos_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True, "method": "lr"},
    }


class HitypeWeightTrainer_CellMarkerPos_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True, "method": "rf"},
    }


class HitypeWeightTrainer_CellMarkerPos_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/CellMarker_Human_Blood.txt")]
    envs = {
        "cancer": "Normal",
        "train_weights": {"pos_only": True, "method": "xgb"},
    }


class HitypeWeightTrainer_PanglaoDB_UNIFORM(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "uniform"},
    }


class HitypeWeightTrainer_PanglaoDB_CORRELATION(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "correlation"},
    }


class HitypeWeightTrainer_PanglaoDB_LR(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "lr"},
    }


class HitypeWeightTrainer_PanglaoDB_RF(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "rf"},
    }


class HitypeWeightTrainer_PanglaoDB_XGB(HitypeWeightTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "train_weights": {"method": "xgb"},
    }




# ----------------------------------------------------------------------
# Garnett at its OWN documented settings (vignette: set.seed(260), db = org.Hs.eg.db,
# SYMBOL ids, num_unknown = 50, lambda grid left at garnett's default). The five
# sources here are the ones that collapse under the harness configuration, so the
# Results table can report both regimes on the same sources. Only the garnett call
# settings change: the marker file and every filter mirror the base arm exactly.
# ----------------------------------------------------------------------

class GarnettClassifierTrainer_ScTypeDBShort_Documented(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_short.txt")]
    envs = {
        "tissue": "Immune system",
        "seed": 260,
        "db": "org.Hs.eg.db",
        "cds_gene_id_type": "SYMBOL",
        "marker_file_gene_id_type": "SYMBOL",
        "classifier_gene_id_type": "SYMBOL",
        "num_unknown": 50,
    }


class GarnettClassifierTrainer_ScTypeDBFull_Documented(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/ScTypeDB_full.txt")]
    envs = {
        "tissue": "Immune system",
        "seed": 260,
        "db": "org.Hs.eg.db",
        "cds_gene_id_type": "SYMBOL",
        "marker_file_gene_id_type": "SYMBOL",
        "classifier_gene_id_type": "SYMBOL",
        "num_unknown": 50,
    }


class GarnettClassifierTrainer_scCATCH_Documented(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/scCATCH_human.txt")]
    envs = {
        "cancer": "Normal",
        "tissue": "Blood",
        "seed": 260,
        "db": "org.Hs.eg.db",
        "cds_gene_id_type": "SYMBOL",
        "marker_file_gene_id_type": "SYMBOL",
        "classifier_gene_id_type": "SYMBOL",
        "num_unknown": 50,
    }


class GarnettClassifierTrainer_PanglaoDB_Documented(GarnettClassifierTrainer_):
    requires = InputData
    input_data = lambda ch: [(ch.iloc[0, 0], "reference/PanglaoDB_Human.txt")]
    envs = {
        "tissue": "Immune system",
        "seed": 260,
        "db": "org.Hs.eg.db",
        "cds_gene_id_type": "SYMBOL",
        "marker_file_gene_id_type": "SYMBOL",
        "classifier_gene_id_type": "SYMBOL",
        "num_unknown": 50,
    }


class GarnettClassifierTrainer_AutoBoth_Documented(GarnettClassifierTrainer_):
    requires = InputData, HitypeWeightTrainer_AutoBoth
    envs = {
        "seed": 260,
        "db": "org.Hs.eg.db",
        "cds_gene_id_type": "SYMBOL",
        "marker_file_gene_id_type": "SYMBOL",
        "classifier_gene_id_type": "SYMBOL",
        "num_unknown": 50,
    }


if __name__ == "__main__":
    run("MarkerTraining", starts=InputData, plugins=["-report"])
