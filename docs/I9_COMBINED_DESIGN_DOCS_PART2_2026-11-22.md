# PHÂN CÔNG NHIỆM VỤ
## Đề tài: Hệ thống phát hiện tương đồng mã nguồn C/C++

### Thành viên 1 — Baseline
- Nghiên cứu SequenceMatcher và các phương pháp so sánh chuỗi.
- Triển khai baseline.
- Kiểm thử và đánh giá.

### Thành viên 2 — CodeBERT
- Nghiên cứu Embedding, Transformer, CodeBERT.
- Triển khai tạo embedding.
- Tính Cosine Similarity.
- Thử nghiệm inference.

### Thành viên 3 — Token và Winnowing
- Nghiên cứu Tokenization, K-gram, Hashing, Winnowing.
- Xây dựng tokenizer.
- Triển khai Winnowing.
- Kiểm thử.

### Thành viên 4 — AST
- Nghiên cứu AST, CST và Tree-sitter.
- Xây dựng parser C++.
- Trích xuất đặc trưng cấu trúc.
- Triển khai AST Similarity.

### Công việc chung
- Thu thập và khảo sát dataset.
- Xây dựng dataset và nhãn.
- Thống nhất preprocessing.
- Tích hợp các thuật toán.
- Đánh giá thực nghiệm.
- Xây dựng ứng dụng.
- Viết báo cáo nghiên cứu.

### Quy định
- Mỗi thành viên làm việc trên branch riêng.
- Không commit trực tiếp lên main.
- Code cần có test.
- Mỗi module cần README hoặc tài liệu hướng dẫn.
- Điểm similarity thống nhất trong khoảng 0.0 đến 1.0.
- Thay đổi phải được review trước khi merge.

---

# CodeSimilarityResearch — POJ-104 Dataset Preparation & Quality Reports (Merged)

Tài liệu này gộp 5 báo cáo về dataset, giữ nguyên toàn bộ nội dung gốc:

