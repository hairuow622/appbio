# Gene-level count matrix from the transcript-level count matrix.
#
# The count of a gene is the sum of the counts of all its transcripts.
# Run src/transcript_counts.r first.
#
# Usage: Rscript src/gene_counts.r [transcript_counts.csv] [output.csv]

args <- commandArgs(trailingOnly = TRUE)
in_file  <- if (length(args) >= 1) args[1] else "results/transcript_counts.csv"
out_file <- if (length(args) >= 2) args[2] else "results/gene_counts.csv"

tx <- read.csv(in_file, check.names = FALSE, stringsAsFactors = FALSE)

samples <- setdiff(colnames(tx), c("transcript", "gene", "name"))

# rowsum() sorts by gene id; reorder genes by their first appearance instead.
sums <- rowsum(as.matrix(tx[, samples]), group = tx$gene, reorder = FALSE)

first <- match(rownames(sums), tx$gene)

result <- data.frame(
    gene = rownames(sums),
    name = tx$name[first],
    round(sums, 3),
    check.names = FALSE,
    stringsAsFactors = FALSE
)

dir.create(dirname(out_file), showWarnings = FALSE, recursive = TRUE)
write.csv(result, out_file, row.names = FALSE, quote = FALSE)

cat("Wrote", nrow(result), "genes x", length(samples), "samples to", out_file, "\n")
