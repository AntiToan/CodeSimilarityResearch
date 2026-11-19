# Transformation Validation Strategy

**Project:** CodeSimilarityResearch  
**Checkpoint:** 2.6.3 — Transformation Validation Strategy  
**Status:** Design specification

---

## 1. Purpose

This document defines the validation strategy for code variants generated during the variant generation process.

The objective is to ensure that generated variants satisfy structural requirements, comply with their declared transformation rules, and provide sufficient evidence of validity before being used in positive pair generation.

A generated variant is not automatically considered valid.

Only variants that pass all mandatory validation requirements may be accepted into the positive pair candidate pool.

---

## 2. Validation Pipeline

The validation pipeline is positioned between variant generation and positive pair generation.

The intended workflow is:

Original Source  
→ Variant Generation  
→ Validation Pipeline  
→ Accepted / Rejected  
→ Positive Pair Candidate Generation

Validation is performed independently for each variant.

A failure in one variant must not automatically interrupt the entire batch. However, critical validation infrastructure failures must be reported because they may affect the reliability of the overall batch.

---

## 3. Validation Levels

Validation is organized into four levels.

### V1 — Structural Validation

Purpose: Verify the integrity of the variant, its files, and its metadata.

Checks include:

- Variant file exists.
- Variant file is not empty.
- Original source exists.
- Variant ID is valid and unique.
- Original sample ID is correct.
- Transformation type is recognized.
- Required metadata is present.
- Variant does not overwrite the original source.
- File paths comply with the project structure.

V1 must pass before a variant proceeds through the remaining validation stages.

### V2 — Transformation Validation

Purpose: Verify that the transformation was performed according to its declared rules.

Examples:

| Transformation | Validation |
|---|---|
| Whitespace changes | Token sequence preservation |
| Formatting changes | Token sequence preservation |
| Comment changes | Non-comment token preservation and preprocessing-sensitive checks |
| Local variable renaming | Scope/reference consistency, collision checks, token validation |
| Function-local identifier renaming | Scope/reference consistency, collision checks, token validation |
| Parameter renaming | Interface/reference validation and token validation |
| Compound transformations | Individual transformation validation and whole-result validation |

V2 is the primary validation level for synthetic positive labels.

### V3 — Syntax Validation

Purpose: Verify that the transformed code remains syntactically valid.

Possible validation methods include:

- Compiler syntax-check
- Parser-based syntax validation
- Language-specific structural validation

For C/C++, compiler syntax-checking without linking may be used where feasible.

V3 detects syntax errors but does not prove semantic equivalence.

### V4 — Semantic Evidence Validation

Purpose: Collect additional evidence that the variant preserves program behavior.

Potential methods include:

- Successful compilation
- Execution on the same test inputs
- Comparison of original and variant outputs
- Runtime behavior comparison
- Additional program-specific checks

V4 provides supporting evidence rather than an absolute proof of semantic equivalence.

Validation requirements may differ depending on the transformation type.

---

## 4. Validation Matrix

The following matrix defines the baseline validation requirements.

| Transformation | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| Whitespace | Required | Required | Optional | Optional |
| Formatting | Required | Required | Optional | Optional |
| Comments | Required | Required | Optional | Optional |
| Local variable renaming | Required | Required | Recommended before enabling | Optional |
| Function-local renaming | Required | Required | Recommended before enabling | Optional |
| Parameter renaming | Required | Required | Required | Gated |
| Compound transformations | Required | Required | Required | Experimental |

### Requirement Interpretation

- **Required:** Failure prevents acceptance.
- **Recommended before enabling:** Must be available and tested before the transformation is enabled for baseline generation.
- **Optional:** May provide additional evidence but is not mandatory for baseline acceptance.
- **Gated / Experimental:** Transformation remains disabled until its validation policy is finalized.

A recommended validation level must not be treated as an unrestricted option to bypass safety checks.

---

## 5. PASS / FAIL Policy

The final validation status of a variant is binary:

- `accepted`
- `rejected`

### ACCEPTED

A variant is accepted only when:

1. Its structural validation passes.
2. Its transformation validation passes.
3. All applicable mandatory validation levels pass.
4. No mandatory validator reports an error.
5. Its metadata is traceable.
6. Its transformation is permitted by the taxonomy and baseline policy.

### REJECTED

A variant is rejected when:

- A mandatory validation fails.
- The variant violates its transformation constraints.
- The source or variant cannot be reliably identified.
- The validator detects an unsafe modification.
- Validation cannot produce a reliable result.
- The transformation is not permitted.

### Fail-Closed Principle

