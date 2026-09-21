SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Override these on the command line, for example:
# make ACCESSION=SRR10192871 N=10000 THREADS=4
ACCESSION ?= SRR10192871
N ?= 10000
THREADS ?= 4

DATA_DIR := data
METADATA_DIR := $(DATA_DIR)/metadata
RAW_DIR := $(DATA_DIR)/raw_reads/$(ACCESSION)
TRIMMED_DIR := $(DATA_DIR)/trimmed_reads/$(ACCESSION)
QC_DIR := results/qc
RAW_QC_DIR := $(QC_DIR)/raw/$(ACCESSION)
TRIMMED_QC_DIR := $(QC_DIR)/trimmed/$(ACCESSION)
FASTP_REPORT_DIR := results/fastp/$(ACCESSION)

METADATA := $(METADATA_DIR)/$(ACCESSION).tsv
DOWNLOAD_DONE := $(RAW_DIR)/.download.N$(N).done
TRIM_DONE := $(TRIMMED_DIR)/.trim.done
RAW_QC_DONE := $(RAW_QC_DIR)/.fastqc.done
TRIMMED_QC_DONE := $(TRIMMED_QC_DIR)/.fastqc.done

ENA_FIELDS := run_accession,sample_title,scientific_name,instrument_platform,instrument_model,library_layout,library_strategy,read_count,base_count
ENA_URL := https://www.ebi.ac.uk/ena/portal/api/filereport?accession=$(ACCESSION)&result=read_run&fields=$(ENA_FIELDS)&format=tsv

.PHONY: all metadata download qc trim qc-trimmed help

all: $(RAW_QC_DONE) $(TRIMMED_QC_DONE)

metadata: $(METADATA)

download: $(DOWNLOAD_DONE)

qc: $(RAW_QC_DONE)

trim: $(TRIM_DONE)

qc-trimmed: $(TRIMMED_QC_DONE)

$(METADATA): | $(METADATA_DIR)
	curl --fail --location "$(ENA_URL)" --output "$@.tmp"
	test "$$(wc -l < "$@.tmp")" -ge 2
	mv "$@.tmp" "$@"

$(DOWNLOAD_DONE): $(METADATA) | $(RAW_DIR)
	rm -f "$(RAW_DIR)"/*.fastq.gz
	rm -f "$(RAW_DIR)"/.download.N*.done
	fastq-dump --split-files --gzip --skip-technical \
		--readids -X "$(N)" \
		--outdir "$(RAW_DIR)" "$(ACCESSION)"
	sample="$$(awk -F '\t' 'NR == 2 {gsub(/\r/, "", $$2); print $$2}' "$(METADATA)")"; \
	label="$$(printf '%s' "$$sample" | tr -cs '[:alnum:]._-' '_' | sed 's/^_*//; s/_*$$//')"; \
	test -n "$$label"; \
	if [[ -f "$(RAW_DIR)/$(ACCESSION)_1.fastq.gz" ]]; then \
		mv "$(RAW_DIR)/$(ACCESSION)_1.fastq.gz" "$(RAW_DIR)/$${label}_R1.fastq.gz"; \
		mv "$(RAW_DIR)/$(ACCESSION)_2.fastq.gz" "$(RAW_DIR)/$${label}_R2.fastq.gz"; \
	elif [[ -f "$(RAW_DIR)/$(ACCESSION).fastq.gz" ]]; then \
		mv "$(RAW_DIR)/$(ACCESSION).fastq.gz" "$(RAW_DIR)/$${label}.fastq.gz"; \
	else \
		echo "No FASTQ output was produced for $(ACCESSION)" >&2; exit 1; \
	fi
	touch "$@"

$(RAW_QC_DONE): $(DOWNLOAD_DONE) | $(RAW_QC_DIR)
	test -n "$$(find "$(RAW_DIR)" -maxdepth 1 -name '*.fastq.gz' -print -quit)"
	fastqc --threads "$(THREADS)" --outdir "$(RAW_QC_DIR)" \
		"$(RAW_DIR)"/*.fastq.gz
	touch "$@"

$(TRIM_DONE): $(DOWNLOAD_DONE) | $(TRIMMED_DIR) $(FASTP_REPORT_DIR)
	rm -f "$(TRIMMED_DIR)"/*.fastq.gz
	r1="$$(find "$(RAW_DIR)" -maxdepth 1 -name '*_R1.fastq.gz' -print -quit)"; \
	r2="$$(find "$(RAW_DIR)" -maxdepth 1 -name '*_R2.fastq.gz' -print -quit)"; \
	if [[ -n "$$r1" && -n "$$r2" ]]; then \
		base="$$(basename "$$r1" _R1.fastq.gz)"; \
		fastp --thread "$(THREADS)" --in1 "$$r1" --in2 "$$r2" \
			--out1 "$(TRIMMED_DIR)/$${base}_trimmed_R1.fastq.gz" \
			--out2 "$(TRIMMED_DIR)/$${base}_trimmed_R2.fastq.gz" \
			--detect_adapter_for_pe \
			--html "$(FASTP_REPORT_DIR)/fastp.html" \
			--json "$(FASTP_REPORT_DIR)/fastp.json"; \
	else \
		r1="$$(find "$(RAW_DIR)" -maxdepth 1 -name '*.fastq.gz' -print -quit)"; \
		test -n "$$r1"; \
		base="$$(basename "$$r1" .fastq.gz)"; \
		fastp --thread "$(THREADS)" --in1 "$$r1" \
			--out1 "$(TRIMMED_DIR)/$${base}_trimmed.fastq.gz" \
			--html "$(FASTP_REPORT_DIR)/fastp.html" \
			--json "$(FASTP_REPORT_DIR)/fastp.json"; \
	fi
	touch "$@"

$(TRIMMED_QC_DONE): $(TRIM_DONE) | $(TRIMMED_QC_DIR)
	test -n "$$(find "$(TRIMMED_DIR)" -maxdepth 1 -name '*.fastq.gz' -print -quit)"
	fastqc --threads "$(THREADS)" --outdir "$(TRIMMED_QC_DIR)" \
		"$(TRIMMED_DIR)"/*.fastq.gz
	touch "$@"

$(METADATA_DIR) $(RAW_DIR) $(TRIMMED_DIR) $(RAW_QC_DIR) $(TRIMMED_QC_DIR) $(FASTP_REPORT_DIR):
	mkdir -p "$@"

help:
	@echo "make                         Run download, raw QC, trimming, and trimmed QC"
	@echo "make ACCESSION=SRR... N=...  Analyze another run/subset"
