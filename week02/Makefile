SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ACCESSION := GCF_000002945.2
ASSEMBLY := ASM294v3
BASE_URL := https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/$(ACCESSION)_$(ASSEMBLY)

DATA_DIR := data
FASTA_DIR := $(DATA_DIR)/fasta
GFF_DIR := $(DATA_DIR)/gff
FASTA := $(FASTA_DIR)/$(ACCESSION)_$(ASSEMBLY)_genomic.fna
GFF := $(GFF_DIR)/$(ACCESSION)_$(ASSEMBLY)_genomic.gff

.PHONY: all

all: $(FASTA) $(GFF)

$(FASTA): | $(FASTA_DIR)
	curl --fail --location "$(BASE_URL)/$(ACCESSION)_$(ASSEMBLY)_genomic.fna.gz" \
		| gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(GFF): | $(GFF_DIR)
	curl --fail --location "$(BASE_URL)/$(ACCESSION)_$(ASSEMBLY)_genomic.gff.gz" \
		| gzip -dc > "$@.tmp"
	mv "$@.tmp" "$@"

$(FASTA_DIR) $(GFF_DIR):
	mkdir -p "$@"
