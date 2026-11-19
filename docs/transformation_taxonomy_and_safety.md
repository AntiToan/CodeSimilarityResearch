# Transformation Taxonomy & Safety Constraints

**Project:** CodeSimilarityResearch  
**Checkpoint:** 2.6.2 — Transformation Taxonomy & Safety Constraints  
**Status:** Design specification

---

## 1. Purpose

This document defines the transformation taxonomy used to generate code variants for positive pair construction.

The primary objective is to create modified versions of source code that retain the original program's semantics while introducing controlled syntactic differences.

Transformation safety is critical because positive pairs are assigned a synthetic similarity label of `1`. Unsafe transformations may alter program behavior and introduce label noise into the training dataset.

This specification classifies transformations into:

- Safe transformations — permitted in the baseline.
- Conditional transformations — permitted only after appropriate implementation and validation.
- Unsafe transformations — excluded from baseline generation.

---

## 2. Transformation Classification

### 2.1 Group A — Safe Transformations

These transformations are permitted in the baseline pipeline, subject to their corresponding validation rules.

| Transformation | Description | Baseline |
|---|---|---|
| Whitespace changes | Modify spaces, tabs, blank lines, indentation | Enabled |
| Formatting changes | Modify code formatting without changing tokens | Enabled |
| Comment changes | Add, remove, or modify comments | Enabled with restrictions |

#### A1. Whitespace Changes

Modify whitespace without changing meaningful code tokens.

Examples:
- Indentation changes
- Adding/removing blank lines
- Spacing around operators
- Spacing between tokens where syntactically valid

Constraint:
- The non-whitespace token sequence must remain unchanged.

#### A2. Formatting Changes

Modify the visual layout of source code while preserving the token sequence.

Examples:
- Reformatting braces
- Changing indentation style
- Reformatting expressions
- Splitting or combining lines

Constraint:
- Formatting must not introduce or remove meaningful tokens.

#### A3. Comment Changes

Modify comments without altering executable code.

Examples:
- Adding comments
- Removing comments
- Rewriting existing comments
- Moving comments when safe

Restrictions:
- Comments affecting preprocessing behavior must not be treated as ordinary comments.
- Preprocessor directives and compiler-sensitive constructs must be preserved.
- Comment transformations must be validated against the language's tokenization rules.

---

### 2.2 Group B — Conditional Transformations

These transformations may be used only when their implementation and validation mechanisms are sufficiently reliable.

They are not automatically enabled in the initial baseline.

| Transformation | Description | Baseline |
|---|---|---|
| Local variable renaming | Rename local variables consistently | Gated |
| Function-local identifier renaming | Rename identifiers within valid scopes | Gated |
| Parameter renaming | Rename function parameters | Disabled by default |
| Compound transformations | Combine multiple transformations | Experimental / disabled |

#### B1. Local Variable Renaming

Rename local variables while preserving all references to the same variable.

Requirements:
- Scope-aware identification
- Consistent renaming of declaration and references
- Collision detection
- No accidental renaming of unrelated identifiers
- Token-level validation

Simple textual replacement is prohibited.

#### B2. Function-Local Identifier Renaming

Rename eligible identifiers inside a function while preserving their relationships and references.

Requirements:
- Correct identifier resolution
- Scope awareness
- Reference consistency
- Collision prevention
- Exclusion of identifiers that cannot be safely resolved

This transformation must not modify function behavior or interfaces.

#### B3. Parameter Renaming

Rename function parameters and their references.

Risks:
- Interface compatibility
- Function pointer usage
- Macro references
- External or indirect references

This transformation remains disabled by default until its safety constraints are formally implemented and validated.

#### B4. Compound Transformations

Combine two or more transformations into one variant-generation operation.

Examples:
- Formatting + comment modification
- Formatting + local variable renaming

Compound transformations introduce additional validation complexity.

Requirements:
- Each constituent transformation must independently be permitted.
- Each constituent transformation must have a valid configuration.
- The combined result must pass whole-variant validation.
- Transformation order must be recorded.
- Compound transformations must not bypass individual safety restrictions.

Compound transformations are reserved for a later experimental stage.

---

### 2.3 Group C — Unsafe or Excluded Transformations

These transformations are excluded from baseline positive variant generation.

| Transformation | Reason for exclusion |
|---|---|
| Statement reordering | May change execution order or dependencies |
| Control flow modification | May change program behavior |
| Constant/literal replacement | May alter outputs |
| Arbitrary identifier replacement | May break references or semantics |
| Statement insertion | May introduce behavior |
| Statement deletion | May remove behavior |
| Operator replacement | May change computation |
| Function modification | May alter function behavior or contracts |
| Algorithm modification | Changes the underlying solution logic |
| Uncontrolled code mutation | Cannot provide reliable semantic guarantees |

These transformations must not be used to create positive pairs under the baseline labeling policy.

