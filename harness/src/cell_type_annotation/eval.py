# --------------------------------------------------------------------------
# WHAT   THE EVALUATOR. Discovers every arm that left an artifact on disk, resolves each
#        emitted label through benchmark/<ds>/mapping.tsv (mapped / Unmapped / ABSTAIN /
#        undeclared), scores the four metric views and renders the pipen-report figures.
#        Cluster-level arms are expanded to cells by joining the arm's cluster2celltype
#        table onto the evaluation partition's `cluster` column, MATCHING CLUSTER IDS AS
#        STRINGS -- the R scoring block reads the table with colClasses = "character" and
#        expands it with
#            match(as.character(cluster), as.character(tab[["Cluster"]]))
#        A cluster the arm's table does not contain is left uncalled and counted as an
#        abstention.
# REVIEW Section 6 and Supplementary Table S3: produces eval-output/
#        (arm_metrics.tsv, per_class.tsv, resources.tsv, confusion tables) from which the
#        reported per-arm accuracies come. The string-keyed expansion is the exact
#        mechanism of the cluster-identifier aliasing defect in Section 6 / Figure 3.
# SOURCE harness/src/cell_type_annotation/eval.py
# --------------------------------------------------------------------------
"""Evaluate the cell-type annotation arms of a dataset.

Implements `docs/EVALUATION.md` §3 (label mapping), §4 (metrics) and §7 (tooling).

`make eval DS=<ds>` discovers every arm that left an artifact on disk, resolves each
label it emitted through `benchmark/<ds>/mapping.tsv` (mapped / Unmapped / ABSTAIN /
undeclared), scores the four views in §4.1, and renders the figures through the
pipen-report template.

Arms are read from disk, never declared: a re-run of `make run-train`/`run-test`
changes the numbers with no change here.
"""

import csv
import shutil
import sys
from pathlib import Path

from pipen import run
from biopipen.core.proc import Proc
from biopipen.core.config import config

OUTDIR = "./eval-output"


class Collect(Proc):
    """Discover the annotation arms of every split, their labels and their resources.

    No arm is declared in the config: each `CellTypeAnnotation_<ds>_<split>-output`
    directory is walked for `CellTypeAnnotation_<Tool>_<arm>/` jobs. Wall time and
    peak RSS come from the pipen-runinfo sidecars under `.pipen/`.
    """

    input = "indir:dir"
    output = "outfile:file:eval.json"
    lang = config.lang.python
    envs = {
        "ds": "pbmc3k",
        "splits": ["train", "test"],
        "truth": "",
        "cluster": "",
        "mapping": "",
        "baseline_mb": 0.0,
        "settings": {},
    }
    script = """
        import hashlib
        import json
        from pathlib import Path

        indir = Path({{in.indir | quote}}).resolve()
        outfile = Path({{out.outfile | quote}})

        ds = {{envs.ds | quote}}
        splits = {{envs.splits | repr}}
        truth_col = {{envs.truth | quote}}
        cluster_col = {{envs.cluster | quote}}
        mapping = {{envs.mapping | quote}}
        baseline_mb = {{envs.baseline_mb | repr}}
        settings = {{envs.settings | repr}}

        # The trainer process each tool's model comes from, under MarkerTraining_<ds>-output.
        TRAINERS = {"garnett": "GarnettClassifierTrainer", "hitype": "HitypeWeightTrainer"}

        missing = []


        def md5(path):
            return hashlib.md5(Path(path).read_bytes()).hexdigest()


        def runinfo(path):
            \"\"\"(elapsed seconds, peak MB) of a pipen-runinfo sidecar, (None, None) if absent.\"\"\"
            path = Path(path)
            if not path.is_file():
                return None, None
            secs = peak = None
            for line in path.read_text().splitlines():
                if line.startswith("Elapsed real time (s):"):
                    secs = float(line.split(":")[1])
                elif line.startswith("Maximum resident set size (kB):"):
                    peak = int(line.split(":")[1]) / 1024.0
            return secs, peak


        def sidecar(pipeline, proc):
            return runinfo(indir / ".pipen" / pipeline / proc / "0" / "job.runinfo.time")


        def phase(times):
            \"\"\"(seconds, MB) for one split; (None, None) when the arm is not in it.\"\"\"
            secs, peak = times if times else (None, None)
            return {\"s\": secs, \"mb\": peak}


        def annotation_dirs():
            \"\"\"`{split: dir}` for every CellTypeAnnotation_<ds>_<split>-output on disk.\"\"\"
            prefix, suffix = f"CellTypeAnnotation_{ds}_", "-output"
            found = {}
            for path in sorted(indir.glob(f"{prefix}*{suffix}")):
                if path.is_dir():
                    found[path.name[len(prefix):-len(suffix)]] = path
            return found


        ann_dirs = annotation_dirs()

        # Annotation wall times are collected per split for the whole panel, so every
        # row can carry `ann_<split>_s` for each split that was annotated.
        ann_times = {
            split: {
                proc.name: sidecar(f"CellTypeAnnotation_{ds}_{split}", proc.name)
                for proc in path.iterdir()
                if proc.is_dir()
            }
            for split, path in sorted(ann_dirs.items())
        }

        data = {
            "ds": ds,
            "truth_col": truth_col,
            "cluster_col": cluster_col,
            "baseline_mb": baseline_mb,
            "settings": settings,
            "settings_provenance": "declared in benchmark/%s/eval.toml" % ds,
            "ann_splits": sorted(ann_dirs),
            "splits": {},
            "stability": [],
            "missing": missing,
        }

        mapping_file = indir / mapping
        if mapping_file.is_file():
            data["mapping"] = {"path": str(mapping_file), "md5": md5(mapping_file)}
        else:
            data["mapping"] = None
            missing.append(f"mapping file: {mapping_file}")

        for split in splits:
            anno = ann_dirs.get(split)
            entry = {"truth_file": None, "truth_md5": None, "arms": []}
            data["splits"][split] = entry

            qs = indir / "benchmark" / ds / "data" / f"{ds}_{split}.qs"
            if qs.is_file():
                entry["truth_file"] = str(qs)
                entry["truth_md5"] = md5(qs)
            else:
                missing.append(f"truth file: {qs}")

            if anno is None:
                missing.append(f"annotation dir: {indir / f'CellTypeAnnotation_{ds}_{split}-output'}")
                continue

            for arm_dir in sorted(p for p in anno.iterdir() if p.is_dir()):
                if not arm_dir.name.startswith("CellTypeAnnotation_"):
                    continue
                tool, _, arm = arm_dir.name[len("CellTypeAnnotation_"):].partition("_")
                tool = tool.lower()
                labels = sorted(arm_dir.glob("*.cell2celltype.tsv"))
                cluster_labels = sorted(arm_dir.glob("*.cluster2celltype.tsv"))
                if not labels and not cluster_labels:
                    missing.append(f"labels: {arm_dir}/*.cell2celltype.tsv")

                train_s, train_mb = sidecar(f"MarkerTraining_{ds}", f"{TRAINERS.get(tool, '')}_{arm}")
                if train_s is None:
                    missing.append(f"train sidecar: {arm_dir.name} ({tool})")

                phases = {
                    name: phase(ann_times[name].get(arm_dir.name))
                    for name in ann_times
                }
                peaks = [v["mb"] for v in phases.values() if v["mb"] is not None]
                if train_mb is not None:
                    peaks.append(train_mb)

                entry["arms"].append({
                    "arm": arm,
                    "tool": tool,
                    "dir": str(arm_dir),
                    "labels": str(labels[0]) if labels else None,
                    "labels_md5": md5(labels[0]) if labels else None,
                    "cluster_labels": str(cluster_labels[0]) if cluster_labels else None,
                    "train_s": train_s,
                    "ann": phases,
                    "peak_mb": max(peaks) if peaks else None,
                })

        # The `garnett-stability` table, embedded (never recomputed) by the report.
        for path in sorted(indir.glob("stability-output/*stability.tsv")):
            if path.name.startswith(f"{ds}."):
                data["stability"].append({
                    "tool": path.name[len(ds) + 1:].split("-")[0],
                    "path": str(path),
                })

        with outfile.open("w") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
    """


