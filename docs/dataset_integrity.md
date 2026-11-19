# Dataset Integrity Validation

## 1. Overview

Dataset Integrity Validation is performed after preprocessing and metadata generation to ensure consistency between the original dataset, processed dataset, and metadata manifest.

The validation process is read-only. It does not modify, delete, or overwrite dataset files.

## 2. Objectives

- Verify the number of raw source files.
- Verify the number of processed source files.
- Verify metadata record count.
- Compare file mappings between Raw, Processed, and Metadata.
- Detect missing files and orphan files.
- Detect duplicate sample IDs.
- Confirm dataset consistency before subsequent data preparation stages.

## 3. Dataset Locations

### Raw Dataset

`data/raw/poj104/ProgramData/`

Contains the original POJ-104 source files and remains unchanged.

### Processed Dataset

`data/processed/poj104/source/`

Contains preprocessed source files, normalized to UTF-8 and LF line endings.

### Metadata Manifest

`data/processed/poj104/metadata/samples.csv`

Contains metadata records mapping each sample to its original and processed file paths.

## 4. Expected Dataset Statistics

| Component | Expected Count |
|---|---:|
| Raw source files | 52,000 |
| Processed source files | 52,000 |
| Metadata records | 52,000 |
| Unique sample IDs | 52,000 |
| Duplicate sample IDs | 0 |

POJ-104 contains 104 problem categories, with 500 samples per problem.

## 5. Integrity Checks

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

## 6. Implementation

The integrity validator is implemented in:

`scripts/validate_dataset_integrity.py`

The script uses Python standard library modules:

- `csv` for reading the metadata manifest.
- `pathlib` for filesystem traversal and path comparison.

No additional dependencies are required.

## 7. Execution

Run the validator from the project root:

```bash
python -m scripts.validate_dataset_integrity
```

The script prints dataset counts, integrity check results, detected inconsistencies, and a final PASS or FAIL status.

## 8. Validation Result

**Status: PASS**

The dataset integrity validation completed successfully.

The validation confirmed that the Raw dataset, Processed dataset, and Metadata manifest passed the consistency checks implemented in the validator.

No integrity errors were reported by the validation run.

## 9. Conclusion

Dataset Integrity Validation confirms that the dataset artifacts are consistent according to the implemented checks.

The POJ-104 dataset has completed the following preparation stages:

1. Raw dataset inspection and quality assessment.
2. Source preprocessing.
3. Metadata manifest generation.
4. Metadata validation.
5. Dataset integrity validation.

The dataset is ready to proceed to the next data preparation activity. This validation does not establish semantic correctness of source code or guarantee that the dataset is free of all possible quality issues.
