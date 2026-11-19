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
