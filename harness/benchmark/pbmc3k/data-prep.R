# --------------------------------------------------------------------------
# WHAT   Builds benchmark/pbmc3k/data/pbmc3k.qs (SeuratData::pbmc3k.final), then the 70/30
#        train/test split with set.seed(8525), caching each object with its md5sum.
# REVIEW Section 6: the source of the pbmc3k truth (`seurat_annotations`) and of the
#        partition its arms must key on. Unlike the gse96583 counterpart this script does
#        not loop over resolutions, so pbmc3k never showed the aliasing defect.
# RUN    bash data-prep.sh   (from benchmark/pbmc3k/)
# SOURCE harness/benchmark/pbmc3k/data-prep.R
# --------------------------------------------------------------------------

set.seed(8525)
options(timeout = 600)
library(Seurat)
library(SeuratData)
library(biopipen.utils)

dataname <- "pbmc3k"

dataset_whole <- "data/pbmc3k.qs"
dataset_train <- "data/pbmc3k_train.qs"
dataset_test <- "data/pbmc3k_test.qs"

dataset_whole_md5sum <- "data/pbmc3k.md5sum"
dataset_train_md5sum <- "data/pbmc3k_train.md5sum"
dataset_test_md5sum <- "data/pbmc3k_test.md5sum"

log <- get_logger()

if (
    !file.exists(dataset_whole) ||
    !file.exists(dataset_whole_md5sum) ||
    tools::md5sum(dataset_whole) != readLines(dataset_whole_md5sum)
) {
    log$info("Downloading pbmc3k dataset...")

    tryCatch({
        InstallData(dataname)
    }, error = function(e) {
        # https://github.com/satijalab/seurat-data/issues/23#issuecomment-1227111059
        install.packages(
            paste0(dataname, ".SeuratData"),
            repos = "https://seurat.nygenome.org/",
            type = "source"
        )
    })
    pbmc3k <- Seurat::UpdateSeuratObject(pbmc3k.final)
    Idents(pbmc3k) <- "seurat_annotations"
    dir.create("data", showWarnings = FALSE)
    save_obj(pbmc3k, dataset_whole)
    writeLines(tools::md5sum(dataset_whole), dataset_whole_md5sum)
} else {
    log$info("Loading pbmc3k dataset...")
    pbmc3k <- load_obj(dataset_whole)
}
log$info("pbmc3k dataset dimensions: ", paste0(dim(pbmc3k), collapse = " x "))

if (!file.exists(dataset_train) || tools::md5sum(dataset_train) != readLines(dataset_train_md5sum) ||
    !file.exists(dataset_test) || tools::md5sum(dataset_test) != readLines(dataset_test_md5sum)) {
    log$info("Preparing pbmc3k training/testing datasets...")
    # Split the dataset for training/testing
    train_cells <- sample(Cells(pbmc3k), size = 0.7 * ncol(pbmc3k))
    test_cells <- setdiff(Cells(pbmc3k), train_cells)
    train_obj <- subset(pbmc3k, cells = train_cells)
    save_obj(train_obj, dataset_train)
    writeLines(tools::md5sum(dataset_train), dataset_train_md5sum)
    log$info("pbmc3k training dataset dimensions: ", paste0(dim(train_obj), collapse = " x "))

    test_obj <- subset(pbmc3k, cells = test_cells)
    save_obj(test_obj, dataset_test)
    writeLines(tools::md5sum(dataset_test), dataset_test_md5sum)
    log$info("pbmc3k testing dataset dimensions: ", paste0(dim(test_obj), collapse = " x "))
} else {
    log$info("Training/Testing sets are already prepared...")
}
