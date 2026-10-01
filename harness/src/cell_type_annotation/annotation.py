# --------------------------------------------------------------------------
# WHAT   The harness's first, minimal pipeline: SeuratPreparing -> SeuratClustering ->
#        MarkersFinder -> CellTypeAnnotation, with a small ScType / CellTypist /
#        scHDeepInsight / Garnett / cellassign roster declared inline.
# REVIEW Superseded by run-test.py. Kept because benchmark/pbmc3k/annotation.toml
#        configures exactly this roster (pipeline CellTypeAnnotation_pbmc3k), which is
#        the ancestor of the demonstration roster in Section 6.
# SOURCE harness/src/cell_type_annotation/annotation.py
# --------------------------------------------------------------------------
from pipen import run
from biopipen.core.proc import Proc
from biopipen.core.config import config
from biopipen.ns.misc import File2Proc
from biopipen.ns.scrna import (
    SeuratPreparing as SeuratPreparing_,
    SeuratClustering as SeuratClustering_,
    MarkersFinder as MarkersFinder_,
    CellTypeAnnotation as CellTypeAnnotation_
)


class InputData(File2Proc):
    """Input data for the pipeline"""


class CellTypeAnnotation_ScType_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "sctype",
        "ident": "ident",
        "sctype": {
            "db": "reference/ScTypeDB_short.txt",
            "tissue": "Immune system",
        },
        "anno_col": "sctype_sctypedb_short",
    }


class CellTypeAnnotation_ScType_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "sctype",
        "ident": "ident",
        "sctype": {
            "db": "reference/ScTypeDB_full.txt",
            "tissue": "Immune system",
        },
        "anno_col": "sctype_sctypedb_full",
    }


class CellTypeAnnotation_scCATCH_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "sccatch",
        "ident": "ident",
        "sccatch": {
            "tissue": "Immune system",
            "marker": "reference/ScTypeDB_short.txt",
        },
        "anno_col": "sccatch_sctypedb_short",
    }


class CellTypeAnnotation_scCATCH_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "sccatch",
        "ident": "ident",
        "sccatch": {
            "tissue": "Immune system",
            "marker": "reference/ScTypeDB_full.txt",
        },
        "anno_col": "sccatch_sctypedb_full",
    }


class CellTypeAnnotation_scSorter_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "scsorter",
        "ident": "ident",
        "scsorter": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_short.txt#cell_type,gene,tissue",
        },
        "anno_col": "scsorter_sctypedb_short",
    }


class CellTypeAnnotation_scSorter_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "scsorter",
        "ident": "ident",
        "scsorter": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_full.txt#cell_type,gene,tissue",
        },
        "anno_col": "scsorter_sctypedb_full",
    }


class CellTypeAnnotation_SCINA_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "SCINA",
        "ident": "ident",
        "scina": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_short.txt",
        },
        "anno_col": "scina_sctypedb_short",
    }


class CellTypeAnnotation_SCINA_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "SCINA",
        "ident": "ident",
        "scina": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_full.txt",
        },
        "anno_col": "scina_sctypedb_full",
    }


class CellTypeAnnotation_CelliD_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "cellid",
        "ident": "ident",
        "cellid": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_short.txt",
        },
        "anno_col": "cellid_sctypedb_short",
    }


class CellTypeAnnotation_CelliD_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "cellid",
        "ident": "ident",
        "cellid": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_full.txt",
        },
        "anno_col": "cellid_sctypedb_full",
    }


class CellTypeAnnotation_cellassign_ScTypeDbShort(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "cellassign",
        "ident": "ident",
        "cellassign": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_short.txt",
        },
        "anno_col": "cellassign_sctypedb_short",
    }


class CellTypeAnnotation_cellassign_ScTypeDbFull(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "cellassign",
        "ident": "ident",
        "cellassign": {
            "tissue": "Immune system",
            "db": "reference/ScTypeDB_full.txt",
        },
        "anno_col": "cellassign_sctypedb_full",
    }


class CellTypeAnnotation_SingleR_SingleRRef(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "singler",
        "ident": "ident",
        "singler": {
            "db": "reference/singler_ref.rds",
        },
        "anno_col": "singler_singler_ref",
    }


class CellTypeAnnotation_CellTypist_CellTypistImmuneAllHigh(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "celltypist",
        "ident": "ident",
        "celltypist": {
            "model": "reference/Immune_All_High.pkl",
        },
        "anno_col": "celltypist_celltypist_immune_all_high",
    }


class CellTypeAnnotation_CellTypist_CellTypistImmuneAllLow(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "celltypist",
        "ident": "ident",
        "celltypist": {
            "model": "reference/Immune_All_Low.pkl",
        },
        "anno_col": "celltypist_celltypist_immune_all_low",
    }


class CellTypeAnnotation_scHDeepInsight_scHDeepInsightRef(CellTypeAnnotation_):
    requires = InputData
    envs = {
        "tool": "schdeepinsight",
        "ident": "ident",
        "schdeepinsight": {
            "ref": "reference/schdeepinsight-reference.rds",
        },
        "anno_col": "schdeepinsight_schdeepinsight_ref",
    }


if __name__ == "__main__":
    run("CellTypeAnnotation", starts=InputData, plugins=["-report"])
