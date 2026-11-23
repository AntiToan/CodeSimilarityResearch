# Batch Preprocessing Design – POJ-104

## 1. Objective

This document defines the batch preprocessing strategy for processing all 52,000 source files in the POJ-104 dataset.

The batch processor will reuse the source reader implemented in Checkpoint 2.5.2.

## 2. Processing Strategy

The project will initially use sequential batch processing.

Each source file will be processed independently to ensure:
- Simple error handling.
- Reproducible results.
- Easy debugging.
- No interruption of the entire batch when one file fails.

Multiprocessing may be considered in future optimization stages.

## 3. Input and Output

**Input:**

`data/raw/poj104/ProgramData/`

**Output:**

`data/processed/poj104/source/`

The original problem directory and filename must be preserved.

Example:

| Raw Path | Processed Path |
|---|---|
| `ProgramData/26/345.txt` | `source/26/345.txt` |
| `ProgramData/62/593.txt` | `source/62/593.txt` |

## 4. Batch Processing Workflow

1. Discover all `.txt` source files recursively.
2. Determine each file's relative path.
3. Read the source using `read_source_file()`.
4. Normalize source text according to the preprocessing policy.
5. Create the corresponding output directory.
6. Save the processed source using UTF-8.
7. Record the processing result.
8. Continue to the next file.
9. Generate a batch processing report.

## 5. Error Handling

If a file cannot be read or decoded:
- Record its path and error message.
- Mark it as failed.
- Continue processing the remaining files.
- Never modify or delete the original file.

## 6. Output Management

The processor must:
- Create missing output directories automatically.
- Preserve problem IDs and original filenames.
- Overwrite existing processed files when rerunning the pipeline.
- Avoid modifying files under the raw dataset directory.

## 7. Processing Statistics

The batch report will include:

- Total discovered files.
- Successful files.
- Failed files.
- Encoding distribution.
- Total original file size.
- Total processed file size.
- Processing duration.

Detailed per-file metadata will be implemented in Checkpoint 2.6.

## 8. Validation Requirements

The batch processor must satisfy the following conditions:

1. Every discovered file has a recorded processing result.
2. Successful files have corresponding processed outputs.
3. Failed files are recorded with error details.
4. Output paths preserve the original directory structure.
5. Processed files can be decoded using UTF-8.
6. Raw files remain unchanged.
7. The batch report accurately reflects the processing results.

## 9. Future Reusability

The source reader and normalization logic should remain independent of POJ-104 directory structure.

This allows the same preprocessing functionality to be reused for source files uploaded through the teacher-facing web application.

---

**Status:** Design completed  
**Stage:** Dataset – Checkpoint 2.5.3.1  
**Next:** Checkpoint 2.5.3.2 – Implement Batch Processor

---

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


---

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


---

# Negative Pair Strategy Design

## 1. Overview

This document defines the strategy for generating negative code similarity pairs for the CodeSimilarityResearch project using POJ-104.

Negative pairs are constructed from different original source samples selected under controlled sampling and filtering rules.

This checkpoint is design-only. No negative pairs are generated yet.

## 2. Objective

The objective is to generate negative training candidates that represent code samples with low similarity while minimizing false negative labels.

Negative labels are heuristic/synthetic and must not be interpreted as ground-truth plagiarism judgments.

## 3. Negative Pair Definition

A negative pair consists of two different original source code samples selected under the initial negative sampling strategy.

**Label convention:** `0` = negative pair.

Different problem IDs are used as an initial selection criterion, but different problem IDs alone do not guarantee that two code samples are unrelated.

## 4. Initial Sampling Strategy

### 4.1 Cross-problem sampling

The initial negative pair strategy uses samples from different problem IDs.

Candidate pairs must satisfy:

- Different original sample IDs.
- Different problem IDs.
- No shared source lineage.
- No known exact-duplicate relationship.
- No duplicate pair records.

Cross-problem sampling is used to reduce the likelihood of selecting code solutions with similar problem-specific logic.

### 4.2 Same-problem sampling

Same-problem negative sampling is excluded from the initial strategy.

Samples solving the same problem may share algorithmic logic, structure, or implementation patterns despite being independently written. They may be useful in future hard-negative experiments, but they are not included in the initial negative pair generation.

## 5. Duplicate and Lineage Exclusion

Negative candidates must exclude:

