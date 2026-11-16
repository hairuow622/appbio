# Transcript-level count matrix from Salmon quantifications.
#
# Rows are transcripts, columns are the samples listed in design.csv.
# Values are the estimated read counts (NumReads), not TPM.
# Gene ids and gene names are taken from the GTF file.
#
# Usage: Rscript src/transcript_counts.r [design.csv] [gtf] [output.csv]

suppressPackageStartupMessages(library(tximport))

args <- commandArgs(trailingOnly = TRUE)
design_file <- if (length(args) >= 1) args[1] else "design.csv"
gtf_file    <- if (length(args) >= 2) args[2] else "gtf/chr22.gtf"
out_file    <- if (length(args) >= 3) args[3] else "results/transcript_counts.csv"

# Extract the value of a GTF attribute such as gene_id "ENSG...";
gtf_attr <- function(attrs, key) {
    sub(paste0('.*', key, ' "([^"]+)".*'), "\\1", attrs)
}

# Map each transcript to its gene id and gene name.
read_tx2gene <- function(gtf_file) {
    gtf <- read.delim(gtf_file, header = FALSE, comment.char = "#",
                      quote = "", stringsAsFactors = FALSE)
    attrs <- gtf$V9[gtf$V3 == "transcript"]
    data.frame(
        transcript = gtf_attr(attrs, "transcript_id"),
        gene       = gtf_attr(attrs, "gene_id"),
        name       = gtf_attr(attrs, "gene_name"),
        stringsAsFactors = FALSE
    )
}

design <- read.csv(design_file, stringsAsFactors = FALSE)

files <- file.path("counts", design$sample, "quant.sf")
names(files) <- design$sample

missing <- files[!file.exists(files)]
if (length(missing) > 0) {
    stop("Missing quantification files: ", paste(missing, collapse = ", "))
}

txi <- tximport(files, type = "salmon", txOut = TRUE)
counts <- round(txi$counts, 3)

tx2gene <- read_tx2gene(gtf_file)
idx <- match(rownames(counts), tx2gene$transcript)

if (anyNA(idx)) {
    stop(sum(is.na(idx)), " transcripts are not in the GTF file, for example: ",
         rownames(counts)[which(is.na(idx))[1]])
}

result <- data.frame(
    transcript = rownames(counts),
    gene       = tx2gene$gene[idx],
    name       = tx2gene$name[idx],
    counts,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

dir.create(dirname(out_file), showWarnings = FALSE, recursive = TRUE)
write.csv(result, out_file, row.names = FALSE, quote = FALSE)

cat("Wrote", nrow(result), "transcripts x", ncol(counts), "samples to", out_file, "\n")
