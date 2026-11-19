# Positive Pair Strategy Design

## 1. Overview

This document defines the strategy for generating positive code similarity pairs for the CodeSimilarityResearch project using the POJ-104 dataset.

Positive pairs are constructed from the same original source code sample and its safely transformed variants.

This checkpoint is design-only. No variants, pairs, or labels are generated yet.

## 2. Objective

The objective is to generate positive pairs representing source code that remains semantically equivalent to its original version despite controlled transformations.

The generated pairs will be used as synthetic training examples for code similarity modeling.

## 3. Positive Pair Definition

A positive pair consists of:

- An original source code sample.
- A variant generated from that same source through controlled transformations.

The original sample and its variant are assigned a positive similarity label.

**Label convention:** `1` = positive pair.

Positive labels represent synthetic transformation-based similarity, not verified plagiarism relationships.

## 4. Transformation Strategy

### 4.1 Accepted Transformations

| Transformation | Description | Safety |
|---|---|---|
| Formatting changes | Modify indentation and formatting | High |
| Whitespace normalization | Change unnecessary whitespace | High |
| Comment modification | Add, remove, or modify comments | High |
| Local variable renaming | Rename local variables with scope-aware handling | High, with validation |
| Function-local identifier renaming | Rename eligible identifiers without collisions | High, with validation |

Identifier transformations must avoid changing language keywords, function signatures where not intended, library identifiers, macros, or other references that may alter behavior.

### 4.2 Deferred or Rejected Transformations

| Transformation | Reason |
|---|---|
| Statement reordering | May change execution behavior or dependencies |
| Control-flow modification | May alter program semantics |
| Constant/literal changes | May change outputs or behavior |
| Arbitrary statement insertion/removal | May change program logic |
| Uncontrolled identifier replacement | May introduce collisions or invalid code |

These transformations are not included in the initial positive pair generation strategy.

## 5. Generation Workflow

1. Select an original sample.
2. Select an eligible transformation.
3. Generate a code variant.
4. Validate the generated source.
5. Reject invalid variants.
6. Record transformation metadata and original lineage.
7. Construct a positive pair from the original and accepted variant.
8. Assign the positive label.

## 6. Lineage and Metadata

Each generated variant must maintain traceability to its original sample.

Recommended metadata:

- `variant_id`
- `original_sample_id`
- `transformation_type`
- `transformation_config`
- `transformed_source_path`
- `validation_status`

Lineage information is essential for dataset splitting and leakage prevention.

## 7. Validation Requirements

Generated variants must:

- Remain syntactically valid where validation is supported.
- Avoid accidental identifier collisions.
- Preserve intended program semantics.
- Maintain the original sample lineage.
- Be reproducible when transformation configuration and random seed are recorded.

Syntax validation alone does not guarantee semantic equivalence. Transformation safety and testing must be considered separately.

## 8. Label Interpretation

Positive labels are synthetic labels derived from known transformations.

They do not establish that two real-world programs are plagiarized or that every generated transformation is perfectly semantics-preserving.

The dataset will be used to train a code similarity model, not to make definitive plagiarism judgments.

## 9. Scope of This Checkpoint

This checkpoint defines the positive pair strategy only.

It does not implement:

- Transformation code
- Variant generation
- Pair generation
- Label creation
- Dataset splitting
- Model training

## 10. Status

**Checkpoint 2.7.3.1 – Positive Pair Strategy Design: COMPLETED**

- [x] Positive pair definition
- [x] Transformation categories
- [x] Safe transformation scope
- [x] Deferred transformations
- [x] Generation workflow
- [x] Lineage metadata requirements
- [x] Validation principles
- [x] Synthetic label interpretation
