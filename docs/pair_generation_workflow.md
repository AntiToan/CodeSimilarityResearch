# Pair Generation Workflow

## 1. Objective

This document defines the overall workflow for generating the code similarity pair dataset.

The workflow integrates the previously defined pair schema, positive and negative pair strategies, sampling, balancing, filtering, and validation requirements.

This checkpoint defines the workflow only. Implementation will be conducted in later checkpoints.

## 2. Inputs

The pair generation workflow requires:

- Preprocessed source files.
- Sample metadata.
- Exact duplicate analysis.
- Variant metadata and source lineage information (when available).
- Source-level split assignments.
- Pair generation and sampling configuration.

Some inputs, including variant metadata and split assignments, are dependencies that must be prepared before actual pair generation.

## 3. Workflow Overview

The pair generation pipeline follows these stages:

1. Load and verify dataset inputs.
2. Assign source-level dataset splits.
3. Generate positive pair candidates.
4. Generate negative pair candidates.
5. Filter invalid candidates.
6. Sample and balance selected pairs.
7. Validate the selected pair dataset.
8. Export pair indexes and audit reports.

## 4. Stage 1 — Load and Verify Dataset

Load sample metadata and source references.

Verify:

- Sample IDs are unique.
- Source paths are valid.
- Required metadata fields are available.
- Source files are readable.
- Dataset references are consistent.

Invalid input records must be reported and must not silently enter pair generation.

## 5. Stage 2 — Assign Dataset Splits

Assign train, validation, and test splits at the source level before generating pairs.

All samples belonging to the same source lineage, including original and controlled variants, must remain in the same split.

Pair generation must operate within each split independently.

No pair may contain samples from different splits.

The split ratios and assignment method require a separate design decision before implementation.

## 6. Stage 3 — Generate Positive Pair Candidates

Positive candidates are generated using the approved positive pair strategy.

Candidate pairs may include:

- Original source paired with a valid controlled variant.
- Other positive relationships explicitly approved by the positive pair strategy.

Each candidate must preserve source lineage information.

Positive candidate generation must not introduce uncontrolled semantic changes or unsupported similarity labels.

## 7. Stage 4 — Generate Negative Pair Candidates

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

## 8. Stage 5 — Candidate Filtering

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

## 9. Stage 6 — Sampling and Balancing

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

## 10. Stage 7 — Pair Validation

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

## 11. Stage 8 — Export Dataset and Reports

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

## 12. Candidate Pool and Selected Pairs

Candidate generation and final pair selection are separate stages.

The candidate pool contains potential pairs that can be audited or considered for sampling.

Selected pairs form the dataset used for training and evaluation.

Not all generated candidates must be selected.

Unused candidates should remain available when retention is supported by the pipeline, enabling alternative sampling experiments without regenerating candidates unnecessarily.

## 13. Data Leakage Prevention

Leakage prevention is enforced through source-level split assignment.

- Splits must be assigned before pair generation.
- All source lineages must remain in the same split.
- Pair generation must be isolated within each split.
- No pair may connect samples from different splits.
- Pair generation and balancing must not move samples across splits.

## 14. Reproducibility

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

## 15. Dependencies Before Implementation

The following decisions must be finalized before actual pair generation:

- Dataset split strategy and ratios.
- Variant generation and lineage schema.
- Similarity screening method and thresholds.
- Pair validation rules.
- Candidate retention and output structure.

## 16. Expected Outcome

The workflow produces a valid, reproducible, auditable pair dataset with controlled positive and negative sampling, split isolation, balancing, and validation.

This checkpoint defines the overall workflow only. Detailed validation rules, output structure, audit design, and implementation are handled by subsequent checkpoints.
