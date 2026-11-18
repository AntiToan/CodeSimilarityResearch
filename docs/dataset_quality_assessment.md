# Dataset Quality Assessment – POJ-104

## 1. Overview

This document records the data quality assessment of the POJ-104 dataset used in the CodeSimilarityResearch project.

The purpose of this assessment is to:
- Verify the integrity and readability of the raw dataset.
- Identify encoding issues and potentially invalid source files.
- Detect exact duplicate files.
- Define data handling policies before preprocessing.

### Dataset Information

| Property | Value |
|---|---|
| Dataset | POJ-104 |
| Programming language | C/C++ |
| Total number of files | 52,000 |
| Number of problems | 104 |
| Files per problem | 500 |
| Data unit | One source code file |
| Raw data directory | `data/raw/poj104/ProgramData/` |

## 2. Data Quality Assessment Results

The dataset inspection and quality assessment scripts were executed on all 52,000 source files.

### 2.1 General Statistics

| Metric | Result |
|---|---:|
| Total files | 52,000 |
| Empty files | 0 |
| Unreadable files (initial UTF-8 check) | 248 |
| Very small files (< 50 bytes) | 0 |
| Very large files (> 100,000 bytes) | 0 |
| Minimum file size | 81 bytes |
| Maximum file size | 15,005 bytes |
| Average file size | 624.93 bytes |

No empty, unusually small, or unusually large files were detected.

### 2.2 Encoding Issues

A total of 248 files could not be decoded using the default UTF-8 encoding.

Further investigation showed:

| Fallback Encoding | Number of Files |
|---|---:|
| cp1252 | 248 |

All 248 files were successfully decoded using the `cp1252` fallback in the investigation script.

Some previews contained unusual or incorrectly displayed characters, mainly in comments. However, the inspected samples still contained recognizable C/C++ source code structures.

**Decision:**
- Keep all 248 files.
- Do not modify the original raw files.
- Use a fallback decoding strategy during preprocessing.
- Record the encoding used for each processed file.
- Treat `cp1252` as a fallback decoding method, not as a confirmed original encoding.

### 2.3 Non-code Candidates

The investigation script identified 101 files as potential non-code candidates.

Manual inspection of sample files showed that some files contained valid C/C++ code but did not include common markers such as:
- `#include`
- `int main`
- `printf`
- `scanf`
- `cout`
- `cin`

For example, a file containing a function definition without a `main()` function was incorrectly classified as a non-code candidate.

This indicates that the current heuristic is insufficient to determine whether a file contains valid source code.

**Decision:**
- Keep all 101 candidate files.
- Do not remove files based only on the current heuristic.
- Perform more reliable syntax validation during later parsing and preprocessing stages.

### 2.4 Exact Duplicate Files

The investigation identified:

| Metric | Result |
|---|---:|
| Exact duplicate groups | 5 |
| Total files in duplicate groups | 10 |

All five duplicate groups contain files located in two different problem directories:

- `ProgramData/26/`
- `ProgramData/62/`

These files are byte-for-byte identical but are assigned different problem IDs.

This is important for pair generation because assigning labels solely based on problem IDs could produce incorrect negative pairs.

**Decision:**
- Keep all original duplicate files.
- Record duplicate relationships in metadata.
- Do not generate negative pairs from known exact duplicate relationships.
- Reconsider duplicate handling during pair generation and dataset splitting.

## 3. Data Handling Policies

The following policies will be applied in subsequent stages.

| Data Quality Issue | Handling Policy |
|---|---|
| UTF-8 decoding failures | Retain files and apply fallback decoding |
| cp1252 fallback | Record the selected decoding method |
| Non-code candidates | Retain files until syntax validation |
| Exact duplicates | Retain raw files and record duplicate relationships |
| Cross-problem duplicates | Exclude known identical pairs from negative pair generation |
| Raw dataset | Preserve original files without modification |

## 4. Data Integrity Principles

The project follows these principles:

1. The raw dataset must remain unchanged.
2. All preprocessing operations must generate outputs in `data/processed/`.
3. Data cleaning decisions must be documented and reproducible.
4. No source file should be removed solely based on an unreliable heuristic.
5. Duplicate relationships must be considered when generating similarity labels and splitting datasets.

## 5. Assessment Conclusion

The POJ-104 dataset contains 52,000 source files distributed across 104 problem categories.

The inspection found:
- No empty files.
- No unusually small or large files under the defined thresholds.
- 248 files requiring fallback decoding.
- 101 files requiring further syntax validation.
- 5 groups of exact duplicate files, containing 10 files in total.

These findings do not require removing any files from the raw dataset.

The dataset is considered suitable to proceed to the preprocessing stage, provided that the documented encoding and duplicate-handling policies are followed.

## 6. Generated Reports

The following reports were generated during the assessment:

| Report | Description |
|---|---|
| `inspection_report.csv` | Dataset structure and file distribution |
| `encoding_issues.csv` | Files requiring fallback decoding |
| `non_code_review.csv` | Potential non-code candidates and previews |
| `duplicate_review.csv` | Exact duplicate groups and file paths |

All reports are stored in:

`data/metadata/poj104/`

---

**Status:** Completed  
**Stage:** Dataset – Checkpoint 2.4: Data Quality Assessment  
**Next Stage:** Checkpoint 2.5 – Preprocessing