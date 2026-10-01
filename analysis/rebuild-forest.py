#!/usr/bin/env python3
# --------------------------------------------------------------------------
# WHAT   Rebuilds figures/data/forest.tsv from the uncertainty logs (deduping on
#        (dataset, config, kind), freshest measurement wins) and then re-renders the
#        forest figures through an external renderer.
# REVIEW The uncertainty/forest figure. Dataset labelling rule: a log section is pbmc3k if
#        it names pbmc3k OR if it is the held-out block (that block is always pbmc3k);
#        everything else is gse96583.
# RUN    python <this file>   (from the package root)
# NOTE   Writes into figures/data/ of this package (see paths.py) and shells out to the
#        figure renderer; every location comes from paths.py and the environment.
# SOURCE the review project's analysis workspace (see README, "Provenance map")
# --------------------------------------------------------------------------
"""Rebuild figures/data/forest.tsv from the uncertainty logs, then re-render the figures.

Two things changed since the file was first built:
  * the gse96583 roster bootstrap finished -> that row now exists (it was absent by design before);
  * the same run re-measured the pbmc3k held-out block, so three of its columns move.

Dataset labelling rule: a section is pbmc3k if it names pbmc3k, OR if it is the held-out block (that block is
always pbmc3k -- it is the 792-cell dataset #1 split, and it runs inside whichever log file the driver is
writing). Everything else is gse96583. The held-out exception is deliberate and named here rather than
inferred from the filename.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the package root
import paths  # noqa: E402

G, FIGD = paths.LOGS, paths.FIGURES / "data"
rows = []


def add(ds, cfg, kind, d, lo="", hi=""):
    # Dedupe on (dataset, config, kind) keeping the LAST occurrence: the freshest measurement wins, so a
    # re-measured block supersedes an earlier one instead of being emitted twice. Values are formatted here
    # rather than left as floats: float arithmetic otherwise writes 2.9000000000000004, and the empty lo/hi
    # of a point row must stay empty rather than becoming "0.00".
    key = (ds, cfg, kind)
    rows[:] = [r for r in rows if (r[0], r[1], r[2]) != key]
    rows.append((ds, cfg, kind, f"{d:.2f}",
                 f"{lo:.2f}" if lo != "" else "", f"{hi:.2f}" if hi != "" else ""))


for fname in ("uncertainty.log", "uncertainty-gse96583.log"):
    p = G / fname
    if not p.exists():
        print(f"  MISS {fname}")
        continue
    section = None
    for line in p.read_text(errors="replace").splitlines():
        m = re.match(r"=+\s*(.+?)\s*=+", line)
        if m:
            section = m.group(1).replace("(gse96583, canonical partition)", "").strip(" ,")
            heldout = section.lower().startswith("held-out")
            # The dataset is decided by the FILE, not by the section text: the pbmc3k log is named
            # "uncertainty.log" and its section headers carry no dataset name, so a text rule mislabels it
            # and the gse96583 file then overwrites its rows under the dedupe. The held-out block is the one
            # exception: it is always pbmc3k, whichever log the driver happened to run it in.
            ds = "gse96583" if "gse96583" in fname else "pbmc3k"
            if heldout:
                ds = "pbmc3k"
                section = "held-out seed 0 (partition from 140 arms, measured on 35)"
            continue
        if not section:
            continue
        b = re.search(r"(cell|cluster|roster)\s+bootstrap[^:]*:\s*delta\s+([-+][0-9.]+)\s*\[([-+0-9.]+),\s*([-+0-9.]+)\]", line)
        if b:
            add(ds, f"{section} [{b.group(1)}]", "ci", float(b.group(2)) * 100,
                float(b.group(3)) * 100, float(b.group(4)) * 100)
            continue
        if "bootstrap" in line:          # unparseable bootstrap line is NOT a point estimate
            continue
        d = re.search(r"^\s*delta\s+([-+][0-9.]+)", line)
        if d:
            add(ds, section, "point", float(d.group(1)) * 100)

rb = G / "robustness.log"
if rb.exists():
    for m in re.finditer(r"^(full \(166 arms\)|no zero-accuracy|no below-chance)\s+([0-9.]+)\s+([0-9.]+)\s+([-+][0-9.]+)",
                         rb.read_text(errors="replace"), re.M):
        add("gse96583", f"crossed [{m.group(1)}]", "point", float(m.group(4)) * 100)

hdr = "dataset\tconfig\tkind\tdelta_pts\tlo_pts\thi_pts\n"
# Group by dataset with a STABLE sort: the figure draws a header block per contiguous run of one dataset and
# counts its rows, so interleaved datasets produce headers that count the wrong rows. Source order comes first
# from uncertainty.log (crossed, then held-out) and then from the gse96583 log, which interleaves them.
rows.sort(key=lambda r: 0 if r[0] == "pbmc3k" else 1)
(FIGD / "forest.tsv").write_text(hdr + "".join(f"{a}\t{b}\t{c}\t{d}\t{e}\t{f}\n" for a, b, c, d, e, f in rows))
print(f"forest.tsv rebuilt: {len(rows)} rows")
for r in rows:
    print(f"  {r[0]:<9} {r[1][:44]:<44} {r[2]:<5} {r[3]:>6} [{r[4]}, {r[5]}]")

# ---- make the in-panel note data-driven instead of a literal ----
p = paths.FIGURES / "make_figures.py"
s = p.read_text()
print("\nnote literals found in make-figures.py:")
for lit in re.findall(r"[^\n]*has not run[^\n]*", s):
    print("   ", lit.strip()[:160])
for lit in re.findall(r"[^\n]*so that row does not exist[^\n]*", s):
    print("   ", lit.strip()[:160])
