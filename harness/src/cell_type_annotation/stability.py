#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Tabulates comparator training stability and label coverage from artifacts already
#        on disk (garnett diagnostics sidecars, cell2celltype tables, hitype weight tables).
#        Runs no pipeline and needs no R.
# REVIEW Section 6: the comparator-stability check, including the
#        `silent-zero-coverage` verdict for an arm that trains non-degenerately and then
#        labels every cell Unknown.
# SOURCE harness/src/cell_type_annotation/stability.py
# --------------------------------------------------------------------------
"""Tabulate comparator training stability and label coverage for a dataset.

Reads the text artifacts already written on disk (garnett diagnostics sidecars,
cell2celltype tables and hitype weight tables). Runs no pipeline, needs no R.

A comparator can train non-degenerately and still annotate every cell as
``Unknown``; that signature is what the ``silent-zero-coverage`` verdict exists
to catch.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

GARNETT_VERDICTS = (
    "missing",
    "degenerate-training",
    "partial-degenerate",
    "stale-annotation",
    "no-annotation",
    "silent-zero-coverage",
    "healthy",
)
HITYPE_VERDICTS = ("inert", "healthy")

# Values are raw (numbers stay numbers for the json); the tables format them.
# The timestamp fields stay raw epoch seconds; `anno_stale` is the judgement made from them.
GARNETT_COLUMNS = (
    "arm",
    "verdict",
    "anno_stale",
    "diag_nodes",
    "degen",
    "lambda_min",
    "max_abs_coef",
    "n_nonzero",
    "labelled",
    "unknown%",
)
HITYPE_COLUMNS = (
    "arm",
    "verdict",
    "anno_stale",
    "classes",
    "rows",
    "genes",
    "min_class_max|w|",
    "max|w|",
)

VERDICT_COLOR = {
    "healthy": "32",
    "no-annotation": "33",
    "partial-degenerate": "33",
    "stale-annotation": "33",
    "missing": "2",
    "degenerate-training": "31",
    "silent-zero-coverage": "31",
    "inert": "31",
}

LEGEND = """legend:
  garnett panel:
    missing              - no classifier diagnostics sidecar on disk; training was not run for this arm
    degenerate-training  - every diagnostic node is degenerate; training produced an all-zero model
    partial-degenerate   - some, but not all, diagnostic nodes are degenerate
    stale-annotation     - the labels came from a superseded model artifact: the cell2celltype.tsv is older than the newest trained model for this arm, so re-training invalidated the annotation. The coverage columns must not be trusted until annotation is re-run for that dataset.
    no-annotation        - trained non-degenerately but no cell2celltype.tsv was written
    silent-zero-coverage - unknown_pct == 100.0 while training was non-degenerate. `silent-zero-coverage` means training looked fine but the annotator labelled nothing; the known cause in this project is a size-factor convention mismatch between garnett's training and prediction stages (fixed in biopipen, CHANGELOG Unreleased) — this tool flags the signature, it does not diagnose the cause.
    healthy              - trained non-degenerately and labelled at least one cell
  hitype panel:
    inert                - every weight is zero (or the weight table has no rows); the model carries no signal
    healthy              - at least one class has a non-zero weight"""


def _num(value):
    """Float value or None (artifacts may hold NA / empty fields)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value):
    """Int value or None (artifacts may hold NA / empty fields)."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _truthy(value) -> bool:
    return str(value).strip().upper() == "TRUE"


def _read_tsv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _first(directory: Path, pattern: str):
    """First file matching `pattern` in `directory`, or None if the dir is absent/empty."""
    if not directory.is_dir():
        return None
    hits = sorted(p for p in directory.glob(pattern) if p.is_file())
    return hits[0] if hits else None


def _newest(directory: Path, pattern: str):
    """Most recently modified file matching `pattern`, or None if the dir is absent/empty."""
    if not directory.is_dir():
        return None
    hits = [p for p in directory.glob(pattern) if p.is_file()]
    return max(hits, key=os.path.getmtime) if hits else None


def _staleness(model_file, anno_file) -> tuple[bool, float | None, float | None]:
    """(anno_stale, model_mtime, anno_mtime) from paths alone -- artifacts are never opened.

    The annotation is stale when it is older than the model that produced it: re-training
    after an annotation run leaves labels that no model on disk can reproduce.
    """
    model_mtime = os.path.getmtime(model_file) if model_file else None
    anno_mtime = os.path.getmtime(anno_file) if anno_file else None
    stale = model_mtime is not None and anno_mtime is not None and model_mtime - anno_mtime > 1.0
    return stale, model_mtime, anno_mtime


def _fmt(value, spec: str = "%.5g", dash: str = "-") -> str:
    return dash if value is None else spec % value


def _paint(text: str, code: str, color: bool) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if color else text


def _coverage(path) -> dict:
    """Per-cell label counts from a `<x>.cell2celltype.tsv` (2nd column is the label)."""
    if path is None:
        return {}
    rows = _read_tsv(path)
    fields = list(rows[0].keys()) if rows else []
    col = fields[1] if len(fields) > 1 else (fields[0] if fields else "Cell")
    counts = Counter(r.get(col) or "" for r in rows)
    n_cells = len(rows)
    n_unknown = counts.get("Unknown", 0)
    return {
        "n_cells": n_cells,
        "n_unknown": n_unknown,
        "unknown_pct": round(100.0 * n_unknown / n_cells, 1) if n_cells else None,
        "n_labels": len(counts),
        "top_labels": "; ".join(f"{label} {n}" for label, n in counts.most_common(3)),
    }


def garnett_arm(arm: str, train_dir: Path, anno_dir: Path) -> dict:
    tdir = train_dir / f"GarnettClassifierTrainer_{arm}"
    adir = anno_dir / f"CellTypeAnnotation_Garnett_{arm}"
    diag_file = _first(tdir, "*.diagnostics.tsv")
    model_file = _newest(tdir, "*.classifier.RDS") or _newest(tdir, "*.classifier.RDS.diagnostics.tsv")
    c2c_file = _newest(adir, "*.cell2celltype.tsv")
    anno_stale, model_mtime, anno_mtime = _staleness(model_file, c2c_file)
    rows = _read_tsv(diag_file) if diag_file else []

    degen = [_truthy(r.get("degenerate")) for r in rows]
    lambdas = [v for v in (_num(r.get("lambda_min")) for r in rows) if v is not None]
    coefs = [v for v in (_num(r.get("max_abs_coef")) for r in rows) if v is not None]
    nonzeros = [v for v in (_int(r.get("n_nonzero")) for r in rows) if v is not None]
    root = next((r for r in rows if (r.get("node") or "").strip() == "root"), None)

    cover = _coverage(c2c_file)
    n_cells, n_unknown = cover.get("n_cells"), cover.get("n_unknown")

    if diag_file is None or not rows:
        # A header-only sidecar carries no evidence; treat it like an absent one.
        verdict = "missing"
    elif all(degen):
        verdict = "degenerate-training"
    elif any(degen):
        verdict = "partial-degenerate"
    elif anno_stale:
        # A coverage verdict from old labels would be presented as authoritative; it is not.
        verdict = "stale-annotation"
    elif c2c_file is None:
        verdict = "no-annotation"
    elif cover.get("unknown_pct") == 100.0:
        verdict = "silent-zero-coverage"
    else:
        verdict = "healthy"

    return {
        "arm": arm,
        "verdict": verdict,
        "diag_file": str(diag_file) if diag_file else None,
        "model_file": str(model_file) if model_file else None,
        "cell2celltype_file": str(c2c_file) if c2c_file else None,
        "anno_stale": anno_stale,
        "model_mtime": model_mtime,
        "anno_mtime": anno_mtime,
        "diag_nodes": len(rows),
        "n_degenerate_nodes": sum(degen),
        "degenerate_all": bool(rows) and all(degen),
        "lambda_min": min(lambdas) if lambdas else None,
        "lambda_max": max(lambdas) if lambdas else None,
        "lambda_at_ceiling": any(v >= 1e5 for v in lambdas),
        "max_abs_coef": max(coefs) if coefs else None,
        "n_nonzero": sum(nonzeros) if nonzeros else None,
        "root_n_classes": _int(root.get("n_classes")) if root else None,
        "n_cells": n_cells,
        "n_unknown": n_unknown,
        "unknown_pct": cover.get("unknown_pct"),
        "n_labels": cover.get("n_labels"),
        "top_labels": cover.get("top_labels"),
    }


def hitype_arm(arm: str, train_dir: Path, anno_dir: Path) -> dict:
    tdir = train_dir / f"HitypeWeightTrainer_{arm}"
    adir = anno_dir / f"CellTypeAnnotation_Hitype_{arm}"
    hitype_file = _newest(tdir, "*.hitype.tsv")
    c2c_file = _newest(adir, "*.cell2celltype.tsv")
    anno_stale, model_mtime, anno_mtime = _staleness(hitype_file, c2c_file)
    rows = _read_tsv(hitype_file) if hitype_file else []

    by_class: dict[str, list[float]] = {}
    for row in rows:
        weight = _num(row.get("weight"))
        by_class.setdefault(row.get("cell_type") or "", []).append(weight or 0.0)
    class_max = [max(abs(w) for w in ws) for ws in by_class.values()]
    all_zero = [c for c, ws in by_class.items() if all(w == 0.0 for w in ws)]

    cover = _coverage(c2c_file)
    inert = not rows or (bool(by_class) and len(all_zero) == len(by_class))

    return {
        "arm": arm,
        "verdict": "inert" if inert else "healthy",
        "hitype_file": str(hitype_file) if hitype_file else None,
        "cell2celltype_file": str(c2c_file) if c2c_file else None,
        "anno_stale": anno_stale,
        "model_mtime": model_mtime,
        "anno_mtime": anno_mtime,
        "n_classes": len(by_class),
        "n_rows": len(rows),
        "n_genes": len({r.get("gene") for r in rows}),
        "n_classes_all_zero": len(all_zero),
        "min_class_max_abs_weight": min(class_max) if class_max else None,
        "max_abs_weight": max(class_max) if class_max else None,
        "n_cells": cover.get("n_cells"),
        "n_unknown": cover.get("n_unknown"),
        "unknown_pct": cover.get("unknown_pct"),
        "n_labels": cover.get("n_labels"),
        "top_labels": cover.get("top_labels"),
    }


def _stale_cell(rec: dict) -> str:
    return "yes" if rec["anno_stale"] else "no"


def _garnett_row(rec: dict) -> list[str]:
    n_cells, n_unknown = rec.get("n_cells"), rec.get("n_unknown")
    labelled = f"{n_cells - n_unknown}/{n_cells}" if n_cells else "-"
    return [
        rec["arm"],
        rec["verdict"],
        _stale_cell(rec),
        _fmt(rec["diag_nodes"], "%d"),
        _fmt(rec["n_degenerate_nodes"], "%d"),
        _fmt(rec["lambda_min"], "%.3g"),
        _fmt(rec["max_abs_coef"], "%.5g"),
        _fmt(rec["n_nonzero"], "%d"),
        labelled,
        _fmt(rec["unknown_pct"], "%.1f"),
    ]


def _hitype_row(rec: dict) -> list[str]:
    return [
        rec["arm"],
        rec["verdict"],
        _stale_cell(rec),
        _fmt(rec["n_classes"], "%d"),
        _fmt(rec["n_rows"], "%d"),
        _fmt(rec["n_genes"], "%d"),
        _fmt(rec["min_class_max_abs_weight"], "%.4g"),
        _fmt(rec["max_abs_weight"], "%.4g"),
    ]


def _table(columns, records, row_fn, color: bool) -> str:
    width = len(columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * width) + "|",
    ]
    for rec in records:
        cells = row_fn(rec)
        # Table cells carry the verdict colour; the tsv/json keep the plain name.
        cells[1] = _paint(cells[1], VERDICT_COLOR.get(cells[1], "0"), color)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _missing_lines(garnett, hitype, train_dir, anno_dir) -> list[str]:
    """For every arm with an absent artifact, the path the tool looked for."""
    lines = []
    for rec in garnett:
        arm = rec["arm"]
        if rec["diag_file"] is None:
            lines.append(f"  garnett {arm} diagnostics: {train_dir / f'GarnettClassifierTrainer_{arm}' / '*.diagnostics.tsv'}")
        if rec["cell2celltype_file"] is None:
            lines.append(f"  garnett {arm} annotation:  {anno_dir / f'CellTypeAnnotation_Garnett_{arm}' / '*.cell2celltype.tsv'}")
    for rec in hitype:
        arm = rec["arm"]
        if rec["hitype_file"] is None:
            lines.append(f"  hitype {arm} weights:     {train_dir / f'HitypeWeightTrainer_{arm}' / '*.hitype.tsv'}")
        if rec["cell2celltype_file"] is None:
            lines.append(f"  hitype {arm} annotation:  {anno_dir / f'CellTypeAnnotation_Hitype_{arm}' / '*.cell2celltype.tsv'}")
    return lines


def _verdict_counts(records, verdicts) -> dict:
    counts = Counter(r["verdict"] for r in records)
    return {v: counts.get(v, 0) for v in verdicts}


def _summary_block(garnett, hitype) -> dict:
    g_counts = _verdict_counts(garnett, GARNETT_VERDICTS)
    h_counts = _verdict_counts(hitype, HITYPE_VERDICTS)
    return {
        "garnett": {
            "n_arms": len(garnett),
            "counts": g_counts,
            "silent_zero_coverage_arms": [
                r["arm"] for r in garnett if r["verdict"] == "silent-zero-coverage"
            ],
            "degenerate_training_arms": [
                r["arm"] for r in garnett if r["verdict"] == "degenerate-training"
            ],
        },
        "hitype": {
            "n_arms": len(hitype),
            "counts": h_counts,
            "inert_arms": [r["arm"] for r in hitype if r["verdict"] == "inert"],
        },
    }


def _render(name: str, train_dir: Path, anno_dir: Path, garnett, hitype, summary, color: bool) -> str:
    parts = [
        f"dataset: {name}",
        f"train dir: {train_dir.resolve()}",
        f"anno dir: {anno_dir.resolve()}",
        "",
        "## garnett",
        _table(GARNETT_COLUMNS, garnett, _garnett_row, color),
        "",
        "## hitype",
        _table(HITYPE_COLUMNS, hitype, _hitype_row, color),
        "",
    ]
    missing = _missing_lines(garnett, hitype, train_dir, anno_dir)
    parts.append("missing artifacts:" if missing else "missing artifacts: none")
    parts.extend(missing)
    parts.append("")

    g_counts, h_counts = summary["garnett"]["counts"], summary["hitype"]["counts"]
    parts.append("summary:")
    parts.append(f"  garnett arms: {summary['garnett']['n_arms']}  " + "  ".join(f"{k}={v}" for k, v in g_counts.items()))
    parts.append(f"  hitype arms: {summary['hitype']['n_arms']}  " + "  ".join(f"{k}={v}" for k, v in h_counts.items()))
    names = summary["garnett"]["silent_zero_coverage_arms"]
    parts.append(f"  silent-zero-coverage arms: {len(names)}  ({', '.join(names)})")
    names = summary["garnett"]["degenerate_training_arms"]
    parts.append(f"  degenerate-training arms: {len(names)}  ({', '.join(names)})")
    parts.append("")
    parts.append(LEGEND)
    return "\n".join(parts)


def _write_outputs(outdir: Path, name: str, payload: dict, garnett, hitype) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for suffix, columns, records, row_fn in (
        ("garnett-stability.tsv", GARNETT_COLUMNS, garnett, _garnett_row),
        ("hitype-stability.tsv", HITYPE_COLUMNS, hitype, _hitype_row),
    ):
        path = outdir / f"{name}.{suffix}"
        with path.open("w", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
            writer.writerow(columns)
            for rec in records:
                writer.writerow(row_fn(rec))
        written.append(path)

    path = outdir / f"{name}.stability.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    written.append(path)
    return written


def _resolve_dir(cwd: Path, name: str, exact_name: str, glob_pat: str, override):
    """`exact_name` for `name`, else a glob match whose dataset part relates to `name`.

    Never borrow an unrelated dataset's directory: reporting one dataset's numbers
    under another's name is the failure class this tool exists to catch.
    """
    if override:
        return Path(override)
    exact = cwd / exact_name
    if exact.is_dir():
        return exact
    hits = [p for p in sorted(cwd.glob(glob_pat)) if p.is_dir() and (name in p.name or p.name in name)]
    if len(hits) > 1:
        print(f"warning: {exact_name} not found; {len(hits)} related candidates match {glob_pat}; using {hits[0].name}", file=sys.stderr)
    return hits[0] if hits else exact


def _arms(train_dir: Path, anno_dir: Path, train_prefix: str, anno_prefix: str, only) -> list[str]:
    names = set()
    for directory, prefix in ((train_dir, train_prefix), (anno_dir, anno_prefix)):
        if directory.is_dir():
            names |= {p.name[len(prefix):] for p in directory.iterdir() if p.is_dir() and p.name.startswith(prefix)}
    if only:
        names &= set(only)
    return sorted(names)


def run_dataset(name: str, cwd: Path, args, color: bool) -> tuple[str, dict]:
    train_dir = _resolve_dir(cwd, name, f"MarkerTraining_{name}-output", "MarkerTraining_*-output", args.train_dir)
    anno_dir = _resolve_dir(cwd, name, f"CellTypeAnnotation_{name}_train-output", "CellTypeAnnotation_*_train-output", args.anno_dir)

    garnett = [
        garnett_arm(arm, train_dir, anno_dir)
        for arm in _arms(train_dir, anno_dir, "GarnettClassifierTrainer_", "CellTypeAnnotation_Garnett_", args.arms)
    ]
    hitype = [
        hitype_arm(arm, train_dir, anno_dir)
        for arm in _arms(train_dir, anno_dir, "HitypeWeightTrainer_", "CellTypeAnnotation_Hitype_", args.arms)
    ]

    if not garnett and not hitype:
        print(
            f"warning: no arms found for dataset {name}; looked in {train_dir.resolve()} and {anno_dir.resolve()}",
            file=sys.stderr,
        )

    summary = _summary_block(garnett, hitype)
    payload = {
        "dataset": name,
        "train_dir": str(train_dir.resolve()),
        "anno_dir": str(anno_dir.resolve()),
        "garnett": garnett,
        "hitype": hitype,
        "summary": summary,
    }
    text = _render(name, train_dir, anno_dir, garnett, hitype, summary, color)
    _write_outputs(Path(args.outdir), name, payload, garnett, hitype)
    return text, payload


def _datasets_in(cwd: Path) -> list[str]:
    suffix, prefix = "-output", "MarkerTraining_"
    return sorted(
        p.name[len(prefix):-len(suffix)]
        for p in cwd.glob(f"{prefix}*{suffix}")
        if p.is_dir() and len(p.name) > len(prefix) + len(suffix)
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Tabulate comparator training stability and label coverage for a dataset.",
        epilog=(
            "Exit status: 0 normally, 1 with --strict when any arm's verdict is not `healthy`."
            "\nstale-annotation: the labels came from a superseded model artifact (cell2celltype.tsv older"
            " than the trained model); the coverage columns must not be trusted until annotation is re-run"
            " for that dataset."
        ),
    )
    parser.add_argument("--ds", required=True, help="dataset name (e.g. pbmc3k), or `all` for every MarkerTraining_*-output in the CWD")
    parser.add_argument("--train-dir", help="training output dir (default MarkerTraining_<DS>-output)")
    parser.add_argument("--anno-dir", help="annotation output dir (default CellTypeAnnotation_<DS>_train-output)")
    parser.add_argument("--outdir", default="./stability-output", help="where to write the tsv/json artifacts (default: ./stability-output)")
    parser.add_argument("--arms", help="comma-separated arm names to keep (default: all)")
    parser.add_argument("--strict", action="store_true", help="exit 1 if any arm's verdict is not `healthy`")
    parser.add_argument("--no-color", action="store_true", help="disable coloured verdicts")
    args = parser.parse_args(argv)
    if args.ds == "all" and (args.train_dir or args.anno_dir):
        parser.error("--train-dir/--anno-dir apply to a single dataset, not to --ds all")
    args.arms = [a.strip() for a in args.arms.split(",") if a.strip()] if args.arms else None

    cwd = Path.cwd()
    color = not args.no_color and sys.stdout.isatty()

    names = _datasets_in(cwd) if args.ds == "all" else [args.ds]
    if not names:
        print(f"no datasets found: no MarkerTraining_*-output directory in {cwd}", file=sys.stderr)
        return 1

    sections, payloads = [], []
    for name in names:
        text, payload = run_dataset(name, cwd, args, color)
        sections.append(text)
        payloads.append(payload)
    print("\n\n".join(sections))

    bad = [
        f"{p['dataset']}/{rec['arm']} ({rec['verdict']})"
        for p in payloads
        for panel in ("garnett", "hitype")
        for rec in p[panel]
        if rec["verdict"] != "healthy"
    ]
    if args.strict and bad:
        sys.stdout.flush()  # keep the strict notice after the report when both streams are piped
        print(f"strict: {len(bad)} arm(s) not healthy: {', '.join(bad)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
