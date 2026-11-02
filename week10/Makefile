SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# One sample per invocation. design.csv lists Atf1 ChIP-seq runs from
# BioProject PRJNA1052023. The background row is one Input sample. Override
# SRR, SAMPLE, N, THREADS, or JOBS on the command line.
#
# The runs are paired-end. The largest selected run has about 4.4 million
# spots, so the default N downloads each run in full. The nuclear assembly
# (ASM294v3 without the mitochondrion NC_088682.1) is 12,571,820 bp.
#
#   make all
#   make background
#   make batch-dry
#   make batch

DESIGN ?= design.csv
SRR ?= SRR27198371
SAMPLE ?= Atf1_methanol_rep1
N ?= 10000000
THREADS ?= 4
JOBS ?= 2
GSIZE ?= 12571820
QVALUE ?= 0.01

GENOME_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.fna.gz
GENOME := data/genome/GCF_000002945.2_ASM294v3_genomic.fna
FAI := $(GENOME).fai
INDEX_PREFIX := data/index/ASM294v3
INDEX := $(INDEX_PREFIX).bwt

FASTQ_DIR := data/fastq/$(SRR)/N$(N)
FASTQ1 := $(FASTQ_DIR)/$(SRR)_1.fastq.gz
FASTQ2 := $(FASTQ_DIR)/$(SRR)_2.fastq.gz
FASTQ_DONE := $(FASTQ_DIR)/.download.done
RESULT_DIR := results/$(SRR)/N$(N)
BAM := $(RESULT_DIR)/$(SAMPLE).sorted.bam
BAI := $(BAM).bai
FLAGSTAT := $(RESULT_DIR)/flagstat.txt
PEAK_DIR := $(RESULT_DIR)/peaks
NARROWPEAK := $(PEAK_DIR)/$(SAMPLE)_peaks.narrowPeak

INPUT_SRR := $(shell awk -F, 'NR > 1 && $$4 == "background" { print $$1; exit }' "$(DESIGN)")
INPUT_SAMPLE := $(shell awk -F, 'NR > 1 && $$4 == "background" { print $$2; exit }' "$(DESIGN)")
INPUT_FASTQ_DIR := data/fastq/$(INPUT_SRR)/N$(N)
INPUT_FASTQ1 := $(INPUT_FASTQ_DIR)/$(INPUT_SRR)_1.fastq.gz
INPUT_FASTQ2 := $(INPUT_FASTQ_DIR)/$(INPUT_SRR)_2.fastq.gz
INPUT_FASTQ_DONE := $(INPUT_FASTQ_DIR)/.download.done
INPUT_RESULT := results/$(INPUT_SRR)/N$(N)
INPUT_BAM := $(INPUT_RESULT)/$(INPUT_SAMPLE).sorted.bam
INPUT_BAI := $(INPUT_BAM).bai

ROLE := $(shell awk -F, -v s="$(SAMPLE)" 'NR > 1 && $$2 == s { print $$4; exit }' "$(DESIGN)")

SUMMARY := results/summary.tsv
CONSISTENCY := results/consistency.tsv

PARALLEL = parallel --colsep , --header : --eta --lb -j $(JOBS)

ALL_TARGETS := $(BAI) $(FLAGSTAT)
ifeq ($(ROLE),chip)
ALL_TARGETS += $(NARROWPEAK)
endif

.PHONY: all prepare genome fastq index align flagstat peaks background \
	batch batch-dry summary consistency tracks check-sample help FORCE

all: check-sample $(ALL_TARGETS)

prepare: $(GENOME) $(FAI) $(INDEX)

genome: $(GENOME)
fastq: $(FASTQ1) $(FASTQ2)
index: $(INDEX)
align: $(BAI)
flagstat: $(FLAGSTAT)
summary: $(SUMMARY)
consistency: $(CONSISTENCY)

FORCE:

check-sample:
	awk -F, -v r="$(SRR)" -v s="$(SAMPLE)" ' \
		NR > 1 && $$1 == r && $$2 == s { found = 1 } \
		END { \
			if (!found) { \
				printf "design.csv has no row for SRR=%s SAMPLE=%s\n", r, s > "/dev/stderr"; \
				exit 1; \
			} \
		}' "$(DESIGN)"

ifeq ($(ROLE),chip)
peaks: $(NARROWPEAK)
else
peaks:
	@echo "$(SAMPLE) is the background sample. Run: make background" >&2
	@exit 1
endif

background:
	$(MAKE) SRR=$(INPUT_SRR) SAMPLE=$(INPUT_SAMPLE) N=$(N) THREADS=$(THREADS) all

$(GENOME):
	mkdir -p "$(dir $@)"
	curl --fail --location --retry 3 "$(GENOME_URL)" | gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(FAI): $(GENOME)
	samtools faidx "$<"

$(INDEX): $(GENOME)
	mkdir -p "$(dir $@)"
	bwa index -p "$(INDEX_PREFIX)" "$<"
	test -s "$@"