- Exact duplicate samples.
- Original and variant pairs from the same lineage.
- Variants derived from the same original sample.
- Known duplicate relationships identified during dataset auditing.

The previously identified exact duplicate groups, including duplicate relationships across problem IDs, must be considered during candidate filtering.

Whitespace-normalized content may be used as part of duplicate screening.

## 6. Similarity Screening

Cross-problem pairs are treated as negative candidates rather than automatically accepted negatives.

A similarity screening stage is proposed to identify pairs with suspiciously high similarity.

Possible screening methods for future implementation include:

- Token similarity.
- Jaccard similarity over tokens or shingles.
- Edit-distance-based similarity.
- AST-based similarity in a future research stage.

Candidates with suspicious similarity should be excluded from the initial negative set or retained for a separate review process.

The screening method and threshold are not defined in this checkpoint.

## 7. Sampling Strategy

Negative pair generation must use controlled sampling.

Requirements:

- Avoid exhaustive Cartesian pair generation.
- Limit the number of negative pairs generated per original sample.
- Avoid duplicate pairs.
- Use deterministic random seeds for reproducibility.
- Consider pair balance in a separate dataset balancing checkpoint.

The exact number of negative pairs per sample and positive-to-negative ratio remain undecided.

## 8. Data Leakage Prevention

Original samples must be split into train, validation, and test partitions before pair generation.

Pair generation must operate within each partition independently.

The same original source sample or its derived variants must not cross partitions.

Randomly splitting pair records independently is prohibited because it can allow the same original source code to appear across training and evaluation partitions.

## 9. Label Interpretation

Negative labels represent heuristic/synthetic negative relationships generated according to sampling and filtering rules.

Label `0` does not prove that two programs are completely unrelated or that plagiarism is absent.

Different problem IDs are a selection signal, not definitive evidence of dissimilarity.

The dataset is intended for code similarity model training and evaluation, not definitive plagiarism adjudication.

## 10. Initial Decisions

| Decision | Status |
|---|---|
| Cross-problem negative sampling | Accepted |
| Same-problem negative sampling | Excluded from initial strategy |
| Exact duplicate exclusion | Required |
| Same-lineage exclusion | Required |
| Whitespace-normalized duplicate screening | Accepted |
| Similarity screening | Required in strategy; implementation deferred |
| Suspicious candidates | Exclude or review |
| Deterministic sampling | Required |
| Unlimited negative pair generation | Rejected |
| Pair generation before source splitting | Rejected |
| Split originals before pair generation | Required |
| Label 0 interpretation | Synthetic/heuristic negative |

## 11. Scope of This Checkpoint

This checkpoint defines the negative pair strategy only.

It does not implement:

- Negative pair generation.
- Similarity screening.
- Sampling limits.
- Pair balancing.
- Label generation.
- Train/validation/test splitting.

These implementation decisions will be addressed in later checkpoints.

## 12. Status

**Checkpoint 2.7.3.2 – Negative Pair Strategy Design: COMPLETED**

- [x] Negative pair definition
- [x] Cross-problem sampling strategy
- [x] Same-problem exclusion for initial strategy
- [x] Duplicate exclusion rules
- [x] Lineage exclusion rules
- [x] Similarity screening strategy
- [x] Sampling reproducibility
- [x] Data leakage prevention
- [x] Synthetic label interpretation


---

# Label Balance Strategy

## 1. Objective

This checkpoint defines the label balancing strategy for the code similarity pair dataset. The objective is to reduce class imbalance between positive and negative pairs while preserving pair validity, diversity, and reproducibility.

## 2. Label Definition

- Label 1: Positive pair — two code samples considered similar according to the defined positive pair generation strategy.
- Label 0: Negative pair — two code samples considered dissimilar according to the defined negative pair generation strategy.

## 3. Target Label Ratio

The primary dataset targets a 1:1 ratio between positive and negative pairs.

| Label | Target proportion |
|---|---:|
| Positive (1) | 50% |
| Negative (0) | 50% |

This ratio is the target for the balanced dataset, not a requirement to generate invalid pairs to achieve it.

## 4. Balancing Rule

Let:

- P = number of valid positive pairs available.
- N = number of valid negative pairs available.

The balancing quota is:

Q = min(P, N)

The final balanced dataset will contain:

- Q positive pairs
- Q negative pairs

