SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# One sample per invocation. design.csv lists ten Illumina MiSeq WGS runs
# from BioProject PRJNA248418. Override SRR, SAMPLE, N, THREADS, or JOBS
# on the command line.
#
# S. pombe is haploid. The ASM294v3 reference is 12,591,253 bp and the SRA
# average spot length for these runs is about 498 bp, so nominal 10x is:
# N = ceil(10 * 12591253 / 498) = 252837 paired-end spots.
#
#   make all
#   make batch-dry
#   make batch

DESIGN ?= design.csv
SRR ?= SRR1297048
SAMPLE ?= CBS10391
N ?= 252837
THREADS ?= 3
JOBS ?= 3

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
MERGED := results/multisample.vcf.gz
VCF_LIST := results/vcf_list.txt
SUMMARY := results/summary.tsv

# Reads the design file. Build the reference once, then call variants.
PARALLEL = parallel --colsep , --header : --eta --lb -j $(JOBS)

# S. pombe is haploid, so call with ploidy 1 rather than the diploid default.
ANN := -d 100 --annotate 'INFO/AD,FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP'
CALL := --ploidy 1 --annotate 'FORMAT/GQ'

.PHONY: all prepare genome fastq index align vcf stats batch batch-dry merge summary help

all: $(VCF) $(STATS) $(TABLE) $(COVERAGE) $(DEPTH) $(FLAGSTAT)

prepare: $(GENOME) $(FAI) $(INDEX)

genome: $(GENOME)
fastq: $(FASTQ1) $(FASTQ2)
index: $(INDEX)
align: $(BAI)
vcf: $(VCF)
stats: $(STATS) $(TABLE) $(COVERAGE) $(DEPTH) $(FLAGSTAT)
summary: $(SUMMARY)

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

# Merging is cheap and must follow the VCFs just produced, so this target
# always rebuilds instead of trusting an older timestamp.
$(MERGED):
	$(MAKE) merge

merge:
	mkdir -p "$(dir $(MERGED))"
	awk -F, 'NR > 1 { printf "results/%s/N$(N)/variants.vcf.gz\n", $$1 }' "$(DESIGN)" > "$(VCF_LIST).tmp"
	mv "$(VCF_LIST).tmp" "$(VCF_LIST)"
	while IFS= read -r f; do \
		test -s "$$f" || { echo "Missing $$f"; exit 1; }; \
	done < "$(VCF_LIST)"
	rm -f "$(MERGED).tmp.vcf.gz" "$(MERGED).tmp.vcf.gz.tbi" "$(MERGED).tmp.vcf.gz.csi"
	bcftools merge --threads $(THREADS) -O z -o "$(MERGED).tmp.vcf.gz" -l "$(VCF_LIST)"
	bcftools index -t -f "$(MERGED).tmp.vcf.gz"
	mv "$(MERGED).tmp.vcf.gz.tbi" "$(MERGED).tbi"
	mv "$(MERGED).tmp.vcf.gz" "$(MERGED)"

$(SUMMARY): $(MERGED) $(DESIGN)
	mkdir -p "$(dir $@)"
	{ \
		printf 'Sample\tRun\tAlias\tRecords\tSNPs\tIndels\tMeanDepth\tNuclearMeanDepth\tMappedPercent\n'; \
		awk -F, 'NR > 1 { print $$1 "\t" $$2 "\t" $$3 }' "$(DESIGN)" \
		| while IFS=$$'\t' read -r run sample alias; do \
			dir="results/$$run/N$(N)"; \
			stats="$$dir/bcftools_stats.txt"; \
			depth="$$dir/depth_summary.txt"; \
			cov="$$dir/coverage.txt"; \
			flag="$$dir/flagstat.txt"; \
			records=$$(awk -F'\t' '$$1=="SN" && $$3=="number of records:" { print $$4 }' "$$stats"); \
			snps=$$(awk -F'\t' '$$1=="SN" && $$3=="number of SNPs:" { print $$4 }' "$$stats"); \
			indels=$$(awk -F'\t' '$$1=="SN" && $$3=="number of indels:" { print $$4 }' "$$stats"); \
			mean=$$(awk '$$1=="mean_depth" { print $$2 }' "$$depth"); \
			nuclear=$$(awk '$$1!="NC_088682.1" && $$1!~/^#/ { w += $$3; d += $$7 * $$3 } END { if (w) printf "%.5f", d / w }' "$$cov"); \
			mapped=$$(awk '/mapped \(/ && !/primary mapped/ { if (match($$0, /[0-9.]+%/)) print substr($$0, RSTART, RLENGTH) }' "$$flag"); \
			printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
				"$$sample" "$$run" "$$alias" "$$records" "$$snps" "$$indels" "$$mean" "$$nuclear" "$$mapped"; \
		done; \
	} > "$@.tmp"
	mv "$@.tmp" "$@"

# Genome download and the BWA index run once. Parallel jobs then call
# variants for every row of the design file and the VCFs are merged.
batch: prepare
	mkdir -p results
	rm -f results/parallel.log
	cat "$(DESIGN)" | $(PARALLEL) --joblog results/parallel.log \
		$(MAKE) SRR={Run} SAMPLE={Sample} N=$(N) THREADS=$(THREADS) all
	$(MAKE) N=$(N) merge
	$(MAKE) N=$(N) summary

batch-dry:
	cat "$(DESIGN)" | $(PARALLEL) --dry-run \
		$(MAKE) SRR={Run} SAMPLE={Sample} N=$(N) THREADS=$(THREADS) all

help:
	@echo "make all                                      Call variants for $(SAMPLE) ($(SRR))"
	@echo "make all SRR=SRR1297050 SAMPLE=CBS2628        Call variants for one other sample"
	@echo "make batch-dry                                Print the ten batch commands"
	@echo "make batch                                    Run design.csv, then merge the VCFs"
	@echo "make merge                                    Merge VCFs listed in $(VCF_LIST)"
	@echo "make summary                                  Write $(SUMMARY)"
