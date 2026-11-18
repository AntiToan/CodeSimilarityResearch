# Preprocessing Pipeline Design – POJ-104

## 1. Objective

This document defines the preprocessing pipeline for the POJ-104 dataset used in the CodeSimilarityResearch project.

The objective is to normalize source files while preserving their original program content and structure.

The preprocessing stage must be reproducible and must never modify the raw dataset.

## 2. Input and Output

**Input directory:**

`data/raw/poj104/ProgramData/`

**Output directory:**

`data/processed/poj104/`

Expected output structure:

```text
data/
├── raw/
│   └── poj104/
│       └── ProgramData/
└── processed/
    └── poj104/
        ├── source/
        │   ├── 1/
        │   ├── 2/
        │   └── ... 104/
        ├── metadata/
        └── preprocessing_report.json
```

Each processed file preserves its original problem ID and filename.

## 3. Preprocessing Principles

The pipeline follows these principles:

1. Preserve the raw dataset without modification.
2. Preserve source code semantics and structure.
3. Apply only safe text normalization.
4. Record the decoding method used for each file.
5. Never silently discard files that cannot be decoded.
6. Keep preprocessing reproducible.

## 4. Preprocessing Operations

### 4.1 File Discovery

- Recursively discover source files under `ProgramData/`.
- Process files with the `.txt` extension.
- Preserve the original relative directory structure.

### 4.2 Encoding Handling

The decoding order is:

1. `utf-8-sig`
2. `utf-8`
3. `cp1252`

The first successful decoding method is recorded.

If all decoding attempts fail:
- Record the file as a processing error.
- Do not silently skip it.
- Preserve the original raw file.

Note: The recorded encoding represents the decoding method used by the pipeline. It does not necessarily prove the original encoding of the file.

### 4.3 Text Normalization

The following transformations are allowed:

- Remove UTF-8 BOM at the beginning of a file.
- Normalize Windows line endings (`CRLF`) to Unix line endings (`LF`).
- Normalize standalone carriage returns (`CR`) to `LF`.
- Encode processed output using UTF-8.

### 4.4 Content Preservation

The following elements must remain unchanged:

- Comments
- String literals
- Variable names
- Function names
- Operators
- Indentation
- Blank lines
- Program statements
- Overall source code structure

The pipeline must not remove comments, strings, or rename identifiers.

It must not apply `strip()` or other whitespace-removal operations that could alter source formatting.

## 5. Duplicate Handling

Exact duplicate files must remain in the processed dataset.

The pipeline must preserve their original problem IDs and filenames.

Duplicate relationships will be considered during metadata generation and pair generation to prevent incorrect negative labels.

## 6. Processing Output and Logging

The pipeline will produce:

- Processed source files.
- Processing status for each file.
- Decoding method used.
- Original and processed file sizes.
- Original and processed SHA-256 hashes.
- A processing report containing success and failure statistics.

Detailed metadata will be finalized in Checkpoint 2.6.

## 7. Validation Requirements

After preprocessing, the following conditions must be checked:

1. Every successfully processed file can be read as UTF-8.
2. The output directory structure matches the original problem directory structure.
3. Comments and string literals are preserved.
4. No raw file has been modified.
5. All processing failures are recorded.
6. The number of discovered files matches the inspection report.

The SHA-256 hash of the raw file and processed file may differ because of the intended BOM and line-ending normalization.

## 8. Expected Outcome

The expected outcome is a normalized copy of the POJ-104 dataset, with source content preserved and UTF-8 output encoding.

The processed dataset will serve as the input for subsequent parsing, metadata generation, pair construction, and code similarity experiments.

---

**Status:** Design completed  
**Stage:** Dataset – Checkpoint 2.5.1  
**Next:** Checkpoint 2.5.2 – Implement Source File Reader and Encoding Handler