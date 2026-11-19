# Variant Data Model & Lineage Design

## 1. Purpose

This document defines the data model, metadata structure, storage organization, identification strategy, and lineage tracking rules for generated code variants in the CodeSimilarityResearch project.

The purpose of variant management is to generate controlled code modifications from original samples while preserving traceability, reproducibility, and dataset integrity.

Every generated variant must be traceable to its original source sample.

---

## 2. Variant Concept

A variant is a code sample generated from an original source through an approved transformation.

Examples of transformation categories:

- Formatting changes
- Whitespace changes
- Comment changes
- Scope-aware local variable renaming
- Safe function-local identifier renaming

Variants are additional code artifacts. They do not replace or modify original samples.

Variants derived from the same original source are considered part of the same source lineage.

---

## 3. Variant Identification

Each variant must have its own unique `variant_id`.

### 3.1 ID Format

The proposed format is:

`<original_sample_id>_v<index>`

Examples:

- `poj104_100_1139_v001`
- `poj104_100_1139_v002`
- `poj104_100_1139_v003`

### 3.2 ID Rules

- Variant IDs must be unique.
- The index starts from `001` for each original sample.
- The index increases within the original sample's variant namespace.
- IDs must be deterministic.
- Variant IDs must not replace the original sample ID.
- IDs of previously registered variants must not be reused.
- IDs are independent of transformation names.

The permanent ID allocation and rejected-generation handling policy will be refined during implementation design.

---

## 4. Variant Metadata Schema

A separate variant metadata registry will be maintained.

Proposed file:

`data/processed/poj104/metadata/variants.csv`

### 4.1 Fields

| Field | Type | Description |
|---|---|---|
| `variant_id` | string | Unique identifier of the generated variant |
| `original_sample_id` | string | ID of the original source sample |
| `problem_id` | string | Problem ID inherited from the original |
| `variant_index` | integer | Variant index within the original sample |
| `transformation_type` | string | Transformation category applied |
| `transformation_config` | JSON/string | Configuration of the applied transformation |
| `generation_seed` | integer/null | Seed used when applicable |
| `source_path` | string | Relative path to the original source code |
| `variant_path` | string | Relative path to the variant code |
| `status` | string | Generation and validation status |
| `created_at` | string | Variant creation timestamp |

### 4.2 Metadata Responsibilities

The variant registry must:

- Identify each variant.
- Reference its original sample.
- Track transformation information.
- Track variant file location.
- Track generation and validation status.
- Support reproducibility and auditing.
- Support positive pair generation.

Original sample metadata must remain unchanged.

---

## 5. Lineage Design

### 5.1 Lineage Definition

In the initial design, lineage is identified directly by:

`lineage_id = original_sample_id`

A separate lineage registry is not required at this stage.

### 5.2 Original-to-Variant Relationship

The relationship is one-to-many:

- One original sample may have zero, one, or multiple variants.
- Every variant belongs to exactly one original sample.
- A variant cannot exist without a valid original sample.
- Variants cannot reference other variants as their parent in the initial design.

### 5.3 Example

Original:

`poj104_100_1139`

Variants:

- `poj104_100_1139_v001`
- `poj104_100_1139_v002`
- `poj104_100_1139_v003`

All variants share the same lineage:

`poj104_100_1139`

The lineage relationship must be used to prevent invalid pair generation and dataset leakage.

---

## 6. Variant Storage Structure

Variant source code must be stored separately from original source code.

Proposed structure:

```text
data/processed/poj104/
├── source/
│   └── ...                       # Original source samples
├── metadata/
│   ├── samples.csv               # Original sample metadata
│   └── variants.csv              # Variant metadata registry
└── variants/
    ├── 1/
    │   └── ...
    ├── 100/
    │   ├── poj104_100_1139_v001.txt
    │   ├── poj104_100_1139_v002.txt
    │   └── ...
    └── ...
```

### 6.1 Storage Rules

- Original source files must never be overwritten.
- Variants must be stored separately from originals.
- Each variant must have its own file.
- Variant metadata must reference the correct variant file.
- Problem directory organization must remain consistent with the original problem ID.
- Accepted variants must have valid corresponding files.
- Rejected variants must not be used for pair generation.

Paths stored in metadata should be portable relative paths rather than machine-specific absolute paths.

---

## 7. Split Inheritance

Dataset splits must be assigned to original source samples before variant generation and pair generation.

Variants inherit the split of their original sample.

### 7.1 Rules

- A variant cannot independently select its split.
- The split is determined by its original source.
- All variants belonging to the same original lineage must remain in the same split.
- No original and its variants may cross train, validation, or test partitions.
- Variant metadata does not need an independent split field in the initial design.

