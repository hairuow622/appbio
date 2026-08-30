# Week 01

AI-ready code editor: **Cursor**

## 1. Samtools version

### Commands

```bash
conda activate bioinfo
samtools --version
```

### Output

```text
samtools 1.24
Using htslib 1.24
Copyright (C) 2026 Genome Research Ltd.
```

The `bioinfo` environment uses **Samtools 1.24** with **HTSlib 1.24**.

## 2. Create a nested directory structure

### Command

```bash
mkdir -p project/data/raw
```

### Output

The command produces no output when successful.

The resulting structure is:

```text
project/
└── data/
    └── raw/
```

## 3. Create files in different directories

### Commands

```bash
touch project/notes.txt
touch project/data/metadata.txt
touch project/data/raw/sample.txt
```

### Output

The commands produce no output when successful.
The resulting structure is:

```text
project/
├── notes.txt
└── data/
    ├── metadata.txt
    └── raw/
        └── sample.txt
```

## 4. Access files using relative and absolute paths

### Current directory

```bash
pwd
```

```text
/Users/hairuow/appbio/week01
```

### Relative paths

```bash
cd project
cat notes.txt

cd data
cat metadata.txt

cd raw
cat sample.txt
```

### Absolute paths

```bash
cd /Users/hairuow/appbio/week01

cat /Users/hairuow/appbio/week01/project/notes.txt
cat /Users/hairuow/appbio/week01/project/data/metadata.txt
cat /Users/hairuow/appbio/week01/project/data/raw/sample.txt
```

The `cat` commands produce no output because these files are empty.