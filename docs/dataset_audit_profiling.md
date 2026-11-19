# Dataset Audit and Statistical Profiling

## 1. Overview

Dataset Audit and Statistical Profiling is performed after dataset integrity validation to understand the statistical characteristics of the POJ-104 processed source dataset.

Integrity validation checks dataset consistency, while profiling examines source size, source length, class distribution, empty files, and exact duplicates.

Profiling is read-only and does not remove or modify samples.

## 2. Objectives

- Analyze source file size distribution.
- Analyze source code line count and character count.
- Verify the distribution of samples across problems.
- Detect empty source files.
- Detect exact duplicate source files using SHA-256.
- Generate a source length histogram for exploratory analysis.

## 3. Implementation

The profiling script is implemented in:

`scripts/profile_dataset.py`

It uses:

- `hashlib` for SHA-256 hashing.
- `statistics` for descriptive statistics.
- `collections.Counter` for problem distribution.
- `matplotlib` for histogram visualization.
- `json` for saving profiling results.

## 4. Output Artifacts

The generated files are stored in:

`data/processed/poj104/audit/`

| File | Description |
|---|---|
| `dataset_profile.json` | Statistical profiling report |
| `source_length_distribution.png` | Histogram of source length in lines |

## 5. Profiling Results

### Dataset Size

- Total samples: 52,000
- Number of problems: 104
- Samples per problem: 500

### File Size (Bytes)

| Metric | Value |
|---|---:|
| Minimum | 76 |
| Maximum | 14,662 |
| Mean | 589.72 |
| Median | 495 |

### Source Line Count

| Metric | Value |
|---|---:|
| Minimum | 1 |
| Maximum | 1,302 |
| Mean | 36.26 |
| Median | 33 |

### Source Character Count

| Metric | Value |
|---|---:|
| Minimum | 76 |
| Maximum | 14,662 |
| Mean | 589.69 |
| Median | 495 |

### Empty Files

- Count: 0

### Exact Duplicates

- Duplicate groups: 5
- Files involved in duplicate groups: 10

## 6. Observations

1. The dataset contains 52,000 samples distributed evenly across 104 problems.
2. The mean source length is slightly greater than the median, indicating that longer samples influence the mean.
3. The longest source contains 1,302 lines, significantly longer than the median source length of 33 lines.
4. No empty source files were detected.
5. Five exact duplicate groups involving ten files were detected using SHA-256.

Exact duplicates are not automatically removed at the profiling stage. Their impact will be considered when designing pair generation and evaluation splitting to prevent data leakage and inappropriate negative pairs.

## 7. Execution

Run the profiling script from the project root:

```bash
python -m scripts.profile_dataset
```

The script saves the JSON report and histogram and prints summary statistics.

## 8. Validation Status

**Status: COMPLETED**

The profiling script executed successfully on the processed POJ-104 dataset. The report and histogram were generated.

## 9. Conclusion

Statistical profiling provides a baseline understanding of the processed dataset before pair construction and model training.

The profiling results are descriptive only. They do not establish semantic quality or justify automatic sample removal.

The dataset remains unchanged after profiling.