The total dataset size will therefore be 2Q.

## 5. Excess Pair Handling

When one class contains more valid pairs than the other:

- The excess pairs will not be deleted from the original candidate pool.
- Only the required quota will be selected for the primary balanced dataset.
- Excess pairs may be retained for future experiments involving alternative sampling or balancing strategies.

## 6. Insufficient Pair Handling

If one class does not contain enough valid pairs:

- The final dataset size will be reduced according to the smaller class.
- No invalid pairs will be introduced to meet the target quota.
- No default oversampling will be applied.
- Pair validity and quality take priority over dataset size.

## 7. Reproducibility

Balancing must be deterministic and reproducible.

- A fixed random seed will be used when selecting pairs from an excess class.
- The selected pairs must be reproducible using the same candidate pool and seed.
- Balancing statistics must be recorded.

## 8. Reporting Requirements

The balancing process must report:

- Positive pair count before balancing.
- Negative pair count before balancing.
- Number of positive pairs selected.
- Number of negative pairs selected.
- Number of excess pairs retained outside the balanced dataset.
- Final label distribution.
- Random seed used for selection.

## 9. Constraints

- Pair validity must not be compromised for balancing.
- No pair may cross train, validation, or test splits.
- Duplicate pairs must not be introduced.
- Balancing must not modify or delete original source code or candidate records.
- The balanced dataset must maintain a 1:1 label ratio whenever both classes contain valid candidates.

## 10. Expected Outcome

The primary pair dataset will have equal positive and negative pair counts, reducing label imbalance and providing a consistent baseline for model training and evaluation.

This checkpoint defines the strategy only. Pair selection and balancing implementation will be conducted in a later checkpoint.


---

# Balance Constraints & Trade-offs

## 1. Objective

This checkpoint defines the constraints, priorities, and trade-offs applied during pair dataset balancing.

The goal is to preserve pair validity, dataset integrity, and diversity while maintaining reasonable label and problem distributions.

## 2. Priority Order

Pair selection follows this priority order:

1. Pair validity and dataset integrity.
2. Pair diversity.
3. Label balance.
4. Problem distribution balance.

Higher-priority constraints must not be violated to satisfy lower-priority balancing objectives.

## 3. Mandatory Constraints

The following conditions are mandatory:

- Positive and negative pairs must follow their respective generation rules.
- Negative pairs must come from different problems.
- Negative pairs must not share source lineage.
- Duplicate pairs must not be included.
- No pair may cross train, validation, or test splits.
- Original source files and candidate records must not be modified or deleted by balancing.
- Pair validity must not be compromised to achieve a target dataset size.

## 4. Soft Constraints

The following objectives are soft constraints:

- Positive-to-negative ratio of 1:1.
- Relatively uniform distribution across the 104 problems.
- Source appearance frequency.
- Negative endpoint diversity.

These objectives should be pursued whenever feasible but must not override mandatory constraints.

## 5. Source Frequency Control

A source may appear in multiple valid pairs. However, excessive source reuse can reduce dataset diversity and increase the risk of source-specific bias.

The balancing process must:

- Track pair appearances per sample ID.
- Monitor sources with unusually high appearance frequencies.
- Prefer less frequently used sources when competing candidates are equally valid.
- Avoid setting a hard source appearance cap before actual pair distribution is audited.

A source frequency cap may be considered in a future experiment if empirical evidence justifies it.

## 6. Insufficient Candidate Handling

When the available valid candidates cannot satisfy a balancing target:

1. Search remaining valid candidates within the defined sampling constraints.
2. Perform bounded resampling if applicable.
3. Record the unmet quota and its reason.
4. Accept a smaller dataset when valid candidates remain insufficient.

Invalid candidates must not be introduced to meet a quota.

## 7. Balancing Trade-offs

The project accepts the following trade-offs:

- A smaller dataset is acceptable when valid candidates are insufficient.
- Imperfect label balance is acceptable when the available valid pairs are limited.
- Imperfect problem balance is acceptable when a problem has insufficient valid candidates.
- Pair diversity is preferred over excessive reuse of the same source.
- Pair validity and integrity take priority over all balancing objectives.

## 8. Audit and Reporting

The balancing process must report:

