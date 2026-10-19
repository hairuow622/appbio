#!/usr/bin/env python3
"""Report reference codon, alternate codon, and amino acid change for coding SNPs.

Uses the standard genetic code. The CDS is taken from the GFF and the
reference genome. A row is kept only when the CDS coordinate matches the
snpEff HGVS.c position, so the codon is the one snpEff annotated.
"""

import argparse
import gzip
import re
import subprocess

GENETIC_CODE = {
    "TTT": "Phe", "TTC": "Phe", "TTA": "Leu", "TTG": "Leu",
    "TCT": "Ser", "TCC": "Ser", "TCA": "Ser", "TCG": "Ser",
    "TAT": "Tyr", "TAC": "Tyr", "TAA": "Ter", "TAG": "Ter",
    "TGT": "Cys", "TGC": "Cys", "TGA": "Ter", "TGG": "Trp",
    "CTT": "Leu", "CTC": "Leu", "CTA": "Leu", "CTG": "Leu",
    "CCT": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro",
    "CAT": "His", "CAC": "His", "CAA": "Gln", "CAG": "Gln",
    "CGT": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg",
    "ATT": "Ile", "ATC": "Ile", "ATA": "Ile", "ATG": "Met",
    "ACT": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr",
    "AAT": "Asn", "AAC": "Asn", "AAA": "Lys", "AAG": "Lys",
    "AGT": "Ser", "AGC": "Ser", "AGA": "Arg", "AGG": "Arg",
    "GTT": "Val", "GTC": "Val", "GTA": "Val", "GTG": "Val",
    "GCT": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala",
    "GAT": "Asp", "GAC": "Asp", "GAA": "Glu", "GAG": "Glu",
    "GGT": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly",
}
COMPLEMENT = str.maketrans("ACGTacgt", "TGCAtgca")
CODING = {"missense_variant", "synonymous_variant", "stop_gained", "stop_lost"}
HGVS_C = re.compile(r"^c\.(\d+)([ACGT])>([ACGT])$")


def open_text(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def load_fasta(path):
    seqs = {}
    name = None
    chunks = []
    with open_text(path) as handle:
        for line in handle:
            if line.startswith(">"):
                if name is not None:
                    seqs[name] = "".join(chunks).upper()
                name = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line.strip())
    if name is not None:
        seqs[name] = "".join(chunks).upper()
    return seqs


def attr_map(field):
    values = {}
    for item in field.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        values[key] = value
    return values


def load_transcripts(path):
    transcripts = {}
    with open_text(path) as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9:
                continue
            chrom, _, feature, start, end, _, strand, phase, attrs = parts
            if feature not in {"mRNA", "CDS"}:
                continue
            info = attr_map(attrs)
            if feature == "mRNA":
                transcripts.setdefault(info["ID"], {
                    "chrom": chrom,
                    "strand": strand,
                    "gene": info.get("gene") or info.get("Name") or info["ID"],
                    "cds": [],
                })
            else:
                parent = info.get("Parent")
                if parent is None:
                    continue
                transcripts.setdefault(parent, {
                    "chrom": chrom,
                    "strand": strand,
                    "gene": info.get("gene") or parent,
                    "cds": [],
                })
                transcripts[parent]["cds"].append((int(start), int(end), phase))
    return {tid: tx for tid, tx in transcripts.items() if tx["cds"]}


def spliced_cds(tx, genome):
    chrom_seq = genome[tx["chrom"]]
    exons = sorted(tx["cds"], key=lambda item: item[0])
    if tx["strand"] == "-":
        exons = list(reversed(exons))
    bases = []
    index_at = {}
    for exon_i, (start, end, phase) in enumerate(exons):
        coords = range(start, end + 1) if tx["strand"] == "+" else range(end, start - 1, -1)
        if exon_i == 0 and phase not in {".", "0"}:
            coords = list(coords)[int(phase):]
        for genomic_pos in coords:
            base = chrom_seq[genomic_pos - 1]
            if tx["strand"] == "-":
                base = base.translate(COMPLEMENT)
            index_at[genomic_pos] = len(bases)
            bases.append(base)
    return "".join(bases), index_at


def parse_effects(ann):
    if not ann or ann == ".":
        return
    for item in ann.split(","):
        fields = item.split("|")
        if len(fields) < 11:
            continue
        if fields[1] not in CODING:
            continue
        match = HGVS_C.match(fields[9])
        if match is None:
            continue
        yield {
            "allele": fields[0],
            "effect": fields[1],
            "impact": fields[2],
            "gene": fields[3],
            "gene_id": fields[4],
            "transcript": fields[6],
            "hgvs_c": fields[9],
            "hgvs_p": fields[10],
            "cds_pos": int(match.group(1)),
            "hgvs_ref": match.group(2),
            "hgvs_alt": match.group(3),
            "ann": item,
        }


def query_vcf(path):
    fmt = "%CHROM\t%POS\t%REF\t%ALT\t%INFO/ANN[\t%GT:%DP:%AD]\n"
    proc = subprocess.run(
        ["bcftools", "query", "-f", fmt, path],
        check=True, text=True, capture_output=True,
    )
    for line in proc.stdout.splitlines():
        yield line.split("\t")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--genome", required=True)
    parser.add_argument("--gff", required=True)
    parser.add_argument("--vcf", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    genome = load_fasta(args.genome)
    transcripts = load_transcripts(args.gff)
    cache = {}
    rows = []
    for fields in query_vcf(args.vcf):
        chrom, pos_s, ref, alt, ann = fields[:5]
        if len(ref) != 1 or len(alt) != 1:
            continue
        if chrom == "NC_088682.1":
            continue
        pos = int(pos_s)
        genotypes = fields[5:]
        for effect in parse_effects(ann):
            if effect["allele"] != alt:
                continue
            tx = transcripts.get(effect["transcript"])
            if tx is None or tx["chrom"] != chrom:
                continue
            if effect["transcript"] not in cache:
                cache[effect["transcript"]] = spliced_cds(tx, genome)
            cds, index_at = cache[effect["transcript"]]
            cds_index = index_at.get(pos)
            if cds_index is None or cds_index + 1 != effect["cds_pos"]:
                continue
            codon_start = (cds_index // 3) * 3
            codon = cds[codon_start:codon_start + 3]
            if len(codon) != 3 or "N" in codon:
                continue
            offset = cds_index % 3
            if codon[offset] != effect["hgvs_ref"]:
                continue
            alt_codon = codon[:offset] + effect["hgvs_alt"] + codon[offset + 1:]
            aa_ref = GENETIC_CODE[codon]
            aa_alt = GENETIC_CODE[alt_codon]
            rows.append((
                chrom, pos_s, ref, alt, tx["gene"], effect["effect"],
                codon, alt_codon, f"{aa_ref}->{aa_alt}", effect["hgvs_p"],
                effect["ann"], "\t".join(genotypes),
            ))

    header = [
        "chrom", "pos", "ref", "alt", "gene", "effect",
        "ref_codon", "alt_codon", "aa_change", "hgvs_p", "ann", "genotypes",
    ]
    with open(args.out, "w") as handle:
        handle.write("\t".join(header) + "\n")
        for row in rows:
            handle.write("\t".join(str(item) for item in row) + "\n")
    print(f"wrote {len(rows)} coding SNPs to {args.out}")


if __name__ == "__main__":
    main()
