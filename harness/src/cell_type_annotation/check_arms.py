#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Arm-coverage guard. Compares the arms DECLARED by a pipeline module against the
#        arms that actually finished on disk; reports missing arms, non-zero exit codes
#        and arms that left no label file.
# REVIEW Section 6 (silent failures): a failing arm stops the remaining pipen schedule
#        while the pipeline still exits 0, so a truncated roster must never be scored
#        silently. This is the guard that detects that state.
# SOURCE harness/src/cell_type_annotation/check_arms.py
# --------------------------------------------------------------------------
"""Arm-coverage guard: did every arm DECLARED by the pipeline actually produce output?

A failing job in a multi-arm pipen pipeline stops the remaining schedule (even with
error_strategy = "ignore"), so a truncated run must never be scored silently. This
compares the arms declared by the pipeline file against the arms that finished, and
reports missing arms, non-zero exit codes, and arms with no label file.

Usage:
    uv run src/cell_type_annotation/check_arms.py --ds pbmc3k
    uv run src/cell_type_annotation/check_arms.py --ds pbmc3k --pipeline CellTypeAnnotation_pbmc3k_train
"""
import argparse
import glob
import importlib.util
import os
import sys


def declared_arms(pipeline_file):
    spec = importlib.util.spec_from_file_location("arm_module", pipeline_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from biopipen.ns.scrna import CellTypeAnnotation as Base
    prefix = "CellTypeAnnotation_"
    return sorted(
        name[len(prefix):] if name.startswith(prefix) else name
        for name, obj in vars(mod).items()
        if isinstance(obj, type) and issubclass(obj, Base) and obj is not Base
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ds", required=True, help="dataset name, e.g. pbmc3k")
    ap.add_argument("--pipeline", default=None,
                    help="pipeline name (default: CellTypeAnnotation_<ds>_test)")
    ap.add_argument("--pipeline-file", default="src/cell_type_annotation/run-test.py",
                    help="the pipeline file that declares the arms")
    args = ap.parse_args()

    pipe = args.pipeline or f"CellTypeAnnotation_{args.ds}_test"
    outdir = f"{pipe}-output"
    workdir = os.path.join(".pipen", pipe)

    if not os.path.isdir(workdir):
        print(f"FAIL  pipeline workdir not found: {workdir}", file=sys.stderr)
        return 1

    arms = declared_arms(args.pipeline_file)
    missing, bad_rc, no_labels, kinds = [], [], [], {"cell": 0, "cluster": 0}
    for arm in arms:
        d = os.path.join(outdir, f"CellTypeAnnotation_{arm}")
        rc_path = os.path.join(workdir, f"CellTypeAnnotation_{arm}", "0", "job.rc")
        rc = open(rc_path).read().strip() if os.path.exists(rc_path) else None
        cell = glob.glob(os.path.join(d, "*.cell2celltype.tsv"))
        clus = glob.glob(os.path.join(d, "*.cluster2celltype.tsv"))
        if rc is None:
            missing.append(arm)
        elif rc != "0":
            bad_rc.append((arm, rc))
        if cell:
            kinds["cell"] += 1
        elif clus:
            kinds["cluster"] += 1
        else:
            no_labels.append(arm)

    declared = len(arms)
    broken = set(missing) | {a for a, _ in bad_rc} | set(no_labels)
    ok = declared - len(broken)
    print(f"arm coverage: declared {declared} | finished with labels {ok} | "
          f"never started {len(missing)} | rc!=0 {len(bad_rc)} | no label file {len(no_labels)}")
    print(f"  label files: {kinds['cell']} cell-level, {kinds['cluster']} cluster-level")
    for name, lst in (("never started", missing), ("rc!=0", [a for a, _ in bad_rc]),
                      ("no label file", no_labels)):
        if lst:
            print(f"  {name} ({len(lst)}):")
            for a in lst[:30]:
                print(f"    {a}")
    if missing or bad_rc or no_labels:
        print("\nARM COVERAGE INCOMPLETE - do not score this run as if it were the full grid.")
        return 1
    print("\nall declared arms produced output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