- Pair counts before and after filtering.
- Pair counts before and after balancing.
- Positive and negative counts.
- Duplicate pairs removed.
- Problem-level distribution.
- Source appearance frequency.
- Sampling seed and configuration.
- Unmet quotas.
- Reasons for constraints or targets not being satisfied.

## 9. Reproducibility

Balancing must be reproducible using the recorded candidate pool, configuration, and random seed.

All sampling and balancing decisions must be traceable through the generated reports.

## 10. Expected Outcome

The final pair dataset should prioritize validity, integrity, and diversity while maintaining a balanced label distribution and broad problem coverage where feasible.

This checkpoint defines constraints and trade-offs only. Implementation will be performed in a later checkpoint.


---

# Design Closure & Implementation Readiness

**Project:** CodeSimilarityResearch  
**Phase:** Phase 2 — Dataset & Pair Generation Design  
**Status:** Design Closure Draft  
**Scope:** Reconciliation of Phase 2.5, 2.6, 2.7 designs and implementation readiness

---

## 1. Purpose & Scope

This document consolidates the approved Pair Dataset, Variant Generation, Pair Sampling, Validation, and Pipeline Orchestration designs into a consistent implementation baseline.

The purpose is to:

- Consolidate all previously approved design decisions.
- Resolve implementation-level inconsistencies between design documents.
- Define canonical contracts for source splitting, variants, candidates, selection, and exports.
- Identify parameters that require pilot calibration before full-scale generation.
- Establish implementation order and readiness criteria.

This document does not redesign previously approved pair-generation logic.

### Scope

Included:

- Source-level split assignment.
- Duplicate leakage prevention.
- Variant generation quantity and transformation distribution.
- Negative pair screening.
- Quota shortage handling.
- Validation tooling and preflight.
- Pair candidate assembly and selection.
- Output artifact consistency.
- Implementation dependencies and acceptance criteria.

Excluded:

- Model architecture.
- Model training.
- Model evaluation methodology beyond dataset readiness.
- Semantic plagiarism detection.
- Full execution-based program equivalence.
- Automated detection and grouping of unverified near-duplicates.

---

## 2. Decision Registry

### 2.1 Source Split Strategy — LOCKED

| Parameter | Decision |
|---|---|
| Split level | Source-level |
| Strategy | Stratified by problem |
| Train | 80% |
| Validation | 10% |
| Test | 10% |
| Seed | Fixed, configurable |
| Split timing | Before variant and pair generation |
| Variant split | Inherited from original |
| Pair split | Both endpoints must belong to the same split |

For the current POJ-104 dataset, each problem contains approximately 500 sources.

Target distribution per problem:

| Split | Target source count |
|---|---:|
| Train | 400 |
| Validation | 50 |
| Test | 50 |

Expected overall target:

| Split | Target source count |
|---|---:|
| Train | 41,600 |
| Validation | 5,200 |
| Test | 5,200 |
| Total | 52,000 |

These counts are targets. Duplicate-group constraints may cause small deviations.

### 2.2 Duplicate Leakage Policy — LOCKED

- Original sources are preserved.
- Exact duplicates are not removed.
- Identified exact-duplicate groups must be assigned to the same split.
- Duplicate groups spanning different problems must remain together.
- Unverified near-duplicates are not automatically grouped.
- Duplicate grouping is used for split integrity, not positive-pair generation.
- Duplicate sources are not automatically considered plagiarism or positive pairs.

Integrity takes priority over exact split proportions.

### 2.3 Variant Generation Quantity — LOCKED

| Parameter | Value |
|---|---|
| Target accepted variants per original | 2 |
| Maximum accepted variants per original | 2 |
| Attempts per variant target | 5 |
| Variant origin | Original only |
| Variant chaining | Not allowed |
| Duplicate output | Reject |
| Failed validation | Reject |
| Quota shortage | Accept partial generation |

The pipeline does not relax validation to reach the target.

### 2.4 Transformation Distribution — LOCKED

Baseline transformation types:

- Whitespace
- Formatting
- Comments

Distribution:

| Transformation | Probability |
|---|---:|
| Whitespace | Approximately 1/3 |
| Formatting | Approximately 1/3 |
| Comments | Approximately 1/3 |

For two variants per original:

- Prefer distinct transformation types.
- Select eligible transformation pairs uniformly.
- Use sampling without replacement.
- If a transformation is not eligible, remove it from the candidate set.
- Do not force an ineligible transformation.
- No adaptive probability adjustment in baseline.