$(FASTQ_DONE):
	test "$(N)" -gt 0
	mkdir -p "$(FASTQ_DIR)"
	fastq-dump --split-files --gzip --skip-technical \
		-X "$(N)" --outdir "$(FASTQ_DIR)" "$(SRR)"
	test -s "$(FASTQ1)" && test -s "$(FASTQ2)"
	touch -r "$(FASTQ1)" "$@"

$(FASTQ1) $(FASTQ2): $(FASTQ_DONE)
	@test -s "$@"

$(BAM): $(INDEX) $(FASTQ1) $(FASTQ2)
	mkdir -p "$(RESULT_DIR)"
	bwa mem -t $(THREADS) \
		-R '@RG\tID:$(SRR)\tSM:$(SAMPLE)\tPL:ILLUMINA' \
		"$(INDEX_PREFIX)" "$(FASTQ1)" "$(FASTQ2)" \
		| samtools sort -@ $(THREADS) -o "$@.tmp" -
	mv "$@.tmp" "$@"

$(BAI): $(BAM)
	samtools index -@ $(THREADS) "$<" "$@"

$(FLAGSTAT): $(BAM)
	samtools flagstat -@ $(THREADS) "$<" > "$@"

# The background BAM is a different sample, so it needs its own download and
# alignment rules. They are omitted when this invocation already is that sample.
ifneq ($(SRR)_$(SAMPLE),$(INPUT_SRR)_$(INPUT_SAMPLE))

$(INPUT_FASTQ_DONE):
	test "$(N)" -gt 0
	mkdir -p "$(INPUT_FASTQ_DIR)"
	fastq-dump --split-files --gzip --skip-technical \
		-X "$(N)" --outdir "$(INPUT_FASTQ_DIR)" "$(INPUT_SRR)"
	test -s "$(INPUT_FASTQ1)" && test -s "$(INPUT_FASTQ2)"
	touch -r "$(INPUT_FASTQ1)" "$@"

$(INPUT_FASTQ1) $(INPUT_FASTQ2): $(INPUT_FASTQ_DONE)
	@test -s "$@"

$(INPUT_BAM): $(INDEX) $(INPUT_FASTQ1) $(INPUT_FASTQ2)
	mkdir -p "$(INPUT_RESULT)"
	bwa mem -t $(THREADS) \
		-R '@RG\tID:$(INPUT_SRR)\tSM:$(INPUT_SAMPLE)\tPL:ILLUMINA' \
		"$(INDEX_PREFIX)" "$(INPUT_FASTQ1)" "$(INPUT_FASTQ2)" \
		| samtools sort -@ $(THREADS) -o "$@.tmp" -
	mv "$@.tmp" "$@"

$(INPUT_BAI): $(INPUT_BAM)
	samtools index -@ $(THREADS) "$<" "$@"

endif

$(NARROWPEAK): $(BAI) $(INPUT_BAI)
	mkdir -p "$(PEAK_DIR)"
	macs3 callpeak \
		-t "$(BAM)" \
		-c "$(INPUT_BAM)" \
		-f BAMPE \
		-n "$(SAMPLE)" \
		-g $(GSIZE) \
		-q $(QVALUE) \
		--threads $(THREADS) \
		--outdir "$(PEAK_DIR)" \
		> "$(PEAK_DIR)/macs3.log" 2>&1 \
		|| { cat "$(PEAK_DIR)/macs3.log" >&2; exit 1; }
	test -f "$@"
	bedtools sort -i "$@" > "$@.sorted"
	mv "$@.sorted" "$@"

$(SUMMARY): $(DESIGN) FORCE
	mkdir -p "$(dir $@)"
	{ \
		printf 'sample\trun\tgroup\trole\treads\tmapped_percent\tpeaks\n'; \
		awk -F, 'NR > 1 { print $$1 "\t" $$2 "\t" $$3 "\t" $$4 }' "$(DESIGN)" \
		| while IFS=$$'\t' read -r run sample group role; do \
			dir="results/$$run/N$(N)"; \
			flag="$$dir/flagstat.txt"; \
			test -s "$$flag"; \
			reads=$$(awk 'NR == 1 { print $$1 }' "$$flag"); \
			mapped=$$(awk '/mapped \(/ && !/primary mapped/ { if (match($$0, /[0-9.]+%/)) print substr($$0, RSTART, RLENGTH) }' "$$flag"); \
			if [ "$$role" = chip ]; then \
				peak="$$dir/peaks/$${sample}_peaks.narrowPeak"; \
				test -f "$$peak"; \
				peaks=$$(wc -l < "$$peak" | awk '{ print $$1 }'); \
			else \
				peaks=NA; \
			fi; \
			printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
				"$$sample" "$$run" "$$group" "$$role" "$$reads" "$$mapped" "$$peaks"; \
		done; \
	} > "$@.tmp"
	mv "$@.tmp" "$@"

