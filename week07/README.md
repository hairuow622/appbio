# Week 07: Call variants

For this assignment I called variants for *Schizosaccharomyces pombe* strain CBS10391, using the ASM294v3 reference genome (GCF_000002945.2), which comes from the lab strain 972h-.

I originally reuse the run from Week 05 (SRR10192871). However, that sample is the same strain as the reference genome, so it contains almost no real variants. Thus, for this assignment I switched to SRR1297048, which is a different strain. It is Illumina MiSeq whole-genome sequencing data.

Since this is whole-genome sequencing, I used `bwa mem` for the alignment. *S. pombe* is haploid, so I also set `--ploidy 1` in `bcftools call`.

## 1. Running the Makefile

You need make, curl, the SRA Toolkit, BWA, samtools, and bcftools installed. The first run downloads the genome and reads, so it needs internet. From the `week07/` folder:

```bash
make THREADS=4
```

To get about 10× coverage, I calculated the number of read pairs from the genome size (~12.6 Mb) and the average spot length on SRA (498 bp, i.e. 2 × 250 bp):

N = 10 × 12,591,253 / 498 ≈ 252,837

This is the default `N` in the Makefile. The steps can also be run one at a time:

- `make genome` downloads the reference genome
- `make fastq` downloads the first N read pairs
- `make index` builds the BWA index
- `make align` aligns the reads and makes a sorted, indexed BAM
- `make vcf` calls variants into `variants.vcf.gz`
- `make stats` writes the stats and coverage reports

The results are in `results/SRR1297048/N252837/`. The main files are `CBS10391.sorted.bam`, `variants.vcf.gz`, and several text reports (`bcftools_stats.txt`, `coverage.txt`, `flagstat.txt`, etc.).

## 2. How many variants were called?

bcftools called about 87,600 variants: around 78,000 SNPs and 9,600 indels. Most of them are on chromosomes I and II, and only a couple hundred are on the mitochondrion.

The Ts/Tv ratio was about 2.4. Random sequencing errors would give a much lower ratio, so most of these SNPs are likely real differences between CBS10391 and the reference strain.

## 3. What kinds of variants are present?

For SNPs, transitions (A>G, T>C, C>T, G>A) were about 2–3 times more common than transversions.

For indels, most were 1 bp insertions or deletions. Some longer ones were also present, up to a few dozen bases.

Most variant sites had a depth of around 3–15×. This matches the nuclear coverage, which was lower than 10× (about 6.5× on chromosomes I and II) because about a quarter of the reads mapped to the mitochondrion. Several thousand calls had a depth of only 1 or 2; these are discussed below.

## 4. Which calls look like true variants, and which look like errors?

I mainly used depth, mapping quality, and agreement between reads. Keeping only SNPs with depth ≥ 10, mapping quality ≥ 55, and all reads showing the alternate base on both strands gives about 8,800 high-confidence SNPs.

Two examples that look real:

- `NC_003424.3:65069` A>C: all 10 reads show C, on both strands, with high mapping quality.
- `NC_003424.3:175866` T>TA: all 11 reads have the extra A, and the site is not in a repeat, so it is unlikely to be an error.

Calls that look like errors:

- Calls with depth 1 or 2. With so few reads, they cannot be distinguished from sequencing errors.
- `NC_003424.3:232688` T>TAAAAAAA: this site is in a long run of A's. Only half of the reads have the insertion, all of them are on one strand, and the insertion length differs between reads (6 vs 7 bp).
- Some calls around `NC_003424.3:3761951` have low mapping quality. These are likely in repeated regions where reads cannot be placed uniquely, so I did not count them as real variants.



## 5. Are the calls supported by the alignments?

I loaded the genome, BAM, and VCF into IGV to check the examples above.

For the SNP at 65069, every read covering the position has a C:

![IGV view of the A>C SNP at NC_003424.3:65069](images/igv_snp.png)

For the insertion at 175866, all reads show the purple insertion mark at the same position:

![IGV view of the T>TA insertion at NC_003424.3:175866](images/igv_insertion.png)

For the poly-A site at 232688, the reads do not agree on how many A's were inserted. This is a common error pattern in homopolymer runs, so this call is likely not a real variant.

![IGV view of the poly-A insertion at NC_003424.3:232688](images/igv_homopolymer.png)