### 2.5 Negative Pair Screening — LOCKED, THRESHOLD PILOT REQUIRED

| Parameter | Decision |
|---|---|
| Metric | Token Jaccard similarity |
| Threshold | 0.85 initial |
| Score ≥ 0.85 | Reject candidate |
| Score < 0.85 | Pass screening |
| Tokenization failure | Fail closed |
| Calibration | Required pilot |

Passing screening does not prove that the candidate is a valid negative pair.

The threshold 0.85 is an initial design value and must be evaluated during pilot calibration before full-scale generation.

### 2.6 Quota Shortage Policy — LOCKED

- Flexible quota.
- Keep valid candidates.
- No oversampling.
- No bypassing validation.
- No cross-split compensation.
- Balance positive and negative pairs independently within each split.
- Select the smaller available label pool when feasible.
- Quota shortage produces warnings and reports.
- A split with no valid pairs for one label is a quality failure.
- Integrity violations are critical failures.

Priority hierarchy:

**Pair integrity > Label validity > Leakage prevention > Diversity > Balance > Quantity**

### 2.7 Validation Tooling — LOCKED, PILOT REQUIRED

| Layer | Requirement |
|---|---|
| V1 | Structural validation |
| V2 | Transformation-specific validation |
| V3 | Syntax validation |
| V4 | Semantic evidence, optional for baseline |

Baseline accepted variants require V1, V2, and V3 to pass.

Proposed baseline tools:

- Tree-sitter C++ parser.
- Clang syntax-only validation.
- GNU C++17 as the initial compiler standard to test.
- Parser timeout: 3 seconds per file.
- Compiler timeout: 10 seconds per file.
- No executable generation.
- No source execution.

Tool availability and environment failures must not be misclassified as source syntax failures.

---

## 3. Source Split Contract

### 3.1 Split Timing

Source split must be completed before:

1. Variant generation.
2. Positive pair generation.
3. Negative pair generation.
4. Candidate assembly.
5. Final pair selection.

Split assignments must be persisted and treated as immutable inputs for a generation run.

### 3.2 Split Assignment Strategy — PROPOSED

Use deterministic group-aware stratified assignment.

Assignment units:

- Non-duplicate source: one source assignment unit.
- Exact duplicate group: one group assignment unit containing all known duplicates.

The assignment algorithm should:

1. Load all original source metadata.
2. Load verified exact-duplicate groups.
3. Construct atomic assignment groups.
4. Assign groups to Train, Validation, or Test.
5. Minimize deviations from 80/10/10 overall and per problem where feasible.
6. Never split a duplicate group to satisfy target proportions.
7. Record deviations caused by group constraints.
8. Verify every original source is assigned exactly once.

Duplicate groups spanning multiple problem IDs may cause local problem proportions to deviate.

### 3.3 Split Assignment Artifact — PROPOSED

Canonical source split registry:

`data/processed/poj104/metadata/source_splits.csv`

Proposed fields:

- `sample_id`
- `problem_id`
- `split`
- `split_seed`
- `split_method`
- `duplicate_group_id`
- `split_version`

Requirements:

- One record per original source.
- All original sources must be assigned.
- No duplicate sample assignments.
- All samples belonging to a verified duplicate group share a split.
- Variants inherit split from their original source.
- Pair endpoints must share the same split.

### 3.4 Split Validation

The split validator must check:

- Missing source assignments.
- Invalid split names.
- Duplicate sample assignments.
- Duplicate groups crossing splits.
- Incorrect problem-level proportions.
- Reproducibility with the same seed and input.
- Assignment coverage for the entire original dataset.

---

## 4. Variant Generation Contract

### 4.1 Variant Quantity

Target:

- Two accepted variants per original.

Maximum:

- Two accepted variants per original.

Retry limit:

- Five attempts per variant target.

### 4.2 Variant Creation

- Variants must be created directly from the original source.
- Variant-to-variant chaining is prohibited.
- Each baseline variant uses one transformation type.
- Original sources remain immutable.
- Variant IDs are deterministic according to the approved variant ID design.
- Variant split is inherited from original source.

### 4.3 Eligible Transformations

Baseline:

- Whitespace.
- Formatting.
- Comments.

Transformation distribution is uniform among eligible transformations.

For two variants:

