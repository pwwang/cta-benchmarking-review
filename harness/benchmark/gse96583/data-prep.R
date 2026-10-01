# --------------------------------------------------------------------------
# WHAT   Builds benchmark/gse96583/data/gse96583{,_train,_test}.qs from the two GEO label
#        tables plus the ctrl/stim matrices, with the 70/30 split (seed 8525) and a purity
#        check per resolution.
# REVIEW Section 6: THIS is the origin of the cluster-identifier aliasing defect. Lines
#        32-34 and 142-149 loop FindClusters over
#        resolutions <- c("0.2","0.3","0.5","0.8","1.0","1.2","1.5"), and FindClusters
#        leaves `seurat_clusters` as an alias for the LAST resolution run (1.5 -> 32
#        clusters), while eval.toml expands labels over RNA_snn_res.0.5 (24 clusters).
# RUN    bash data-prep.sh   (from benchmark/gse96583/)
# SOURCE harness/benchmark/gse96583/data-prep.R
# --------------------------------------------------------------------------

set.seed(8525)
library(Seurat)
library(Matrix)
library(biopipen.utils)

# Raw GEO download (not redistributed). Override with $CTA_GEO_RAW, same variable
# name and default as paths.py; the default is relative to this directory.
raw_dir <- Sys.getenv("CTA_GEO_RAW", unset = file.path("data", "geo", "gse96583", "raw"))
unpack_dir <- file.path(raw_dir, "unpack")

dataset_whole <- "data/gse96583.qs"
dataset_train <- "data/gse96583_train.qs"
dataset_test <- "data/gse96583_test.qs"

dataset_whole_md5sum <- "data/gse96583.md5sum"
dataset_train_md5sum <- "data/gse96583_train.md5sum"
dataset_test_md5sum <- "data/gse96583_test.md5sum"

# GSM id -> batch and matrix file. The barcode files are named by GSM only,
# not after the sample letter.
samples <- data.frame(
    sample = c("GSM2560245", "GSM2560246", "GSM2560247", "GSM2560248", "GSM2560249"),
    batch = c(1L, 1L, 1L, 2L, 2L),
    mat = c("GSM2560245_A.mat.gz", "GSM2560246_B.mat.gz", "GSM2560247_C.mat.gz",
            "GSM2560248_2.1.mtx.gz", "GSM2560249_2.2.mtx.gz"),
    stringsAsFactors = FALSE
)

# Batch 1 labels carry the sample letter, batch 2 the stimulation condition.
sample_of_batch <- c(A = "GSM2560245", B = "GSM2560246", C = "GSM2560247")
sample_of_stim <- c(ctrl = "GSM2560248", stim = "GSM2560249")

# Seurat names the FindClusters column after the numeric resolution, which would
# turn a requested "1.0" into "RNA_snn_res.1"; keep the labels as strings.
resolutions <- c("0.2", "0.3", "0.5", "0.8", "1.0", "1.2", "1.5")

log <- get_logger()

# The label tables' header omits a name for the barcode column: 7 names, 8
# fields. Prepend it and check the parsed width against a real data row, or a
# short name list shifts every column silently.
read_labels <- function(path) {
    lines <- strsplit(readLines(gzfile(path), n = 2), "\t")
    col_names <- c("barcode", lines[[1]])
    if (length(col_names) != length(lines[[2]])) {
        stop(sprintf("%s: %d names for %d fields", basename(path),
                     length(col_names), length(lines[[2]])))
    }
    labels <- read.delim(path, header = FALSE, skip = 1, col.names = col_names,
                         colClasses = "character")
    if (ncol(labels) != length(lines[[2]]) || !all(grepl("^[ACGT]+-[0-9]+$", labels$barcode))) {
        stop(sprintf("%s: parsed into unexpected columns: %s", basename(path),
                     paste0(colnames(labels), collapse = ", ")))
    }
    labels
}

# Barcodes repeat across samples. The label tables disambiguate the repeated
# copies by appending "1" to the suffix (-1 -> -11), which is not what the
# barcode files use; normalise back so both sides join.
norm_barcode <- function(barcodes) sub("-[0-9]+$", "-1", barcodes)

