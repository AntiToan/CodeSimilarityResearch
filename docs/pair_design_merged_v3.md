# CodeSimilarityResearch — Pair Dataset Design (Merged)

Tài liệu này gộp 9 tài liệu thiết kế, giữ nguyên toàn bộ nội dung gốc:

1. [Part 1 — Pair Schema and Pairing Rules](#part-1--pair-schema-and-pairing-rules) (Checkpoint 2.5.1)
2. [Part 2 — Pair Sampling Strategy Design](#part-2--pair-sampling-strategy-design) (Checkpoint 2.5.2)
3. [Part 3 — Pair Generation Workflow](#part-3--pair-generation-workflow)
4. [Part 4 — Pair Validation Rules](#part-4--pair-validation-rules) (Checkpoint 2.5.4.2)
5. [Part 5 — Pair Generation Output & Reproducibility Design](#part-5--pair-generation-output--reproducibility-design) (Checkpoint 2.5.4.3)
6. [Part 6 — Positive Pair Strategy Design](#part-6--positive-pair-strategy-design) (Checkpoint 2.7.3.1)
7. [Part 7 — Pair Candidate Assembly Strategy](#part-7--pair-candidate-assembly-strategy) (Checkpoint 2.7.4.1)
8. [Part 8 — Final Pair Selection & Balancing Integration](#part-8--final-pair-selection--balancing-integration) (Checkpoint 2.7.4.2)
9. [Part 9 — Pair Generation Pipeline Integration & Orchestration Design](#part-9--pair-generation-pipeline-integration--orchestration-design) (Checkpoint 2.7.4.3)

> Lưu ý: trong mỗi Part, các mục được đánh số lại từ đầu (1, 2, 3…) theo tài liệu gốc.

---

## Part 1 — Pair Schema and Pairing Rules

### 1. Overview

This checkpoint defines the pair record schema, pair identity rules, storage format, and validation requirements for the CodeSimilarityResearch project.

Pair records reference source samples using IDs rather than duplicating source code content.

This checkpoint is design-only. No pair records are generated yet.

### 2. Pair Record Schema

| Field | Type | Description |
|---|---|---|
| `pair_id` | string | Unique pair identifier |
| `sample_a_id` | string | First sample ID |
| `sample_b_id` | string | Second sample ID |
| `label` | integer | 1 for positive, 0 for negative |
| `pair_type` | string | positive or negative |
| `split` | string | train, validation, or test |
| `source_a_id` | string | Original lineage of sample A |
| `source_b_id` | string | Original lineage of sample B |
| `problem_a_id` | string | Problem ID of sample A |
| `problem_b_id` | string | Problem ID of sample B |
| `generation_method` | string | Pair generation method |
| `created_seed` | integer/null | Random seed, when applicable |

### 3. Pair Definition

#### Positive pairs

An original source and its generated variant from the same lineage.

- Label: `1`
- Pair type: `positive`
- Both samples must share the same original lineage.

#### Negative pairs

Two original samples selected using cross-problem sampling and negative candidate filtering.

- Label: `0`
- Pair type: `negative`
- Different problem IDs
- Different source lineage
- No known duplicate relationship
- Candidate must pass the defined similarity screening strategy

Labels represent synthetic/heuristic similarity relationships, not confirmed plagiarism ground truth.

### 4. Canonical Ordering

Pair identity is independent of sample order.

The two sample IDs are sorted lexicographically before pair record creation.

The pairs `(A, B)` and `(B, A)` are treated as the same pair.

Only one canonical record is stored.

### 5. Pair Storage

Pair metadata is stored in CSV format.

Source code files are stored separately and referenced by sample IDs.

This avoids source duplication, reduces storage, and supports independent source and pair management.

Proposed location:

`data/pairs/`

### 6. Pair Identity and Duplicate Prevention

Pair generation must:

1. Verify that sample IDs are different.
2. Sort IDs canonically.
3. Generate a canonical pair key.
4. Check whether the pair already exists.
5. Reject duplicate pair records.

Pair identity is independent of label. A pair must not appear with conflicting positive and negative labels.

### 7. Split Assignment

Original samples must be assigned to train, validation, and test before pair generation.

Pairs may only be created within their assigned partition.

- Positive pairs must inherit the split of their original lineage.
- Negative pairs must use two samples belonging to the same partition.
- Cross-partition pairs are prohibited.

Split ratios and grouping details are deferred to the split design checkpoint.

### 8. Validation Rules

The pair dataset validator must check:

- Unique pair IDs
- Valid sample references
- No self-pairs
- Labels restricted to 0 or 1
- Pair type consistent with label
- Canonical A/B ordering
- No reversed duplicate pairs
- Positive pair lineage consistency
- Negative pair constraints
- Split consistency
- Reproducible generation metadata where applicable

### 9. Proposed Storage Structure

```text
data/
└── pairs/
    ├── pair_index.csv
    └── splits/
        ├── train.csv
        ├── validation.csv
        └── test.csv
```

This is a proposed structure and has not been created in this checkpoint.

### 10. Scope

This checkpoint defines pair schema and pairing rules only.

It does not implement:

- Pair generation
- Pair validation scripts
- Positive or negative labels
- Dataset split assignment
- Pair sampling or balancing

### 11. Status

**Checkpoint 2.5.1 – Pair Schema and Pairing Rules: COMPLETED**

- [x] Pair record schema
- [x] Positive/negative definitions
- [x] Canonical ordering
- [x] Pair identity
- [x] Duplicate prevention
- [x] CSV storage design
- [x] Split consistency rules
- [x] Pair validation requirements



---

## Part 2 — Pair Sampling Strategy Design

### 1. Overview

This checkpoint defines the sampling strategy for generating negative code similarity pairs in CodeSimilarityResearch using POJ-104.

The goal is to control pair volume, improve problem diversity, maintain reproducibility, and avoid exhaustive pair generation.

This checkpoint is design-only. No pairs are generated yet.

### 2. Motivation

The POJ-104 dataset contains 52,000 source samples.

Exhaustive unique pair generation would produce:

\[
\frac{52,000 \times 51,999}{2}
= 1,351,974,000
\]

pairs, which is unnecessary for the initial research experiments.

Controlled sampling is therefore required.

### 3. Sampling Method

The initial strategy uses a combination of:

- Per-anchor sampling
- Problem-balanced selection

Each original sample acts as an anchor. Negative candidates are selected from different problem IDs.

### 4. Sampling Workflow

For each anchor:

1. Select the anchor sample.
2. Randomly select a problem ID different from the anchor's problem ID.
3. Select a sample from the selected problem.
4. Check negative pair eligibility.
5. Apply duplicate, lineage, and similarity screening.
6. Accept valid candidates.
7. Repeat until the quota is reached or retry limits are exhausted.

### 5. Negative Quota

The initial quota is three valid negative pairs per anchor.

| Configuration | Value |
|---|---:|
| Anchors | 52,000 |
| Negative quota per anchor | 3 |
| Initial negative selection target | 156,000 |

The 156,000 figure represents the target number of negative pair selections before deduplication and filtering. The final unique pair count may be lower.

### 6. Problem Diversity

The sampling strategy prioritizes selecting three negative pairs from three different problem IDs.

This reduces over-reliance on a single problem source and encourages diversity in the negative pair dataset.

The selected problem IDs must differ from the anchor's problem ID.

### 7. Eligibility Rules

Negative candidates must:

- Have a different sample ID from the anchor.
- Have a different problem ID.
- Have different source lineage.
- Not belong to known exact duplicate groups.
- Not violate negative pair constraints.
- Pass the configured similarity screening.
- Not already exist as a canonical pair.

### 8. Reproducibility

Sampling must use a configured deterministic random seed.

Given the same dataset, configuration, and seed, sampling should be reproducible.

Sampling parameters must be recorded for auditability.

### 9. Quota Failure Handling

If an anchor cannot obtain three valid negative pairs:

- Retain the valid pairs obtained.
- Do not force acceptance of suspicious candidates.
- Do not use an unlimited retry loop.
- Record the actual count and failure/rejection information.
- Report sampling coverage during validation.

Pair quality takes precedence over satisfying the quota.

### 10. Efficiency

Exhaustive Cartesian pair generation is not used.

The sampling procedure should operate on problem-level candidate pools and sample only the candidates required to meet the quota.

This keeps pair generation manageable for the initial experiments.

### 11. Scope

This checkpoint defines the negative pair sampling strategy only.

It does not implement:

- Sampling code
- Negative pair generation
- Pair balancing
- Positive pair quota
- Positive-to-negative ratio
- Similarity screening implementation
- Dataset splitting

### 12. Status

**Checkpoint 2.5.2 – Pair Sampling Strategy Design: COMPLETED**

- [x] Per-anchor sampling
- [x] Problem-balanced selection
- [x] Negative quota
- [x] Problem diversity
- [x] Deterministic seed
- [x] Eligibility rules
- [x] Quota failure handling
- [x] Non-exhaustive sampling



---

## Part 3 — Pair Generation Workflow

### 1. Objective

This document defines the overall workflow for generating the code similarity pair dataset.

The workflow integrates the previously defined pair schema, positive and negative pair strategies, sampling, balancing, filtering, and validation requirements.

This checkpoint defines the workflow only. Implementation will be conducted in later checkpoints.

### 2. Inputs

The pair generation workflow requires:

- Preprocessed source files.
- Sample metadata.
- Exact duplicate analysis.
- Variant metadata and source lineage information (when available).
- Source-level split assignments.
- Pair generation and sampling configuration.

Some inputs, including variant metadata and split assignments, are dependencies that must be prepared before actual pair generation.

### 3. Workflow Overview

The pair generation pipeline follows these stages:

1. Load and verify dataset inputs.
2. Assign source-level dataset splits.
3. Generate positive pair candidates.
4. Generate negative pair candidates.
5. Filter invalid candidates.
6. Sample and balance selected pairs.
7. Validate the selected pair dataset.
8. Export pair indexes and audit reports.

### 4. Stage 1 — Load and Verify Dataset

Load sample metadata and source references.

Verify:

- Sample IDs are unique.
- Source paths are valid.
- Required metadata fields are available.
- Source files are readable.
- Dataset references are consistent.

Invalid input records must be reported and must not silently enter pair generation.

### 5. Stage 2 — Assign Dataset Splits

Assign train, validation, and test splits at the source level before generating pairs.

All samples belonging to the same source lineage, including original and controlled variants, must remain in the same split.

Pair generation must operate within each split independently.

No pair may contain samples from different splits.

The split ratios and assignment method require a separate design decision before implementation.

### 6. Stage 3 — Generate Positive Pair Candidates

Positive candidates are generated using the approved positive pair strategy.

Candidate pairs may include:

- Original source paired with a valid controlled variant.
- Other positive relationships explicitly approved by the positive pair strategy.

Each candidate must preserve source lineage information.

Positive candidate generation must not introduce uncontrolled semantic changes or unsupported similarity labels.

### 7. Stage 4 — Generate Negative Pair Candidates

Negative candidates are generated using the approved negative pair strategy.

Initial negative sampling uses cross-problem source pairs.

Candidates must respect:

- Different problem IDs.
- Different source lineages.
- Exact duplicate exclusions.
- Split isolation.
- Approved similarity screening rules.
- Controlled and reproducible sampling.

Negative candidates are heuristic/synthetic labels, not ground-truth judgments.

### 8. Stage 5 — Candidate Filtering

Candidate filtering removes pairs that violate the approved constraints.

Filtering includes:

- Invalid sample references.
- Same-lineage negative pairs.
- Same-problem negative pairs.
- Exact duplicate pairs.
- Reversed duplicate pairs.
- Split violations.
- Invalid pair structure.
- Negative candidates rejected by similarity screening.

Candidate rejection reasons must be recorded for audit.

### 9. Stage 6 — Sampling and Balancing

Sampling and balancing follow the approved strategies:

- Per-anchor negative sampling.
- Problem-aware sampling.
- Diversity prioritization.
- Deterministic random seed.
- Bounded retries.
- Target positive-to-negative ratio of 1:1.
- Soft problem distribution balance.
- Pair validity and diversity take priority over balance.
- Excess valid candidates are retained in the candidate pool when applicable.

Sampling must not force invalid pairs to satisfy quotas.

### 10. Stage 7 — Pair Validation

The selected pairs must be validated before export.

Validation must verify:

- Pair schema.
- Valid sample references.
- Label validity.
- Pair uniqueness.
- Split consistency.
- Positive lineage constraints.
- Negative cross-problem constraints.
- Negative lineage constraints.
- Label distribution.
- Problem distribution.
- Source frequency statistics.

Validation failures must be reported and must not silently pass.

Detailed validation rules will be defined in the Pair Validation Rules checkpoint.

### 11. Stage 8 — Export Dataset and Reports

The workflow exports:

- Pair index dataset.
- Split-specific pair indexes.
- Candidate records where applicable.
- Sampling and balancing statistics.
- Pair validation report.
- Reproducibility configuration.
- Rejection and filtering statistics.

Pair indexes reference sample IDs rather than embedding source code.

Source code remains stored independently in the processed source dataset.

### 12. Candidate Pool and Selected Pairs

Candidate generation and final pair selection are separate stages.

The candidate pool contains potential pairs that can be audited or considered for sampling.

Selected pairs form the dataset used for training and evaluation.

Not all generated candidates must be selected.

Unused candidates should remain available when retention is supported by the pipeline, enabling alternative sampling experiments without regenerating candidates unnecessarily.

### 13. Data Leakage Prevention

Leakage prevention is enforced through source-level split assignment.

- Splits must be assigned before pair generation.
- All source lineages must remain in the same split.
- Pair generation must be isolated within each split.
- No pair may connect samples from different splits.
- Pair generation and balancing must not move samples across splits.

### 14. Reproducibility

The workflow must be reproducible using:

- Dataset version.
- Variant generation version and configuration.
- Split assignment configuration.
- Pair generation configuration.
- Sampling configuration.
- Random seed.
- Filtering rules.
- Validation rules.

All relevant configurations and audit reports must be retained.

### 15. Dependencies Before Implementation

The following decisions must be finalized before actual pair generation:

- Dataset split strategy and ratios.
- Variant generation and lineage schema.
- Similarity screening method and thresholds.
- Pair validation rules.
- Candidate retention and output structure.

### 16. Expected Outcome

The workflow produces a valid, reproducible, auditable pair dataset with controlled positive and negative sampling, split isolation, balancing, and validation.

This checkpoint defines the overall workflow only. Detailed validation rules, output structure, audit design, and implementation are handled by subsequent checkpoints.



---

## Part 4 — Pair Validation Rules

### 1. Purpose

This document defines the validation rules for generated code similarity pairs in the CodeSimilarityResearch project.

The validation process ensures that pair records are structurally valid, reference existing samples, follow positive/negative pair constraints, respect dataset splits, and preserve the integrity of the pair dataset.

Validation distinguishes between mandatory constraints and soft distribution targets.

- **FAIL**: A mandatory constraint is violated.
- **WARNING**: A soft target is not achieved, but the dataset may still be valid.
- **PASS**: All mandatory validation rules are satisfied.

---

### 2. Validation Scope

Pair validation is divided into the following layers:

1. Schema validation
2. Sample reference validation
3. Pair semantic validation
4. Canonical identity and duplicate validation
5. Split and leakage validation
6. Sampling and distribution audit

Each layer is responsible for validating a different aspect of the pair dataset.

---

### 3. Schema Validation

Each pair record must conform to the established pair schema.

Required fields:

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

Validation rules:

- All required fields must exist.
- IDs and categorical fields must use valid types.
- `label` must be either `0` or `1`.
- `pair_type` must be either `positive` or `negative`.
- `split` must be one of `train`, `validation`, or `test`.
- `created_seed` must be an integer or `null`.
- Null seed values are permitted when a seed is not applicable.
- Pair IDs must be unique.

Schema violations result in **FAIL**.

---

### 4. Sample Reference Validation

Every pair must reference existing samples in the sample metadata.

Validation rules:

- `sample_a_id` and `sample_b_id` must exist.
- Neither sample reference may be missing or invalid.
- A sample cannot be paired with itself.
- Source IDs and problem IDs recorded in the pair must match the referenced samples' metadata.

Invalid or dangling references result in **FAIL**.

---

### 5. Positive Pair Validation

A positive pair represents two code samples derived from the same original source lineage.

Expected characteristics:

- `label = 1`
- `pair_type = positive`
- Both samples belong to the same original source lineage.
- One sample is the original source.
- The other sample is a valid transformed variant.
- The transformation must belong to the approved transformation categories.
- Variant transformation metadata must be available and valid.
- Both samples must belong to the same dataset split.

Approved transformation categories are defined in the Positive Pair Strategy:

- Formatting changes
- Whitespace changes
- Comment changes
- Scope-aware local variable renaming
- Safe function-local identifier renaming

Validation must confirm that the pair references the expected original and variant records and that transformation metadata is valid.

Syntax validation or transformation checks do not independently prove semantic equivalence. The validator must not claim that generated variants are semantically identical merely because they pass syntax checks.

Any mandatory positive-pair violation results in **FAIL**.

---

### 6. Negative Pair Validation

A negative pair represents two different original code samples that are treated as non-similar training examples under the project's sampling strategy.

Expected characteristics:

- `label = 0`
- `pair_type = negative`
- Both samples are original samples, not generated variants.
- `problem_a_id != problem_b_id`
- Both samples belong to different source lineages.
- No known exact duplicate relationship exists.
- The pair has passed the required similarity screening process.
- Both samples belong to the same dataset split.

Validation rules:

- Same-problem pairs are invalid under the initial negative pair strategy.
- Same-lineage pairs are invalid.
- Pairs involving generated variants are invalid under the initial negative strategy.
- Known duplicate samples must not form negative pairs.
- Negative pairs without a valid screening record must not be accepted.
- Negative screening status must be traceable to the screening process.

The similarity screening method and threshold are defined in a separate design/implementation step. This validator must not invent or assume an unspecified screening threshold.

Any mandatory negative-pair violation results in **FAIL**.

---

### 7. Canonical Pair Identity and Duplicate Validation

Pair identity is independent of sample order.

Canonical ordering is established by sorting the two sample IDs lexicographically:

`sample_a_id < sample_b_id`

Validation rules:

- Every pair must use canonical ordering.
- Self-pairs are prohibited.
- Duplicate pair records are prohibited.
- Reversed duplicates are prohibited.
- A canonical pair must not have conflicting labels.
- A canonical pair must not appear in different splits.

Pair identity must be determined from the two sample IDs rather than the pair label.

Violations result in **FAIL**.

---

### 8. Split and Leakage Validation

Dataset splitting must happen at the original-source level before pair generation.

Validation rules:

- Both samples in a pair must belong to the same split.
- Positive pairs must inherit the split of their original source lineage.
- Variants belonging to the same original source must not cross splits.
- Pair generation must not create cross-split pairs.
- Pair records must reference the correct split assignments.

Any split leakage or cross-split pair results in **FAIL**.

Known duplicate groups spanning different problems should also be considered during split design to reduce potential leakage. The exact duplicate-group split enforcement policy remains subject to the dedicated split design checkpoint.

---

### 9. Sampling and Distribution Audit

Sampling and distribution objectives are soft targets. Their violation does not automatically invalidate an individual pair.

The validator/auditor should report the following:

#### 9.1 Label balance

- Positive pair count
- Negative pair count
- Positive-to-negative ratio
- Deviation from the target 1:1 balance

Target: 1:1 positive and negative pairs.

Deviation results in **WARNING**.

#### 9.2 Problem distribution

Report pair representation across the 104 problem groups, including:

- Positive pair counts by problem
- Negative anchor counts by problem
- Negative endpoint coverage
- Underrepresented and overrepresented problems

Problem distribution imbalance results in **WARNING**.

#### 9.3 Negative sampling quota

Target: 3 valid negative pairs per anchor.

The target does not represent a mandatory final quota.

- Report actual negative pairs per anchor.
- Report anchors with fewer than 3 valid negative pairs.
- Do not force invalid or suspicious pairs to satisfy the quota.
- Use bounded retries.
- Preserve valid pairs even if the target cannot be reached.

Failure to reach the target results in **WARNING**, not **FAIL**.

#### 9.4 Source frequency and diversity

Report:

- Samples appearing unusually frequently
- Negative endpoint frequency
- Problem diversity
- Candidate coverage
- Sampling rejection counts

Unusual source frequency or low candidate coverage results in **WARNING**.

---

### 10. Validation Severity

#### Mandatory constraints — FAIL

The following conditions must invalidate the dataset or the affected validation run:

- Invalid pair schema
- Missing required fields
- Invalid field types
- Invalid label
- Invalid pair type
- Label and pair type mismatch
- Invalid split value
- Missing sample references
- Self-pair
- Incorrect source/problem metadata
- Non-canonical pair ordering
- Duplicate or reversed pair
- Conflicting labels for the same pair identity
- Positive pair with invalid lineage
- Positive pair without a valid original/variant relationship
- Invalid positive transformation metadata
- Negative pair from the same problem
- Negative pair from the same source lineage
- Negative pair involving variants
- Negative pair involving known duplicates
- Negative pair without successful similarity screening
- Cross-split pair
- Split leakage involving the same original lineage

#### Soft targets — WARNING

The following conditions should generate warnings without automatically invalidating the dataset:

- Label ratio deviates from 1:1
- Problem distribution is imbalanced
- An anchor has fewer than 3 negative pairs
- High source frequency
- Low candidate coverage
- Sampling quota not achieved
- Distribution diversity is lower than expected

---

### 11. Validation Workflow

The validation process should follow this order:

1. Validate pair schema.
2. Validate sample references and metadata.
3. Validate positive and negative pair semantics.
4. Validate canonical ordering and duplicate identity.
5. Validate split consistency and leakage constraints.
6. Audit sampling quota and distribution.
7. Produce a final validation summary.

The validator should collect independent errors where possible instead of stopping at the first violation.

It must not automatically modify or repair pair records. Pair generation, filtering, or sampling procedures are responsible for resolving invalid records.

---

### 12. Validation Output

The validation process should produce:

- Overall validation status
- Total pair count
- Valid pair count
- Invalid pair count
- Error count
- Warning count
- Error details
- Warning details
- Positive and negative pair counts
- Split distribution
- Problem distribution summary
- Negative quota coverage
- Duplicate pair statistics
- Validation configuration or version information

The detailed report format and storage location will be finalized in the Output Structure, Audit & Reproducibility Design checkpoint.

---

### 13. Acceptance Criteria

A pair dataset is accepted when:

- All mandatory constraints pass.
- No invalid pair records remain in the accepted dataset.
- Split consistency is satisfied.
- Positive and negative pair rules are respected.
- Pair identity and uniqueness are preserved.
- Validation results are recorded and reproducible where applicable.

Soft targets are evaluated separately and documented in the audit report.

A dataset may be accepted with warnings if mandatory constraints are satisfied and all deviations are transparent.

---

### 14. Design Principles

The validation system follows these principles:

1. **Integrity before balance** — Never accept invalid pairs to achieve a target ratio.
2. **Validity before quantity** — A smaller valid dataset is preferable to a larger contaminated dataset.
3. **Warnings are transparent** — Soft-target deviations must be reported.
4. **No silent repairs** — The validator must not silently alter pair records.
5. **Reproducibility** — Validation must be repeatable with the same inputs and configuration.
6. **Synthetic labels are not ground truth** — Positive and negative labels represent the project's construction strategy, not verified plagiarism judgments.

---

### 15. Status

Checkpoint: **2.5.4.2 — Pair Validation Rules Design**

Status: **Design completed, pending repository commit.**



---

## Part 5 — Pair Generation Output & Reproducibility Design

### 1. Purpose

This document defines the output structure, audit reports, configuration management, candidate retention policy, and reproducibility requirements for the pair generation pipeline in CodeSimilarityResearch.

The purpose is to ensure that generated pair datasets are:

- Traceable
- Auditable
- Reproducible
- Easy to load for model training
- Easy to compare across different generation runs

Pair generation must produce more than a training dataset. It must also preserve sufficient information to explain how the dataset was created and evaluate its quality.

---

### 2. Output Structure

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

### 3. Pair Master Index

#### 3.1 `pair_index.csv`

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

#### 3.2 Responsibilities

- Store all accepted pair records.
- Serve as the master pair dataset.
- Provide references to the source samples and their metadata.
- Preserve pair identity and canonical ordering.
- Serve as the source for reconstructing split datasets.

Source code must not be stored directly inside the pair index.

---

### 4. Split Files

The following files are generated:

- `splits/train.csv`
- `splits/validation.csv`
- `splits/test.csv`

#### 4.1 Split File Format

Split files store only `pair_id` references.

Example:

```csv
pair_id
pair_000001
pair_000002
pair_000003
```

#### 4.2 Design Rationale

The master index stores full pair metadata. Split files reference records through pair IDs rather than duplicating all fields.

Benefits:

- Avoid duplicated pair records.
- Prevent inconsistencies between master index and split files.
- Make split assignments easy to inspect.
- Simplify dataset loading.
- Keep pair metadata centralized.

The dataset loader retrieves the pair records from `pair_index.csv` using the pair IDs in the selected split file.

---

### 5. Generation Report

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

### 6. Validation Report

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

### 7. Sampling Report

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

#### 7.1 Rejection Reasons

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

### 8. Distribution Report

File: `reports/distribution_report.json`

This report evaluates the quality and composition of the accepted dataset.

#### 8.1 Label Distribution

Report:

- Positive pair count
- Negative pair count
- Total pair count
- Positive/negative ratio
- Deviation from the target 1:1 balance

#### 8.2 Problem Distribution

Report:

- Pair count per problem
- Positive pair count per problem
- Negative anchor count per problem
- Negative endpoint coverage per problem
- Underrepresented problems
- Overrepresented problems

#### 8.3 Source Frequency

Report:

- Number of positive pairs per source
- Number of negative pairs per source
- Total source appearances
- Sources appearing unusually frequently

#### 8.4 Sampling Coverage

Report:

- Total anchors used
- Anchors with zero negative pairs
- Anchors with one or two negative pairs
- Anchors reaching the target of three negative pairs
- Candidate coverage by problem

These statistics help identify sampling concentration, source bias, and insufficient representation.

---

### 9. Generation Configuration

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

### 10. Reproducibility Requirements

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

#### 10.1 Deterministic Behavior

- Randomized sampling must be deterministic when using the same seed and inputs.
- All random steps must use controlled random state.
- Filesystem enumeration must not rely on unspecified ordering.
- Configurations must be retained.
- Repeated generation with the same inputs, configuration, seed, code, and controlled environment should reproduce pair selection.

#### 10.2 Limitations

A random seed alone does not guarantee reproducibility if:

- Input data changes.
- Pipeline code changes.
- Dependency versions change.
- Filesystem ordering changes.
- Similarity screening implementation changes.
- Split assignments change.

Reproducibility therefore requires versioning and input tracking, not only a seed.

---

### 11. Candidate Retention Policy

Candidate generation may produce a large number of potential pairs. Retaining every candidate is not required by the initial pipeline.

#### 11.1 Default Retention

The default policy is:

- Retain accepted pairs.
- Retain rejection statistics by reason.
- Retain aggregate candidate counts.
- Retain sufficient traceability for accepted pairs.
- Do not retain all rejected candidates by default.

#### 11.2 Debug Mode

An optional debug mode may retain rejected candidate records for troubleshooting or analysis.

Debug retention may be:

- Limited to a selected sampling stage.
- Limited to a specific rejection category.
- Limited to a subset of candidate records.
- Enabled only for selected experiments.

#### 11.3 Rationale

This policy avoids unnecessary storage consumption and large intermediate datasets while retaining sufficient audit information for routine runs.

The absence of full rejected-candidate records must not prevent reporting candidate counts and rejection reasons.

---

### 12. Generation Run Tracking

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

### 13. Acceptance Criteria

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

### 14. Design Principles

1. **Traceability** — Accepted pairs must be traceable to their original samples.
2. **Auditability** — Generation and validation results must be inspectable.
3. **Reproducibility** — The same controlled inputs should reproduce the same selections.
4. **Storage efficiency** — Avoid unnecessary duplication and retention of massive rejected candidate pools.
5. **Separation of concerns** — Pair records, split assignments, reports, and configs serve distinct roles.
6. **Transparency** — Warnings and deviations must be recorded rather than hidden.
7. **Research integrity** — Reports must represent actual results, not intended targets.

---

### 15. Status

Checkpoint: **2.5.4.3 — Output Structure, Audit & Reproducibility Design**

Status: **Design completed, pending repository commit.**

---

## Part 6 — Positive Pair Strategy Design

### 1. Overview

This document defines the strategy for generating positive code similarity pairs for the CodeSimilarityResearch project using the POJ-104 dataset.

Positive pairs are constructed from the same original source code sample and its safely transformed variants.

This checkpoint is design-only. No variants, pairs, or labels are generated yet.

### 2. Objective

The objective is to generate positive pairs representing source code that remains semantically equivalent to its original version despite controlled transformations.

The generated pairs will be used as synthetic training examples for code similarity modeling.

### 3. Positive Pair Definition

A positive pair consists of:

- An original source code sample.
- A variant generated from that same source through controlled transformations.

The original sample and its variant are assigned a positive similarity label.

**Label convention:** `1` = positive pair.

Positive labels represent synthetic transformation-based similarity, not verified plagiarism relationships.

### 4. Transformation Strategy

#### 4.1 Accepted Transformations

| Transformation | Description | Safety |
|---|---|---|
| Formatting changes | Modify indentation and formatting | High |
| Whitespace normalization | Change unnecessary whitespace | High |
| Comment modification | Add, remove, or modify comments | High |
| Local variable renaming | Rename local variables with scope-aware handling | High, with validation |
| Function-local identifier renaming | Rename eligible identifiers without collisions | High, with validation |

Identifier transformations must avoid changing language keywords, function signatures where not intended, library identifiers, macros, or other references that may alter behavior.

#### 4.2 Deferred or Rejected Transformations

| Transformation | Reason |
|---|---|
| Statement reordering | May change execution behavior or dependencies |
| Control-flow modification | May alter program semantics |
| Constant/literal changes | May change outputs or behavior |
| Arbitrary statement insertion/removal | May change program logic |
| Uncontrolled identifier replacement | May introduce collisions or invalid code |

These transformations are not included in the initial positive pair generation strategy.

### 5. Generation Workflow

1. Select an original sample.
2. Select an eligible transformation.
3. Generate a code variant.
4. Validate the generated source.
5. Reject invalid variants.
6. Record transformation metadata and original lineage.
7. Construct a positive pair from the original and accepted variant.
8. Assign the positive label.

### 6. Lineage and Metadata

Each generated variant must maintain traceability to its original sample.

Recommended metadata:

- `variant_id`
- `original_sample_id`
- `transformation_type`
- `transformation_config`
- `transformed_source_path`
- `validation_status`

Lineage information is essential for dataset splitting and leakage prevention.

### 7. Validation Requirements

Generated variants must:

- Remain syntactically valid where validation is supported.
- Avoid accidental identifier collisions.
- Preserve intended program semantics.
- Maintain the original sample lineage.
- Be reproducible when transformation configuration and random seed are recorded.

Syntax validation alone does not guarantee semantic equivalence. Transformation safety and testing must be considered separately.

### 8. Label Interpretation

Positive labels are synthetic labels derived from known transformations.

They do not establish that two real-world programs are plagiarized or that every generated transformation is perfectly semantics-preserving.

The dataset will be used to train a code similarity model, not to make definitive plagiarism judgments.

### 9. Scope of This Checkpoint

This checkpoint defines the positive pair strategy only.

It does not implement:

- Transformation code
- Variant generation
- Pair generation
- Label creation
- Dataset splitting
- Model training

### 10. Status

**Checkpoint 2.7.3.1 – Positive Pair Strategy Design: COMPLETED**

- [x] Positive pair definition
- [x] Transformation categories
- [x] Safe transformation scope
- [x] Deferred transformations
- [x] Generation workflow
- [x] Lineage metadata requirements
- [x] Validation principles
- [x] Synthetic label interpretation

---

## Part 7 — Pair Candidate Assembly Strategy

**Project:** CodeSimilarityResearch  
**Checkpoint:** 2.7.4.1 — Pair Candidate Assembly & Finalization Strategy  
**Status:** Design specification

---

### 1. Purpose

This document defines the strategy for assembling positive and negative pair candidates into a unified candidate pool before final pair selection, balancing, validation, and export.

The assembly stage is responsible for consolidating candidate records generated by the positive and negative pair strategies while preserving pair identity, label consistency, split integrity, traceability, and reproducibility.

Candidate assembly does not generate new pair labels and does not perform final dataset balancing.

---

### 2. Candidate Sources

Pair candidates originate from two independent pipelines.

#### 2.1 Positive Candidate Pool

Positive candidates are generated according to the approved positive pair strategy.

Eligible sources include:

- Original samples
- Accepted variants derived from the same original lineage

Positive candidates must satisfy the positive pair rules defined in the project's pair generation design.

Synthetic label:

- `label = 1`
- `pair_type = positive`

Only accepted variants are eligible for positive candidate assembly.

Variants with the following statuses must not be used:

- `generated`
- `validated` but not accepted
- `rejected`

#### 2.2 Negative Candidate Pool

Negative candidates are generated according to the approved negative pair strategy.

Baseline restrictions:

- Negative pairs use original samples only.
- Endpoints must belong to different problem IDs.
- Endpoints must satisfy the approved negative candidate screening rules.
- Known duplicates and prohibited lineage relationships must be excluded.

Synthetic label:

- `label = 0`
- `pair_type = negative`

Negative candidates must not use transformed variants in the baseline pipeline.

---

### 3. Candidate Assembly Pipeline

The assembly process follows these stages:

1. Load positive candidate records.
2. Load negative candidate records.
3. Validate candidate schema and required metadata.
4. Validate endpoint references.
5. Validate split assignments.
6. Validate pair identity and canonical ordering.
7. Detect self-pairs.
8. Deduplicate candidates.
9. Detect label conflicts.
10. Apply candidate-level rejection rules.
11. Produce the validated assembled candidate pool.
12. Generate assembly reports and rejection statistics.

Assembly must not modify the original candidate generation records.

---

### 4. Assembly Rules

#### 4.1 Independent Candidate Sources

Positive and negative candidates must be generated and maintained independently according to their respective strategies.

The assembly stage must not:

- Generate new positive candidates
- Generate new negative candidates
- Modify candidate labels
- Convert positive candidates into negative candidates
- Convert negative candidates into positive candidates

Assembly only consolidates and validates candidates.

#### 4.2 Accepted Variant Eligibility

Positive candidate assembly may use variants only when their validation and lifecycle status indicate acceptance.

The accepted variant registry is the authoritative source for variant eligibility.

Variants that are not accepted must not enter the positive candidate pool.

#### 4.3 Negative Pair Restrictions

Baseline negative pairs must use original samples only.

Negative pairs must satisfy:

- Different problem IDs
- Different source identities
- No known duplicate relationship
- No prohibited lineage relationship
- Valid negative screening results

The assembly stage must preserve the negative pair strategy's screening metadata when available.

#### 4.4 Canonical Pair Identity

Pair identity must be independent of endpoint order.

For any pair of sample IDs `A` and `B`:

- The pair `(A, B)` and `(B, A)` must resolve to the same canonical identity.
- Sample IDs must be sorted consistently before pair identity is determined.
- Self-pairs are prohibited.

Canonical ordering prevents duplicate reversed pairs from entering the assembled candidate pool.

#### 4.5 Duplicate Candidate Handling

Duplicate candidates with the same canonical pair identity and the same label must be consolidated into a single assembled record.

Deduplication must not depend on input order.

Duplicate records must not silently discard meaningful provenance. Where multiple generation records exist, the assembly report should retain duplicate statistics and source information.

#### 4.6 Label Conflict Handling

A label conflict occurs when the same canonical pair identity appears with different labels.

Example:

- Pair `(A, B)` appears in the positive candidate pool with label `1`.
- Pair `(B, A)` appears in the negative candidate pool with label `0`.

This is a critical integrity violation.

The assembly stage must:

1. Detect the canonical pair identity conflict.
2. Record the conflicting candidate sources and labels.
3. Mark the conflict as a critical error.
4. Prevent the conflicting pair from entering the assembled pool.
5. Fail the assembly run under the critical failure policy.

Assembly must never resolve label conflicts by arbitrarily choosing one label.

---

### 5. Split Integrity

Split assignment must occur at source level before pair generation.

Every pair must inherit split information from its source endpoints.

The assembly stage must enforce the following rules:

- Both endpoints of a pair must belong to the same split.
- A pair must not cross train, validation, or test boundaries.
- Variants must inherit split assignment from their original samples.
- Assembly must not independently assign or modify splits.
- Invalid or missing split assignments must be rejected or treated as a critical configuration error, depending on the scope of the failure.

Split integrity is mandatory for preventing data leakage.

---

### 6. Candidate Resolution Policy

Candidate assembly must handle invalid or conflicting records according to deterministic rules.

| Situation | Resolution |
|---|---|
| Duplicate pair with same label | Consolidate into one canonical record |
| Duplicate pair with conflicting labels | Critical error |
| Self-pair | Reject candidate |
| Cross-split pair | Reject candidate and report integrity violation |
| Variant not accepted | Reject candidate |
| Missing endpoint | Reject candidate |
| Invalid metadata | Reject candidate |
| Invalid schema | Reject candidate |
| Repeated generation of the same candidate | Deduplicate |
| Unknown candidate source | Reject candidate |

Rejected candidates must not enter the assembled pool.

Rejection reasons must be recorded using structured reason codes where possible.

---

### 7. Deterministic Assembly

Assembly must be reproducible.

Given the same:

- Original sample metadata
- Variant registry
- Variant validation registry
- Split assignments
- Positive candidate inputs
- Negative candidate inputs
- Pair generation configuration
- Assembly configuration
- Pipeline version

the assembly process must produce the same assembled candidate pool and equivalent reports.

Determinism requirements:

- Canonical pair identity
- Stable deduplication
- Stable ordering of output records
- Stable conflict detection
- No dependence on filesystem iteration order
- No dependence on arbitrary candidate input ordering

Candidate IDs and pair IDs, if generated during assembly, must follow deterministic rules.

---

### 8. Assembly Report

Each assembly run must generate a report containing candidate statistics and rejection information.

#### 8.1 Required Statistics

The report must include:

- Positive candidates received
- Negative candidates received
- Total candidates received
- Unique canonical pair identities
- Duplicate candidates consolidated
- Self-pairs rejected
- Missing endpoint candidates rejected
- Invalid metadata candidates rejected
- Invalid schema candidates rejected
- Split violations
- Label conflicts
- Invalid candidates rejected
- Final assembled candidate count

#### 8.2 Rejection Statistics

Rejections must be categorized by reason.

The report should provide:

- Rejection reason code
- Candidate count for each reason
- Candidate source pool
- Relevant pair identities where appropriate

#### 8.3 Run Metadata

The report must also include:

- `run_id`
- Generation seed, if applicable
- Assembly configuration
- Pipeline version
- Input artifact references
- Execution timestamp
- Assembly status

The report is intended for auditability and reproducibility.

---

### 9. Failure Policy

Assembly failures are divided into critical failures and candidate-level failures.

#### 9.1 Critical Failures

Critical failures invalidate the assembly run.

Examples:

- Label conflict
- Split leakage
- Invalid assembly configuration
- Invalid global schema
- Unreliable source mapping
- Integrity violations affecting the entire assembly process

When a critical failure occurs:

- The run must be marked failed.
- The assembled pool must not be treated as valid output.
- Final dataset export must not proceed.
- The error must be recorded in the run report.

#### 9.2 Candidate-Level Failures

Candidate-level failures affect individual candidates only.

Examples:

- Self-pair
- Missing endpoint
- Unaccepted variant
- Candidate metadata error
- Invalid candidate record

Candidate-level failures must be rejected and recorded.

The assembly process may continue processing other candidates if the remaining inputs and global integrity are reliable.

---

### 10. Relationship to Final Selection and Balancing

Candidate assembly produces a validated candidate pool.

It does not perform:

- Label balancing
- Problem-level balancing
- Endpoint frequency balancing
- Diversity selection
- Final pair quota selection
- Dataset split reassignment
- Training dataset export

These operations belong to subsequent final selection, balancing, validation, and export stages.

The assembled pool is an intermediate artifact and must not be treated as the final training dataset.

---

### 11. Acceptance Criteria

The assembly strategy is considered valid when the implementation satisfies the following:

- Positive and negative candidates are assembled independently.
- Only accepted variants are eligible for positive candidates.
- Baseline negative candidates use original samples only.
- Canonical pair identity is enforced.
- Duplicate pairs are consolidated deterministically.
- Label conflicts are detected and treated as critical errors.
- Split integrity is enforced.
- Assembly does not perform balancing.
- Assembly is reproducible.
- Assembly reports include required statistics and rejection reasons.
- Critical failures prevent invalid outputs from being used downstream.
- Candidate-level failures are isolated and recorded.

---

### 12. Design Decision Summary

The candidate assembly stage is a strict consolidation and integrity boundary between candidate generation and final pair selection.

Its primary responsibilities are correctness, consistency, traceability, and reproducibility.

Assembly must not make decisions that belong to candidate generation or final balancing. It must preserve approved pair-generation policies, reject invalid candidates, detect critical conflicts, and provide a trustworthy assembled pool for downstream processing.

Only candidates that satisfy the assembly integrity rules may proceed to final selection, balancing, and export.



---

## Part 8 — Final Pair Selection & Balancing Integration

### 1. Purpose

This document defines the strategy for selecting the final pair dataset from the assembled pair candidate pool.

The selection process integrates the previously defined pair generation, validation, sampling, and balancing strategies to produce a final dataset suitable for subsequent model training and evaluation.

The selection process must:

- Operate only on assembled and validated pair candidates.
- Preserve pair labels and pair identities.
- Maintain source-level split isolation.
- Balance positive and negative pairs where possible.
- Improve problem distribution and endpoint diversity.
- Ensure deterministic selection under a fixed configuration and seed.
- Report selection results and limitations transparently.

This checkpoint focuses exclusively on final pair selection and balancing integration.

It does not implement pair generation, variant generation, model training, or evaluation.

---

### 2. Input Data

The final selection process receives the following inputs:

| Input | Description |
|---|---|
| Assembled candidate pool | Validated positive and negative pair candidates |
| Pair schema | Approved pair record structure |
| Sample metadata | Sample IDs, problem IDs, source paths and related metadata |
| Source split assignments | Train, validation, and test assignments at source level |
| Label information | Positive and negative labels |
| Sampling configuration | Selection parameters and diversity preferences |
| Balancing configuration | Label balance and problem distribution preferences |
| Random seed | Seed used for deterministic selection |

The candidate pool must have passed the candidate assembly and validation checkpoint before selection begins.

The selection process must not generate new pairs or modify existing pair labels.

---

### 3. Split-wise Selection

Selection must be performed independently for each dataset split:

- Train
- Validation
- Test

Candidates belonging to one split must never be transferred to another split to improve balance.

The selection process must preserve the source-level split assignments established before pair generation.

For every selected pair:

- Both endpoints must belong to the same split.
- The pair must remain in its original split.
- Variants must inherit the split of their original source.
- No source may cross dataset splits through pair selection.

Selection must not reassign samples or pairs between splits.

---

### 4. Label Balancing Strategy

Positive and negative pair counts should be balanced independently within each split.

For split \(s\), let:

- \(P_s\): number of valid positive pair candidates.
- \(N_s\): number of valid negative pair candidates.

The target number of selected pairs per label is:

\[
Q_s = \min(P_s, N_s)
\]

Therefore:

\[
P_s^{selected} = N_s^{selected} = Q_s
\]

when sufficient valid candidates are available.

#### 4.1 Selection Rules

- Select equal numbers of positive and negative pairs whenever feasible.
- Do not oversample existing pairs.
- Do not duplicate pairs to achieve balance.
- Do not create artificial pairs during balancing.
- Do not move candidates between splits.
- Preserve excess candidates in the assembled candidate pool.
- If a split lacks sufficient candidates for one label, select the maximum feasible number and report the resulting imbalance.

Label balance is a target, not a reason to violate pair validity.

---

### 5. Problem Distribution Balancing

Problem distribution should be improved where possible without imposing hard quotas.

The selection process should prefer:

- Relatively balanced representation of problem IDs.
- Reduced dominance by frequently occurring problems.
- Diverse problem combinations among negative pairs.
- Better coverage of available problems.

However, problem distribution is a soft optimization objective.

The selection process must not force the inclusion of invalid candidates or candidates that violate negative pair rules.

If the candidate pool does not provide sufficient diversity, the selection process should preserve pair integrity and report the limitation.

---

### 6. Endpoint Diversity

Endpoint diversity aims to reduce excessive usage of a small number of source samples.

The selection process should prefer candidates that:

- Use samples with lower pair-selection frequency.
- Introduce different endpoints when equivalent candidates are available.
- Reduce excessive concentration of pairs around a small number of samples.
- Improve endpoint coverage across the selected dataset.

#### 6.1 Endpoint Usage

Endpoint usage frequency should be calculated for each source sample.

For a sample \(x\):

\[
F(x) = \text{number of selected pairs containing } x
\]

Selection should prefer lower-frequency endpoints when competing candidates have equivalent validity and priority.

No strict endpoint cap is imposed at this stage.

A hard cap may unnecessarily discard valid candidates and reduce dataset size. Endpoint frequency should instead be monitored and reported for empirical analysis.

---

### 7. Selection Priority

When selection objectives conflict, the following priority order must be respected:

1. Pair integrity and validity
2. Endpoint and pair diversity
3. Label balance
4. Problem distribution refinement

Higher-priority requirements must never be violated to satisfy a lower-priority objective.

For example, label balancing must not introduce invalid negative pairs, and problem balancing must not cause split leakage.

---

### 8. Selection Workflow

The final selection pipeline follows these steps:

1. Load the assembled candidate pool.
2. Verify input schema and metadata.
3. Verify source-level split assignments.
4. Partition candidates by split.
5. Evaluate positive and negative candidate counts per split.
6. Apply label balancing targets.
7. Apply endpoint diversity preferences.
8. Refine problem distribution where feasible.
9. Select final pairs using deterministic selection rules.
10. Normalize final pair records.
11. Validate the selected dataset.
12. Generate selection reports.
13. Export final selected pairs and split indexes.

Candidate selection and final validation must remain separate stages.

Selection must not silently modify candidate metadata or labels.

---

### 9. Determinism and Reproducibility

The selection process must be reproducible under the same inputs and configuration.

Determinism requirements:

- Fixed random seed.
- Fixed selection configuration.
- Stable candidate ordering.
- Stable priority rules.
- Seeded random tie-breaking only when necessary.
- No dependence on filesystem ordering.
- No dependence on input arrival order.
- No uncontrolled randomness.

The same candidate pool, configuration, and seed must produce the same selected pair dataset.

The selection process must record enough information to reproduce a selection run.

---

### 10. Candidate Preservation

Selection must not destroy or overwrite the assembled candidate pool.

The candidate pool and selected dataset are distinct artifacts.

The assembled pool contains candidates that passed the assembly stage, while the selected dataset contains the subset chosen for downstream use.

Unselected candidates must remain available for:

- Future selection experiments.
- Alternative balancing configurations.
- Sampling strategy comparisons.
- Dataset analysis.

Selection should record selected and unselected candidate counts.

---

### 11. Final Dataset Validation

After selection, the resulting dataset must undergo independent validation.

#### 11.1 Structural Validation

Verify:

- Required fields exist.
- Pair IDs are valid.
- Sample references exist.
- Pair records follow the approved schema.
- Pair identity is canonical.
- No self-pairs exist.

#### 11.2 Label Validation

Verify:

- Positive pairs have label `1` and type `positive`.
- Negative pairs have label `0` and type `negative`.
- No conflicting labels exist for the same canonical pair.

#### 11.3 Split Validation

Verify:

- Each pair belongs to exactly one split.
- Both endpoints belong to the same split.
- Source-level split assignments are preserved.
- No source-level leakage exists across train, validation, and test.

#### 11.4 Selection Validation

Verify:

- Every selected pair belongs to the assembled candidate pool.
- No duplicate pairs exist in the selected dataset.
- No pairs were created during selection.
- No labels were modified.
- Selected pair counts match reported counts.

#### 11.5 Balance and Diversity Validation

Report:

- Positive and negative pair counts.
- Label ratio for each split.
- Problem distribution.
- Endpoint frequency distribution.
- Number of unique endpoints.
- Duplicate pair count.
- Split distribution.

Integrity violations must cause the finalization process to fail.

Balance and diversity limitations should generate warnings rather than invalidate otherwise correct pairs.

---

### 12. Output Artifacts

The selection stage produces the following artifacts.

| Artifact | Purpose |
|---|---|
| `assembled_candidates.csv` | Intermediate assembled candidate pool |
| `selected_pairs.csv` | Final selected pair records |
| `train.csv` | Training split index |
| `validation.csv` | Validation split index |
| `test.csv` | Test split index |
| `selection_report.json` | Selection statistics and reproducibility information |

The proposed intermediate paths are:

```text
data/
└── pairs/
    ├── candidates/
    │   └── assembled_candidates.csv
    ├── selected/
    │   └── selected_pairs.csv
    ├── splits/
    │   ├── train.csv
    │   ├── validation.csv
    │   └── test.csv
    └── reports/
        └── selection_report.json
```

The canonical pair schema and split-index conventions must remain consistent with the previously approved Phase 2.5 output design.

The candidate and selected artifacts are intermediate/final selection products and must not introduce a conflicting pair schema or split structure.

---

### 13. Selection Report

The selection report should contain the following information.

#### 13.1 Input Statistics

- Total assembled candidates.
- Positive candidates.
- Negative candidates.
- Candidate counts by split.
- Invalid candidates, if any were rejected during selection checks.

#### 13.2 Selected Statistics

- Total selected pairs.
- Selected positive pairs.
- Selected negative pairs.
- Selected counts by split.
- Label balance per split.

#### 13.3 Distribution Statistics

- Problem distribution.
- Endpoint usage frequency.
- Unique endpoint count.
- Pair diversity statistics.
- Duplicate count.

#### 13.4 Reproducibility Metadata

- Selection seed.
- Configuration version.
- Selection strategy version.
- Input artifact reference.
- Run identifier.

The report must reflect actual selection results rather than target values.

---

### 14. Insufficient Candidate Handling

If the candidate pool does not contain enough valid candidates to achieve the desired selection targets:

- Do not generate additional pairs during selection.
- Do not oversample existing pairs.
- Do not transfer pairs between splits.
- Do not force invalid candidates into the final dataset.
- Select the maximum feasible number of valid pairs.
- Report shortages and resulting imbalance.

The selection stage must be conservative.

Dataset size may be reduced when candidate validity and split integrity require it.

---

### 15. Acceptance Criteria

This checkpoint is considered complete when the final pair selection strategy satisfies the following requirements:

- Selection operates exclusively on assembled candidate pairs.
- Pair labels and identities are preserved.
- Train, validation, and test are selected independently.
- Source-level split integrity is maintained.
- Label balance is applied per split where feasible.
- No oversampling or duplicate pairs are introduced.
- Problem distribution is improved where feasible.
- Endpoint diversity is considered.
- Pair integrity takes priority over balancing.
- Selection is reproducible with a fixed seed and configuration.
- Candidate pools remain preserved.
- Insufficient candidates are handled conservatively.
- A selection report is generated.
- The selected dataset undergoes independent final validation.

---

### 16. Scope Boundary

This checkpoint defines the strategy for integrating candidate assembly with final pair selection and balancing.

It does not define:

- Positive pair generation.
- Negative pair generation.
- Transformation generation.
- Source splitting implementation.
- Model architecture.
- Model training.
- Model evaluation.
- Similarity inference.

These topics belong to their respective checkpoints.

---

### 17. Conclusion

The final pair selection stage transforms a validated candidate pool into a usable pair dataset while preserving pair validity, label integrity, and source-level split isolation.

Balancing and diversity are optimization objectives rather than absolute requirements.

The final dataset must prioritize valid, reproducible, and leakage-free pairs over artificially satisfying numerical targets.

The resulting selected pair dataset will serve as the input artifact for subsequent dataset preparation and model training stages.



---

## Part 9 — Pair Generation Pipeline Integration & Orchestration Design

### 1. Purpose

This document defines the orchestration strategy for integrating the previously designed pair generation, candidate assembly, validation, selection, and balancing components into a unified Pair Generation Pipeline.

The pipeline must:

- Execute pair generation stages in a controlled order.
- Enforce stage dependencies.
- Maintain data integrity between stages.
- Prevent invalid intermediate results from reaching final dataset export.
- Support reproducible pipeline runs.
- Track execution status and failures.
- Preserve intermediate artifacts for auditing.
- Produce a final dataset and pipeline run report.

This checkpoint focuses exclusively on pipeline integration and orchestration design.

It does not implement the pipeline or modify the algorithms defined in previous checkpoints.

---

### 2. Pipeline Overview

The Pair Generation Pipeline consists of the following stages:

1. Load input data and configuration.
2. Verify metadata and source split assignments.
3. Generate positive pair candidates.
4. Generate negative pair candidates.
5. Assemble pair candidates.
6. Validate assembled candidates.
7. Perform final pair selection and balancing.
8. Validate the final selected dataset.
9. Export the final dataset and split indexes.
10. Generate the pipeline run report.

The pipeline must execute stages in the defined order and ensure that each stage receives valid inputs from its required dependencies.

---

### 3. Pipeline Stage Definitions

| Stage | Responsibility | Expected Output |
|---|---|---|
| Input Preparation | Load inputs and configuration | Loaded input artifacts |
| Metadata & Split Verification | Validate metadata and split consistency | Verification result |
| Positive Generation | Generate positive pair candidates | Positive candidate pool |
| Negative Generation | Generate negative pair candidates | Negative candidate pool |
| Candidate Assembly | Combine and normalize candidates | Assembled candidate pool |
| Candidate Validation | Validate candidate integrity | Validation report and valid pool |
| Final Selection | Select pairs and apply balancing | Selected pair dataset |
| Final Validation | Independently validate final dataset | Final validation report |
| Export | Export final dataset and split indexes | Final artifacts |
| Run Reporting | Summarize pipeline execution | Pipeline run report |

Each stage must have a clearly defined responsibility and must not silently perform the responsibilities of another stage.

---

### 4. Stage Dependency Strategy

The pipeline must respect stage dependencies.

#### 4.1 Execution Dependencies

- Input preparation must complete before metadata and split verification.
- Metadata and split verification must pass before pair generation.
- Positive and negative generation must use the same approved split assignments.
- Candidate assembly must receive positive and negative candidate outputs.
- Candidate validation must pass before final selection.
- Final selection must operate only on validated assembled candidates.
- Final validation must pass before final export.
- Run reporting must record the results of all executed stages.

#### 4.2 Dependency Integrity

A stage must not execute when its required upstream stage has failed or produced invalid output.

The pipeline must not:

- Perform final selection on an invalid candidate pool.
- Export an invalid final dataset.
- Reassign pairs or sources between splits.
- Modify pair labels during orchestration.
- Bypass validation stages to force pipeline completion.

---

### 5. Stage Contract

Every pipeline stage must define the following components.

#### 5.1 Input Contract

Defines the required inputs, metadata, configuration, and upstream artifacts needed for execution.

#### 5.2 Processing Responsibility

Defines the operations that the stage is permitted to perform.

Each stage must remain within its designated scope.

#### 5.3 Output Contract

Defines the expected output artifacts, structure, and status.

Downstream stages must rely only on outputs that satisfy the relevant contract.

#### 5.4 Failure Conditions

Defines the conditions under which a stage is considered unsuccessful.

A failed stage must not be treated as a successful stage merely because some intermediate files were created.

---

### 6. Failure Handling Strategy

The pipeline follows a fail-safe execution strategy.

#### 6.1 Failure Classification

| Failure Type | Handling |
|---|---|
| Missing input | Stop pipeline |
| Invalid metadata | Stop pipeline |
| Invalid split assignments | Stop pipeline |
| Generation stage failure | Mark run as failed |
| Candidate-level rejection | Reject candidate and record statistics |
| Assembly integrity failure | Stop pipeline |
| Selection failure | Stop finalization |
| Final validation failure | Prohibit final export |
| Report generation failure | Record incomplete run |

#### 6.2 Critical Failures

Critical failures invalidate the pipeline run.

The pipeline must not silently ignore critical errors or continue exporting a final dataset when its integrity is no longer guaranteed.

Candidate-level rejection is different from pipeline-level failure. Individual invalid candidates may be rejected while the stage continues, provided the stage itself completes according to its validation rules.

---

### 7. Pipeline Run Management

Each execution must be treated as an independent pipeline run.

#### 7.1 Run Metadata

Each run must record:

- `run_id`
- `created_at`
- `seed`
- `config_version`
- `pipeline_version`
- Input artifact references
- Run status

#### 7.2 Run Status

The pipeline uses the following run states:

| Status | Description |
|---|---|
| `PENDING` | Run initialized but not started |
| `RUNNING` | Pipeline stages are executing |
| `COMPLETED` | All required stages completed successfully and final artifacts passed validation |
| `FAILED` | Pipeline terminated due to a critical failure |

A run must not be marked `COMPLETED` if required stages failed, final validation failed, or final artifacts were not successfully produced.

The existence of intermediate artifacts alone does not indicate successful completion.

---

### 8. Intermediate Artifacts and Final Artifacts

Pipeline artifacts must be divided into two categories.

#### 8.1 Intermediate Artifacts

Intermediate artifacts may include:

- Positive candidate pool.
- Negative candidate pool.
- Assembled candidate pool.
- Candidate validation results.
- Selection statistics.
- Intermediate stage reports.

These artifacts support auditing, debugging, and reproducibility.

They must not be mistaken for the final training dataset.

#### 8.2 Final Artifacts

Final artifacts may include:

- Final selected pair dataset.
- Train split index.
- Validation split index.
- Test split index.
- Final validation report.
- Pipeline run report.

Final artifacts are considered valid only after the final validation stage passes.

Artifact paths and naming conventions must remain consistent with the previously approved Phase 2.5 and Phase 2.7.4.2 output designs.

This checkpoint does not introduce a competing output schema or split structure.

---

### 9. Re-run and Reproducibility Strategy

The pipeline must support controlled reruns without affecting previous completed runs.

#### 9.1 Reproducibility Requirements

- Use a fixed seed recorded for each run.
- Record the pipeline and configuration versions.
- Use stable ordering for inputs and candidates.
- Avoid filesystem-order-dependent behavior.
- Avoid uncontrolled randomness.
- Use seeded random tie-breaking only when required.
- Ensure identical inputs, configuration, seed, and pipeline version can reproduce the same outputs.

#### 9.2 Rerun Policy

Each rerun must create an independent run record.

The pipeline must not silently overwrite artifacts belonging to a previously completed run.

By default, a failed run should be rerun from the beginning rather than resumed from an arbitrary stage.

Stage-level resume is deferred because reusing intermediate artifacts without complete dependency verification may compromise reproducibility and data integrity.

---

### 10. Pipeline Run Report

Each pipeline execution must generate a report describing its actual execution.

#### 10.1 Run Information

- Run ID.
- Creation time.
- Seed.
- Configuration version.
- Pipeline version.
- Final status.

#### 10.2 Input Information

- Input metadata references.
- Split assignments.
- Input artifact references.
- Input verification results.

#### 10.3 Stage Information

- Stage name.
- Execution status.
- Stage output references.
- Error information, if applicable.
- Warnings.
- Candidate counts where applicable.

#### 10.4 Generation Information

- Positive candidate statistics.
- Negative candidate statistics.
- Accepted and rejected candidate counts.
- Rejection statistics.

#### 10.5 Assembly and Selection Information

- Assembled candidate counts.
- Duplicate statistics.
- Invalid candidate counts.
- Selected and unselected pair counts.
- Label balance.
- Problem distribution.
- Endpoint diversity statistics.

#### 10.6 Final Validation and Export

- Final validation status.
- Pair counts by split.
- Positive and negative counts per split.
- Exported artifact paths.
- Export status.

The report must reflect actual execution results rather than target values or expected counts.

---

### 11. Pipeline Execution Workflow

The complete pipeline follows this workflow:

1. Initialize a new pipeline run.
2. Load configuration and input artifacts.
3. Validate input metadata and split assignments.
4. Generate positive pair candidates.
5. Generate negative pair candidates.
6. Assemble positive and negative candidates.
7. Validate the assembled candidate pool.
8. Perform final pair selection and balancing.
9. Validate the final selected pair dataset.
10. Export final dataset artifacts.
11. Generate the pipeline run report.
12. Mark the run as completed only if all required stages succeed.

If a critical stage fails, the pipeline must stop the dependent stages and mark the run as failed.

Candidate-level rejection does not necessarily invalidate the entire pipeline run if the candidate processing stage completes successfully and the resulting pool satisfies the required integrity conditions.

---

### 12. Output Consistency

The pipeline must maintain consistency between:

- Assembled candidate pool.
- Selected pair records.
- Pair IDs.
- Train, validation, and test indexes.
- Pair labels.
- Sample references.
- Source split assignments.
- Selection reports.
- Pipeline run reports.

The final split indexes must reference the selected pair dataset correctly.

The pipeline must not create inconsistent pair IDs, missing references, duplicate records, or conflicting split assignments during orchestration.

Output path conventions will be consolidated with the previously approved pair generation output design before implementation.

---

### 13. Scope Boundary

This checkpoint defines the orchestration strategy for the Pair Generation Pipeline.

It does not define or implement:

- Variant generation algorithms.
- Positive pair generation algorithms.
- Negative pair generation algorithms.
- Pair sampling algorithms.
- Candidate assembly implementation.
- Validation implementation.
- Final selection implementation.
- Python package architecture.
- Model architecture.
- Model training.
- Model evaluation.
- Inference.

These responsibilities belong to their respective checkpoints or later implementation phases.

---

### 14. Acceptance Criteria

This checkpoint is considered complete when the pipeline orchestration design satisfies the following criteria:

- [ ] All required pipeline stages are identified.
- [ ] Stage execution order is defined.
- [ ] Stage dependencies are defined.
- [ ] Input and output contracts are specified.
- [ ] Stage responsibilities are clearly separated.
- [ ] Critical failure handling is defined.
- [ ] Candidate-level rejection is distinguished from pipeline-level failure.
- [ ] Run status management is defined.
- [ ] Intermediate and final artifacts are distinguished.
- [ ] Reproducibility requirements are defined.
- [ ] Rerun policy is defined.
- [ ] Pipeline reporting requirements are defined.
- [ ] Final export is protected by validation.
- [ ] Output conventions remain consistent with previous checkpoints.

---

### 15. Conclusion

The Pair Generation Pipeline Orchestration stage integrates the previously designed pair generation, candidate assembly, validation, selection, and balancing components into a single controlled workflow.

The pipeline must prioritize integrity, reproducibility, stage dependency enforcement, and transparent reporting.

A pipeline run is considered successful only when all required stages complete correctly, final validation passes, and final artifacts are successfully produced.

This design establishes the orchestration foundation for the future implementation of the Pair Generation Pipeline.