If a validator cannot execute, encounters an error, times out, or cannot determine validity, the affected variant must not be accepted.

A validation failure must not be converted into a PASS merely because the transformation was expected to be safe.

---

## 6. Rejection Handling

Rejected variants must not be used for positive pair construction.

Rejected records should be retained for audit and analysis rather than deleted immediately.

The rejection process must:

- Preserve the rejection record.
- Record the reason for rejection.
- Exclude the variant from the accepted variant pool.
- Avoid automatic modification to force acceptance.
- Avoid unlimited retries.
- Support rejection statistics and quality analysis.

If retry behavior is introduced, retries must be bounded, deterministic when configured, and separately traceable.

---

## 7. Rejection Reason Codes

Rejection reasons should use standardized codes.

| Code | Meaning |
|---|---|
| `FILE_MISSING` | Variant file does not exist |
| `EMPTY_FILE` | Variant file is empty |
| `METADATA_INVALID` | Metadata is invalid or incomplete |
| `TOKEN_MISMATCH` | Unexpected token changes detected |
| `IDENTIFIER_COLLISION` | Renaming caused identifier collision |
| `SCOPE_UNRESOLVED` | Identifier scope could not be reliably resolved |
| `SYNTAX_ERROR` | Syntax validation failed |
| `TRANSFORMATION_UNSUPPORTED` | Transformation is unsupported or disallowed |
| `VALIDATOR_ERROR` | Validator encountered an internal error |
| `VALIDATION_TIMEOUT` | Validation exceeded its allowed execution time |

Additional codes may be introduced when new validation rules are designed, but they must be documented and standardized.

---

## 8. Validation Registry

Validation results must be stored separately from the variant registry.

Proposed output:

`data/processed/poj104/metadata/variant_validation.csv`

### Proposed Fields

| Field | Description |
|---|---|
| `variant_id` | Variant identifier |
| `original_sample_id` | Original source identifier |
| `transformation_type` | Applied transformation |
| `validation_status` | accepted / rejected |
| `v1_status` | Structural validation result |
| `v2_status` | Transformation validation result |
| `v3_status` | Syntax validation result |
| `v4_status` | Semantic evidence result |
| `rejection_reason` | Rejection code, if rejected |
| `validator_version` | Validator version |
| `validated_at` | Validation timestamp |

This registry complements `variants.csv` and does not replace the variant data model.

---

## 9. Validation Execution Policy

The validation pipeline must follow these execution rules:

1. Validate variants independently.
2. Continue processing other variants when an individual variant fails.
3. Report critical infrastructure failures that affect batch reliability.
4. Support deterministic validation where applicable.
5. Apply timeouts to potentially long-running validation operations.
6. Produce validation summary statistics.
7. Expose only accepted variants to downstream pair generation.

Batch processing must distinguish between individual variant failures and system-level validation failures.

---

## 10. Relationship to Positive Pair Generation

The validation pipeline acts as a mandatory gate for positive pair generation.

The intended flow is:

Original Source  
→ Transformation Selection  
→ Variant Generation  
→ Validation  
→ Acceptance / Rejection  
→ Positive Pair Candidate Generation

Only accepted variants are eligible for positive pair candidates.

The synthetic positive label indicates that the pair satisfies the project's controlled generation and validation rules. It does not represent human-confirmed plagiarism or absolute proof of semantic equivalence.

---

## 11. Out of Scope

The following are not finalized in this checkpoint:

- Specific compiler and compiler version
- Parser or tokenizer implementation
- Identifier scope analysis implementation
- Compilation configuration
- Runtime test inputs
- Runtime equivalence methodology
- Timeout values
- Retry limits
- Validator implementation
- Automated test implementation
- Semantic equivalence guarantees

These decisions will be addressed in later implementation and tooling design checkpoints.

---

## 12. Acceptance Criteria

Checkpoint 2.6.3 is considered complete when the following design decisions are finalized:

- Validation pipeline structure
- Four validation levels
- Validation matrix
- PASS / FAIL policy
- Fail-closed behavior
- Rejection policy
- Standard rejection reason codes
- Validation registry schema
- Validation execution policy
- Eligibility rules for positive pair generation

---

## 13. Design Decision Summary

The project adopts a strict validation gate between variant generation and positive pair generation.

Variant generation and variant acceptance are separate operations. A generated variant must pass the applicable validation requirements before it can be used as a synthetic positive sample.

This strategy prioritizes label reliability, traceability, and dataset integrity over maximizing the number of generated variants.

Validation failure must never be silently ignored or converted into acceptance.
