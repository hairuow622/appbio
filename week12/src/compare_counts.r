# Compare the Salmon gene counts with the featureCounts gene counts from week 11.
#
# Prints per-sample correlations and the genes with the largest disagreement.
#
# Usage: Rscript src/compare_counts.r [gene_counts.csv] [featureCounts dir] [design.csv]

args <- commandArgs(trailingOnly = TRUE)
gene_file   <- if (length(args) >= 1) args[1] else "results/gene_counts.csv"
fc_dir      <- if (length(args) >= 2) args[2] else "../week11/counts"
design_file <- if (length(args) >= 3) args[3] else "design.csv"

design <- read.csv(design_file, stringsAsFactors = FALSE)
salmon <- read.csv(gene_file, check.names = FALSE, stringsAsFactors = FALSE)

# Column 7 of a featureCounts output file holds the counts.
read_fc <- function(sample) {
    fc <- read.delim(file.path(fc_dir, paste0(sample, ".txt")), comment.char = "#",
                     stringsAsFactors = FALSE)
    setNames(fc[[7]], fc$Geneid)
}

fc <- sapply(design$sample, read_fc)

genes <- intersect(salmon$gene, rownames(fc))
cat("Genes in Salmon matrix:", nrow(salmon), "\n")
cat("Genes in featureCounts:", nrow(fc), "\n")
cat("Genes in both:         ", length(genes), "\n\n")

s <- as.matrix(salmon[match(genes, salmon$gene), design$sample])
f <- fc[genes, design$sample]

stats <- data.frame(
    sample       = design$sample,
    salmon_total = round(colSums(s)),
    fc_total     = colSums(f),
    pearson_log  = sapply(design$sample, function(x) cor(log1p(s[, x]), log1p(f[, x]))),
    spearman     = sapply(design$sample, function(x) cor(s[, x], f[, x], method = "spearman")),
    row.names = NULL
)
stats$pearson_log <- round(stats$pearson_log, 3)
stats$spearman <- round(stats$spearman, 3)
print(stats, row.names = FALSE)

# Expressed genes ranked by the log2 ratio of the mean counts of the two methods.
name <- salmon$name[match(genes, salmon$gene)]
ms <- rowMeans(s)
mf <- rowMeans(f)
lfc <- log2((ms + 1) / (mf + 1))
keep <- (ms + mf) >= 20

diff <- data.frame(name = name, salmon_mean = round(ms, 1), fc_mean = round(mf, 1),
                   log2_ratio = round(lfc, 2))[keep, ]
diff <- diff[order(-abs(diff$log2_ratio)), ]

cat("\nGenes with salmon_mean + fc_mean >= 20:", nrow(diff), "\n")
cat("Of these, within 2-fold of each other:", sum(abs(diff$log2_ratio) <= 1), "\n")
cat("\nLargest disagreements:\n")
print(head(diff, 10), row.names = FALSE)