1. [Part 1 — POJ-104 Dataset Inspection Report](#part-1--poj-104-dataset-inspection-report) (Dataset Inspection)
2. [Part 2 — Dataset Quality Assessment – POJ-104](#part-2--dataset-quality-assessment--poj-104) (Checkpoint 2.4)
3. [Part 3 — Dataset Integrity Validation](#part-3--dataset-integrity-validation)
4. [Part 4 — Dataset Audit and Statistical Profiling](#part-4--dataset-audit-and-statistical-profiling)
5. [Part 5 — Dataset Outlier Analysis](#part-5--dataset-outlier-analysis) (Checkpoint 2.7.2.2)

> Lưu ý: trong mỗi Part, các mục được đánh số lại từ đầu (1, 2, 3…) theo tài liệu gốc.

---

## Part 1 — POJ-104 Dataset Inspection Report


### 1. Dataset Information

- Dataset: POJ-104
- Programming language: C/C++
- Total problems: 104
- Total source files: 52,000
- Samples per problem: 500
- File extension: .txt

### 2. Dataset Quality

| Metric            | Result    |
|---                |---:       |
| Total files       | 52,000    |
| Empty files       | 0         |
| Unreadable files  | 0         |
| Problem folders   | 104       |
| Files per problem | 500       |

### 3. Directory Structure

The dataset contains 104 problem directories.
Each directory contains 500 source-code files.

### 4. Initial Assessment

The downloaded dataset matches the
expected size and directory organization
of POJ-104.

All source files use the .txt extension.
The original files are preserved without
modification.

### 5. Inspection Script

- scripts/inspect_dataset.py

### 6. Generated Report

- data/metadata/poj104/inspection_report.csv

---

## Part 2 — Dataset Quality Assessment – POJ-104


### 1. Overview

This document records the data quality assessment of the POJ-104 dataset used in the CodeSimilarityResearch project.

The purpose of this assessment is to:
- Verify the integrity and readability of the raw dataset.
- Identify encoding issues and potentially invalid source files.
- Detect exact duplicate files.
- Define data handling policies before preprocessing.

#### Dataset Information

| Property | Value |
|---|---|
| Dataset | POJ-104 |
| Programming language | C/C++ |
| Total number of files | 52,000 |
| Number of problems | 104 |
| Files per problem | 500 |
| Data unit | One source code file |
| Raw data directory | `data/raw/poj104/ProgramData/` |

### 2. Data Quality Assessment Results

The dataset inspection and quality assessment scripts were executed on all 52,000 source files.

#### 2.1 General Statistics

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

#### 2.2 Encoding Issues

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

#### 2.3 Non-code Candidates

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

#### 2.4 Exact Duplicate Files

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

### 3. Data Handling Policies

The following policies will be applied in subsequent stages.

| Data Quality Issue | Handling Policy |
|---|---|
| UTF-8 decoding failures | Retain files and apply fallback decoding |
| cp1252 fallback | Record the selected decoding method |
| Non-code candidates | Retain files until syntax validation |
| Exact duplicates | Retain raw files and record duplicate relationships |
| Cross-problem duplicates | Exclude known identical pairs from negative pair generation |
| Raw dataset | Preserve original files without modification |

### 4. Data Integrity Principles

The project follows these principles:

1. The raw dataset must remain unchanged.
2. All preprocessing operations must generate outputs in `data/processed/`.
3. Data cleaning decisions must be documented and reproducible.
4. No source file should be removed solely based on an unreliable heuristic.
5. Duplicate relationships must be considered when generating similarity labels and splitting datasets.

### 5. Assessment Conclusion

The POJ-104 dataset contains 52,000 source files distributed across 104 problem categories.

The inspection found:
- No empty files.
- No unusually small or large files under the defined thresholds.
- 248 files requiring fallback decoding.
- 101 files requiring further syntax validation.
- 5 groups of exact duplicate files, containing 10 files in total.

These findings do not require removing any files from the raw dataset.

The dataset is considered suitable to proceed to the preprocessing stage, provided that the documented encoding and duplicate-handling policies are followed.

### 6. Generated Reports

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

---

## Part 3 — Dataset Integrity Validation


### 1. Overview

Dataset Integrity Validation is performed after preprocessing and metadata generation to ensure consistency between the original dataset, processed dataset, and metadata manifest.

The validation process is read-only. It does not modify, delete, or overwrite dataset files.

### 2. Objectives

- Verify the number of raw source files.
- Verify the number of processed source files.
- Verify metadata record count.
- Compare file mappings between Raw, Processed, and Metadata.
- Detect missing files and orphan files.
- Detect duplicate sample IDs.
- Confirm dataset consistency before subsequent data preparation stages.

### 3. Dataset Locations

#### Raw Dataset

`data/raw/poj104/ProgramData/`

Contains the original POJ-104 source files and remains unchanged.

#### Processed Dataset

`data/processed/poj104/source/`

Contains preprocessed source files, normalized to UTF-8 and LF line endings.

#### Metadata Manifest

`data/processed/poj104/metadata/samples.csv`

Contains metadata records mapping each sample to its original and processed file paths.

### 4. Expected Dataset Statistics

| Component | Expected Count |
|---|---:|
| Raw source files | 52,000 |
| Processed source files | 52,000 |
| Metadata records | 52,000 |
| Unique sample IDs | 52,000 |
| Duplicate sample IDs | 0 |

POJ-104 contains 104 problem categories, with 500 samples per problem.

### 5. Integrity Checks

The validation script checks the following:

| Check | Description |
|---|---|
| Raw count | Number of raw `.txt` source files |
| Processed count | Number of processed `.txt` source files |
| Metadata count | Number of metadata records |
| Unique sample IDs | Uniqueness of sample identifiers |
| Missing processed files | Raw files without corresponding processed files |
| Orphan processed files | Processed files without corresponding raw files |
| Missing raw metadata | Raw files not referenced in metadata |
| Orphan raw metadata | Metadata paths referencing nonexistent raw files |
| Missing processed metadata | Processed files not referenced in metadata |
| Orphan processed metadata | Metadata paths referencing nonexistent processed files |

### 6. Implementation

The integrity validator is implemented in:

`scripts/validate_dataset_integrity.py`

The script uses Python standard library modules:

- `csv` for reading the metadata manifest.
- `pathlib` for filesystem traversal and path comparison.

No additional dependencies are required.

### 7. Execution

Run the validator from the project root:

```bash
python -m scripts.validate_dataset_integrity
```

The script prints dataset counts, integrity check results, detected inconsistencies, and a final PASS or FAIL status.

### 8. Validation Result

**Status: PASS**

The dataset integrity validation completed successfully.

The validation confirmed that the Raw dataset, Processed dataset, and Metadata manifest passed the consistency checks implemented in the validator.

No integrity errors were reported by the validation run.

### 9. Conclusion

Dataset Integrity Validation confirms that the dataset artifacts are consistent according to the implemented checks.

The POJ-104 dataset has completed the following preparation stages:

1. Raw dataset inspection and quality assessment.
2. Source preprocessing.
3. Metadata manifest generation.
4. Metadata validation.
5. Dataset integrity validation.

The dataset is ready to proceed to the next data preparation activity. This validation does not establish semantic correctness of source code or guarantee that the dataset is free of all possible quality issues.

---

## Part 4 — Dataset Audit and Statistical Profiling


### 1. Overview

Dataset Audit and Statistical Profiling is performed after dataset integrity validation to understand the statistical characteristics of the POJ-104 processed source dataset.

Integrity validation checks dataset consistency, while profiling examines source size, source length, class distribution, empty files, and exact duplicates.

Profiling is read-only and does not remove or modify samples.

### 2. Objectives

- Analyze source file size distribution.
- Analyze source code line count and character count.
- Verify the distribution of samples across problems.
- Detect empty source files.
- Detect exact duplicate source files using SHA-256.
- Generate a source length histogram for exploratory analysis.

### 3. Implementation

The profiling script is implemented in:

`scripts/profile_dataset.py`

It uses:

- `hashlib` for SHA-256 hashing.
- `statistics` for descriptive statistics.
- `collections.Counter` for problem distribution.
- `matplotlib` for histogram visualization.
- `json` for saving profiling results.

### 4. Output Artifacts

The generated files are stored in:

`data/processed/poj104/audit/`

| File | Description |
|---|---|
| `dataset_profile.json` | Statistical profiling report |
| `source_length_distribution.png` | Histogram of source length in lines |

### 5. Profiling Results

#### Dataset Size

- Total samples: 52,000
- Number of problems: 104
- Samples per problem: 500

#### File Size (Bytes)

| Metric | Value |
|---|---:|
| Minimum | 76 |
| Maximum | 14,662 |
| Mean | 589.72 |
| Median | 495 |

#### Source Line Count

| Metric | Value |
|---|---:|
| Minimum | 1 |
| Maximum | 1,302 |
| Mean | 36.26 |
| Median | 33 |

#### Source Character Count

| Metric | Value |
|---|---:|
| Minimum | 76 |
| Maximum | 14,662 |
| Mean | 589.69 |
| Median | 495 |

#### Empty Files

- Count: 0

#### Exact Duplicates

- Duplicate groups: 5
- Files involved in duplicate groups: 10

### 6. Observations

1. The dataset contains 52,000 samples distributed evenly across 104 problems.
2. The mean source length is slightly greater than the median, indicating that longer samples influence the mean.
3. The longest source contains 1,302 lines, significantly longer than the median source length of 33 lines.
4. No empty source files were detected.
5. Five exact duplicate groups involving ten files were detected using SHA-256.

Exact duplicates are not automatically removed at the profiling stage. Their impact will be considered when designing pair generation and evaluation splitting to prevent data leakage and inappropriate negative pairs.

### 7. Execution

Run the profiling script from the project root:

```bash
python -m scripts.profile_dataset
```

The script saves the JSON report and histogram and prints summary statistics.

### 8. Validation Status

**Status: COMPLETED**

The profiling script executed successfully on the processed POJ-104 dataset. The report and histogram were generated.

### 9. Conclusion

Statistical profiling provides a baseline understanding of the processed dataset before pair construction and model training.

The profiling results are descriptive only. They do not establish semantic quality or justify automatic sample removal.

The dataset remains unchanged after profiling.

---

## Part 5 — Dataset Outlier Analysis


### 1. Overview

This checkpoint performs statistical outlier analysis on the POJ-104 processed source code dataset.

The purpose is to identify unusually long source code samples, investigate potential formatting anomalies, and determine whether these samples should be retained for subsequent model training.

Outlier detection is used for dataset analysis only. It does not automatically remove or modify any samples.

### 2. Objectives

- Identify unusually long source code samples.
- Detect potential formatting-related anomalies.
- Inspect representative outliers manually.
- Distinguish genuine long source code from unusual whitespace formatting.
- Preserve potentially valuable training samples.

### 3. Detection Method

The Interquartile Range (IQR) method was used based on source code line counts.

The upper outlier threshold is calculated as:

Upper Bound = Q3 + 1.5 × IQR

Where:

- Q1: First quartile (25th percentile)
- Q3: Third quartile (75th percentile)
- IQR: Interquartile range, calculated as Q3 − Q1

#### Dataset thresholds

| Statistic | Value |
|---|---:|
| Q1 | 25 lines |
| Q3 | 43 lines |
| IQR | 18 lines |
| Upper bound | 70 lines |

Samples containing more than 70 lines are classified as outliers for this analysis.

### 4. Implementation

The analysis was implemented in:

` scripts/analyze_dataset_outliers.py `

The script analyzes source code samples and generates:

- Outlier statistics
- Outlier sample records
- Largest samples ranked by line count and file size

### 5. Output Artifacts

Generated reports are stored in:

`data/processed/poj104/audit/`

| Artifact | Description |
|---|---|
| `outlier_analysis.json` | Statistical analysis and outlier summary |
| `outlier_samples.csv` | Samples exceeding the IQR threshold |
| `largest_samples.csv` | Top 20 largest samples |

### 6. Dataset Results

| Metric | Result |
|---|---:|
| Total samples | 52,000 |
| Upper outlier threshold | 70 lines |
| Outlier samples | 2,190 |
| Outlier percentage | 4.2115% |

Approximately 4.21% of the dataset samples were classified as line-count outliers.

### 7. Manual Inspection

Two representative samples were selected for manual investigation.

#### 7.1 Sample: `100/1139.txt`

| Metric | Value |
|---|---:|
| Total lines | 1,302 |
| Non-empty lines | 25 |
| Blank lines | 1,277 |
| Blank-line percentage | 98.08% |
| File size | 1,531 bytes |

The sample contains only 25 non-empty lines. The unusually high line count is primarily caused by excessive blank lines.

**Classification:** Formatting/whitespace outlier.

The source code is not considered corrupted based on the inspection. It is retained without modification.

#### 7.2 Sample: `80/1376.txt`

| Metric | Value |
|---|---:|
| Total lines | 343 |
| Non-empty lines | 343 |
| Blank lines | 0 |
| File size | 14,662 bytes |

All 343 lines contain code. The sample is genuinely long and uses verbose logic with multiple conditional branches and switch-case structures.

**Classification:** Genuine long-code outlier.

The sample is retained because its coding style and implementation structure may be useful for model training.

### 8. Findings

The investigation confirmed that unusually high line counts can have different causes:

1. Formatting anomalies, such as excessive blank lines.
2. Genuine long source code with verbose logic and implementation structures.

Therefore, line-count outliers should not automatically be considered invalid data.

### 9. Data Handling Decision

All detected outliers are retained.

No automatic filtering or source modification is performed during this checkpoint.

The outlier analysis will inform future model design decisions, particularly:

- Tokenization strategy
- Maximum sequence length
- Truncation or chunking strategy
- Handling of excessively long source code
- Potential preprocessing strategies for whitespace

These decisions will be evaluated in later model preparation stages.

### 10. Limitations

The IQR method identifies statistical outliers based on line count, not source code correctness.

The manual investigation covered representative samples, not all 2,190 outliers. Therefore, the findings should not be interpreted as a complete semantic validation of every outlier.

### 11. Status

**Checkpoint 2.7.2.2 – Dataset Outlier Analysis: COMPLETED**

- [x] Statistical outlier detection
- [x] IQR threshold calculation
- [x] Outlier sample export
- [x] Largest sample export
- [x] Manual inspection of representative samples
- [x] Classification of formatting vs. genuine long-code outliers
- [x] Data retention decision
- [x] Documentation completed



---

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

---

# Variant Data Model & Lineage Design

## 1. Purpose

This document defines the data model, metadata structure, storage organization, identification strategy, and lineage tracking rules for generated code variants in the CodeSimilarityResearch project.

The purpose of variant management is to generate controlled code modifications from original samples while preserving traceability, reproducibility, and dataset integrity.

Every generated variant must be traceable to its original source sample.

---

## 2. Variant Concept

A variant is a code sample generated from an original source through an approved transformation.

Examples of transformation categories:

- Formatting changes
- Whitespace changes
- Comment changes
- Scope-aware local variable renaming
- Safe function-local identifier renaming

Variants are additional code artifacts. They do not replace or modify original samples.

Variants derived from the same original source are considered part of the same source lineage.

---

## 3. Variant Identification

Each variant must have its own unique `variant_id`.

### 3.1 ID Format

The proposed format is:

`<original_sample_id>_v<index>`

Examples:

- `poj104_100_1139_v001`
- `poj104_100_1139_v002`
- `poj104_100_1139_v003`

### 3.2 ID Rules

- Variant IDs must be unique.
- The index starts from `001` for each original sample.
- The index increases within the original sample's variant namespace.
- IDs must be deterministic.
- Variant IDs must not replace the original sample ID.
- IDs of previously registered variants must not be reused.
- IDs are independent of transformation names.

The permanent ID allocation and rejected-generation handling policy will be refined during implementation design.

---

## 4. Variant Metadata Schema

A separate variant metadata registry will be maintained.

Proposed file:

`data/processed/poj104/metadata/variants.csv`

### 4.1 Fields

| Field | Type | Description |
|---|---|---|
| `variant_id` | string | Unique identifier of the generated variant |
| `original_sample_id` | string | ID of the original source sample |
| `problem_id` | string | Problem ID inherited from the original |
| `variant_index` | integer | Variant index within the original sample |
| `transformation_type` | string | Transformation category applied |
| `transformation_config` | JSON/string | Configuration of the applied transformation |
| `generation_seed` | integer/null | Seed used when applicable |
| `source_path` | string | Relative path to the original source code |
| `variant_path` | string | Relative path to the variant code |
| `status` | string | Generation and validation status |
| `created_at` | string | Variant creation timestamp |

### 4.2 Metadata Responsibilities

The variant registry must:

- Identify each variant.
- Reference its original sample.
- Track transformation information.
- Track variant file location.
- Track generation and validation status.
- Support reproducibility and auditing.
- Support positive pair generation.

Original sample metadata must remain unchanged.

---

## 5. Lineage Design

### 5.1 Lineage Definition

In the initial design, lineage is identified directly by:

`lineage_id = original_sample_id`

A separate lineage registry is not required at this stage.

### 5.2 Original-to-Variant Relationship

The relationship is one-to-many:

- One original sample may have zero, one, or multiple variants.
- Every variant belongs to exactly one original sample.
- A variant cannot exist without a valid original sample.
- Variants cannot reference other variants as their parent in the initial design.

### 5.3 Example

Original:

`poj104_100_1139`

Variants:

- `poj104_100_1139_v001`
- `poj104_100_1139_v002`
- `poj104_100_1139_v003`

All variants share the same lineage:

`poj104_100_1139`

The lineage relationship must be used to prevent invalid pair generation and dataset leakage.

---

## 6. Variant Storage Structure

Variant source code must be stored separately from original source code.

Proposed structure:

```text
data/processed/poj104/
├── source/
│   └── ...                       # Original source samples
├── metadata/
│   ├── samples.csv               # Original sample metadata
│   └── variants.csv              # Variant metadata registry
└── variants/
    ├── 1/
    │   └── ...
    ├── 100/
    │   ├── poj104_100_1139_v001.txt
    │   ├── poj104_100_1139_v002.txt
    │   └── ...
    └── ...
```

### 6.1 Storage Rules

- Original source files must never be overwritten.
- Variants must be stored separately from originals.
- Each variant must have its own file.
- Variant metadata must reference the correct variant file.
- Problem directory organization must remain consistent with the original problem ID.
- Accepted variants must have valid corresponding files.
- Rejected variants must not be used for pair generation.

Paths stored in metadata should be portable relative paths rather than machine-specific absolute paths.

---

## 7. Split Inheritance

Dataset splits must be assigned to original source samples before variant generation and pair generation.

Variants inherit the split of their original sample.

### 7.1 Rules

- A variant cannot independently select its split.
- The split is determined by its original source.
- All variants belonging to the same original lineage must remain in the same split.
- No original and its variants may cross train, validation, or test partitions.
- Variant metadata does not need an independent split field in the initial design.

The split can be resolved through the original sample's split assignment.

### 7.2 Example

If the original sample is assigned to `train`:

| Sample | Split |
|---|---|
| `poj104_100_1139` | train |
| `poj104_100_1139_v001` | train |
| `poj104_100_1139_v002` | train |
| `poj104_100_1139_v003` | train |

The following is invalid:

| Sample | Split |
|---|---|
| Original | train |
| Variant 1 | test |
| Variant 2 | validation |

Split inheritance is a mandatory constraint to prevent data leakage.

---

## 8. Variant Registry Validation Rules

The variant registry must enforce the following rules:

| Rule | Severity |
|---|---|
| `variant_id` must be unique | Mandatory |
| `original_sample_id` must exist | Mandatory |
| Original reference must point to an original sample, not another variant | Mandatory |
| Every variant must belong to exactly one original source | Mandatory |
| Accepted variants must have an existing code file | Mandatory |
| `variant_path` must be valid | Mandatory |
| Transformation type must be approved | Mandatory |
| Variant must not overwrite original source | Mandatory |
| Variants of the same lineage must share the same split | Mandatory |
| Rejected variants must not enter positive pairs | Mandatory |
| ID generation must be deterministic | Reproducibility requirement |

Invalid registry records must not be used to generate accepted positive pairs.

---

## 9. Variant Generation Strategy

### 9.1 Direct Generation from Originals

All variants must be generated directly from original samples.

The initial pipeline must not use variant-to-variant chaining.

Example:

```text
Original
 ├── Variant 1
 ├── Variant 2
 ├── Variant 3
 └── Variant 4
```

The following is prohibited in the initial design:

```text
Original
   ↓
Variant 1
   ↓
Variant 2
   ↓
Variant 3
```

This restriction simplifies lineage management and prevents compounded transformation errors.

### 9.2 One Transformation Type per Variant

The initial baseline applies one transformation type to each variant.

Examples:

- Variant 1: formatting
- Variant 2: comment change
- Variant 3: whitespace change
- Variant 4: safe variable renaming

Combined transformations are deferred to future experiments.

### 9.3 Rationale

This design provides:

- Easier transformation evaluation
- Easier debugging
- Better failure attribution
- More controlled semantic risk
- Clearer experimental analysis
- A simpler baseline for research

---

## 10. Variant Status

The `status` field must distinguish variants that are not eligible for pairing from accepted variants.

Proposed lifecycle:

- `generated` — Variant code has been generated.
- `validated` — Validation checks have passed.
- `accepted` — Variant is approved for use in positive pair generation.
- `rejected` — Variant has failed a mandatory validation or acceptance condition.

The exact transition rules and validation mechanisms will be defined in the transformation and validation design checkpoints.

Only variants with `accepted` status may be used for positive pair generation.

---

## 11. ID and Reproducibility Considerations

Variant generation should be deterministic under controlled inputs.

Reproducibility information should include:

- Original sample ID
- Variant index
- Transformation type
- Transformation configuration
- Generation seed where applicable
- Pipeline version
- Validation result
- Relative source and variant paths

Permanent IDs must not be randomly generated.

ID allocation behavior for failed, rejected, or retried generations must be finalized before implementation.

---

## 12. Scope Exclusions

This checkpoint does not define:

- Transformation algorithms
- Formatting implementation
- Comment modification rules
- Variable renaming implementation
- Number of variants per source
- Transformation probabilities
- Semantic equivalence testing
- Variant generation scripts
- Positive pair generation implementation
- Combined transformations

These topics will be addressed in subsequent checkpoints.

---

## 13. Acceptance Criteria

Variant data model and lineage design is considered complete when:

- Variant IDs are defined.
- Variant metadata schema is defined.
- Original-to-variant lineage is defined.
- Variant storage paths are defined.
- Split inheritance rules are defined.
- Registry validation rules are defined.
- Variant generation relationship is defined.
- Transformation isolation is defined.
- Variant statuses are defined.
- Reproducibility requirements are documented.

---

## 14. Design Principles

1. **Original preservation** — Original source files are immutable.
2. **Traceability** — Every variant must be traceable to its original sample.
3. **Controlled transformations** — Variants are generated under approved transformation rules.
4. **Lineage integrity** — A variant belongs to exactly one original lineage.
5. **Split integrity** — Original and variants remain within the same split.
6. **Reproducibility** — Variant generation must preserve relevant configuration and seed information.
7. **Experimental isolation** — Baseline variants apply one transformation type at a time.
8. **No chaining** — Variants are generated directly from originals in the initial design.

---

## 15. Status

Checkpoint: **2.6.1 — Variant Data Model & Lineage Design**

Status: **Design completed, pending repository commit.**


---

# Transformation Taxonomy & Safety Constraints

**Project:** CodeSimilarityResearch  
**Checkpoint:** 2.6.2 — Transformation Taxonomy & Safety Constraints  
**Status:** Design specification

---

## 1. Purpose

This document defines the transformation taxonomy used to generate code variants for positive pair construction.

The primary objective is to create modified versions of source code that retain the original program's semantics while introducing controlled syntactic differences.

Transformation safety is critical because positive pairs are assigned a synthetic similarity label of `1`. Unsafe transformations may alter program behavior and introduce label noise into the training dataset.

This specification classifies transformations into:

- Safe transformations — permitted in the baseline.
- Conditional transformations — permitted only after appropriate implementation and validation.
- Unsafe transformations — excluded from baseline generation.

---

## 2. Transformation Classification

### 2.1 Group A — Safe Transformations

These transformations are permitted in the baseline pipeline, subject to their corresponding validation rules.

| Transformation | Description | Baseline |
|---|---|---|
| Whitespace changes | Modify spaces, tabs, blank lines, indentation | Enabled |
| Formatting changes | Modify code formatting without changing tokens | Enabled |
| Comment changes | Add, remove, or modify comments | Enabled with restrictions |

#### A1. Whitespace Changes

Modify whitespace without changing meaningful code tokens.

Examples:
- Indentation changes
- Adding/removing blank lines
- Spacing around operators
- Spacing between tokens where syntactically valid

Constraint:
- The non-whitespace token sequence must remain unchanged.

#### A2. Formatting Changes

Modify the visual layout of source code while preserving the token sequence.

Examples:
- Reformatting braces
- Changing indentation style
- Reformatting expressions
- Splitting or combining lines

Constraint:
- Formatting must not introduce or remove meaningful tokens.

#### A3. Comment Changes

Modify comments without altering executable code.

Examples:
- Adding comments
- Removing comments
- Rewriting existing comments
- Moving comments when safe

Restrictions:
- Comments affecting preprocessing behavior must not be treated as ordinary comments.
- Preprocessor directives and compiler-sensitive constructs must be preserved.
- Comment transformations must be validated against the language's tokenization rules.

---

### 2.2 Group B — Conditional Transformations

These transformations may be used only when their implementation and validation mechanisms are sufficiently reliable.

They are not automatically enabled in the initial baseline.

| Transformation | Description | Baseline |
|---|---|---|
| Local variable renaming | Rename local variables consistently | Gated |
| Function-local identifier renaming | Rename identifiers within valid scopes | Gated |
| Parameter renaming | Rename function parameters | Disabled by default |
| Compound transformations | Combine multiple transformations | Experimental / disabled |

#### B1. Local Variable Renaming

Rename local variables while preserving all references to the same variable.

Requirements:
- Scope-aware identification
- Consistent renaming of declaration and references
- Collision detection
- No accidental renaming of unrelated identifiers
- Token-level validation

Simple textual replacement is prohibited.

#### B2. Function-Local Identifier Renaming

Rename eligible identifiers inside a function while preserving their relationships and references.

Requirements:
- Correct identifier resolution
- Scope awareness
- Reference consistency
- Collision prevention
- Exclusion of identifiers that cannot be safely resolved

This transformation must not modify function behavior or interfaces.

#### B3. Parameter Renaming

Rename function parameters and their references.

Risks:
- Interface compatibility
- Function pointer usage
- Macro references
- External or indirect references

This transformation remains disabled by default until its safety constraints are formally implemented and validated.

#### B4. Compound Transformations

Combine two or more transformations into one variant-generation operation.

Examples:
- Formatting + comment modification
- Formatting + local variable renaming

Compound transformations introduce additional validation complexity.

Requirements:
- Each constituent transformation must independently be permitted.
- Each constituent transformation must have a valid configuration.
- The combined result must pass whole-variant validation.
- Transformation order must be recorded.
- Compound transformations must not bypass individual safety restrictions.

Compound transformations are reserved for a later experimental stage.

---

### 2.3 Group C — Unsafe or Excluded Transformations

These transformations are excluded from baseline positive variant generation.

| Transformation | Reason for exclusion |
|---|---|
| Statement reordering | May change execution order or dependencies |
| Control flow modification | May change program behavior |
| Constant/literal replacement | May alter outputs |
| Arbitrary identifier replacement | May break references or semantics |
| Statement insertion | May introduce behavior |
| Statement deletion | May remove behavior |
| Operator replacement | May change computation |
| Function modification | May alter function behavior or contracts |
| Algorithm modification | Changes the underlying solution logic |
| Uncontrolled code mutation | Cannot provide reliable semantic guarantees |

These transformations must not be used to create positive pairs under the baseline labeling policy.

They may be investigated separately in future research experiments, but any such experiment must define its own labeling and validation methodology.

---

## 3. Common Safety Constraints

All transformation implementations must comply with the following constraints.

### 3.1 Original Source Protection

- Original source files are immutable.
- Transformation operations must never overwrite original files.
- All variants must be stored in the designated variants directory.

### 3.2 Controlled Modification

- Each transformation may only modify elements permitted by its classification.
- No unrelated modification is allowed.
- Transformation behavior must be deterministic when provided the same input, configuration, and seed.

### 3.3 Traceability

Every variant must be traceable to:

- Original sample ID
- Transformation type
- Transformation configuration
- Generation seed, when applicable
- Generator version
- Validation result

This information must be recorded in the variant registry according to the variant data model.

### 3.4 Fail-Safe Generation

If a transformation encounters:

- Ambiguous identifier resolution
- Scope uncertainty
- Name collision
- Parsing failure
- Unexpected token changes
- Potential semantic modification
- Unsupported source construct

The transformation must reject the variant rather than force acceptance.

### 3.5 No Unclassified Transformations

Every transformation must belong to a documented category and have defined validation requirements.

Unknown or undocumented transformation types must not enter the baseline generation pipeline.

---

## 4. Validation Requirements by Transformation

| Transformation | Minimum validation requirement |
|---|---|
| Whitespace changes | Token preservation |
| Formatting changes | Token sequence preservation |
| Comment changes | Non-comment token preservation + preprocessing-sensitive checks |
| Local variable renaming | Scope/reference consistency + collision checks + token validation |
| Function-local identifier renaming | Scope/reference consistency + collision checks + token validation |
| Parameter renaming | Interface/reference validation + token validation |
| Compound transformations | Individual validation + whole-variant validation |

### 4.1 Token Preservation

For transformations that should not modify meaningful tokens, the token sequence before and after transformation must remain identical.

Token preservation is a validation method for formatting-related transformations. It is not a universal proof of semantic equivalence for all transformation types.

### 4.2 Renaming Validation

Identifier renaming requires stronger checks than formatting transformations.

Validation must ensure:
- The intended identifier was renamed.
- All valid references were renamed consistently.
- Unrelated identifiers remain unchanged.
- No identifier collision was introduced.
- The transformed code remains syntactically valid.

### 4.3 Compound Validation

Compound transformations must be validated both individually and as a complete result.

Passing individual checks does not automatically guarantee that a combination is valid.

---

## 5. Baseline Transformation Policy

### 5.1 Enabled

The initial baseline allows:

1. Whitespace changes
2. Formatting changes
3. Comment changes, subject to preprocessing-related restrictions

These transformations are preferred because they can introduce syntactic diversity with relatively low semantic risk.

### 5.2 Gated

The following transformations are candidates for enabling after their implementation and validators are ready:

1. Local variable renaming
2. Function-local identifier renaming

A transformation may be enabled only when its safety requirements are implemented and tested.

### 5.3 Disabled by Default

1. Parameter renaming
2. Compound transformations

These may be revisited after the baseline is established and independently evaluated.

### 5.4 Excluded

All transformations in Group C remain excluded from baseline positive pair generation.

---

## 6. Transformation Acceptance Policy

A transformation is eligible for acceptance only when:

1. It belongs to an allowed transformation category.
2. Its implementation complies with the defined safety constraints.
3. The required validator is available.
4. The variant passes all applicable validation rules.
5. The variant has valid lineage metadata.
6. The variant can be reproduced or traced according to the generation configuration.

A variant that fails validation must be rejected.

Only accepted variants are eligible for positive pair construction.

---

## 7. Relationship to Positive Pair Generation

The transformation taxonomy directly controls the positive pair pipeline.

The intended flow is:

Original Source  
→ Transformation Selection  
→ Variant Generation  
→ Transformation Validation  
→ Variant Acceptance / Rejection  
→ Positive Pair Candidate Generation

Only accepted variants may be used to create positive pairs.

The synthetic label `1` indicates that the pair was generated under the project's positive-pair construction rules. It does not represent independently verified plagiarism or human-annotated semantic equivalence.

---

## 8. Future Extensions

The following topics are outside the scope of this checkpoint:

- Implementing transformation algorithms
- Selecting transformation probabilities
- Selecting the number of variants per original sample
- Implementing AST-based renaming
- Implementing validators
- Compiler integration
- Automated testing of semantic equivalence
- Compound transformation experiments
- Evaluating the impact of transformations on model performance

These topics will be addressed in subsequent checkpoints.

---

## 9. Design Decision Summary

The project adopts a conservative transformation policy.

The baseline prioritizes reliable synthetic positive labels over aggressive code mutation. Transformations that introduce semantic uncertainty are gated or excluded.

This policy is intended to reduce label noise, preserve source lineage, maintain reproducibility, and provide a reliable foundation for future experiments in code similarity research.


---

# Transformation Validation Strategy

**Project:** CodeSimilarityResearch  
**Checkpoint:** 2.6.3 — Transformation Validation Strategy  
**Status:** Design specification

---

## 1. Purpose

This document defines the validation strategy for code variants generated during the variant generation process.

The objective is to ensure that generated variants satisfy structural requirements, comply with their declared transformation rules, and provide sufficient evidence of validity before being used in positive pair generation.

A generated variant is not automatically considered valid.

Only variants that pass all mandatory validation requirements may be accepted into the positive pair candidate pool.

---

## 2. Validation Pipeline

The validation pipeline is positioned between variant generation and positive pair generation.

The intended workflow is:

Original Source  
→ Variant Generation  
→ Validation Pipeline  
→ Accepted / Rejected  
→ Positive Pair Candidate Generation

Validation is performed independently for each variant.

A failure in one variant must not automatically interrupt the entire batch. However, critical validation infrastructure failures must be reported because they may affect the reliability of the overall batch.

---

## 3. Validation Levels

Validation is organized into four levels.

### V1 — Structural Validation

Purpose: Verify the integrity of the variant, its files, and its metadata.

Checks include:

- Variant file exists.
- Variant file is not empty.
- Original source exists.
- Variant ID is valid and unique.
- Original sample ID is correct.
- Transformation type is recognized.
- Required metadata is present.
- Variant does not overwrite the original source.
- File paths comply with the project structure.

V1 must pass before a variant proceeds through the remaining validation stages.

### V2 — Transformation Validation

Purpose: Verify that the transformation was performed according to its declared rules.

Examples:

| Transformation | Validation |
|---|---|
| Whitespace changes | Token sequence preservation |
| Formatting changes | Token sequence preservation |
| Comment changes | Non-comment token preservation and preprocessing-sensitive checks |
| Local variable renaming | Scope/reference consistency, collision checks, token validation |
| Function-local identifier renaming | Scope/reference consistency, collision checks, token validation |
| Parameter renaming | Interface/reference validation and token validation |
| Compound transformations | Individual transformation validation and whole-result validation |

V2 is the primary validation level for synthetic positive labels.

### V3 — Syntax Validation

Purpose: Verify that the transformed code remains syntactically valid.

Possible validation methods include:

- Compiler syntax-check
- Parser-based syntax validation
- Language-specific structural validation

For C/C++, compiler syntax-checking without linking may be used where feasible.

V3 detects syntax errors but does not prove semantic equivalence.

### V4 — Semantic Evidence Validation

Purpose: Collect additional evidence that the variant preserves program behavior.

Potential methods include:

- Successful compilation
- Execution on the same test inputs
- Comparison of original and variant outputs
- Runtime behavior comparison
- Additional program-specific checks

V4 provides supporting evidence rather than an absolute proof of semantic equivalence.

Validation requirements may differ depending on the transformation type.

---

## 4. Validation Matrix

The following matrix defines the baseline validation requirements.

| Transformation | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| Whitespace | Required | Required | Optional | Optional |
| Formatting | Required | Required | Optional | Optional |
| Comments | Required | Required | Optional | Optional |
| Local variable renaming | Required | Required | Recommended before enabling | Optional |
| Function-local renaming | Required | Required | Recommended before enabling | Optional |
| Parameter renaming | Required | Required | Required | Gated |
| Compound transformations | Required | Required | Required | Experimental |

### Requirement Interpretation

- **Required:** Failure prevents acceptance.
- **Recommended before enabling:** Must be available and tested before the transformation is enabled for baseline generation.
- **Optional:** May provide additional evidence but is not mandatory for baseline acceptance.
- **Gated / Experimental:** Transformation remains disabled until its validation policy is finalized.

A recommended validation level must not be treated as an unrestricted option to bypass safety checks.

---

## 5. PASS / FAIL Policy

The final validation status of a variant is binary:

- `accepted`
- `rejected`

### ACCEPTED

A variant is accepted only when:

1. Its structural validation passes.
2. Its transformation validation passes.
3. All applicable mandatory validation levels pass.
4. No mandatory validator reports an error.
5. Its metadata is traceable.
6. Its transformation is permitted by the taxonomy and baseline policy.

### REJECTED

A variant is rejected when:

- A mandatory validation fails.
- The variant violates its transformation constraints.
- The source or variant cannot be reliably identified.
- The validator detects an unsafe modification.
- Validation cannot produce a reliable result.
- The transformation is not permitted.

### Fail-Closed Principle

If a validator cannot execute, encounters an error, times out, or cannot determine validity, the affected variant must not be accepted.

A validation failure must not be converted into a PASS merely because the transformation was expected to be safe.

---

## 6. Rejection Handling

Rejected variants must not be used for positive pair construction.

Rejected records should be retained for audit and analysis rather than deleted immediately.

The rejection process must:

- Preserve the rejection record.
- Record the reason for rejection.
- Exclude the variant from the accepted variant pool.
- Avoid automatic modification to force acceptance.
- Avoid unlimited retries.
- Support rejection statistics and quality analysis.

If retry behavior is introduced, retries must be bounded, deterministic when configured, and separately traceable.

---

## 7. Rejection Reason Codes

Rejection reasons should use standardized codes.

| Code | Meaning |
|---|---|
| `FILE_MISSING` | Variant file does not exist |
| `EMPTY_FILE` | Variant file is empty |
| `METADATA_INVALID` | Metadata is invalid or incomplete |
| `TOKEN_MISMATCH` | Unexpected token changes detected |
| `IDENTIFIER_COLLISION` | Renaming caused identifier collision |
| `SCOPE_UNRESOLVED` | Identifier scope could not be reliably resolved |
| `SYNTAX_ERROR` | Syntax validation failed |
| `TRANSFORMATION_UNSUPPORTED` | Transformation is unsupported or disallowed |
| `VALIDATOR_ERROR` | Validator encountered an internal error |
| `VALIDATION_TIMEOUT` | Validation exceeded its allowed execution time |

Additional codes may be introduced when new validation rules are designed, but they must be documented and standardized.

---

## 8. Validation Registry

Validation results must be stored separately from the variant registry.

Proposed output:

`data/processed/poj104/metadata/variant_validation.csv`

### Proposed Fields

| Field | Description |
|---|---|
| `variant_id` | Variant identifier |
| `original_sample_id` | Original source identifier |
| `transformation_type` | Applied transformation |
| `validation_status` | accepted / rejected |
| `v1_status` | Structural validation result |
| `v2_status` | Transformation validation result |
| `v3_status` | Syntax validation result |
| `v4_status` | Semantic evidence result |
| `rejection_reason` | Rejection code, if rejected |
| `validator_version` | Validator version |
| `validated_at` | Validation timestamp |

This registry complements `variants.csv` and does not replace the variant data model.

---

## 9. Validation Execution Policy

The validation pipeline must follow these execution rules:

1. Validate variants independently.
2. Continue processing other variants when an individual variant fails.
3. Report critical infrastructure failures that affect batch reliability.
4. Support deterministic validation where applicable.
5. Apply timeouts to potentially long-running validation operations.
6. Produce validation summary statistics.
7. Expose only accepted variants to downstream pair generation.

Batch processing must distinguish between individual variant failures and system-level validation failures.

---

## 10. Relationship to Positive Pair Generation

The validation pipeline acts as a mandatory gate for positive pair generation.

The intended flow is:

Original Source  
→ Transformation Selection  
→ Variant Generation  
→ Validation  
→ Acceptance / Rejection  
→ Positive Pair Candidate Generation

Only accepted variants are eligible for positive pair candidates.

The synthetic positive label indicates that the pair satisfies the project's controlled generation and validation rules. It does not represent human-confirmed plagiarism or absolute proof of semantic equivalence.

---

## 11. Out of Scope

The following are not finalized in this checkpoint:

- Specific compiler and compiler version
- Parser or tokenizer implementation
- Identifier scope analysis implementation
- Compilation configuration
- Runtime test inputs
- Runtime equivalence methodology
- Timeout values
- Retry limits
- Validator implementation
- Automated test implementation
- Semantic equivalence guarantees

These decisions will be addressed in later implementation and tooling design checkpoints.

---

## 12. Acceptance Criteria

Checkpoint 2.6.3 is considered complete when the following design decisions are finalized:

- Validation pipeline structure
- Four validation levels
- Validation matrix
- PASS / FAIL policy
- Fail-closed behavior
- Rejection policy
- Standard rejection reason codes
- Validation registry schema
- Validation execution policy
- Eligibility rules for positive pair generation

---

## 13. Design Decision Summary

The project adopts a strict validation gate between variant generation and positive pair generation.

Variant generation and variant acceptance are separate operations. A generated variant must pass the applicable validation requirements before it can be used as a synthetic positive sample.

This strategy prioritizes label reliability, traceability, and dataset integrity over maximizing the number of generated variants.

Validation failure must never be silently ignored or converted into acceptance.


---

# Problem Distribution Balance

## 1. Objective

This checkpoint defines the strategy for balancing pair distributions across the 104 programming problems in POJ-104.

The objective is to reduce problem-level sampling bias, improve problem diversity, and avoid excessive representation of a small subset of problems in the pair dataset.

## 2. Dataset Context

- Total problems: 104
- Original samples per problem: 500
- Positive pairs are primarily generated from the same source and its controlled variants.
- Negative pairs are sampled from different problems.

Although the original dataset is balanced at the sample level, pair generation can introduce problem-level imbalance.

## 3. Selected Strategy

The project adopts hierarchical / stratified problem sampling with soft balancing.

Sampling is performed with problem distribution considered as a priority, while pair validity and availability remain the primary constraints.

## 4. Positive Pair Distribution

Positive pair sampling must:

- Prioritize relatively uniform representation across the 104 problems.
- Select valid positive pairs within each problem.
- Avoid allowing problems with many variants to dominate the positive pair dataset.
- Accept lower counts for problems with fewer valid positive candidates.

No invalid positive pairs will be created to satisfy problem-level quotas.

## 5. Negative Pair Distribution

Negative pair sampling must:

- Distribute anchors across the 104 problems.
- Select negative samples from different problems than the anchor.
- Prioritize distinct negative problem IDs for the negative pairs associated with an anchor.
- Avoid repeatedly selecting a small subset of problems as negative endpoints.
- Track problem appearances across both pair endpoints.

## 6. Soft Balance Policy

Problem-level balance is a priority, not a strict quota.

- No mandatory fixed pair count per problem.
- Problems with insufficient valid pairs may contribute fewer pairs.
- Excess candidates may be sampled using controlled selection.
- Invalid pairs must never be forced into the dataset.
- Pair validity and diversity take priority over perfect uniformity.

## 7. Distribution Audit

The pair generation and balancing process must record problem-level statistics, including:

- Positive pair counts per problem.
- Negative pair counts per anchor problem.
- Negative endpoint appearances per problem.
- Minimum, maximum, mean, and median problem representation.
- Problems with unusually low or high pair representation.
- Distribution imbalance observations.

Negative endpoint appearances count a problem each time it appears as either endpoint of a negative pair.

## 8. Reproducibility

Problem-level sampling must be reproducible using a fixed random seed.

The same candidate pool, configuration, and seed should produce the same selected pair distribution.

## 9. Constraints

- No hard quota requiring invalid pairs.
- No duplicate pairs.
- No same-problem negative pairs under the current negative sampling policy.
- No pair crossing train, validation, or test splits.
- Problem balancing must not modify original source code or candidate records.
- Candidate pairs that are not selected must remain available in the candidate pool when applicable.

## 10. Expected Outcome

The resulting dataset should maintain broad coverage across POJ-104 problems, reduce excessive problem concentration, and preserve pair validity and diversity.

This checkpoint defines the problem distribution balancing strategy only. Implementation and actual pair generation will occur in later checkpoints.