class Score(Proc):
    """Resolve every emitted label through the mapping file and write the metric tables.

    §2 states: mapped / Unmapped / ABSTAIN / undeclared. ABSTAIN and `Unmapped` are
    reserved tokens declared by the mapping file, so no per-tool sentinel list lives
    here. A label that matches no row, or a row with an empty `truth`, is `undeclared`:
    it is warned about, counted, excluded from every accuracy denominator, and only
    fails the run under `--strict`.
    """

    requires = Collect
    input = "infile:file"
    output = "outdir:dir:metrics"
    lang = config.lang.rscript
    script = """
        suppressPackageStartupMessages({
            library(jsonlite)
            library(biopipen.utils)
        })

        infile <- {{in.infile | quote}}
        outdir <- {{out.outdir | quote}}
        joboutdir <- {{job.outdir | quote}}

        spec <- fromJSON(infile, simplifyVector = FALSE)

        ABSTAIN <- "ABSTAIN"
        UNMAPPED <- "Unmapped"

        ds <- spec$ds
        truth_col <- spec$truth_col
        cluster_col <- spec$cluster_col
        baseline_mb <- spec$baseline_mb
        ann_splits <- unlist(spec$ann_splits)
        mapping <- spec$mapping

        if (is.null(mapping$path)) {
            stop("no mapping file on disk: ", spec$missing)
        }

        map <- read.delim(
            mapping$path,
            colClasses = "character",
            check.names = FALSE,
            quote = "",
            comment.char = ""
        )

        ## --- §3 label mapping -------------------------------------------------

        # Exact (tool, label) beats (*, label). Empty means "no such row".
        find_row <- function(tool, label) {
            idx <- which(map$tool == tool & map$label == label)
            if (length(idx) == 0L) {
                idx <- which(map$tool == "*" & map$label == label)
            }
            if (length(idx) == 0L) 0L else idx[1]
        }

        cell <- function(row, column) {
            if (row == 0L) return("")
            value <- map[[column]][row]
            if (is.na(value)) "" else as.character(value)
        }

        # The coarse cell: a class name, the reserved `Unmapped`, or empty -- in which
        # case the coarse class is inherited from the `*` truth -> coarse rules, one
        # lookup per fine class the label legitimately covers.
        coarse_of <- function(coarse_cell, classes) {
            if (nzchar(coarse_cell)) {
                return(if (coarse_cell == UNMAPPED) character(0) else coarse_cell)
            }
            out <- character(0)
            for (cls in classes) {
                row <- find_row("*", cls)
                if (row == 0L) next
                value <- cell(row, "coarse")
                if (nzchar(value) && value != UNMAPPED) out <- c(out, value)
            }
            unique(out)
        }

        resolve <- function(tool, label) {
            row <- find_row(tool, label)
            if (row == 0L) return(list(state = "undeclared", classes = character(0), coarse = character(0)))
            truth_cell <- cell(row, "truth")
            if (!nzchar(truth_cell)) {
                return(list(state = "undeclared", classes = character(0), coarse = character(0)))
            }
            if (truth_cell == ABSTAIN) {
                return(list(state = "abstain", classes = character(0), coarse = character(0)))
            }
            if (truth_cell == UNMAPPED) {
                # A committed call with no reference counterpart: it stays out of the
                # fine view, but keeps its coarse class when the cell names one.
                return(list(state = "unmapped", classes = character(0),
                            coarse = coarse_of(cell(row, "coarse"), character(0))))
            }
            classes <- trimws(strsplit(truth_cell, ",", fixed = TRUE)[[1]])
            classes <- classes[nzchar(classes)]
            if (length(classes) == 0L) {
                # A `truth` cell of only separators declares nothing: undeclared, not a
                # mapped call with an empty class set (which would score as an NA class).
                return(list(state = "undeclared", classes = character(0), coarse = character(0)))
            }
            list(state = "mapped", classes = classes,
                 coarse = coarse_of(cell(row, "coarse"), classes))
        }

        ## --- §4.1 metric helpers ---------------------------------------------

        # Normalized mutual information, sqrt normalization (the convention used by
        # aricode/sklearn's 'geometric' variant).
        nmi <- function(a, b) {
            tab <- table(a, b)
            n <- sum(tab)
            if (n == 0) return(NA_real_)
            p <- tab / n
            px <- rowSums(p)
            py <- colSums(p)
            expected <- outer(px, py)
            keep <- p > 0
            mi <- sum(p[keep] * log(p[keep] / expected[keep]))
            hx <- -sum(px[px > 0] * log(px[px > 0]))
            hy <- -sum(py[py > 0] * log(py[py > 0]))
            if (hx <= 0 || hy <= 0) return(NA_real_)
            mi / sqrt(hx * hy)
        }

        ratio <- function(num, den) if (den > 0) num / den else NA_real_

        finite <- function(x) if (is.finite(x)) x else NA_real_

        fmt <- function(x, digits) {
            ifelse(is.na(x), "NA", sprintf(paste0("%.", digits, "f"), x))
        }

        # Confusion-derived per-class scores. A class absent from the mapped view has
        # no recall: it is dropped from the macro means rather than scored as zero.
        class_scores <- function(conf) {
            tp <- diag(conf)
            support <- rowSums(conf)
            predicted <- colSums(conf)
            precision <- ifelse(
                support > 0,
                ifelse(tp + predicted - tp > 0, tp / (tp + predicted - tp), 0),
                NA_real_
            )
            recall <- ifelse(support > 0, tp / support, NA_real_)
            f1 <- ifelse(
                is.na(precision) | is.na(recall),
                NA_real_,
                ifelse(precision + recall > 0, 2 * precision * recall / (precision + recall), 0)
            )
            data.frame(class = rownames(conf), precision = precision, recall = recall,
                       f1 = f1, support = as.integer(support), stringsAsFactors = FALSE)
        }

        # The labels a state holds, counted by name (alphabetical, so the tables are
        # byte-identical between runs).
        counts <- function(labels) {
            if (length(labels) == 0L) {
                return(data.frame(label = character(0), n_cells = integer(0),
                                  stringsAsFactors = FALSE))
            }
            out <- as.data.frame(table(label = labels), stringsAsFactors = FALSE)
            names(out) <- c("label", "n_cells")
            out
        }

        score_arm <- function(record, split, truth, cluster) {
            n <- length(truth)
            cells <- names(truth)
            labels <- record$labels

            called <- rep(NA_character_, n)
            if (!is.null(labels)) {
                emitted <- read.delim(
                    labels, colClasses = "character", check.names = FALSE,
                    quote = "", comment.char = ""
                )
                if (ncol(emitted) >= 2) {
                    idx <- match(cells, emitted[[1]])
                    called[!is.na(idx)] <- emitted[[2]][idx[!is.na(idx)]]
                } else {
                    warning("no label column in ", labels, call. = FALSE)
                }
            } else if (!is.null(record$cluster_labels)) {
                # A cluster-level tool (ScType, scCATCH, scSorter) writes one call
                # per cluster: expand it over the UNSUPERVISED cluster column of
                # the data object -- never over the truth labels.
                tab <- read.delim(
                    record$cluster_labels, colClasses = "character",
                    check.names = FALSE, quote = "", comment.char = ""
                )
                annot <- setdiff(names(tab), c("Cluster", "Size"))
                if (length(annot) >= 1L && !is.null(cluster)) {
                    called <- unname(as.character(tab[[annot[1L]]])[
                        match(as.character(cluster), as.character(tab[["Cluster"]]))
                    ])
                } else {
                    warning("unusable cluster-level table: ", record$cluster_labels,
                            call. = FALSE)
                }
            }
            # A cell the tool never wrote a row for was not called: counted as an
            # abstention. Never happens for a complete artifact; it is a loud guard.
            uncalled <- sum(is.na(called))
            if (uncalled > 0) {
                warning("no prediction for ", uncalled, " of ", n, " cells in ",
                        if (is.null(labels)) "<no labels file>" else labels,
                        " -- counted as abstained", call. = FALSE)
            }

            states <- rep("abstain", n)
            predicted <- rep(list(character(0)), n)
            coarse <- rep(list(character(0)), n)
            for (label in unique(called[!is.na(called)])) {
                resolved <- resolve(record$tool, label)
                sel <- which(!is.na(called) & called == label)
                states[sel] <- resolved$state
                for (i in sel) {
                    predicted[[i]] <- resolved$classes
                    coarse[[i]] <- resolved$coarse
                }
            }

            mapped <- states == "mapped"
            unmapped <- states == "unmapped"
            n_mapped <- sum(mapped)
            n_unmapped <- sum(unmapped)

            # A cell predicted to cover several fine classes counts as a hit when its
            # own truth is among them, and is attributed to that truth for the
            # confusion; otherwise it lands on the first class the label names. Every
            # mapped cell is therefore counted exactly once.
            attributed <- rep(NA_character_, n)
            correct <- logical(n)
            for (i in which(mapped)) {
                hit <- length(predicted[[i]]) > 0 && truth[i] %in% predicted[[i]]
                correct[i] <- hit
                attributed[i] <- if (hit) truth[i] else predicted[[i]][1]
            }

            # A class the truth never shows still gets a row and a column: as a factor
            # level it can be scored (recall NA), as an unknown level it would silently
            # drop its cells from the table and bias every other class's precision.
            levels <- sort(unique(c(truth, attributed[mapped])))
            conf <- table(
                factor(truth[mapped], levels = levels),
                factor(attributed[mapped], levels = levels)
            )
            scores <- class_scores(conf)
            scored <- !is.na(scores$f1)

            truth_coarse <- vapply(
                truth, function(cls) {
                    value <- coarse_of("", cls)
                    if (length(value)) value[1] else NA_character_
                },
                character(1)
            )
            coarse_called <- vapply(coarse, function(x) length(x) > 0, logical(1))
            # The coarse view exists to rescue cells the fine taxonomy cannot express, so it
            # covers every cell with a coarse class -- NOT only the fine-mapped ones. The old
            # `mapped &` restriction made the numerator and denominator count different cells
            # (113 correct over 118 cells, while 256 cells were coarse-scorable).
            coarse_ok <- logical(n)
            for (i in which(coarse_called & !is.na(truth_coarse))) {
                coarse_ok[i] <- truth_coarse[i] %in% coarse[[i]]
            }
            coarse_denom <- coarse_called & !is.na(truth_coarse)

            cluster_ok <- !is.na(cluster) & nzchar(cluster)
            keep <- mapped & cluster_ok
            purity <- if (sum(keep) > 0) {
                sum(vapply(
                    split(attributed[keep], cluster[keep]),
                    function(x) max(table(x)),
                    numeric(1)
                )) / sum(keep)
            } else {
                NA_real_
            }

            list(
                n_cells = n,
                n_abstain = sum(states == "abstain"),
                n_unmapped = n_unmapped,
                n_mapped = n_mapped,
                n_undeclared = sum(states == "undeclared"),
                coverage_committed = 100 * ratio(n_mapped + n_unmapped, n),
                coverage_mapped = 100 * ratio(n_mapped, n),
                acc_mapped = ratio(sum(correct), n_mapped),
                acc_mapped_conservative = ratio(sum(correct), n_mapped + n_unmapped),
                acc_all = ratio(sum(correct), n),
                coarse_acc_mapped = ratio(sum(coarse_ok), sum(coarse_denom)),
                coarse_acc_all = ratio(sum(coarse_ok), n),
                macro_f1 = if (any(scored, na.rm = TRUE)) mean(scores$f1[scored]) else NA_real_,
                weighted_f1 = if (any(scored, na.rm = TRUE)) {
                    weighted.mean(scores$f1[scored], scores$support[scored])
                } else {
                    NA_real_
                },
                balanced_acc = if (any(scored, na.rm = TRUE)) mean(scores$recall[scored]) else NA_real_,
                ari = finite(suppressWarnings(tryCatch(
                    mclust::adjustedRandIndex(truth[mapped], attributed[mapped]),
                    error = function(e) NA_real_
                ))),
                nmi = finite(nmi(truth[mapped], attributed[mapped])),
                cluster_purity = purity,
                scores = scores,
                confusion = conf,
                # §3 decision 3: the labels a tool committed to off-taxonomy are part
                # of the comparison, never a footnote -- so they are counted by name.
                unmapped = counts(called[unmapped]),
                undeclared = counts(called[states == "undeclared"])
            )
        }

        ## --- §4.1 tables ------------------------------------------------------

        num <- function(x) round(as.numeric(x), 4)

        # `NULL` (no sidecar on disk) must become an explicit NA: a NULL would be
        # dropped from the data frame and shift every later column.
        scalar <- function(x) if (is.null(x) || length(x) == 0L) NA_real_ else as.numeric(x)[[1]]

        # The .qs holds one metadata row per cell: its rownames are the barcodes the
        # label TSVs key on, so truth and clusters are aligned to those names.
        read_truth <- function(entry, split) {
            if (is.null(entry$truth_file)) {
                stop("no truth file for split ", split, ": ", spec$missing)
            }
            meta <- load_obj(entry$truth_file)[[]]
            cells <- rownames(meta)
            for (column in c(truth_col, if (nzchar(cluster_col)) cluster_col)) {
                if (!column %in% colnames(meta)) {
                    stop("column '", column, "' is not in ", entry$truth_file,
                         " -- available: ", paste(colnames(meta), collapse = ", "))
                }
            }
            truth <- setNames(as.character(meta[[truth_col]]), cells)
            if (anyNA(truth)) {
                stop(sum(is.na(truth)), " of ", length(truth), " cells in ",
                     entry$truth_file, " have no '", truth_col, "' label")
            }
            list(
                truth = truth,
                cluster = if (nzchar(cluster_col)) {
                    setNames(as.character(meta[[cluster_col]]), cells)
                }
            )
        }

        write_tsv <- function(df, path) {
            write.table(df, path, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
            path
        }

        # Zero-row frames keep the file (and its header) on disk for every split, so a
        # re-run overwrites rather than leaves a stale table behind.
        empty_calls <- function() {
            data.frame(split = character(0), tool = character(0), arm = character(0),
                       label = character(0), n_cells = integer(0), stringsAsFactors = FALSE)
        }
        bind <- function(rows) if (length(rows) == 0L) empty_calls() else do.call(rbind, rows)

        # §3: a mapping row that declares no truth class is undeclared by declaration.
        # The warning belongs to the mapping file, whoever ends up emitting the label.
        blank <- which(!nzchar(trimws(map$truth)))
        if (length(blank) > 0L) {
            warning("mapping rows declaring no truth class: ",
                    paste(unique(map$label[blank]), collapse = ", "), call. = FALSE)
        }

        resources <- list()

        for (split in names(spec$splits)) {
            entry <- spec$splits[[split]]
            cells <- read_truth(entry, split)

            metrics <- list()
            per_class <- list()
            unmapped <- list()
            undeclared <- list()

            for (record in entry$arms) {
                result <- score_arm(record, split, cells$truth, cells$cluster)

                # A label the mapping does not declare is a benchmark defect, not a
                # silently droppable cell: say so in the log, with the labels and counts,
                # so an NA row can never hide a malformed arm.
                if (!is.null(result$n_undeclared) && result$n_undeclared > 0) {
                    detail <- if (nrow(result$undeclared) > 0) {
                        paste(sprintf("%s x%d", result$undeclared$label,
                                      result$undeclared$n_cells), collapse = ", ")
                    } else {
                        "<labels not retained>"
                    }
                    cat("UNDECLARED LABELS: ", record$tool, "/", record$arm, " [", split, "]: ",
                        result$n_undeclared, " cells -- ", detail, "\n", sep = "")
                    warning("undeclared labels (no mapping row) in ", record$tool, "/",
                            record$arm, " [", split, "]: ", result$n_undeclared, " cells",
                            call. = FALSE)
                }

                # §4.1 times: the annotation phases the arm ran, plus its training arm
                # when a sidecar exists; `peak_mb_delta` subtracts the idle R/Seurat
                # baseline measured for this dataset in eval.toml.
                phase_s <- function(name) scalar(record$ann[[name]]$s)
                ann_train_s <- phase_s("train")
                ann_test_s <- phase_s("test")
                train_s <- scalar(record$train_s)
                peak_mb <- scalar(record$peak_mb)
                total_s <- sum(c(train_s, ann_train_s, ann_test_s), na.rm = TRUE)
                peak_mb_delta <- if (is.na(peak_mb)) NA_real_ else peak_mb - baseline_mb

                metrics[[length(metrics) + 1L]] <- data.frame(
                    split = split,
                    tool = record$tool,
                    arm = record$arm,
                    n_cells = result$n_cells,
                    n_abstain = result$n_abstain,
                    n_unmapped = result$n_unmapped,
                    n_mapped = result$n_mapped,
                    n_undeclared = result$n_undeclared,
                    coverage_committed = num(result$coverage_committed),
                    coverage_mapped = num(result$coverage_mapped),
                    acc_mapped = num(result$acc_mapped),
                    acc_mapped_conservative = num(result$acc_mapped_conservative),
                    acc_all = num(result$acc_all),
                    coarse_acc_mapped = num(result$coarse_acc_mapped),
                    coarse_acc_all = num(result$coarse_acc_all),
                    macro_f1 = num(result$macro_f1),
                    weighted_f1 = num(result$weighted_f1),
                    balanced_acc = num(result$balanced_acc),
                    ari = num(result$ari),
                    nmi = num(result$nmi),
                    cluster_purity = num(result$cluster_purity),
                    train_s = num(train_s),
                    ann_train_s = num(ann_train_s),
                    ann_test_s = num(ann_test_s),
                    peak_mb = num(peak_mb),
                    total_s = num(total_s),
                    peak_mb_delta = num(peak_mb_delta),
                    stringsAsFactors = FALSE
                )

                scores <- result$scores
                per_class[[length(per_class) + 1L]] <- data.frame(
                    split = split, tool = record$tool, arm = record$arm,
                    class = scores$class,
                    precision = num(scores$precision),
                    recall = num(scores$recall),
                    f1 = num(scores$f1),
                    support = scores$support,
                    stringsAsFactors = FALSE
                )

                if (nrow(result$unmapped) > 0L) {
                    unmapped[[length(unmapped) + 1L]] <- data.frame(
                        split = split, tool = record$tool, arm = record$arm,
                        result$unmapped, stringsAsFactors = FALSE
                    )
                }
                if (nrow(result$undeclared) > 0L) {
                    undeclared[[length(undeclared) + 1L]] <- data.frame(
                        split = split, tool = record$tool, arm = record$arm,
                        result$undeclared, stringsAsFactors = FALSE
                    )
                }

                confusion_dir <- file.path(outdir, paste0(ds, ".", split, ".confusion"))
                dir.create(confusion_dir, showWarnings = FALSE, recursive = TRUE)
                write_tsv(
                    data.frame(truth = rownames(result$confusion),
                               as.data.frame.matrix(result$confusion),
                               check.names = FALSE),
                    file.path(confusion_dir, paste0(record$tool, "_", record$arm, ".tsv"))
                )

                resources[[paste(record$tool, record$arm, sep = "/")]] <- data.frame(
                    tool = record$tool, arm = record$arm,
                    train_s = num(train_s), ann_train_s = num(ann_train_s),
                    ann_test_s = num(ann_test_s), total_s = num(total_s),
                    peak_mb = num(peak_mb), peak_mb_delta = num(peak_mb_delta),
                    stringsAsFactors = FALSE
                )
            }

            write_tsv(do.call(rbind, metrics),
                      file.path(outdir, paste0(ds, ".", split, ".arm_metrics.tsv")))
            write_tsv(do.call(rbind, per_class),
                      file.path(outdir, paste0(ds, ".", split, ".per_class.tsv")))
            write_tsv(bind(unmapped), file.path(outdir, paste0(ds, ".", split, ".unmapped.tsv")))

            # One undeclared file per split, next to the job -- the `Score/*.undeclared.tsv`
            # the exit code of `make eval` reads.
            write_tsv(bind(undeclared),
                      file.path(joboutdir, paste0(ds, ".", split, ".undeclared.tsv")))

            # §6: the settings header travels with every table, in the JSON.
            header <- list(
                ds = ds,
                split = split,
                n_cells = length(cells$truth),
                settings = spec$settings,
                settings_provenance = spec$settings_provenance,
                mapping = list(path = mapping$path, md5 = mapping$md5),
                truth = list(file = entry$truth_file, md5 = entry$truth_md5),
                baseline_mb = baseline_mb,
                arms = lapply(entry$arms, function(record) {
                    list(tool = record$tool, arm = record$arm,
                         labels = record$labels, labels_md5 = record$labels_md5)
                })
            )
            jsonlite::write_json(
                header, file.path(outdir, paste0(ds, ".", split, ".eval.json")),
                auto_unbox = TRUE, pretty = TRUE
            )
        }

        if (length(resources) > 0L) {
            write_tsv(do.call(rbind, resources), file.path(outdir, paste0(ds, ".resources.tsv")))
        }

        # §7: the training-stability panel is embedded, never recomputed here.
        for (stability in spec$stability) {
            file.copy(stability$path, file.path(outdir, basename(stability$path)), overwrite = TRUE)
        }
    """


