#!/usr/bin/env python3
"""Write a snpEff GFF with gene, mRNA, and CDS rows only.

snpEff names a gene from the CDS ID in this RefSeq file. Replace that ID
with the gene symbol so the ANN field reports the PomBase gene name.
"""

import sys

src, dest = sys.argv[1], sys.argv[2]
kept = []
with open(src) as handle:
    for line in handle:
        if line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 9 or parts[2] not in {"gene", "mRNA", "CDS"}:
            continue
        if parts[2] == "CDS":
            attrs = {}
            for item in parts[8].split(";"):
                if "=" in item:
                    key, value = item.split("=", 1)
                    attrs[key] = value
            symbol = attrs.get("gene") or attrs.get("locus_tag") or attrs.get("ID")
            fields = []
            replaced = False
            for item in parts[8].split(";"):
                if item.startswith("ID="):
                    fields.append("ID=" + symbol)
                    replaced = True
                else:
                    fields.append(item)
            if not replaced:
                fields.insert(0, "ID=" + symbol)
            parts[8] = ";".join(fields)
        kept.append("\t".join(parts))

with open(dest, "w") as handle:
    handle.write("##gff-version 3\n")
    handle.write("\n".join(kept))
    handle.write("\n")
