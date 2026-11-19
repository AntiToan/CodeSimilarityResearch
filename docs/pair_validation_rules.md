# Pair Validation Rules

## 1. Purpose

This document defines the validation rules for generated code similarity pairs in the CodeSimilarityResearch project.

The validation process ensures that pair records are structurally valid, reference existing samples, follow positive/negative pair constraints, respect dataset splits, and preserve the integrity of the pair dataset.

Validation distinguishes between mandatory constraints and soft distribution targets.

- **FAIL**: A mandatory constraint is violated.
- **WARNING**: A soft target is not achieved, but the dataset may still be valid.
- **PASS**: All mandatory validation rules are satisfied.

---

## 2. Validation Scope

Pair validation is divided into the following layers:

1. Schema validation
2. Sample reference validation
3. Pair semantic validation
4. Canonical identity and duplicate validation
5. Split and leakage validation
6. Sampling and distribution audit

Each layer is responsible for validating a different aspect of the pair dataset.

---

## 3. Schema Validation

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

## 4. Sample Reference Validation

Every pair must reference existing samples in the sample metadata.

Validation rules:

- `sample_a_id` and `sample_b_id` must exist.
- Neither sample reference may be missing or invalid.
- A sample cannot be paired with itself.
- Source IDs and problem IDs recorded in the pair must match the referenced samples' metadata.

Invalid or dangling references result in **FAIL**.

---

## 5. Positive Pair Validation

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

## 6. Negative Pair Validation

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

## 7. Canonical Pair Identity and Duplicate Validation

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

## 8. Split and Leakage Validation

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

## 9. Sampling and Distribution Audit

Sampling and distribution objectives are soft targets. Their violation does not automatically invalidate an individual pair.

The validator/auditor should report the following:

### 9.1 Label balance

- Positive pair count
- Negative pair count
- Positive-to-negative ratio
- Deviation from the target 1:1 balance

Target: 1:1 positive and negative pairs.

Deviation results in **WARNING**.

### 9.2 Problem distribution

Report pair representation across the 104 problem groups, including:

- Positive pair counts by problem
- Negative anchor counts by problem
- Negative endpoint coverage
- Underrepresented and overrepresented problems

Problem distribution imbalance results in **WARNING**.

### 9.3 Negative sampling quota

Target: 3 valid negative pairs per anchor.

The target does not represent a mandatory final quota.

- Report actual negative pairs per anchor.
- Report anchors with fewer than 3 valid negative pairs.
- Do not force invalid or suspicious pairs to satisfy the quota.
- Use bounded retries.
- Preserve valid pairs even if the target cannot be reached.

Failure to reach the target results in **WARNING**, not **FAIL**.

### 9.4 Source frequency and diversity

Report:

- Samples appearing unusually frequently
- Negative endpoint frequency
- Problem diversity
- Candidate coverage
- Sampling rejection counts

Unusual source frequency or low candidate coverage results in **WARNING**.

---

## 10. Validation Severity

### Mandatory constraints — FAIL

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

### Soft targets — WARNING

The following conditions should generate warnings without automatically invalidating the dataset:

- Label ratio deviates from 1:1
- Problem distribution is imbalanced
- An anchor has fewer than 3 negative pairs
- High source frequency
- Low candidate coverage
- Sampling quota not achieved
- Distribution diversity is lower than expected

---

## 11. Validation Workflow

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

## 12. Validation Output

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

## 13. Acceptance Criteria

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

## 14. Design Principles

The validation system follows these principles:

1. **Integrity before balance** — Never accept invalid pairs to achieve a target ratio.
2. **Validity before quantity** — A smaller valid dataset is preferable to a larger contaminated dataset.
3. **Warnings are transparent** — Soft-target deviations must be reported.
4. **No silent repairs** — The validator must not silently alter pair records.
5. **Reproducibility** — Validation must be repeatable with the same inputs and configuration.
6. **Synthetic labels are not ground truth** — Positive and negative labels represent the project's construction strategy, not verified plagiarism judgments.

---

## 15. Status

Checkpoint: **2.5.4.2 — Pair Validation Rules Design**

Status: **Design completed, pending repository commit.**
