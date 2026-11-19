# Pair Schema and Pairing Rules

## 1. Overview

This checkpoint defines the pair record schema, pair identity rules, storage format, and validation requirements for the CodeSimilarityResearch project.

Pair records reference source samples using IDs rather than duplicating source code content.

This checkpoint is design-only. No pair records are generated yet.

## 2. Pair Record Schema

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

## 3. Pair Definition

### Positive pairs

An original source and its generated variant from the same lineage.

- Label: `1`
- Pair type: `positive`
- Both samples must share the same original lineage.

### Negative pairs

Two original samples selected using cross-problem sampling and negative candidate filtering.

- Label: `0`
- Pair type: `negative`
- Different problem IDs
- Different source lineage
- No known duplicate relationship
- Candidate must pass the defined similarity screening strategy

Labels represent synthetic/heuristic similarity relationships, not confirmed plagiarism ground truth.

## 4. Canonical Ordering

Pair identity is independent of sample order.

The two sample IDs are sorted lexicographically before pair record creation.

The pairs `(A, B)` and `(B, A)` are treated as the same pair.

Only one canonical record is stored.

## 5. Pair Storage

Pair metadata is stored in CSV format.

Source code files are stored separately and referenced by sample IDs.

This avoids source duplication, reduces storage, and supports independent source and pair management.

Proposed location:

`data/pairs/`

## 6. Pair Identity and Duplicate Prevention

Pair generation must:

1. Verify that sample IDs are different.
2. Sort IDs canonically.
3. Generate a canonical pair key.
4. Check whether the pair already exists.
5. Reject duplicate pair records.

Pair identity is independent of label. A pair must not appear with conflicting positive and negative labels.

## 7. Split Assignment

Original samples must be assigned to train, validation, and test before pair generation.

Pairs may only be created within their assigned partition.

- Positive pairs must inherit the split of their original lineage.
- Negative pairs must use two samples belonging to the same partition.
- Cross-partition pairs are prohibited.

Split ratios and grouping details are deferred to the split design checkpoint.

## 8. Validation Rules

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

## 9. Proposed Storage Structure

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

## 10. Scope

This checkpoint defines pair schema and pairing rules only.

It does not implement:

- Pair generation
- Pair validation scripts
- Positive or negative labels
- Dataset split assignment
- Pair sampling or balancing

## 11. Status

**Checkpoint 2.5.1 – Pair Schema and Pairing Rules: COMPLETED**

- [x] Pair record schema
- [x] Positive/negative definitions
- [x] Canonical ordering
- [x] Pair identity
- [x] Duplicate prevention
- [x] CSV storage design
- [x] Split consistency rules
- [x] Pair validation requirements
