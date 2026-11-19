# Pair Generation Output & Reproducibility Design

## 1. Purpose

This document defines the output structure, audit reports, configuration management, candidate retention policy, and reproducibility requirements for the pair generation pipeline in CodeSimilarityResearch.

The purpose is to ensure that generated pair datasets are:

- Traceable
- Auditable
- Reproducible
- Easy to load for model training
- Easy to compare across different generation runs

Pair generation must produce more than a training dataset. It must also preserve sufficient information to explain how the dataset was created and evaluate its quality.

---

## 2. Output Structure

The proposed output structure is:

```text
data/pairs/
├── pair_index.csv
├── splits/
│   ├── train.csv
│   ├── validation.csv
│   └── test.csv
├── reports/
│   ├── generation_report.json
│   ├── validation_report.json
│   ├── sampling_report.json
│   └── distribution_report.json
└── configs/
    └── pair_generation_config.json
```

The structure separates pair records, split assignments, audit reports, and generation configuration.

---

## 3. Pair Master Index

### 3.1 `pair_index.csv`

This file contains the full metadata records of all accepted pairs.

It uses the schema defined in Pair Schema & Pairing Rules:

- `pair_id`
- `sample_a_id`
- `sample_b_id`
- `label`
- `pair_type`
- `split`
- `source_a_id`
- `source_b_id`
- `problem_a_id`
- `problem_b_id`
- `generation_method`
- `created_seed`

### 3.2 Responsibilities

- Store all accepted pair records.
- Serve as the master pair dataset.
- Provide references to the source samples and their metadata.
- Preserve pair identity and canonical ordering.
- Serve as the source for reconstructing split datasets.

Source code must not be stored directly inside the pair index.

---

## 4. Split Files

The following files are generated:

- `splits/train.csv`
- `splits/validation.csv`
- `splits/test.csv`

### 4.1 Split File Format

Split files store only `pair_id` references.

Example:

```csv
pair_id
pair_000001
pair_000002
pair_000003
```

### 4.2 Design Rationale

The master index stores full pair metadata. Split files reference records through pair IDs rather than duplicating all fields.

Benefits:

- Avoid duplicated pair records.
- Prevent inconsistencies between master index and split files.
- Make split assignments easy to inspect.
- Simplify dataset loading.
- Keep pair metadata centralized.

The dataset loader retrieves the pair records from `pair_index.csv` using the pair IDs in the selected split file.

---

## 5. Generation Report

File: `reports/generation_report.json`

This report summarizes an individual generation run.

Proposed fields:

- `run_id`
- `started_at`
- `completed_at`
- `status`
- `total_samples`
- `positive_pairs_generated`
- `negative_pairs_generated`
- `total_pairs_generated`
- `seed`
- `config_path`
- `pipeline_version`

The report must distinguish generation attempts from the final accepted dataset counts where applicable.

Its purpose is to describe how the generation process executed.

---

## 6. Validation Report

File: `reports/validation_report.json`

This report stores the results of pair validation defined in Pair Validation Rules.

It includes:

- Overall validation status
- Total pairs
- Valid pairs
- Invalid pairs
- Error count
- Warning count
- Validation checks
- Error details
- Warning details
- Split distribution
- Duplicate statistics
- Validation configuration or version

Example:

```json
{
  "status": "PASS",
  "total_pairs": 100000,
  "valid_pairs": 100000,
  "invalid_pairs": 0,
  "error_count": 0,
  "warning_count": 3,
  "checks": {
    "schema": "PASS",
    "sample_references": "PASS",
    "pair_semantics": "PASS",
    "canonical_identity": "PASS",
    "split_integrity": "PASS"
  }
}
```

This is an illustrative schema only, not actual generation output.

The report must preserve enough information to identify and investigate invalid pair records.

---

## 7. Sampling Report

File: `reports/sampling_report.json`

The sampling report records the pair selection process, particularly negative sampling.

Proposed information:

- Negative pair target
- Actual negative pair count
- Number of anchors reaching the target quota
- Number of anchors below the target quota
- Candidates considered
- Candidates accepted
- Candidates rejected
- Rejection reasons
- Retry counts
- Negative pair distribution by anchor
- Negative pair distribution by problem

### 7.1 Rejection Reasons

Rejection reasons should use standardized codes rather than unrestricted strings.

Proposed rejection reason codes:

- `same_problem`
- `same_lineage`
- `known_duplicate`
- `similarity_screen_failed`
- `duplicate_pair`
- `invalid_reference`

Additional codes may be introduced when justified by the implementation.

The sampling report must support understanding why candidates were rejected without requiring every rejected candidate to be stored.

---

## 8. Distribution Report

File: `reports/distribution_report.json`

This report evaluates the quality and composition of the accepted dataset.

### 8.1 Label Distribution

Report:

- Positive pair count
- Negative pair count
- Total pair count
- Positive/negative ratio
- Deviation from the target 1:1 balance

