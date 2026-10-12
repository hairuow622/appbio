SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Override N, SRR, or THREADS on the make command line.
# SRR1297048 is Illumina MiSeq WGS of S. pombe strain CBS10391.
# The SRA average spot length is 498 bp, so nominal 10x of the
# 12,591,253 bp genome is:
# N = ceil(10 * 12591253 / 498) = 252837 paired-end spots.
SRR ?= SRR1297048
N ?= 252837
THREADS ?= 4
SAMPLE ?= CBS10391

GENOME_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.fna.gz
GENOME := data/genome/GCF_000002945.2_ASM294v3_genomic.fna
FAI := $(GENOME).fai
FASTQ_DIR := data/fastq/$(SRR)/N$(N)
FASTQ1 := $(FASTQ_DIR)/$(SRR)_1.fastq.gz
FASTQ2 := $(FASTQ_DIR)/$(SRR)_2.fastq.gz
FASTQ_DONE := $(FASTQ_DIR)/.download.done
INDEX_PREFIX := data/index/ASM294v3
INDEX := $(INDEX_PREFIX).bwt
RESULT_DIR := results/$(SRR)/N$(N)
BAM := $(RESULT_DIR)/$(SAMPLE).sorted.bam
BAI := $(BAM).bai
VCF := $(RESULT_DIR)/variants.vcf.gz
STATS := $(RESULT_DIR)/bcftools_stats.txt
TABLE := $(RESULT_DIR)/variants.txt
COVERAGE := $(RESULT_DIR)/coverage.txt
DEPTH := $(RESULT_DIR)/depth_summary.txt
FLAGSTAT := $(RESULT_DIR)/flagstat.txt

# S. pombe is haploid, so call with ploidy 1 rather than the diploid default.
ANN := -d 100 --annotate 'INFO/AD,FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP'
CALL := --ploidy 1 --annotate 'FORMAT/GQ'

.PHONY: all genome fastq index align vcf stats help
all: $(VCF) $(STATS) $(TABLE) $(COVERAGE) $(DEPTH) $(FLAGSTAT)
genome: $(GENOME)
fastq: $(FASTQ1) $(FASTQ2)
index: $(INDEX)
align: $(BAI)
vcf: $(VCF)
stats: $(STATS) $(TABLE) $(COVERAGE) $(DEPTH) $(FLAGSTAT)

$(GENOME):
	mkdir -p "$(dir $@)"
	curl --fail --location --retry 3 "$(GENOME_URL)" | gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(FAI): $(GENOME)
	samtools faidx "$<"

$(FASTQ_DONE):
	test "$(N)" -gt 0
	mkdir -p "$(FASTQ_DIR)"
	fastq-dump --split-files --gzip --skip-technical \
		-X "$(N)" --outdir "$(FASTQ_DIR)" "$(SRR)"
	test -s "$(FASTQ1)" && test -s "$(FASTQ2)"
	touch -r "$(FASTQ1)" "$@"

$(FASTQ1) $(FASTQ2): $(FASTQ_DONE)
	@test -s "$@"

$(INDEX): $(GENOME)
	mkdir -p "$(dir $@)"
	bwa index -p "$(INDEX_PREFIX)" "$<"
	test -s "$@"

$(BAM): $(INDEX) $(FASTQ1) $(FASTQ2)
	mkdir -p "$(RESULT_DIR)"
	bwa mem -t $(THREADS) \
		-R '@RG\tID:$(SRR)\tSM:$(SAMPLE)\tPL:ILLUMINA' \
		"$(INDEX_PREFIX)" "$(FASTQ1)" "$(FASTQ2)" \
		| samtools sort -@ $(THREADS) -o "$@.tmp" -
	mv "$@.tmp" "$@"

$(BAI): $(BAM)
	samtools index -@ $(THREADS) "$<" "$@"

$(VCF): $(FAI) $(BAI)
	mkdir -p "$(dir $@)"
	rm -f "$@.tmp.vcf.gz" "$@.tmp.vcf.gz.tbi" "$@.tmp.vcf.gz.csi"
	bcftools mpileup $(ANN) -O u -f "$(GENOME)" "$(BAM)" \
		| bcftools call $(CALL) -mv -O u \
		| bcftools norm -f "$(GENOME)" -d all -O u \
		| bcftools sort -O z -o "$@.tmp.vcf.gz"
	bcftools index -t -f "$@.tmp.vcf.gz"
	mv "$@.tmp.vcf.gz.tbi" "$@.tbi"
	mv "$@.tmp.vcf.gz" "$@"

$(STATS): $(VCF)
	bcftools stats "$<" > "$@"

$(TABLE): $(VCF)
	bcftools query \
		-f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%INFO/DP\t[%GT\t%DP\t%AD\t%ADF\t%ADR\t%GQ\t%SP]\n' \
		"$<" > "$@"

$(COVERAGE): $(BAI)
	samtools coverage "$(BAM)" > "$@"

$(FLAGSTAT): $(BAM)
	samtools flagstat -@ $(THREADS) "$<" > "$@"

$(DEPTH): $(BAI)
	samtools depth -a "$(BAM)" \
		| awk 'BEGIN { OFS = "\t" } \
			{ n++; d += $$3; if ($$3 >= 10) c++ } \
			END { \
				print "bases", n + 0; \
				print "bases_depth_ge10", c + 0; \
				print "fraction_depth_ge10", (n ? c / n : 0); \
				print "mean_depth", (n ? d / n : 0); \
			}' > "$@"

help:
	@echo "make genome              Download and decompress the reference FASTA"
	@echo "make fastq N=252837      Download N spots as paired FASTQ files"
	@echo "make index               Build the BWA genome index"
	@echo "make align               Align with bwa mem, sort, and index the BAM"
	@echo "make vcf                 Call variants and write a VCF"
	@echo "make stats               Write bcftools stats, a variant table, and coverage"
	@echo "make                     Run every step"