They may be investigated separately in future research experiments, but any such experiment must define its own labeling and validation methodology.

---

## 3. Common Safety Constraints

All transformation implementations must comply with the following constraints.

### 3.1 Original Source Protection

- Original source files are immutable.
- Transformation operations must never overwrite original files.
- All variants must be stored in the designated variants directory.

### 3.2 Controlled Modification

- Each transformation may only modify elements permitted by its classification.
- No unrelated modification is allowed.
- Transformation behavior must be deterministic when provided the same input, configuration, and seed.

### 3.3 Traceability

Every variant must be traceable to:

- Original sample ID
- Transformation type
- Transformation configuration
- Generation seed, when applicable
- Generator version
- Validation result

This information must be recorded in the variant registry according to the variant data model.

### 3.4 Fail-Safe Generation

If a transformation encounters:

- Ambiguous identifier resolution
- Scope uncertainty
- Name collision
- Parsing failure
- Unexpected token changes
- Potential semantic modification
- Unsupported source construct

The transformation must reject the variant rather than force acceptance.

### 3.5 No Unclassified Transformations

Every transformation must belong to a documented category and have defined validation requirements.

Unknown or undocumented transformation types must not enter the baseline generation pipeline.

---

## 4. Validation Requirements by Transformation

| Transformation | Minimum validation requirement |
|---|---|
| Whitespace changes | Token preservation |
| Formatting changes | Token sequence preservation |
| Comment changes | Non-comment token preservation + preprocessing-sensitive checks |
| Local variable renaming | Scope/reference consistency + collision checks + token validation |
| Function-local identifier renaming | Scope/reference consistency + collision checks + token validation |
| Parameter renaming | Interface/reference validation + token validation |
| Compound transformations | Individual validation + whole-variant validation |

### 4.1 Token Preservation

For transformations that should not modify meaningful tokens, the token sequence before and after transformation must remain identical.

Token preservation is a validation method for formatting-related transformations. It is not a universal proof of semantic equivalence for all transformation types.

### 4.2 Renaming Validation

Identifier renaming requires stronger checks than formatting transformations.

Validation must ensure:
- The intended identifier was renamed.
- All valid references were renamed consistently.
- Unrelated identifiers remain unchanged.
- No identifier collision was introduced.
- The transformed code remains syntactically valid.

### 4.3 Compound Validation

Compound transformations must be validated both individually and as a complete result.

Passing individual checks does not automatically guarantee that a combination is valid.

---

## 5. Baseline Transformation Policy

### 5.1 Enabled

The initial baseline allows:

1. Whitespace changes
2. Formatting changes
3. Comment changes, subject to preprocessing-related restrictions

These transformations are preferred because they can introduce syntactic diversity with relatively low semantic risk.

### 5.2 Gated

The following transformations are candidates for enabling after their implementation and validators are ready:

1. Local variable renaming
2. Function-local identifier renaming

A transformation may be enabled only when its safety requirements are implemented and tested.

### 5.3 Disabled by Default

1. Parameter renaming
2. Compound transformations

These may be revisited after the baseline is established and independently evaluated.

### 5.4 Excluded

All transformations in Group C remain excluded from baseline positive pair generation.

---

## 6. Transformation Acceptance Policy

A transformation is eligible for acceptance only when:

1. It belongs to an allowed transformation category.
2. Its implementation complies with the defined safety constraints.
3. The required validator is available.
4. The variant passes all applicable validation rules.
5. The variant has valid lineage metadata.
6. The variant can be reproduced or traced according to the generation configuration.

A variant that fails validation must be rejected.

Only accepted variants are eligible for positive pair construction.

---

## 7. Relationship to Positive Pair Generation

The transformation taxonomy directly controls the positive pair pipeline.

The intended flow is:

Original Source  
→ Transformation Selection  
→ Variant Generation  
→ Transformation Validation  
→ Variant Acceptance / Rejection  
→ Positive Pair Candidate Generation

Only accepted variants may be used to create positive pairs.

The synthetic label `1` indicates that the pair was generated under the project's positive-pair construction rules. It does not represent independently verified plagiarism or human-annotated semantic equivalence.

---

## 8. Future Extensions

The following topics are outside the scope of this checkpoint:

- Implementing transformation algorithms
- Selecting transformation probabilities
- Selecting the number of variants per original sample
- Implementing AST-based renaming
- Implementing validators
- Compiler integration
- Automated testing of semantic equivalence
- Compound transformation experiments
- Evaluating the impact of transformations on model performance

These topics will be addressed in subsequent checkpoints.

---

## 9. Design Decision Summary

The project adopts a conservative transformation policy.

The baseline prioritizes reliable synthetic positive labels over aggressive code mutation. Transformations that introduce semantic uncertainty are gated or excluded.

This policy is intended to reduce label noise, preserve source lineage, maintain reproducibility, and provide a reliable foundation for future experiments in code similarity research.