- Prefer different transformation types.
- Use uniform selection among eligible transformation pairs.
- Use sampling without replacement.
- Reject outputs that are unchanged or duplicate an existing output.

### 4.4 Validation and Acceptance

A variant may be accepted only if:

- Output exists.
- Output is non-empty.
- Metadata is valid.
- Transformation is supported.
- Transformation-specific validation passes.
- Syntax validation passes.
- No duplicate variant output is detected.
- Required validation tooling is available.

Generation must not bypass validation to meet quantity targets.

### 4.5 Partial Generation

If a source produces fewer than two accepted variants:

- Preserve the original.
- Preserve accepted variants.
- Record failed attempts and reasons.
- Do not force additional transformations beyond retry limits.
- Do not treat rejected variants as positive data.

---

## 5. Negative Screening Contract

### 5.1 Metric

Token Jaccard similarity:

\[
J(A,B)=\frac{|T_A\cap T_B|}{|T_A\cup T_B|}
\]

Where:

- \(T_A\) and \(T_B\) are unique token sets.
- The result ranges from 0 to 1.

### 5.2 Threshold

Initial threshold:

`0.85`

Decision rule:

- Score >= 0.85: Reject as suspiciously similar.
- Score < 0.85: Pass screening.
- Tokenization error: Reject or fail candidate with a recorded error.

### 5.3 Tokenization and Normalization — PROPOSED

Use a C++-aware tokenizer rather than simple regex-based token extraction.

Normalization should:

- Remove comments correctly.
- Ignore whitespace and formatting.
- Preserve identifiers.
- Preserve numeric and string literals.
- Preserve operators.
- Avoid altering original source files.

Similarity is computed using unique token sets, not token frequency.

### 5.4 Screening Records

Each screening result should record:

- Candidate ID or pair ID.
- `sample_a_id`.
- `sample_b_id`.
- Metric name.
- Similarity score.
- Threshold.
- Screening status.
- Screening implementation version.
- Error reason if screening failed.

### 5.5 Calibration

Before full generation:

1. Select a representative sample of negative candidates.
2. Compute screening scores.
3. Review high-similarity and borderline candidates.
4. Measure candidate rejection rate.
5. Review whether the threshold rejects too many legitimate negatives.
6. Record calibration results.
7. Approve the threshold for the full run.

The threshold must not be changed silently.

---

## 6. Pair Assembly, Selection & Balancing Contract

### 6.1 Positive Pair Definition

Authoritative positive pair definition:

- Original source + accepted variant from the same lineage.
- Label = 1.
- Pair type = `positive`.
- Both endpoints must belong to the same split.

Baseline does not generate variant–variant positive pairs.

Each accepted variant may produce at most one original–variant positive pair.

### 6.2 Negative Pair Definition

Negative pair candidates must:

- Use original sources only.
- Have different problem IDs.
- Have different lineages.
- Not be known exact duplicates.
- Pass similarity screening.
- Pass candidate validation.
- Belong to the same split.

Label = 0.

Negative labels are synthetic labels derived from the generation rules. They are not ground-truth plagiarism annotations.

### 6.3 Candidate Assembly

Candidate assembly must:

1. Load positive and negative candidate pools.
2. Validate schemas and source references.
3. Verify split membership.
4. Canonicalize pair identity.
5. Reject self-pairs.
6. Deduplicate candidates.
7. Detect conflicting labels.
8. Validate pair rules.
9. Produce an assembled candidate pool.
10. Generate candidate assembly reports.

Candidate assembly does not perform final balancing or selection.

### 6.4 Canonical Pair Identity

- Pair identity is independent of label.
- Source IDs are sorted canonically.
- A–B and B–A represent the same pair.
- Self-pairs are forbidden.
- Duplicate identities are consolidated.
- Conflicting labels for one pair identity are critical errors.

### 6.5 Final Selection

Selection is performed independently for each split.

For split \(s\):

\[
Q_s=\min(P_s,N_s)
\]

Where:

- \(P_s\) is the valid positive candidate count.
- \(N_s\) is the valid negative candidate count.
- \(Q_s\) is the selected count per label.

Selection priorities:

1. Pair integrity.
2. Label validity.
3. Leakage prevention.
4. Endpoint diversity.
5. Label balance.
6. Problem distribution.

Do not oversample.