# One row per pair of ChIP replicates in the same group.
$(CONSISTENCY): $(DESIGN) FORCE
	mkdir -p "$(dir $@)"
	{ \
		printf 'group\tsample1\tsample2\tpeaks1\tpeaks2\toverlap1\toverlap2\tonly1\tonly2\tintersection_bp\tunion_bp\tjaccard\n'; \
		awk -F, 'NR > 1 && $$4 == "chip" { print $$3, $$1, $$2 }' "$(DESIGN)" \
		| awk ' \
			{ g[NR] = $$1; r[NR] = $$2; s[NR] = $$3; n = NR } \
			END { \
				for (i = 1; i <= n; i++) \
					for (j = i + 1; j <= n; j++) \
						if (g[i] == g[j]) \
							print g[i], r[i], s[i], r[j], s[j]; \
			}' \
		| while read -r group run1 sample1 run2 sample2; do \
			a="results/$$run1/N$(N)/peaks/$${sample1}_peaks.narrowPeak"; \
			b="results/$$run2/N$(N)/peaks/$${sample2}_peaks.narrowPeak"; \
			test -f "$$a"; \
			test -f "$$b"; \
			peaks1=$$(wc -l < "$$a" | awk '{ print $$1 }'); \
			peaks2=$$(wc -l < "$$b" | awk '{ print $$1 }'); \
			overlap1=$$(bedtools intersect -u -a "$$a" -b "$$b" | wc -l | awk '{ print $$1 }'); \
			overlap2=$$(bedtools intersect -u -a "$$b" -b "$$a" | wc -l | awk '{ print $$1 }'); \
			only1=$$(bedtools intersect -v -a "$$a" -b "$$b" | wc -l | awk '{ print $$1 }'); \
			only2=$$(bedtools intersect -v -a "$$b" -b "$$a" | wc -l | awk '{ print $$1 }'); \
			read -r ibp ubp jaccard _ < <(bedtools jaccard -a "$$a" -b "$$b" | awk 'NR == 2'); \
			printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
				"$$group" "$$sample1" "$$sample2" "$$peaks1" "$$peaks2" \
				"$$overlap1" "$$overlap2" "$$only1" "$$only2" "$$ibp" "$$ubp" "$$jaccard"; \
		done; \
	} > "$@.tmp"
	mv "$@.tmp" "$@"

# Genome download and the BWA index run once. The Input BAM is built next,
# then each ChIP row is aligned and used to call peaks against that Input.
batch: prepare
	$(MAKE) N=$(N) THREADS=$(THREADS) background
	mkdir -p results
	rm -f results/parallel.log
	{ printf 'run,sample,group,role\n'; awk -F, 'NR > 1 && $$4 == "chip"' "$(DESIGN)"; } \
		| $(PARALLEL) --joblog results/parallel.log \
			$(MAKE) SRR={run} SAMPLE={sample} N=$(N) THREADS=$(THREADS) all
	$(MAKE) N=$(N) summary consistency

batch-dry:
	@echo "$(MAKE) SRR=$(INPUT_SRR) SAMPLE=$(INPUT_SAMPLE) N=$(N) THREADS=$(THREADS) all"
	{ printf 'run,sample,group,role\n'; awk -F, 'NR > 1 && $$4 == "chip"' "$(DESIGN)"; } \
		| $(PARALLEL) --dry-run \
			$(MAKE) SRR={run} SAMPLE={sample} N=$(N) THREADS=$(THREADS) all

# Short names for igv_batch.txt. IGV draws coverage from the BAM.
tracks:
	mkdir -p tracks
	rm -f tracks/*.bam tracks/*.bam.bai tracks/*.narrowPeak tracks/*.broadPeak \
		tracks/*.bedGraph tracks/*.cpm.bedGraph
	awk -F, 'NR > 1 { print $$1, $$2, $$4 }' "$(DESIGN)" \
	| while read -r run sample role; do \
		ln -sfn "../results/$$run/N$(N)/$$sample.sorted.bam" "tracks/$$sample.bam"; \
		ln -sfn "../results/$$run/N$(N)/$$sample.sorted.bam.bai" "tracks/$$sample.bam.bai"; \
		if [ "$$role" = chip ]; then \
			ln -sfn "../results/$$run/N$(N)/peaks/$${sample}_peaks.narrowPeak" "tracks/$$sample.narrowPeak"; \
		fi; \
	done

help:
	@echo "make all                                      Align $(SAMPLE) and call peaks"
	@echo "make background                               Align the Input sample"
	@echo "make peaks SRR=SRR27198368 SAMPLE=Atf1_NSF_rep1"
	@echo "make batch-dry                                Print the batch commands"
	@echo "make batch                                    Run design.csv, then summarize peaks"
	@echo "make summary                                  Write $(SUMMARY)"
	@echo "make consistency                              Write $(CONSISTENCY)"
	@echo "make tracks                                   Links for igv_batch.txt"
