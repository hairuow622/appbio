# Week 03: Repository Review

For this assignment, I selected the Week 02 submission from
[AyanDasAE7788/Applied_Bioinformatics](https://github.com/AyanDasAE7788/Applied_Bioinformatics)
to review.

## 1. Fork and clone the repository

First, I opened the original repository on GitHub and clicked **Fork** to
create a copy under my GitHub account:

```text
https://github.com/hairuow622/Applied_Bioinformatics
```

I then cloned my fork to my computer:

```bash
cd ~/Documents/psu_course
git clone https://github.com/hairuow622/Applied_Bioinformatics.git
cd Applied_Bioinformatics
```

I checked the repository status and confirmed that the working tree was clean:

```bash
git status
```

I also checked the configured remote repository:

```bash
git remote -v
```

The `origin` remote pointed to my fork:

```text
origin  https://github.com/hairuow622/Applied_Bioinformatics.git (fetch)
origin  https://github.com/hairuow622/Applied_Bioinformatics.git (push)
```

To keep a reference to the classmate's original repository, I added it as the
`upstream` remote:

```bash
git remote add upstream https://github.com/AyanDasAE7788/Applied_Bioinformatics.git
git remote -v
```

Finally, I created a separate branch for my review and proposed correction:

```bash
git switch -c week02-review-fix
```

All review work and changes will be made on this branch rather than directly
on `main`.

## 2. Verify the code is not doing something dangerous

### Prompt

> Review the `Week_02/Makefile` for potentially dangerous behavior. Check for
> destructive commands, privilege escalation, unknown network sources,
> arbitrary code execution, and writes outside the project directory.

### AI (GPT-5.6 Sol) result

The Makefile does not appear to do anything dangerous. It downloads two
genome files over HTTPS from the official NCBI server and writes them only to
the local `data/` directory. It does not use `sudo`, execute downloaded code,
upload information, or modify system files. The `clean` command removes only
the two explicitly named downloaded files. One reliability issue is that
`curl -L` does not include `--fail`, so an HTTP error could be saved as if it
were a data file; adding `--fail` would make download failures clearer.

## 3&4. Evaluation of the README

The README clearly identifies the selected genome, required tools, download
command, generated files, analysis commands, and expected numerical results.
A reviewer can understand that running `make` downloads the FASTA and GFF
files, and the reported outcomes include genome size, chromosome count, and
annotation count.

However, the reproduction instructions unnecessarily ask the reviewer to
create a new directory and copy the Makefile instead of simply cloning the
repository and running `make` in `Week_02`. It also lists `samtools` even
though none of the documented commands use it. 

Overall, the command-line analysis is explained clearly.

## 5. Verify that the results are reproducible.

I followed the instructions provided in the README and was able to successfully
run the workflow and reproduce the expected results. The steps were clear, so
the analysis is reproducible. However, the documented `zcat` command has a
compatibility issue on macOS because it expects a `.Z` file. I used
`gzip -dc` instead and obtained the expected genome size of 4,641,652 bp.

## 6&7&8 . Ask the AI (GPT-5.6 Sol) Agent to compare and evaluate your solution to theirs.

### Prompt

> Compare my Week 02 `README.md` and `Makefile` in `appbio/week02` with the
> classmate's files in `Applied_Bioinformatics/Week_02`. Evaluate
> reproducibility, readability, repository structure, safety, and error
> handling. The projects use different organisms, so do not judge the choice
> of genome. Explain the strengths and weaknesses of each approach, decide
> which solution is better overall, and summarize the conclusion in one or two
> paragraphs.

### AI comparison and final summary

Both solutions document the selected genome, download data from the official
NCBI source, report expected statistics, and provide enough information to
repeat the analysis. The classmate's README gives detailed explanations and
their Makefile is simple and includes a useful `clean` target. However, its
setup instructions are longer than necessary, `samtools` is listed but not
used, `curl` does not detect HTTP errors, and the documented `zcat` command is
not compatible with macOS. Despite that issue, I reproduced all reported
numerical results by replacing `zcat` with `gzip -dc`.

AI think my solution is slightly better overall in technical reproducibility and structure. Its Makefile uses `curl --fail`, enables `pipefail`, writes to
temporary files before moving them into place, and separates FASTA and GFF
data into clear directories. These safeguards reduce the chance of keeping a
partial or failed download. The classmate's solution remains readable and
reproducible, but adding safer download handling and a macOS-compatible genome
size command would improve it.

# 9. Make a change to the forked repository

I changed the genome-size command in the forked repository's
`Week_02/README.md` from:

```bash
zcat data/GCF_000005845.2_ASM584v2_genomic.fna.gz | grep -v "^>" | tr -d '\n' | wc -c
```

to:

```bash
gzip -dc data/GCF_000005845.2_ASM584v2_genomic.fna.gz | grep -v "^>" | tr -d '\n' | wc -c
```

I made this change because the macOS implementation of `zcat` treated the
input as a `.Z` file and failed to open the `.gz` file. `gzip -dc` works with
gzip-compressed files on both macOS and Linux and produces the same expected
genome size of **4,641,652 bp**, making the instructions more portable and
reproducible.

# 10&11. Create a pull request

I committed and pushed the change to the `week02-review-fix` branch of my
fork, then opened the following pull request to the original repository:

[Pull Request #1: Use portable command for genome size calculation](https://github.com/AyanDasAE7788/Applied_Bioinformatics/pull/1)