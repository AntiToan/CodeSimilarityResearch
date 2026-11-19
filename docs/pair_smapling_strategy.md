# Pair Sampling Strategy Design

## 1. Overview

This checkpoint defines the sampling strategy for generating negative code similarity pairs in CodeSimilarityResearch using POJ-104.

The goal is to control pair volume, improve problem diversity, maintain reproducibility, and avoid exhaustive pair generation.

This checkpoint is design-only. No pairs are generated yet.

## 2. Motivation

The POJ-104 dataset contains 52,000 source samples.

Exhaustive unique pair generation would produce:

\[
\frac{52,000 \times 51,999}{2}
= 1,351,974,000
\]

pairs, which is unnecessary for the initial research experiments.

Controlled sampling is therefore required.

## 3. Sampling Method

The initial strategy uses a combination of:

- Per-anchor sampling
- Problem-balanced selection

Each original sample acts as an anchor. Negative candidates are selected from different problem IDs.

## 4. Sampling Workflow

For each anchor:

1. Select the anchor sample.
2. Randomly select a problem ID different from the anchor's problem ID.
3. Select a sample from the selected problem.
4. Check negative pair eligibility.
5. Apply duplicate, lineage, and similarity screening.
6. Accept valid candidates.
7. Repeat until the quota is reached or retry limits are exhausted.

## 5. Negative Quota

The initial quota is three valid negative pairs per anchor.

| Configuration | Value |
|---|---:|
| Anchors | 52,000 |
| Negative quota per anchor | 3 |
| Initial negative selection target | 156,000 |

The 156,000 figure represents the target number of negative pair selections before deduplication and filtering. The final unique pair count may be lower.

## 6. Problem Diversity

The sampling strategy prioritizes selecting three negative pairs from three different problem IDs.

This reduces over-reliance on a single problem source and encourages diversity in the negative pair dataset.

The selected problem IDs must differ from the anchor's problem ID.

## 7. Eligibility Rules

Negative candidates must:

- Have a different sample ID from the anchor.
- Have a different problem ID.
- Have different source lineage.
- Not belong to known exact duplicate groups.
- Not violate negative pair constraints.
- Pass the configured similarity screening.
- Not already exist as a canonical pair.

## 8. Reproducibility

Sampling must use a configured deterministic random seed.

Given the same dataset, configuration, and seed, sampling should be reproducible.

Sampling parameters must be recorded for auditability.

## 9. Quota Failure Handling

If an anchor cannot obtain three valid negative pairs:

- Retain the valid pairs obtained.
- Do not force acceptance of suspicious candidates.
- Do not use an unlimited retry loop.
- Record the actual count and failure/rejection information.
- Report sampling coverage during validation.

Pair quality takes precedence over satisfying the quota.

## 10. Efficiency

Exhaustive Cartesian pair generation is not used.

The sampling procedure should operate on problem-level candidate pools and sample only the candidates required to meet the quota.

This keeps pair generation manageable for the initial experiments.

## 11. Scope

This checkpoint defines the negative pair sampling strategy only.

It does not implement:

- Sampling code
- Negative pair generation
- Pair balancing
- Positive pair quota
- Positive-to-negative ratio
- Similarity screening implementation
- Dataset splitting

## 12. Status

**Checkpoint 2.5.2 – Pair Sampling Strategy Design: COMPLETED**

- [x] Per-anchor sampling
- [x] Problem-balanced selection
- [x] Negative quota
- [x] Problem diversity
- [x] Deterministic seed
- [x] Eligibility rules
- [x] Quota failure handling
- [x] Non-exhaustive sampling
