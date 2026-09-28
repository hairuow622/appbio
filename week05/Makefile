SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Override N, SRR, or THREADS on the make command line.
SRR ?= SRR10192871
N ?= 828372
THREADS ?= 4
SAMPLE ?= Glyc_spo_rep_1

GENOME_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.fna.gz
GENOME := data/genome/GCF_000002945.2_ASM294v3_genomic.fna
FASTQ_DIR := data/fastq/$(SRR)/N$(N)
FASTQ1 := $(FASTQ_DIR)/$(SRR)_1.fastq.gz
FASTQ2 := $(FASTQ_DIR)/$(SRR)_2.fastq.gz
FASTQ_DONE := $(FASTQ_DIR)/.download.done
INDEX_PREFIX := data/index/ASM294v3
INDEX := $(INDEX_PREFIX).1.ht2
RESULT_DIR := results/$(SRR)/N$(N)
BAM := $(RESULT_DIR)/$(SAMPLE).sorted.bam
BAI := $(BAM).bai
REPORTS := $(RESULT_DIR)/flagstat.txt $(RESULT_DIR)/idxstats.txt $(RESULT_DIR)/coverage.txt $(RESULT_DIR)/samtools_stats.txt

.PHONY: all genome fastq index align stats help
all: $(BAI) $(REPORTS)
genome: $(GENOME)
fastq: $(FASTQ1) $(FASTQ2)
index: $(INDEX)
align: $(BAI)
stats: $(REPORTS)

$(GENOME):
	mkdir -p "$(dir $@)"
	curl --fail --location --retry 3 "$(GENOME_URL)" | gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(FASTQ_DONE):
	test "$(N)" -gt 0
	mkdir -p "$(FASTQ_DIR)"
	fastq-dump --split-files --gzip --skip-technical --readids \
		-X "$(N)" --outdir "$(FASTQ_DIR)" "$(SRR)"
	test -s "$(FASTQ1)" && test -s "$(FASTQ2)"
	touch -r "$(FASTQ1)" "$@"

$(FASTQ1) $(FASTQ2): $(FASTQ_DONE)
	@test -s "$@"

$(INDEX): $(GENOME)
	mkdir -p "$(dir $@)"
	hisat2-build -p $(THREADS) "$(GENOME)" "$(INDEX_PREFIX)"
	@test -s "$@"

$(BAM): $(INDEX) $(FASTQ1) $(FASTQ2)
	mkdir -p "$(RESULT_DIR)"
	hisat2 -p $(THREADS) -x "$(INDEX_PREFIX)" \
		-1 "$(FASTQ1)" -2 "$(FASTQ2)" \
		--summary-file "$(RESULT_DIR)/hisat2_summary.txt" --new-summary \
		| samtools sort -@ $(THREADS) -o "$@.tmp" -
	mv "$@.tmp" "$@"

$(BAI): $(BAM)
	samtools index -@ $(THREADS) "$<" "$@"

$(RESULT_DIR)/flagstat.txt: $(BAM)
	samtools flagstat -@ $(THREADS) "$<" > "$@"

$(RESULT_DIR)/idxstats.txt: $(BAI)
	samtools idxstats "$(BAM)" > "$@"

$(RESULT_DIR)/coverage.txt: $(BAI)
	samtools coverage -H "$(BAM)" > "$@"

$(RESULT_DIR)/samtools_stats.txt: $(BAM)
	samtools stats -@ $(THREADS) "$<" > "$@"

help:
	@echo "make genome              Download and decompress the reference FASTA"
	@echo "make fastq N=828372      Download N spots as paired FASTQ files"
	@echo "make index               Build the HISAT2 genome index"
	@echo "make align               Align, sort, and index the BAM"
	@echo "make stats               Generate BAM statistics"
	@echo "make                     Run every step"
