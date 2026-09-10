# Assignment 3

## Fork the code:

I am reviewing Hairuo Wang's Week 2 assignment where he visualized the reference genome for Schizosaccharomyces pombe.

```bash
git clone https://github.com/hairuow622/appbio-KL.git .
```

After forking, to check the reproducibility of the make file I removed the existing .FASTA and .gff files

```bash
rm -f data/fasta/GCF_000002945.2_ASM294v3_genomic.fna
rm -f data/gff/GCF_000002945.2_ASM294v3_genomic.gff
```
Run:

```bash
make
```

Output:

```bash
kenny@MacBook-Pro ~/BMMB852/Week03/week02
$ make
curl --fail --location "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.fna.gz" \
	| gzip -dc > "data/fasta/GCF_000002945.2_ASM294v3_genomic.fna.tmp"
  % Total    % Received % Xferd  Average Speed  Time    Time    Time   Current
                                 Dload  Upload  Total   Spent   Left   Speed
100  3.80M 100  3.80M   0      0  7.31M      0                              0
mv "data/fasta/GCF_000002945.2_ASM294v3_genomic.fna.tmp" "data/fasta/GCF_000002945.2_ASM294v3_genomic.fna"
curl --fail --location "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/002/945/GCF_000002945.2_ASM294v3/GCF_000002945.2_ASM294v3_genomic.gff.gz" \
	| gzip -dc > "data/gff/GCF_000002945.2_ASM294v3_genomic.gff.tmp"
  % Total    % Received % Xferd  Average Speed  Time    Time    Time   Current
                                 Dload  Upload  Total   Spent   Left   Speed
100  1.42M 100  1.42M   0      0  5.74M      0                              0
mv "data/gff/GCF_000002945.2_ASM294v3_genomic.gff.tmp" "data/gff/GCF_000002945.2_ASM294v3_genomic.gff"
(bioinfo) 
```

## Check reproducibility of the downstream code from the files created by Mr. Wang's Makefile

### How large is the genome?

Ran code from his "week02" file:

```bash
seqkit stats data/fasta/GCF_000002945.2_ASM294v3_genomic.fna
```

Output (pasted from my terminal):

```bash
file                                             format  type  num_seqs     sum_len  min_len      avg_len    max_len
data/fasta/GCF_000002945.2_ASM294v3_genomic.fna  FASTA   DNA          4  12,591,253   19,433  3,147,813.3  5,579,133
(bioinfo) 
```
### How many chromosomes does it have?

Ran code from his "week02" file:

```bash
grep -c '^>.*chromosome:' data/fasta/GCF_000002945.2_ASM294v3_genomic.fna
```

Output (pasted from my terminal):

```bash
3
```

## Questions from Assignment 3

The code is extremely reproducible. I after cloning Mr. Wang's makefile from his Github, I was able to acheive the same
outputs from his commands as he was. My AI agent said that his solution is better than mine, only because his has more
validation steps than mine does and is cleaner. Although I have a sneaking suspicion it is just saying that since I
have already loaded in Mr. Wang's code it has a preference his code instead. There is not much I would change, but I 
would update the file names to be the organisms' names instead of just the accession number. The .gff files are also
not indexed.

### Change file names:

Command:

```bash
mv data/fasta/GCF_000002945.2_ASM294v3_genomic.fna data/fasta/SPombe_genomic.fna
mv data/fasta/GCF_000002945.2_ASM294v3_genomic.fna.fai data/fasta/SPombe_genomic.fna.fai
mv data/gff/GCF_000002945.2_ASM294v3_genomic.gff data/gff/SPombe_genomic.gff
```

Resulting file names:

```bash
kenny@MacBook-Pro ~/BMMB852/Week03/week02/data
$ ls fasta
SPombe_genomic.fna     SPombe_genomic.fna.fai
(bioinfo) 

kenny@MacBook-Pro ~/BMMB852/Week03/week02/data
$ ls gff
SPombe_genomic.gff
(bioinfo) 
```

### Index files:

Command:

```bash
bgzip -c data/gff/SPombe_genomic.gff > data/gff/SPombe_genomic.gff.gz
```

Output:

```bash
kenny@MacBook-Pro ~/BMMB852/Week03/week02/data/gff
$ ls
SPombe_genomic.gff    SPombe_genomic.gff.gz
(bioinfo) 
```