The split can be resolved through the original sample's split assignment.

### 7.2 Example

If the original sample is assigned to `train`:

| Sample | Split |
|---|---|
| `poj104_100_1139` | train |
| `poj104_100_1139_v001` | train |
| `poj104_100_1139_v002` | train |
| `poj104_100_1139_v003` | train |

The following is invalid:

| Sample | Split |
|---|---|
| Original | train |
| Variant 1 | test |
| Variant 2 | validation |

Split inheritance is a mandatory constraint to prevent data leakage.

---

## 8. Variant Registry Validation Rules

The variant registry must enforce the following rules:

| Rule | Severity |
|---|---|
| `variant_id` must be unique | Mandatory |
| `original_sample_id` must exist | Mandatory |
| Original reference must point to an original sample, not another variant | Mandatory |
| Every variant must belong to exactly one original source | Mandatory |
| Accepted variants must have an existing code file | Mandatory |
| `variant_path` must be valid | Mandatory |
| Transformation type must be approved | Mandatory |
| Variant must not overwrite original source | Mandatory |
| Variants of the same lineage must share the same split | Mandatory |
| Rejected variants must not enter positive pairs | Mandatory |
| ID generation must be deterministic | Reproducibility requirement |

Invalid registry records must not be used to generate accepted positive pairs.

---

## 9. Variant Generation Strategy

### 9.1 Direct Generation from Originals

All variants must be generated directly from original samples.

The initial pipeline must not use variant-to-variant chaining.

Example:

```text
Original
 ├── Variant 1
 ├── Variant 2
 ├── Variant 3
 └── Variant 4
```

The following is prohibited in the initial design:

```text
Original
   ↓
Variant 1
   ↓
Variant 2
   ↓
Variant 3
```

This restriction simplifies lineage management and prevents compounded transformation errors.

### 9.2 One Transformation Type per Variant

The initial baseline applies one transformation type to each variant.

Examples:

- Variant 1: formatting
- Variant 2: comment change
- Variant 3: whitespace change
- Variant 4: safe variable renaming

Combined transformations are deferred to future experiments.

### 9.3 Rationale

This design provides:

- Easier transformation evaluation
- Easier debugging
- Better failure attribution
- More controlled semantic risk
- Clearer experimental analysis
- A simpler baseline for research

---

## 10. Variant Status

The `status` field must distinguish variants that are not eligible for pairing from accepted variants.

Proposed lifecycle:

- `generated` — Variant code has been generated.
- `validated` — Validation checks have passed.
- `accepted` — Variant is approved for use in positive pair generation.
- `rejected` — Variant has failed a mandatory validation or acceptance condition.

The exact transition rules and validation mechanisms will be defined in the transformation and validation design checkpoints.

Only variants with `accepted` status may be used for positive pair generation.

---

## 11. ID and Reproducibility Considerations

Variant generation should be deterministic under controlled inputs.

Reproducibility information should include:

- Original sample ID
- Variant index
- Transformation type
- Transformation configuration
- Generation seed where applicable
- Pipeline version
- Validation result
- Relative source and variant paths

Permanent IDs must not be randomly generated.

ID allocation behavior for failed, rejected, or retried generations must be finalized before implementation.

---

## 12. Scope Exclusions

This checkpoint does not define:

- Transformation algorithms
- Formatting implementation
- Comment modification rules
- Variable renaming implementation
- Number of variants per source
- Transformation probabilities
- Semantic equivalence testing
- Variant generation scripts
- Positive pair generation implementation
- Combined transformations

These topics will be addressed in subsequent checkpoints.

---

## 13. Acceptance Criteria

Variant data model and lineage design is considered complete when:

- Variant IDs are defined.
- Variant metadata schema is defined.
- Original-to-variant lineage is defined.
- Variant storage paths are defined.
- Split inheritance rules are defined.
- Registry validation rules are defined.
- Variant generation relationship is defined.
- Transformation isolation is defined.
- Variant statuses are defined.
- Reproducibility requirements are documented.

---

## 14. Design Principles

1. **Original preservation** — Original source files are immutable.
2. **Traceability** — Every variant must be traceable to its original sample.
3. **Controlled transformations** — Variants are generated under approved transformation rules.
4. **Lineage integrity** — A variant belongs to exactly one original lineage.
5. **Split integrity** — Original and variants remain within the same split.
6. **Reproducibility** — Variant generation must preserve relevant configuration and seed information.
7. **Experimental isolation** — Baseline variants apply one transformation type at a time.
8. **No chaining** — Variants are generated directly from originals in the initial design.

---

## 15. Status

Checkpoint: **2.6.1 — Variant Data Model & Lineage Design**

Status: **Design completed, pending repository commit.**