Do not transfer pairs between splits.

Do not generate new pairs during final selection.

If candidates are insufficient, use the maximum feasible valid count and record the shortage.

### 6.6 Final Validation

Final validation must verify:

- Schema validity.
- Source references exist.
- No self-pairs.
- No duplicate pair identities.
- No conflicting labels.
- Correct pair type and label.
- Same-split endpoints.
- No source-level split leakage.
- Positive pairs satisfy lineage rules.
- Negative pairs satisfy cross-problem and screening rules.
- Selected pairs originate from assembled candidates.
- Split index files match the master pair index.
- Counts and reports are accurate.

---

## 7. Canonical Output Layout — PROPOSED

This layout harmonizes the output paths proposed in the earlier pair generation and orchestration designs.

```text
data/
├── processed/
│   └── poj104/
│       ├── source/
│       ├── variants/
│       └── metadata/
│           ├── samples.csv
│           ├── source_splits.csv
│           ├── variants.csv
│           └── variant_validation.csv
│
└── pairs/
    ├── candidates/
    │   └── assembled_candidates.csv
    │
    ├── pair_index.csv
    │
    ├── splits/
    │   ├── train.csv
    │   ├── validation.csv
    │   └── test.csv
    │
    └── reports/
        ├── generation_report.json
        ├── split_report.json
        ├── variant_report.json
        ├── screening_report.json
        ├── assembly_report.json
        ├── selection_report.json
        └── final_validation_report.json

configs/
└── pair_generation_config.json
```

### 7.1 Artifact Roles

#### `candidates/assembled_candidates.csv`

Contains validated assembled candidates before final selection and balancing.

It is an intermediate artifact, not the final training/evaluation dataset.

#### `pair_index.csv`

Canonical master index for selected final pairs.

This is the authoritative final pair dataset.

It contains full pair records according to the approved pair schema.

#### `splits/train.csv`, `validation.csv`, `test.csv`

Split index files contain `pair_id` references to the canonical master pair index.

They do not duplicate the full pair records.

### 7.2 Output Consistency Rules

- The master pair index is authoritative.
- Split files are indexes into the master pair index.
- Every selected pair belongs to exactly one split.
- Split files must not contain pair IDs absent from the master index.
- Intermediate candidates must not be confused with final selected pairs.
- Previous design output paths must be reconciled to this layout during implementation.

---

## 8. Validation Preflight & Pilot Requirements

Full-scale generation must not begin until preflight and pilot checks pass.

### 8.1 Environment Preflight

Verify:

- Python environment.
- Required dependencies.
- Tree-sitter C++ parser availability.
- Clang availability.
- Compiler version.
- Compiler flags.
- C++ language standard.
- Input dataset integrity.
- Metadata consistency.
- Split registry consistency.
- Output directory permissions.
- Config validity.

If required tooling is unavailable, the run must stop before batch generation.

Environment errors must not be classified as source syntax failures.

### 8.2 Pilot Sample

Pilot generation should use a reproducible sample covering:

- Multiple problem IDs.
- Short source files.
- Long source files.
- Sources with comments.
- Sources with minimal formatting.
- Sources with unusual but valid structures.
- Sources previously identified as outliers where feasible.

Pilot must measure:

- Variant generation success rate.
- Transformation distribution.
- Validation pass/reject rate.
- Parser compatibility.
- Compiler compatibility.
- Runtime per transformation.
- Runtime per validation stage.
- Timeout rate.
- Negative screening distribution.
- Negative candidate rejection rate.
- Pair candidate shortage.
- Duplicate detection effectiveness.

### 8.3 Pilot Acceptance

Pilot acceptance criteria:

- No original source modified.
- Variants have valid lineage.
- Split inheritance is correct.
- Required validators operate successfully.
- Environment failures are distinguishable from source failures.
- Transformation-specific validators detect invalid output.
- Generation is deterministic under the same seed/config/tool versions.
- Reports contain sufficient information to audit.
- Runtime is measured and practical for full-scale processing.

Threshold calibration must be reviewed before the full negative candidate generation run.

---

## 9. Implementation Dependency Order

Implementation should follow dependency order.

### Stage 1 — Shared contracts and configuration

- Pair schema.
- Variant schema.
- Split schema.
- IDs and canonical identity.
- Config loader.
- Path definitions.
- Seed management.
- Version metadata.