### 8.2 Problem Distribution

Report:

- Pair count per problem
- Positive pair count per problem
- Negative anchor count per problem
- Negative endpoint coverage per problem
- Underrepresented problems
- Overrepresented problems

### 8.3 Source Frequency

Report:

- Number of positive pairs per source
- Number of negative pairs per source
- Total source appearances
- Sources appearing unusually frequently

### 8.4 Sampling Coverage

Report:

- Total anchors used
- Anchors with zero negative pairs
- Anchors with one or two negative pairs
- Anchors reaching the target of three negative pairs
- Candidate coverage by problem

These statistics help identify sampling concentration, source bias, and insufficient representation.

---

## 9. Generation Configuration

File: `configs/pair_generation_config.json`

The configuration stores the parameters used for an individual generation run.

Proposed configuration groups:

| Group | Parameters |
|---|---|
| Sampling | Target negative pairs per anchor |
| Negative strategy | Cross-problem sampling |
| Pair balance | Target label ratio |
| Randomness | Random seed |
| Similarity screening | Method, threshold, version |
| Positive transformations | Enabled transformation types |
| Retry policy | Maximum retries |
| Split configuration | Split method and ratios |
| Validation configuration | Validation rules/version |

The configuration must be preserved with the corresponding generation outputs.

Configurations must not exist only as implicit values inside source code.

---

## 10. Reproducibility Requirements

The generation pipeline must record sufficient information to reproduce a generation run.

Required reproducibility information:

- Input dataset version
- Metadata version or snapshot
- Random seed for randomized steps
- Generation configuration
- Similarity screening method and configuration
- Pipeline version or Git commit hash
- Important dependency versions
- Split assignments
- Generation reports
- Validation and audit reports

### 10.1 Deterministic Behavior

- Randomized sampling must be deterministic when using the same seed and inputs.
- All random steps must use controlled random state.
- Filesystem enumeration must not rely on unspecified ordering.
- Configurations must be retained.
- Repeated generation with the same inputs, configuration, seed, code, and controlled environment should reproduce pair selection.

### 10.2 Limitations

A random seed alone does not guarantee reproducibility if:

- Input data changes.
- Pipeline code changes.
- Dependency versions change.
- Filesystem ordering changes.
- Similarity screening implementation changes.
- Split assignments change.

Reproducibility therefore requires versioning and input tracking, not only a seed.

---

## 11. Candidate Retention Policy

Candidate generation may produce a large number of potential pairs. Retaining every candidate is not required by the initial pipeline.

### 11.1 Default Retention

The default policy is:

- Retain accepted pairs.
- Retain rejection statistics by reason.
- Retain aggregate candidate counts.
- Retain sufficient traceability for accepted pairs.
- Do not retain all rejected candidates by default.

### 11.2 Debug Mode

An optional debug mode may retain rejected candidate records for troubleshooting or analysis.

Debug retention may be:

- Limited to a selected sampling stage.
- Limited to a specific rejection category.
- Limited to a subset of candidate records.
- Enabled only for selected experiments.

### 11.3 Rationale

This policy avoids unnecessary storage consumption and large intermediate datasets while retaining sufficient audit information for routine runs.

The absence of full rejected-candidate records must not prevent reporting candidate counts and rejection reasons.

---

## 12. Generation Run Tracking

Each generation run must have a unique `run_id`.

A run represents one execution of the pair generation process with a specific input dataset and configuration.

The run should be associated with:

- Input dataset version
- Generation configuration
- Random seed
- Pipeline version
- Generation report
- Validation report
- Sampling report
- Distribution report

Run tracking enables comparisons between different sampling strategies, thresholds, transformation configurations, or experiments.

The exact run directory structure and retention strategy may be refined during implementation.

---

## 13. Acceptance Criteria

The pair generation output design is considered complete when:

- A master pair index structure is defined.
- Split files reference pair records using `pair_id`.
- Generation report requirements are defined.
- Validation report requirements are defined.
- Sampling report requirements are defined.
- Distribution report requirements are defined.
- Generation configuration is preserved.
- Reproducibility requirements are defined.
- Candidate retention policy is established.
- Generation runs are traceable using `run_id`.

---

## 14. Design Principles

1. **Traceability** — Accepted pairs must be traceable to their original samples.
2. **Auditability** — Generation and validation results must be inspectable.
3. **Reproducibility** — The same controlled inputs should reproduce the same selections.
4. **Storage efficiency** — Avoid unnecessary duplication and retention of massive rejected candidate pools.
5. **Separation of concerns** — Pair records, split assignments, reports, and configs serve distinct roles.
6. **Transparency** — Warnings and deviations must be recorded rather than hidden.
7. **Research integrity** — Reports must represent actual results, not intended targets.

---

## 15. Status

Checkpoint: **2.5.4.3 — Output Structure, Audit & Reproducibility Design**

Status: **Design completed, pending repository commit.**