if (
    !file.exists(dataset_whole) ||
    !file.exists(dataset_whole_md5sum) ||
    tools::md5sum(dataset_whole) != readLines(dataset_whole_md5sum)
) {
    log$info("Building gse96583 dataset from ", raw_dir, "...")

    batch1_labels <- read_labels(file.path(raw_dir, "GSE96583_batch1.total.tsne.df.tsv.gz"))
    batch2_labels <- read_labels(file.path(raw_dir, "GSE96583_batch2.total.tsne.df.tsv.gz"))
    labels <- rbind(
        data.frame(
            key = paste0(sample_of_batch[batch1_labels$batch], "_", norm_barcode(batch1_labels$barcode)),
            type = batch1_labels$cell.type,
            donor = batch1_labels$ind,
            condition = NA_character_,
            sample = sample_of_batch[batch1_labels$batch],
            multiplets = batch1_labels$multiplets,
            stringsAsFactors = FALSE
        ),
        data.frame(
            key = paste0(sample_of_stim[batch2_labels$stim], "_", norm_barcode(batch2_labels$barcode)),
            type = batch2_labels$cell,
            donor = batch2_labels$ind,
            condition = batch2_labels$stim,
            sample = sample_of_stim[batch2_labels$stim],
            multiplets = batch2_labels$multiplets,
            stringsAsFactors = FALSE
        )
    )
    stopifnot(!anyDuplicated(labels$key), !anyNA(labels$sample))

    # The two batches were aligned to different gene lists -> use the intersection
    gene_lists <- lapply(1:2, function(batch) {
        read.delim(gzfile(file.path(raw_dir, sprintf("GSE96583_batch%d.genes.tsv.gz", batch))),
                   header = FALSE, col.names = c("ensembl", "symbol"))
    })
    shared_genes <- intersect(gene_lists[[1]]$ensembl, gene_lists[[2]]$ensembl)
    features <- make.unique(gene_lists[[1]]$symbol[match(shared_genes, gene_lists[[1]]$ensembl)])
    log$info("Genes: batch1 ", nrow(gene_lists[[1]]), ", batch2 ", nrow(gene_lists[[2]]),
             ", intersection ", length(shared_genes))

    objects <- list()
    for (i in seq_len(nrow(samples))) {
        sample <- samples$sample[i]
        batch <- samples$batch[i]
        counts <- as(Matrix::readMM(gzfile(file.path(unpack_dir, samples$mat[i]))), "CsparseMatrix")
        barcodes <- readLines(gzfile(file.path(unpack_dir, paste0(sample, "_barcodes.tsv.gz"))))
        stopifnot(
            ncol(counts) == length(barcodes),
            nrow(counts) == nrow(gene_lists[[batch]]),
            all(endsWith(barcodes, "-1"))
        )
        counts <- counts[match(shared_genes, gene_lists[[batch]]$ensembl), , drop = FALSE]
        # prefix with the GSM, or barcodes repeated across samples cross-link
        dimnames(counts) <- list(features, paste0(sample, "_", barcodes))
        objects[[sample]] <- CreateSeuratObject(counts = counts, project = sample)
    }
    gse96583 <- merge(objects[[1]], objects[-1])

    metadata <- labels[match(Cells(gse96583), labels$key), ]
    stopifnot(!anyNA(metadata$key))
    types <- metadata$type
    types[types == ""] <- NA_character_
    gse96583$type <- factor(types, levels = sort(unique(types[!is.na(types)])))
    gse96583$donor <- metadata$donor
    gse96583$condition <- metadata$condition
    gse96583$sample <- metadata$sample
    gse96583$doublet <- metadata$multiplets

    log$info("Dropping ", sum(is.na(gse96583$type)), " unlabelled cells and ",
             sum(!is.na(gse96583$type) & gse96583$doublet != "singlet"),
             " labelled non-singlet cells")
    keep <- !is.na(gse96583$type) & gse96583$doublet == "singlet"
    gse96583 <- subset(gse96583, cells = Cells(gse96583)[keep])

    gse96583 <- NormalizeData(gse96583, verbose = FALSE)
    gse96583 <- FindVariableFeatures(gse96583, verbose = FALSE)
    gse96583 <- ScaleData(gse96583, verbose = FALSE)
    gse96583 <- RunPCA(gse96583, verbose = FALSE)
    gse96583 <- FindNeighbors(gse96583, dims = 1:30, verbose = FALSE)
    for (resolution in resolutions) {
        before <- colnames(gse96583[[]])
        gse96583 <- FindClusters(gse96583, resolution = as.numeric(resolution), verbose = FALSE)
        # FindClusters writes the requested resolution plus a seurat_clusters alias
        found <- grep("^RNA_snn_res\\.", setdiff(colnames(gse96583[[]]), before), value = TRUE)
        stopifnot(length(found) == 1)
        gse96583[[paste0("RNA_snn_res.", resolution)]] <- gse96583[[found]][, 1]
        if (found != paste0("RNA_snn_res.", resolution)) {
            gse96583[[found]] <- NULL
        }
    }
    gse96583 <- RunUMAP(gse96583, dims = 1:30, verbose = FALSE)
    Idents(gse96583) <- "type"

    dir.create("data", showWarnings = FALSE)
    save_obj(gse96583, dataset_whole)
    writeLines(tools::md5sum(dataset_whole), dataset_whole_md5sum)
} else {
    log$info("Loading gse96583 dataset...")
    gse96583 <- load_obj(dataset_whole)
}
log$info("gse96583 dataset dimensions: ", paste0(dim(gse96583), collapse = " x "))