### Stage 2 — Source splitting and duplicate groups

- Load original metadata.
- Load verified duplicate groups.
- Construct atomic split groups.
- Deterministic stratified assignment.
- Persist split assignments.
- Validate leakage and distribution.

### Stage 3 — Variant generation and validation

- Transformation implementations.
- Eligibility checks.
- Retry logic.
- Variant registry.
- Structural validators.
- Transformation validators.
- Parser and compiler validators.
- Rejection logging.

### Stage 4 — Positive pair generation

- Original–accepted variant pairing.
- Lineage checks.
- Split inheritance.
- Canonical identity.
- Candidate output.

### Stage 5 — Negative candidate generation

- Cross-problem source sampling.
- Per-anchor negative target.
- Duplicate checks.
- Similarity screening.
- Bounded retries.
- Rejection reports.

### Stage 6 — Candidate assembly

- Load positive and negative pools.
- Schema validation.
- Pair canonicalization.
- Duplicate consolidation.
- Conflict detection.
- Split validation.

### Stage 7 — Selection and balancing

- Independent selection per split.
- Label balancing.
- Endpoint diversity preference.
- Problem distribution reporting.
- Shortage handling.

### Stage 8 — Final validation and export

- Validate final master index.
- Validate split references.
- Generate reports.
- Export canonical artifacts.
- Record run metadata.

### Stage 9 — Orchestration

- Integrate all stages.
- Stage contracts.
- Run status.
- Fail-safe behavior.
- Reproducibility.
- End-to-end tests.

Implementation checkpoints must remain small enough for independent testing and user verification.

---

## 10. Implementation Readiness Checklist

### Design consistency

- [x] Source split is source-level.
- [x] Split occurs before variant and pair generation.
- [x] Variants inherit original split.
- [x] Exact duplicate groups cannot cross splits.
- [x] Positive pair definition is consistent.
- [x] Negative pair definition is consistent.
- [x] Pair identity is canonical.
- [x] Selection cannot generate new candidates.
- [x] Balancing is independent per split.
- [x] Quota shortage does not bypass integrity rules.
- [x] Output artifacts have defined roles.
- [x] Reproducibility is required.

### Implementation prerequisites

- [ ] Source split algorithm implemented.
- [ ] Duplicate group input verified.
- [ ] Configuration schema finalized.
- [ ] Tokenizer behavior specified and tested.
- [ ] Tree-sitter parser installed and verified.
- [ ] Clang preflight completed.
- [ ] GNU C++17 compatibility pilot completed.
- [ ] Timeout behavior tested.
- [ ] Pilot generation completed.
- [ ] Pilot screening calibration reviewed.
- [ ] Canonical output layout adopted in code.

---

## 11. Readiness Criteria

The project is ready to begin implementation when:

1. All approved Phase 2 design decisions are represented in this document or their authoritative design documents.
2. No unresolved design conflict blocks implementation.
3. Proposed reconciliation rules are reviewed and approved.
4. Configuration and output contracts are finalized.
5. Validation tooling can be preflighted.
6. Pilot requirements are defined.
7. Implementation checkpoints and tests are planned.

The project is not yet ready for full-scale pair generation until pilot validation, threshold calibration, and runtime assessment have been completed.

---

## 12. Status Summary

### Locked design decisions

- Source split strategy: 80/10/10 stratified source-level split.
- Exact duplicate groups remain together.
- Two accepted variants per original target.
- Five attempts per variant target.
- Uniform baseline transformation distribution.
- Token Jaccard screening, initial threshold 0.85.
- Flexible quota policy.
- Per-split balancing.
- Layered validation V1–V3 required.
- Tree-sitter and Clang syntax-only validation.
- Fail-closed validation.

### Proposed reconciliation rules

- Deterministic group-aware stratified source assignment.
- C++-aware tokenization for negative screening.
- Canonical final pair index and split reference files.
- Environment preflight before generation.
- Pilot calibration before full-scale execution.

### Pilot-required parameters

- GNU C++17 compatibility.
- Parser and compiler runtime.
- Parser timeout.
- Compiler timeout.
- Negative screening threshold calibration.
- Transformation success and rejection rates.
- Full-scale runtime estimation.

---

**Document status:** Design Closure Draft  
**Next action:** Review and approve reconciliation rules before implementation planning is finalized.