class Report(Proc):
    """Plot the metric tables with plotthis and assemble the pipen-report page."""

    requires = Score
    input = "indir:dir"
    output = "outdir:dir:report"
    lang = config.lang.rscript
    script = """
        suppressPackageStartupMessages({
            library(plotthis)
            library(jsonlite)
            library(biopipen.utils)
        })

        reporter <- get_reporter()

        indir <- {{in.indir | quote}}
        outdir <- {{out.outdir | quote}}
        joboutdir <- {{job.outdir | quote}}

        tables <- list.files(indir, pattern = "\\\\.arm_metrics\\\\.tsv$", full.names = TRUE)
        if (length(tables) == 0) {
            stop("no <ds>.<split>.arm_metrics.tsv in ", indir)
        }
        metrics <- do.call(rbind, lapply(tables, function(path) {
            read.delim(path, check.names = FALSE, colClasses = "character")
        }))
        for (column in setdiff(colnames(metrics), c("arm", "tool", "split"))) {
            metrics[[column]] <- as.numeric(metrics[[column]])
        }
        metrics <- metrics[order(metrics$split, metrics$tool, metrics$arm), , drop = FALSE]

        # Dataset name from the table names, so nothing here knows which dataset it is.
        ds <- sub("[.].*$", "", basename(tables[1]))

        read_tables <- function(pattern) {
            paths <- list.files(indir, pattern = pattern, full.names = TRUE)
            if (length(paths) == 0L) return(NULL)
            do.call(rbind, lapply(paths, function(path) {
                read.delim(path, check.names = FALSE, colClasses = "character")
            }))
        }

        ggsave <- function(name, plot, width = 14, height = 8) {
            path <- file.path(outdir, paste0(name, ".png"))
            ggplot2::ggsave(path, plot, width = width, height = height, dpi = 120)
            path
        }

        # Every figure goes through here, so no plot can be drawn without reaching the
        # page, and `src` is absolute -- pipen-report copies it into REPORTS/data.
        figure <- function(name, plot, width = 14, height = 8) {
            path <- ggsave(paste(ds, name, sep = "."), plot, width, height)
            reporter$add(list(kind = "image", src = path), h1 = ds, h2 = name)
            invisible(path)
        }

        ## --- §6 settings header, leading the page -----------------------------
        header_file <- list.files(indir, pattern = "[.]eval[.]json$", full.names = TRUE)
        if (length(header_file) > 0L) {
            header <- jsonlite::fromJSON(header_file[1], simplifyVector = FALSE)
            settings <- unlist(header$settings)
            reporter$add(
                list(
                    kind = "descr",
                    markdown = TRUE,
                    content = paste(c(
                        sprintf("**dataset** `%s` · **split** `%s` · %s cells",
                                header$ds, header$split, header$n_cells),
                        sprintf("**settings** %s — %s",
                                paste(sprintf("`%s` = %s", names(settings), settings), collapse = " · "),
                                header$settings_provenance),
                        sprintf("**mapping** `%s` (md5 `%s`)", header$mapping$path, header$mapping$md5),
                        sprintf("**truth** `%s` (md5 `%s`)", header$truth$file, header$truth$md5),
                        sprintf("**idle baseline** %.1f MB, subtracted from every peak RSS",
                                header$baseline_mb)
                    ), collapse = "\n")
                ),
                h1 = ds, h2 = "Settings"
            )
        }

        ## --- 1. stacked coverage bars per arm ---------------------------------
        states <- c("mapped" = "n_mapped", "unmapped" = "n_unmapped", "abstained" = "n_abstain")
        coverage <- do.call(rbind, lapply(names(states), function(state) {
            data.frame(
                split = metrics$split, tool = metrics$tool, arm = metrics$arm,
                state = state,
                n = metrics[[states[[state]]]],
                pct = 100 * metrics[[states[[state]]]] / metrics$n_cells,
                stringsAsFactors = FALSE
            )
        }))
        coverage$state <- factor(coverage$state, levels = names(states))
        figure("coverage", BarPlot(
            coverage, x = "arm", y = "pct", fill_by = "state",
            facet_by = "split", facet_scales = "free_x", ncol = 1,
            x_text_angle = 90, xlab = "", ylab = "% of cells",
            title = "Coverage per arm: mapped / unmapped / abstained",
            legend.position = "bottom"
        ), width = 14, height = 13)

        ## --- 2. grouped accuracy bars -----------------------------------------
        views <- c("acc_mapped", "acc_mapped_conservative", "acc_all")
        accuracy <- do.call(rbind, lapply(views, function(view) {
            data.frame(
                split = metrics$split, tool = metrics$tool, arm = metrics$arm,
                view = view, value = metrics[[view]],
                # §4.1's primary number, so the coverage it was measured on rides along.
                coverage = if (view == views[1]) sprintf("cov %.1f%%", metrics$coverage_mapped) else "",
                stringsAsFactors = FALSE
            )
        }))
        accuracy$view <- factor(accuracy$view, levels = views)
        # Arms that labelled no cell have NA accuracy (0/0). plotthis cannot draw NA bars and a
        # 0% bar would be a lie, so those arms are dropped from THIS figure only: they remain in
        # the coverage figure and in the metrics table, where "labelled 0 cells" stays visible.
        accuracy <- accuracy[!is.na(accuracy$value), , drop = FALSE]
        figure("accuracy", BarPlot(
            accuracy, x = "arm", y = "value", fill_by = "view", dodge_by = "view",
            label = "coverage", facet_by = "split", facet_scales = "free_x", ncol = 1,
            x_text_angle = 90, xlab = "", ylab = "accuracy",
            title = "Accuracy per arm (labels on the mapped bars: coverage_mapped)",
            legend.position = "bottom"
        ), width = 14, height = 13)

        ## --- 3. coverage vs accuracy ------------------------------------------
        figure("coverage_vs_accuracy", ScatterPlot(
            metrics, x = "coverage_mapped", y = "acc_mapped", color_by = "tool",
            xlab = "coverage_mapped (%)", ylab = "acc_mapped",
            title = "Coverage vs accuracy, one point per arm (100%-abstained arms have no acc_mapped)"
        ), width = 12, height = 7)

        ## --- 4. per-class recall heatmap --------------------------------------
        per_class <- read_tables("[.]per_class[.]tsv$")
        if (!is.null(per_class)) {
            for (column in c("precision", "recall", "f1", "support")) {
                per_class[[column]] <- as.numeric(per_class[[column]])
            }
            per_class$arm_id <- paste(per_class$tool, per_class$arm, sep = " / ")
            # A class with no support in the split has undefined precision/recall and a class
            # never predicted has no precision; NA reaches the heatmap clustering (hclust) and
            # aborts the whole report. Drop unsupported classes, score "never predicted" as 0.
            per_class <- per_class[is.finite(per_class$support) & per_class$support > 0, , drop = FALSE]
            for (column in c("precision", "recall", "f1")) {
                per_class[[column]][!is.finite(per_class[[column]])] <- 0
            }
            # plotthis pivots the long table to wide, so an (arm, class) pair ABSENT
            # from it becomes an NA cell -- and NA reaches ComplexHeatmap's clustering
            # (hclust) and aborts the entire report. Complete the grid per split and
            # score a pair with no supporters as 0 explicitly.
            per_class <- do.call(rbind, lapply(split(per_class, per_class$split), function(part) {
                grid <- expand.grid(arm_id = unique(part$arm_id), class = unique(part$class),
                                    stringsAsFactors = FALSE)
                grid$split <- part$split[1]
                merged <- merge(grid, part, by = c("arm_id", "class", "split"), all.x = TRUE)
                for (column in c("precision", "recall", "f1", "support")) {
                    merged[[column]][!is.finite(merged[[column]])] <- 0
                }
                merged
            }))
            figure("per_class_recall", Heatmap(
                per_class, rows_by = "arm_id", columns_by = "class", values_by = "recall",
                split_by = "split", combine = TRUE, ncol = 2,
                lower_cutoff = 0, upper_cutoff = 1,
                title = "Per-class recall (mapped view; grey = class not in the split)"
            ), width = 14, height = 10)
        }

        ## --- 5. confusion heatmaps, small multiples ---------------------------
        conf_dirs <- list.dirs(indir, recursive = FALSE)
        conf_dirs <- conf_dirs[grepl("[.]confusion$", conf_dirs)]
        if (length(conf_dirs) > 0L) {
            confusion <- do.call(rbind, lapply(conf_dirs, function(dir) {
                split <- sub("^[^.]+[.]", "", sub("[.]confusion$", "", basename(dir)))
                do.call(rbind, lapply(list.files(dir, pattern = "[.]tsv$", full.names = TRUE), function(path) {
                    m <- read.delim(path, check.names = FALSE, colClasses = "character")
                    classes <- colnames(m)[-1]
                    do.call(rbind, lapply(seq_along(classes), function(i) {
                        data.frame(
                            split = split, arm = sub("[.]tsv$", "", basename(path)),
                            truth = m[[1]], predicted = classes[i],
                            n = as.numeric(m[[i + 1]]),
                            stringsAsFactors = FALSE
                        )
                    }))
                }))
            }))
            # "Selected arms" is the top few by macro_f1 within each split: a rule, not a
            # hand-picked list, so the panels follow the data on any dataset.
            selected <- do.call(rbind, lapply(split(metrics, metrics$split), function(part) {
                head(part[order(-part$macro_f1), , drop = FALSE], 3)
            }))
            confusion <- confusion[
                paste(confusion$arm) %in% paste(selected$tool, selected$arm, sep = "_"), ,
                drop = FALSE
            ]
            # An unobserved truth x predicted pair arrives as an empty cell, i.e. NA after
            # as.numeric(); NA reaches ComplexHeatmap's row clustering (hclust) and aborts
            # the whole report. A missing pair is a zero count.
            confusion$n[!is.finite(confusion$n)] <- 0
            confusion$panel <- paste(confusion$split, confusion$arm, sep = " / ")
            # and the same absent-cell problem: complete truth x predicted per panel
            confusion <- do.call(rbind, lapply(split(confusion, confusion$panel), function(part) {
                grid <- expand.grid(truth = unique(part$truth), predicted = unique(part$predicted),
                                    stringsAsFactors = FALSE)
                grid$panel <- part$panel[1]
                merged <- merge(grid, part, by = c("truth", "predicted", "panel"), all.x = TRUE)
                merged$n[!is.finite(merged$n)] <- 0
                merged
            }))
            figure("confusion", Heatmap(
                confusion, rows_by = "truth", columns_by = "predicted", values_by = "n",
                split_by = "panel", combine = TRUE, ncol = 3,
                title = "Confusion, top 3 arms per split by macro_f1 (rows truth, columns predicted)"
            ), width = 16, height = 10)
        }

        ## --- 6. resources: time by phase, plus peak-RSS delta ------------------
        resources <- read_tables("[.]resources[.]tsv$")
        if (!is.null(resources)) {
            for (column in c("train_s", "ann_train_s", "ann_test_s", "total_s", "peak_mb", "peak_mb_delta")) {
                resources[[column]] <- as.numeric(resources[[column]])
            }
            resources$arm_id <- paste(resources$tool, resources$arm, sep = " / ")
            phases <- do.call(rbind, lapply(
                c("train_s", "ann_train_s", "ann_test_s"),
                function(phase) {
                    data.frame(
                        arm_id = resources$arm_id, tool = resources$tool,
                        phase = sub("_s$", "", phase), seconds = resources[[phase]],
                        stringsAsFactors = FALSE
                    )
                }
            ))
            # Sidecars are absent for arms that never ran a phase; plotthis aborts the whole
            # report on NA, so drop non-finite values from these two figures only.
            phases <- phases[is.finite(phases$seconds), , drop = FALSE]
            resources_plot <- resources[is.finite(resources$peak_mb_delta), , drop = FALSE]
            figure("resources", patchwork::wrap_plots(
                BarPlot(
                    phases, x = "arm_id", y = "seconds", fill_by = "phase",
                    x_text_angle = 90, xlab = "", ylab = "seconds",
                    title = "Time per arm, stacked by phase",
                    legend.position = "bottom"
                ),
                BarPlot(
                    resources_plot, x = "arm_id", y = "peak_mb_delta", fill_by = "tool",
                    x_text_angle = 90, xlab = "", ylab = "MB over the idle baseline",
                    legend.position = "none", title = "Peak RSS delta"
                ),
                widths = c(3, 2)
            ), width = 16, height = 9)
        }

        ## --- 7. training stability (embedded from stability-output/) -----------
        stability_files <- list.files(indir, pattern = "-stability[.]tsv$", full.names = TRUE)
        if (length(stability_files) > 0L) {
            stability_parts <- lapply(stability_files, function(path) {
                out <- read.delim(path, check.names = FALSE, colClasses = "character")
                out$tool <- sub("-stability[.]tsv$", "", sub("^[^.]+[.]", "", basename(path)))
                out
            })
            # The comparator panel reports label coverage on the training split; the hitype panel
            # reports weight structure instead, so only the former can go into a coverage chart.
            # Chart those; if none report coverage, say so rather than silently dropping it.
            panels <- Filter(
                function(out) all(c("arm", "verdict", "labelled") %in% colnames(out)),
                stability_parts
            )
            if (length(panels) == 0L) {
                message("stability figure skipped: no panel reports arm/verdict/labelled")
            } else {
                stability <- do.call(rbind, lapply(panels, function(out) {
                    out[, c("arm", "verdict", "labelled", "tool"), drop = FALSE]
                }))
                # `labelled` is "<n>/<total>", counted on the training split.
                stability$labelled_pct <- 100 * as.numeric(sub("/.*$", "", stability$labelled)) /
                    as.numeric(sub("^.*/", "", stability$labelled))
                figure("stability", BarPlot(
                    stability, x = "arm", y = "labelled_pct", fill_by = "verdict",
                    facet_by = "tool", facet_scales = "free_x", ncol = 2,
                    x_text_angle = 90, xlab = "", ylab = "% of training cells labelled",
                    title = "Training stability: label coverage on the training split, by verdict",
                    legend.position = "bottom"
                ), width = 14, height = 8)
            }
        }

        ## --- 8. marker-source summary, macro-average over arms -----------------
        summary_rows <- do.call(rbind, lapply(split(metrics, list(metrics$split, metrics$tool)), function(part) {
            # §0.4: an arm that abstains 100% is a separate failure mode -- a mean never
            # absorbs it, so only the arms that made a mapped call contribute.
            keep <- !is.na(part$acc_mapped)
            if (!any(keep)) return(NULL)
            data.frame(
                split = part$split[1], tool = part$tool[1], arms = sum(keep),
                acc_mapped = mean(part$acc_mapped[keep]),
                macro_f1 = mean(part$macro_f1[keep]),
                stringsAsFactors = FALSE
            )
        }))
        if (!is.null(summary_rows)) {
            summary_long <- do.call(rbind, lapply(c("acc_mapped", "macro_f1"), function(metric) {
                data.frame(
                    split = summary_rows$split, tool = summary_rows$tool,
                    arms = summary_rows$arms, metric = metric,
                    value = summary_rows[[metric]], stringsAsFactors = FALSE
                )
            }))
            summary_long$n <- ifelse(
                summary_long$metric == "acc_mapped", sprintf("%d arms", summary_long$arms), ""
            )
            figure("marker_sources", BarPlot(
                summary_long, x = "tool", y = "value", fill_by = "metric", dodge_by = "metric",
                label = "n", facet_by = "split", facet_scales = "free_x", xlab = "",
                ylab = "macro-average over arms",
                title = "Marker-source summary: arms averaged equally, 100%-abstained arms excluded",
                legend.position = "bottom"
            ), width = 12, height = 7)
        }

        ## --- the numbers behind the figures ------------------------------------
        table_path <- file.path(joboutdir, "arm_metrics.tsv")
        write.table(metrics, table_path, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
        reporter$add(list(kind = "table", src = table_path), h1 = ds, h2 = "Metrics")

        reporter$save(joboutdir)
    """
    plugin_opts = {
        "report": """
            {% macro report_jobs(jobs, job_head_macro, job_report_macro) %}

            {% if len(jobs) == 1 %}

            {{  job_report_macro(jobs[0], h=1) }}

            {% else %}

            {%  for job in jobs %}
            {{      job_head_macro(job)}}
            {{      job_report_macro(job, h=2) }}
            {%  endfor %}

            {% endif %}
            {% endmacro %}

            <script>
                import { Image, DataTable, Descr, Plotly } from "$libs";
                import { Tabs, Tab, TabContent, UnorderedList, ListItem, InlineNotification } from "$ccs";
            </script>

            {%- macro report_job(job, h=1) -%}
                {{ job | render_job: h=h }}
            {%- endmacro -%}

            {%- macro head_job(job) -%}
                <h1>Evaluation</h1>
            {%- endmacro -%}

            {{ report_jobs(jobs, head_job, report_job) }}
        """
    }


