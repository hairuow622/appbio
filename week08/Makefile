SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# One sample per invocation. Override SRR, SAMPLE, N, or THREADS on the
# command line. The three strains below are Illumina MiSeq WGS runs from
# BioProject PRJNA248418. S. pombe is haploid and the reference is 12,591,253 bp.
# Average spot length is about 498 bp, so nominal 10x is:
# N = ceil(10 * 12591253 / 498) = 252837 paired-end spots.
#
#   make vcf SRR=SRR1297048 SAMPLE=CBS10391 N=252837
#   make vcf SRR=SRR1297050 SAMPLE=CBS2628  N=252837
#   make vcf SRR=SRR1297012 SAMPLE=CBS10460 N=252837
#   make
SRR ?= SRR1297048
N ?= 252837
THREADS ?= 4
SAMPLE ?= CBS10391

GENOME_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.fna.gz
GFF_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.gff.gz
GENOME := data/genome/GCF_000002945.2_ASM294v3_genomic.fna
FAI := $(GENOME).fai
GFF := data/gff/GCF_000002945.2_ASM294v3_genomic.gff
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

VCF1 := results/SRR1297048/N252837/variants.vcf.gz
VCF2 := results/SRR1297050/N252837/variants.vcf.gz
VCF3 := results/SRR1297012/N252837/variants.vcf.gz
MERGED := results/multisample.vcf.gz
ANNOTATED := results/multisample.ann.vcf.gz

SNPEFF_CFG := snpEff.config
SNPEFF_DIR := data/snpeff/ASM294v3
SNPEFF_SEQ := $(SNPEFF_DIR)/sequences.fa
SNPEFF_GFF := $(SNPEFF_DIR)/genes.gff
SNPEFF_DB := $(SNPEFF_DIR)/snpEffectPredictor.bin

# S. pombe is haploid, so call with ploidy 1 rather than the diploid default.
ANN := -d 100 --annotate 'INFO/AD,FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP'
CALL := --ploidy 1 --annotate 'FORMAT/GQ'

.PHONY: all samples genome gff fastq index align vcf merge annotate help

all:
	$(MAKE) samples
	$(MAKE) annotate

samples:
	$(MAKE) vcf SRR=SRR1297048 SAMPLE=CBS10391 N=252837
	$(MAKE) vcf SRR=SRR1297050 SAMPLE=CBS2628 N=252837
	$(MAKE) vcf SRR=SRR1297012 SAMPLE=CBS10460 N=252837

genome: $(GENOME)
gff: $(GFF)
fastq: $(FASTQ1) $(FASTQ2)
index: $(INDEX)
align: $(BAI)
vcf: $(VCF)
merge: $(MERGED)
annotate: $(ANNOTATED)

$(GENOME):
	mkdir -p "$(dir $@)"
	curl --fail --location --retry 3 "$(GENOME_URL)" | gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(FAI): $(GENOME)
	samtools faidx "$<"

$(GFF):
	mkdir -p "$(dir $@)"
	curl --fail --location --retry 3 "$(GFF_URL)" | gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

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

$(MERGED):
	mkdir -p "$(dir $@)"
	@test -s "$(VCF1)" || { echo "Missing $(VCF1). Run: make vcf SRR=SRR1297048 SAMPLE=CBS10391 N=252837"; exit 1; }
	@test -s "$(VCF2)" || { echo "Missing $(VCF2). Run: make vcf SRR=SRR1297050 SAMPLE=CBS2628 N=252837"; exit 1; }
	@test -s "$(VCF3)" || { echo "Missing $(VCF3). Run: make vcf SRR=SRR1297012 SAMPLE=CBS10460 N=252837"; exit 1; }
	rm -f "$@.tmp.vcf.gz" "$@.tmp.vcf.gz.tbi" "$@.tmp.vcf.gz.csi"
	bcftools merge -O z -o "$@.tmp.vcf.gz" "$(VCF1)" "$(VCF2)" "$(VCF3)"
	bcftools index -t -f "$@.tmp.vcf.gz"
	mv "$@.tmp.vcf.gz.tbi" "$@.tbi"
	mv "$@.tmp.vcf.gz" "$@"

$(SNPEFF_SEQ): $(GENOME)
	mkdir -p "$(SNPEFF_DIR)"
	awk '/^>/ { print $$1; next } { print }' "$<" > "$@.tmp"
	mv "$@.tmp" "$@"

# NCBI exon rows make snpEff use the exon ID as the gene name. Keep gene,
# mRNA, and CDS, and name each CDS by the gene symbol from the gene attribute.
$(SNPEFF_GFF): $(GFF)
	mkdir -p "$(SNPEFF_DIR)"
	python3 scripts/snpeff_gff.py "$<" "$@"

$(SNPEFF_DB): $(SNPEFF_SEQ) $(SNPEFF_GFF) $(SNPEFF_CFG)
	snpEff -Xmx4g build -c "$(SNPEFF_CFG)" -gff3 -v -noCheckCds -noCheckProtein ASM294v3

$(ANNOTATED): $(MERGED) $(SNPEFF_DB)
	mkdir -p "$(dir $@)" results
	snpEff -Xmx4g -c "$(SNPEFF_CFG)" -stats results/snpEff_summary.html \
		ASM294v3 "$(MERGED)" > "$@.tmp.vcf"
	if [ -f snpEff_genes.txt ]; then mv snpEff_genes.txt results/snpEff_summary.genes.txt; fi
	bcftools view -O z -o "$@.tmp.vcf.gz" "$@.tmp.vcf"
	bcftools index -t -f "$@.tmp.vcf.gz"
	rm -f "$@.tmp.vcf"
	mv "$@.tmp.vcf.gz.tbi" "$@.tbi"
	mv "$@.tmp.vcf.gz" "$@"

help:
	@echo "make vcf SRR=SRR1297048 SAMPLE=CBS10391 N=252837   Call variants for one sample"
	@echo "make vcf SRR=SRR1297050 SAMPLE=CBS2628  N=252837   Call variants for one sample"
	@echo "make vcf SRR=SRR1297012 SAMPLE=CBS10460 N=252837   Call variants for one sample"
	@echo "make merge                                             Merge the three VCFs"
	@echo "make annotate                                          Build the snpEff database and annotate"
	@echo "make                                                   Run every sample, then annotate"
