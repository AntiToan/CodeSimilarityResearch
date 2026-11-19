# Metadata & Dataset Manifest – POJ-104

## 1. Overview

This activity implements metadata generation and validation for the preprocessed POJ-104 dataset.

The metadata manifest provides a structured index of source code samples. It serves as the foundation for subsequent dataset construction, code pair generation, labeling, dataset splitting, model training, and evaluation.

Each source file is represented by one metadata record.

## 2. Objectives

- Generate metadata for all POJ-104 source files.
- Assign stable and unique sample IDs.
- Record problem IDs and source file information.
- Link raw source files with their processed counterparts.
- Record processed file sizes and preprocessing status.
- Use portable relative paths.
- Validate manifest integrity.
- Ensure all metadata records correspond to existing raw and processed files.

## 3. Dataset Overview

| Property | Value |
|---|---:|
| Dataset | POJ-104 |
| Language | C/C++ |
| Total samples | 52,000 |
| Number of problems | 104 |
| Samples per problem | 500 |
| Processed samples | 52,000 |
| Failed preprocessing samples | 0 |

## 4. Metadata Schema

The manifest contains the following fields.

| Field | Type | Description |
|---|---|---|
| `sample_id` | String | Stable unique identifier for a source sample |
| `problem_id` | String | POJ-104 problem identifier |
| `filename` | String | Original source filename |
| `language` | String | Programming language identifier |
| `source_path` | String | Relative path to processed source |
| `original_path` | String | Relative path to raw source |
| `file_size_bytes` | Integer | Processed source file size in bytes |
| `status` | String | Metadata processing status |

### Example record

```csv
sample_id,problem_id,filename,language,source_path,original_path,file_size_bytes,status
poj104_1_1,1,1.txt,cpp,source/1/1.txt,ProgramData/1/1.txt,523,success
```

The file size shown above is an illustrative example.

## 5. Sample ID Design

Sample IDs are generated deterministically using the following pattern:

```text
poj104_<problem_id>_<filename_without_extension>
```

Examples:

```text
poj104_1_1
poj104_1_2
poj104_2_1
poj104_104_500
```

This design ensures that IDs remain stable across repeated metadata generation runs, provided the source dataset structure remains unchanged.

## 6. Path Design

Metadata uses relative paths instead of absolute machine-specific paths.

### Processed source path

```text
source/1/1.txt
```

### Original source path

```text
ProgramData/1/1.txt
```

Relative paths improve portability across different machines and environments.

Paths can be resolved using the project dataset root directories.

## 7. Metadata Generator

Implementation file:

```text
src/data/metadata_generator.py
```

The generator performs the following operations:

1. Discover raw `.txt` source files recursively.
2. Sort the source paths for deterministic iteration.
3. Extract the problem ID from the relative directory path.
4. Extract the original filename and filename stem.
5. Generate a stable sample ID.
6. Locate the corresponding processed source file.
7. Determine processing status.
8. Calculate processed file size.
9. Write metadata records into a CSV file.
10. Return summary statistics.

### Output

```text
data/processed/poj104/metadata/samples.csv
```

## 8. Manifest Structure

```text
data/processed/poj104/
├── source/
│   ├── 1/
│   ├── 2/
│   ├── ...
│   └── 104/
├── metadata/
│   └── samples.csv
└── preprocessing_report.json
```

The CSV file contains one record for each source code sample.

## 9. Metadata Validation

Implementation file:

```text
scripts/validate_metadata.py
```

The validator checks:

- Total sample count
- Sample ID uniqueness
- Number of problem IDs
- Samples per problem
- Preprocessing status
- Required fields
- File size validity
- Existence of processed source files
- Existence of original raw files

### Expected constraints

| Validation rule | Expected value |
|---|---:|
| Total samples | 52,000 |
| Unique sample IDs | 52,000 |
| Unique problems | 104 |
| Samples per problem | 500 |
| Failed samples | 0 |
| Duplicate sample IDs | 0 |
| Empty required fields | 0 |
| Invalid file sizes | 0 |
| Missing processed files | 0 |
| Missing raw files | 0 |

## 10. Testing

### 10.1 Unit Test

Test file:

```text
tests/test_metadata_generator.py
```

The unit test verifies:

- Metadata generation from a small synthetic dataset.
- Successful and failed sample handling.
- Stable sample ID format.
- Field values.
- File size recording.
- Relative path behavior.
- CSV output correctness.

Result:

**PASSED**

### 10.2 Full Dataset Generation

The metadata generator was executed on the complete POJ-104 dataset.

| Metric | Result |
|---|---:|
| Total samples | 52,000 |
| Successful | 52,000 |
| Failed | 0 |

Result:

**PASSED**

### 10.3 Full Dataset Validation

The validation script was executed against the generated manifest.

| Check | Result |
|---|---|
| Total samples | PASS |
| Unique sample IDs | PASS |
| Unique problems | PASS |
| Samples per problem | PASS |
| Failed samples | PASS |
| Duplicate sample IDs | PASS |
| Empty required fields | PASS |
| Invalid file sizes | PASS |
| Missing processed files | PASS |
| Missing raw files | PASS |

Final validation result:

```text
VALIDATION PASSED
All metadata integrity checks passed.
```

## 11. Debugging Record

During full metadata validation, the first generated manifest reported:

- 52,000 failed samples.
- 52,000 invalid file sizes.
- No missing processed files.
- No missing raw files.

The investigation revealed that the processed dataset directory had been incorrectly configured as:

```text
dataprocessed/poj104/source
```

instead of:

```text
data/processed/poj104/source
```

As a result, the generator checked the wrong directory and incorrectly marked every sample as failed.

### Resolution

The `PROCESSED_DIR` declaration in the metadata generation script was corrected.

The metadata generator was executed again to regenerate the manifest.

The validation process was repeated and passed all integrity checks.

The processed source files were not modified or regenerated during this debugging process.

## 12. Reproducibility

### Generate metadata

```bash
python -m scripts.generate_metadata
```

### Validate metadata

```bash
python -m scripts.validate_metadata
```

The metadata generator can be rerun without repeating preprocessing.

## 13. Limitations

The manifest currently records file-level metadata only.

It does not contain:

- Code similarity labels
- Pairwise sample relationships
- AST features
- Token sequences
- Embeddings
- Train/validation/test assignments

These will be generated in subsequent dataset preparation stages.

The `status` field indicates whether the processed file exists and was recognized by the metadata generator. It does not guarantee syntactic validity or semantic correctness of the source code.

## 14. Final Status

**Checkpoint 2.6 – Metadata & Dataset Manifest: COMPLETED**

- [x] Metadata schema designed
- [x] Stable sample ID scheme defined
- [x] Metadata generator implemented
- [x] Unit test passed
- [x] Full dataset metadata generated
- [x] 52,000 records generated
- [x] 104 problems represented
- [x] 500 samples per problem
- [x] Relative paths used
- [x] Metadata validation implemented
- [x] Full metadata validation passed
- [x] Path bug identified and resolved
- [x] Documentation completed

Next checkpoint: **Checkpoint 2.7 – Dataset Preparation for Code Similarity Pairs**