if __name__ == "__main__":
    # `--strict` makes an undeclared label a non-zero exit, `--allow-undeclared` is the
    # escape hatch of §7. Both are ours, not pipen's, so neither may reach pipen.
    strict = "--strict" in sys.argv
    allow = "--allow-undeclared" in sys.argv
    for flag in ("--strict", "--allow-undeclared"):
        if flag in sys.argv:
            sys.argv.remove(flag)

    ok = run("CellTypeAnnotationEval", starts=Collect, data=["."], outdir=OUTDIR)
    if not ok:
        print("eval: the pipeline did not finish -- see the logs above", file=sys.stderr)
        sys.exit(1)

    # §7: an arm that abstains on every cell is a result, never a failure, so the only
    # thing that can fail the run is a label the mapping file does not declare -- and
    # only under `--strict`. Every run warns about it.
    # The metric tables live in pipen's workdir; mirror them beside the report so there is one
    # stable location for the paper's tooling (docs/EVALUATION.md §7).
    metrics_dir = Path(".pipen/CellTypeAnnotationEval/Score/0/output/metrics")
    if metrics_dir.is_dir():
        out = Path(OUTDIR)
        out.mkdir(parents=True, exist_ok=True)
        for item in sorted(metrics_dir.iterdir()):
            if item.is_dir():
                shutil.copytree(item, out / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, out / item.name)
        print(f"metric tables mirrored to {out}/")

    undeclared = []
    for path in sorted(Path(OUTDIR).glob("Score/*.undeclared.tsv")):
        with path.open() as fh:
            undeclared.extend(csv.DictReader(fh, delimiter="\t"))

    if undeclared:
        print(
            f"!! {len(undeclared)} undeclared label(s): emitted with no mapping row, or "
            "declared with no truth class -- excluded from every denominator:",
            file=sys.stderr,
        )
        for row in undeclared:
            print(
                f"!!   {row['label']!r}: {row['n_cells']} cell(s) "
                f"[{row['split']} / {row['tool']} / {row['arm']}]",
                file=sys.stderr,
            )
        if strict and not allow:
            sys.exit(1)