if (!file.exists(dataset_train) || !file.exists(dataset_train_md5sum) ||
    tools::md5sum(dataset_train) != readLines(dataset_train_md5sum) ||
    !file.exists(dataset_test) || !file.exists(dataset_test_md5sum) ||
    tools::md5sum(dataset_test) != readLines(dataset_test_md5sum)) {
    log$info("Preparing gse96583 training/testing datasets...")
    # Split the dataset for training/testing. Reseed: the build above draws from
    # the RNG, so without this the split depends on whether the object was built
    # or loaded from cache.
    set.seed(8525)
    train_cells <- sample(Cells(gse96583), size = 0.7 * ncol(gse96583))
    test_cells <- setdiff(Cells(gse96583), train_cells)
    train_obj <- subset(gse96583, cells = train_cells)
    save_obj(train_obj, dataset_train)
    writeLines(tools::md5sum(dataset_train), dataset_train_md5sum)
    log$info("gse96583 training dataset dimensions: ", paste0(dim(train_obj), collapse = " x "))

    test_obj <- subset(gse96583, cells = test_cells)
    save_obj(test_obj, dataset_test)
    writeLines(tools::md5sum(dataset_test), dataset_test_md5sum)
    log$info("gse96583 testing dataset dimensions: ", paste0(dim(test_obj), collapse = " x "))
} else {
    log$info("Training/Testing sets are already prepared...")
}

# What this dataset is for: unlike pbmc3k, whose labels are its clusters, the
# expert types here cut across the unsupervised clusters.
log$info("Cells per type: ", paste0(names(table(gse96583$type)), "=",
                                    as.integer(table(gse96583$type)), collapse = " "))
for (resolution in resolutions) {
    clusters <- gse96583[[paste0("RNA_snn_res.", resolution)]][, 1]
    counts <- table(cluster = clusters, type = gse96583$type)
    majority <- apply(counts, 1, max)
    share <- majority / rowSums(counts)
    log$info("Resolution ", resolution, ": ", nrow(counts), " clusters, cell-weighted purity ",
             sprintf("%.4f", sum(majority) / sum(counts)))
    log$info(paste0(sprintf("  cluster %s: n=%d majority=%s share=%.4f",
                            rownames(counts), rowSums(counts),
                            colnames(counts)[apply(counts, 1, which.max)], share),
                     collapse = "\n"))
}
