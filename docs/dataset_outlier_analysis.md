# Dataset Outlier Analysis

## 1. Overview

This checkpoint performs statistical outlier analysis on the POJ-104 processed source code dataset.

The purpose is to identify unusually long source code samples, investigate potential formatting anomalies, and determine whether these samples should be retained for subsequent model training.

Outlier detection is used for dataset analysis only. It does not automatically remove or modify any samples.

## 2. Objectives

- Identify unusually long source code samples.
- Detect potential formatting-related anomalies.
- Inspect representative outliers manually.
- Distinguish genuine long source code from unusual whitespace formatting.
- Preserve potentially valuable training samples.

## 3. Detection Method

The Interquartile Range (IQR) method was used based on source code line counts.

The upper outlier threshold is calculated as:

Upper Bound = Q3 + 1.5 × IQR

Where:

- Q1: First quartile (25th percentile)
- Q3: Third quartile (75th percentile)
- IQR: Interquartile range, calculated as Q3 − Q1

### Dataset thresholds

| Statistic | Value |
|---|---:|
| Q1 | 25 lines |
| Q3 | 43 lines |
| IQR | 18 lines |
| Upper bound | 70 lines |

Samples containing more than 70 lines are classified as outliers for this analysis.

## 4. Implementation

The analysis was implemented in:

` scripts/analyze_dataset_outliers.py `

The script analyzes source code samples and generates:

- Outlier statistics
- Outlier sample records
- Largest samples ranked by line count and file size

## 5. Output Artifacts

Generated reports are stored in:

`data/processed/poj104/audit/`

| Artifact | Description |
|---|---|
| `outlier_analysis.json` | Statistical analysis and outlier summary |
| `outlier_samples.csv` | Samples exceeding the IQR threshold |
| `largest_samples.csv` | Top 20 largest samples |

## 6. Dataset Results

| Metric | Result |
|---|---:|
| Total samples | 52,000 |
| Upper outlier threshold | 70 lines |
| Outlier samples | 2,190 |
| Outlier percentage | 4.2115% |

Approximately 4.21% of the dataset samples were classified as line-count outliers.

## 7. Manual Inspection

Two representative samples were selected for manual investigation.

### 7.1 Sample: `100/1139.txt`

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

### 7.2 Sample: `80/1376.txt`

| Metric | Value |
|---|---:|
| Total lines | 343 |
| Non-empty lines | 343 |
| Blank lines | 0 |
| File size | 14,662 bytes |

All 343 lines contain code. The sample is genuinely long and uses verbose logic with multiple conditional branches and switch-case structures.

**Classification:** Genuine long-code outlier.

The sample is retained because its coding style and implementation structure may be useful for model training.

## 8. Findings

The investigation confirmed that unusually high line counts can have different causes:

1. Formatting anomalies, such as excessive blank lines.
2. Genuine long source code with verbose logic and implementation structures.

Therefore, line-count outliers should not automatically be considered invalid data.

## 9. Data Handling Decision

All detected outliers are retained.

No automatic filtering or source modification is performed during this checkpoint.

The outlier analysis will inform future model design decisions, particularly:

- Tokenization strategy
- Maximum sequence length
- Truncation or chunking strategy
- Handling of excessively long source code
- Potential preprocessing strategies for whitespace

These decisions will be evaluated in later model preparation stages.

## 10. Limitations

The IQR method identifies statistical outliers based on line count, not source code correctness.

The manual investigation covered representative samples, not all 2,190 outliers. Therefore, the findings should not be interpreted as a complete semantic validation of every outlier.

## 11. Status

**Checkpoint 2.7.2.2 – Dataset Outlier Analysis: COMPLETED**

- [x] Statistical outlier detection
- [x] IQR threshold calculation
- [x] Outlier sample export
- [x] Largest sample export
- [x] Manual inspection of representative samples
- [x] Classification of formatting vs. genuine long-code outliers
- [x] Data retention decision
- [x] Documentation completed
