# Batch Preprocessing – POJ-104

## 1. Overview

This activity implements the batch preprocessing pipeline for the POJ-104 dataset.

The purpose is to normalize source code files into a consistent format before performing code similarity analysis, feature extraction, dataset construction, and model training.

The pipeline processes source files independently and preserves the original dataset directory structure.

## 2. Objectives

- Process all source files in the POJ-104 dataset.
- Reuse the single-file source reader.
- Normalize source file encoding and line endings.
- Preserve source code content and structure.
- Preserve problem IDs and filenames.
- Handle file-level errors without stopping the entire batch.
- Generate a preprocessing summary report.
- Keep the raw dataset unchanged.

## 3. Input Dataset

Dataset: POJ-104

Language: C/C++

Total source files: 52,000

Number of problems: 104

Files per problem: 500

### Input directory

```text
data/raw/poj104/ProgramData/
├── 1/
│   ├── 1.txt
│   ├── 2.txt
│   └── ...
├── 2/
├── ...
└── 104/
```

Each source file is treated as an independent sample.

The original files are retained without modification.

## 4. Preprocessing Architecture

The batch processor reuses the source reader implemented in the previous checkpoint.

### Components

- `src/preprocessing/source_reader.py`
  - Reads source files.
  - Detects supported encodings through decoding attempts.
  - Normalizes line endings.
  - Removes UTF-8 BOM if present.
  - Preserves comments, string literals, identifiers, operators, indentation, and code structure.

- `src/preprocessing/batch_processor.py`
  - Discovers source files recursively.
  - Processes files sequentially.
  - Preserves directory structure.
  - Writes processed source files.
  - Collects statistics.
  - Records file-level errors.
  - Generates the preprocessing report.

### Processing workflow

1. Discover all `.txt` source files.
2. Sort source file paths for deterministic processing order.
3. Compute each file's relative path.
4. Read and normalize the source using `read_source_file()`.
5. Create the corresponding output directory.
6. Write the processed source as UTF-8.
7. Collect processing statistics.
8. Continue processing if an individual file fails.
9. Generate `preprocessing_report.json`.

## 5. Normalization Policy

The following transformations are applied:

| Operation | Description |
|---|---|
| Encoding normalization | Output all successfully decoded files as UTF-8 |
| BOM removal | Remove UTF-8 BOM at the beginning of a file |
| CRLF normalization | Convert Windows line endings to LF |
| CR normalization | Convert standalone CR to LF |
| Content preservation | Preserve comments, string literals, whitespace indentation, and code structure |

The pipeline does not perform:

- Comment removal
- String literal removal
- Identifier renaming
- Code formatting
- Code simplification
- Syntax transformation
- Whitespace trimming
- Source code modification beyond safe normalization

## 6. Encoding Handling

The source reader attempts decoding using the following order:

1. `utf-8-sig`
2. `utf-8`
3. `cp1252`

Decoding uses strict error handling.

If all supported encoding attempts fail, the file is recorded as a failed file and processing continues with the next source file.

Encoding statistics are collected for successfully processed files.

Note: `utf-8-sig` can decode both UTF-8 files with BOM and ordinary UTF-8 files without BOM. Therefore, the reported encoding method does not necessarily indicate that the original file contained a BOM.

## 7. Output Structure

The official preprocessing output is stored in:

```text
data/processed/poj104/
├── source/
│   ├── 1/
│   │   ├── 1.txt
│   │   ├── 2.txt
│   │   └── ...
│   ├── 2/
│   ├── ...
│   └── 104/
└── preprocessing_report.json
```

The problem directory and source filename are preserved.

Each processed file corresponds to its original raw file.

## 8. Error Handling

The batch processor handles file-level errors independently.

When a file cannot be read or decoded:

- The file is counted as failed.
- The error is recorded in the report.
- The file is not written to the processed output.
- Processing continues with the remaining files.

This prevents a single problematic source file from terminating the entire preprocessing process.

## 9. Preprocessing Report

The batch processor generates:

`data/processed/poj104/preprocessing_report.json`

The report includes:

- Total number of files
- Number of successfully processed files
- Number of failed files
- Encoding distribution
- Total original file size
- Total processed file size
- Processing duration
- File-level error details

The report is used for verification and reproducibility.

## 10. Testing

### 10.1 Unit Tests

Test file:

`tests/test_batch_processor.py`

Two tests were executed.

#### Test 1: Successful batch processing

Verified:

- Multiple input files are processed.
- Directory structure is preserved.
- Output files are created.
- Line endings are normalized.
- Report is generated.
- Success statistics are correct.

Result: **PASSED**

#### Test 2: Handling invalid source files

Verified:

- Invalid encoding file is detected.
- Processing does not terminate.
- Valid files are still processed.
- Invalid files are not written to output.
- Error information is recorded.

Result: **PASSED**

Unit test summary:

```text
2 passed
```

### 10.2 Real Dataset – Problem 1

A real dataset test was performed on Problem 1, containing 500 source files.

Results:

| Metric | Result |
|---|---:|
| Total files | 500 |
| Successful files | 500 |
| Failed files | 0 |
| Success rate | 100% |
| Processing time | 3.28 seconds |

Encoding distribution:

| Encoding method | Files |
|---|---:|
| utf-8-sig | 495 |
| cp1252 | 5 |
| Total | 500 |

Result: **PASSED**

### 10.3 Full Dataset Preprocessing

The batch processor was executed on the entire POJ-104 dataset.

| Metric | Result |
|---|---:|
| Total source files | 52,000 |
| Successfully processed | 52,000 |
| Failed files | 0 |
| Success rate | 100% |

Result: **PASSED**

All 52,000 source files were processed successfully.

## 11. Final Results

The preprocessing pipeline successfully processed the complete POJ-104 dataset.

The processed dataset:

- Contains 52,000 source files.
- Preserves the original problem directory structure.
- Preserves original filenames.
- Uses UTF-8 encoding.
- Uses normalized LF line endings.
- Retains comments and string literals.
- Does not modify the raw dataset.
- Has zero failed files in the full preprocessing run.

The batch processor is considered ready for downstream dataset preparation.

## 12. Limitations

Successful decoding and normalization do not guarantee that every source file is syntactically valid C/C++.

Some files may contain unusual code structure, incomplete source code, or syntax errors.

Syntax validation and code parsing will be handled in later preprocessing stages.

The processed dataset is not yet a training dataset. Further stages are required to parse source code, generate sample metadata, construct code pairs, assign labels, and prepare model inputs.

## 13. Reproducibility

Main script:

```text
scripts/run_preprocessing.py
```

To rerun preprocessing from the project root:

```bash
python scripts/run_preprocessing.py
```

The script uses the raw dataset as input and writes the normalized files to the official processed dataset directory.

## 14. Checkpoint Status

**Checkpoint 2.5.3 – Batch Preprocessing: COMPLETED**

- [x] Batch preprocessing design documented
- [x] Batch processor implemented
- [x] Unit tests passed
- [x] Real dataset test on Problem 1 passed
- [x] Full POJ-104 preprocessing completed
- [x] 52,000/52,000 files processed successfully
- [x] Preprocessing report generated

Next checkpoint:

**Checkpoint 2.6 – Metadata & Dataset Manifest**
