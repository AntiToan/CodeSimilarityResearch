# Design Closure & Implementation Readiness

**Project:** CodeSimilarityResearch  
**Phase:** Phase 2 — Dataset & Pair Generation Design  
**Status:** Design Closure Draft  
**Scope:** Reconciliation of Phase 2.5, 2.6, 2.7 designs and implementation readiness

---

## 1. Purpose & Scope

This document consolidates the approved Pair Dataset, Variant Generation, Pair Sampling, Validation, and Pipeline Orchestration designs into a consistent implementation baseline.

The purpose is to:

- Consolidate all previously approved design decisions.
- Resolve implementation-level inconsistencies between design documents.
- Define canonical contracts for source splitting, variants, candidates, selection, and exports.
- Identify parameters that require pilot calibration before full-scale generation.
- Establish implementation order and readiness criteria.

This document does not redesign previously approved pair-generation logic.

### Scope

Included:

- Source-level split assignment.
- Duplicate leakage prevention.
- Variant generation quantity and transformation distribution.
- Negative pair screening.
- Quota shortage handling.
- Validation tooling and preflight.
- Pair candidate assembly and selection.
- Output artifact consistency.
- Implementation dependencies and acceptance criteria.

Excluded:

- Model architecture.
- Model training.
- Model evaluation methodology beyond dataset readiness.
- Semantic plagiarism detection.
- Full execution-based program equivalence.
- Automated detection and grouping of unverified near-duplicates.

---

## 2. Decision Registry

### 2.1 Source Split Strategy — LOCKED

| Parameter | Decision |
|---|---|
| Split level | Source-level |
| Strategy | Stratified by problem |
| Train | 80% |
| Validation | 10% |
| Test | 10% |
| Seed | Fixed, configurable |
| Split timing | Before variant and pair generation |
| Variant split | Inherited from original |
| Pair split | Both endpoints must belong to the same split |

For the current POJ-104 dataset, each problem contains approximately 500 sources.

Target distribution per problem:

| Split | Target source count |
|---|---:|
| Train | 400 |
| Validation | 50 |
| Test | 50 |

Expected overall target:

| Split | Target source count |
|---|---:|
| Train | 41,600 |
| Validation | 5,200 |
| Test | 5,200 |
| Total | 52,000 |

These counts are targets. Duplicate-group constraints may cause small deviations.

### 2.2 Duplicate Leakage Policy — LOCKED

- Original sources are preserved.
- Exact duplicates are not removed.
- Identified exact-duplicate groups must be assigned to the same split.
- Duplicate groups spanning different problems must remain together.
- Unverified near-duplicates are not automatically grouped.
- Duplicate grouping is used for split integrity, not positive-pair generation.
- Duplicate sources are not automatically considered plagiarism or positive pairs.

Integrity takes priority over exact split proportions.

### 2.3 Variant Generation Quantity — LOCKED

| Parameter | Value |
|---|---|
| Target accepted variants per original | 2 |
| Maximum accepted variants per original | 2 |
| Attempts per variant target | 5 |
| Variant origin | Original only |
| Variant chaining | Not allowed |
| Duplicate output | Reject |
| Failed validation | Reject |
| Quota shortage | Accept partial generation |

The pipeline does not relax validation to reach the target.

### 2.4 Transformation Distribution — LOCKED

Baseline transformation types:

- Whitespace
- Formatting
- Comments

Distribution:

| Transformation | Probability |
|---|---:|
| Whitespace | Approximately 1/3 |
| Formatting | Approximately 1/3 |
| Comments | Approximately 1/3 |

For two variants per original:

- Prefer distinct transformation types.
- Select eligible transformation pairs uniformly.
- Use sampling without replacement.
- If a transformation is not eligible, remove it from the candidate set.
- Do not force an ineligible transformation.
- No adaptive probability adjustment in baseline.

### 2.5 Negative Pair Screening — LOCKED, THRESHOLD PILOT REQUIRED

| Parameter | Decision |
|---|---|
| Metric | Token Jaccard similarity |
| Threshold | 0.85 initial |
| Score ≥ 0.85 | Reject candidate |
| Score < 0.85 | Pass screening |
| Tokenization failure | Fail closed |
| Calibration | Required pilot |

Passing screening does not prove that the candidate is a valid negative pair.

The threshold 0.85 is an initial design value and must be evaluated during pilot calibration before full-scale generation.

### 2.6 Quota Shortage Policy — LOCKED

- Flexible quota.
- Keep valid candidates.
- No oversampling.
- No bypassing validation.
- No cross-split compensation.
- Balance positive and negative pairs independently within each split.
- Select the smaller available label pool when feasible.
- Quota shortage produces warnings and reports.
- A split with no valid pairs for one label is a quality failure.
- Integrity violations are critical failures.

Priority hierarchy:

**Pair integrity > Label validity > Leakage prevention > Diversity > Balance > Quantity**

### 2.7 Validation Tooling — LOCKED, PILOT REQUIRED

| Layer | Requirement |
|---|---|
| V1 | Structural validation |
| V2 | Transformation-specific validation |
| V3 | Syntax validation |
| V4 | Semantic evidence, optional for baseline |

Baseline accepted variants require V1, V2, and V3 to pass.

Proposed baseline tools:

- Tree-sitter C++ parser.
- Clang syntax-only validation.
- GNU C++17 as the initial compiler standard to test.
- Parser timeout: 3 seconds per file.
- Compiler timeout: 10 seconds per file.
- No executable generation.
- No source execution.

Tool availability and environment failures must not be misclassified as source syntax failures.

---

## 3. Source Split Contract

### 3.1 Split Timing

Source split must be completed before:

1. Variant generation.
2. Positive pair generation.
3. Negative pair generation.
4. Candidate assembly.
5. Final pair selection.

Split assignments must be persisted and treated as immutable inputs for a generation run.

### 3.2 Split Assignment Strategy — PROPOSED

Use deterministic group-aware stratified assignment.

Assignment units:

- Non-duplicate source: one source assignment unit.
- Exact duplicate group: one group assignment unit containing all known duplicates.

The assignment algorithm should:

1. Load all original source metadata.
2. Load verified exact-duplicate groups.
3. Construct atomic assignment groups.
4. Assign groups to Train, Validation, or Test.
5. Minimize deviations from 80/10/10 overall and per problem where feasible.
6. Never split a duplicate group to satisfy target proportions.
7. Record deviations caused by group constraints.
8. Verify every original source is assigned exactly once.

Duplicate groups spanning multiple problem IDs may cause local problem proportions to deviate.

### 3.3 Split Assignment Artifact — PROPOSED

Canonical source split registry:

`data/processed/poj104/metadata/source_splits.csv`

Proposed fields:

- `sample_id`
- `problem_id`
- `split`
- `split_seed`
- `split_method`
- `duplicate_group_id`
- `split_version`

Requirements:

- One record per original source.
- All original sources must be assigned.
- No duplicate sample assignments.
- All samples belonging to a verified duplicate group share a split.
- Variants inherit split from their original source.
- Pair endpoints must share the same split.

### 3.4 Split Validation

The split validator must check:

- Missing source assignments.
- Invalid split names.
- Duplicate sample assignments.
- Duplicate groups crossing splits.
- Incorrect problem-level proportions.
- Reproducibility with the same seed and input.
- Assignment coverage for the entire original dataset.

---

## 4. Variant Generation Contract

### 4.1 Variant Quantity

Target:

- Two accepted variants per original.

Maximum:

- Two accepted variants per original.

Retry limit:

- Five attempts per variant target.

### 4.2 Variant Creation

- Variants must be created directly from the original source.
- Variant-to-variant chaining is prohibited.
- Each baseline variant uses one transformation type.
- Original sources remain immutable.
- Variant IDs are deterministic according to the approved variant ID design.
- Variant split is inherited from original source.

### 4.3 Eligible Transformations

Baseline:

- Whitespace.
- Formatting.
- Comments.

Transformation distribution is uniform among eligible transformations.

For two variants:

- Prefer different transformation types.
- Use uniform selection among eligible transformation pairs.
- Use sampling without replacement.
- Reject outputs that are unchanged or duplicate an existing output.

### 4.4 Validation and Acceptance

A variant may be accepted only if:

- Output exists.
- Output is non-empty.
- Metadata is valid.
- Transformation is supported.
- Transformation-specific validation passes.
- Syntax validation passes.
- No duplicate variant output is detected.
- Required validation tooling is available.

Generation must not bypass validation to meet quantity targets.

### 4.5 Partial Generation

If a source produces fewer than two accepted variants:

- Preserve the original.
- Preserve accepted variants.
- Record failed attempts and reasons.
- Do not force additional transformations beyond retry limits.
- Do not treat rejected variants as positive data.

---

## 5. Negative Screening Contract

### 5.1 Metric

Token Jaccard similarity:

\[
J(A,B)=\frac{|T_A\cap T_B|}{|T_A\cup T_B|}
\]

Where:

- \(T_A\) and \(T_B\) are unique token sets.
- The result ranges from 0 to 1.

### 5.2 Threshold

Initial threshold:

`0.85`

Decision rule:

- Score >= 0.85: Reject as suspiciously similar.
- Score < 0.85: Pass screening.
- Tokenization error: Reject or fail candidate with a recorded error.

### 5.3 Tokenization and Normalization — PROPOSED

Use a C++-aware tokenizer rather than simple regex-based token extraction.

Normalization should:

- Remove comments correctly.
- Ignore whitespace and formatting.
- Preserve identifiers.
- Preserve numeric and string literals.
- Preserve operators.
- Avoid altering original source files.

Similarity is computed using unique token sets, not token frequency.

### 5.4 Screening Records

Each screening result should record:

- Candidate ID or pair ID.
- `sample_a_id`.
- `sample_b_id`.
- Metric name.
- Similarity score.
- Threshold.
- Screening status.
- Screening implementation version.
- Error reason if screening failed.

### 5.5 Calibration

Before full generation:

1. Select a representative sample of negative candidates.
2. Compute screening scores.
3. Review high-similarity and borderline candidates.
4. Measure candidate rejection rate.
5. Review whether the threshold rejects too many legitimate negatives.
6. Record calibration results.
7. Approve the threshold for the full run.

The threshold must not be changed silently.

---

## 6. Pair Assembly, Selection & Balancing Contract

### 6.1 Positive Pair Definition

Authoritative positive pair definition:

- Original source + accepted variant from the same lineage.
- Label = 1.
- Pair type = `positive`.
- Both endpoints must belong to the same split.

Baseline does not generate variant–variant positive pairs.

Each accepted variant may produce at most one original–variant positive pair.

### 6.2 Negative Pair Definition

Negative pair candidates must:

- Use original sources only.
- Have different problem IDs.
- Have different lineages.
- Not be known exact duplicates.
- Pass similarity screening.
- Pass candidate validation.
- Belong to the same split.

Label = 0.

Negative labels are synthetic labels derived from the generation rules. They are not ground-truth plagiarism annotations.

### 6.3 Candidate Assembly

Candidate assembly must:

1. Load positive and negative candidate pools.
2. Validate schemas and source references.
3. Verify split membership.
4. Canonicalize pair identity.
5. Reject self-pairs.
6. Deduplicate candidates.
7. Detect conflicting labels.
8. Validate pair rules.
9. Produce an assembled candidate pool.
10. Generate candidate assembly reports.

Candidate assembly does not perform final balancing or selection.

### 6.4 Canonical Pair Identity

- Pair identity is independent of label.
- Source IDs are sorted canonically.
- A–B and B–A represent the same pair.
- Self-pairs are forbidden.
- Duplicate identities are consolidated.
- Conflicting labels for one pair identity are critical errors.

### 6.5 Final Selection

Selection is performed independently for each split.

For split \(s\):

\[
Q_s=\min(P_s,N_s)
\]

Where:

- \(P_s\) is the valid positive candidate count.
- \(N_s\) is the valid negative candidate count.
- \(Q_s\) is the selected count per label.

Selection priorities:

1. Pair integrity.
2. Label validity.
3. Leakage prevention.
4. Endpoint diversity.
5. Label balance.
6. Problem distribution.

Do not oversample.

Do not transfer pairs between splits.

Do not generate new pairs during final selection.

If candidates are insufficient, use the maximum feasible valid count and record the shortage.

### 6.6 Final Validation

Final validation must verify:

- Schema validity.
- Source references exist.
- No self-pairs.
- No duplicate pair identities.
- No conflicting labels.
- Correct pair type and label.
- Same-split endpoints.
- No source-level split leakage.
- Positive pairs satisfy lineage rules.
- Negative pairs satisfy cross-problem and screening rules.
- Selected pairs originate from assembled candidates.
- Split index files match the master pair index.
- Counts and reports are accurate.

---

## 7. Canonical Output Layout — PROPOSED

This layout harmonizes the output paths proposed in the earlier pair generation and orchestration designs.

```text
data/
├── processed/
│   └── poj104/
│       ├── source/
│       ├── variants/
│       └── metadata/
│           ├── samples.csv
│           ├── source_splits.csv
│           ├── variants.csv
│           └── variant_validation.csv
│
└── pairs/
    ├── candidates/
    │   └── assembled_candidates.csv
    │
    ├── pair_index.csv
    │
    ├── splits/
    │   ├── train.csv
    │   ├── validation.csv
    │   └── test.csv
    │
    └── reports/
        ├── generation_report.json
        ├── split_report.json
        ├── variant_report.json
        ├── screening_report.json
        ├── assembly_report.json
        ├── selection_report.json
        └── final_validation_report.json

configs/
└── pair_generation_config.json
```

### 7.1 Artifact Roles

#### `candidates/assembled_candidates.csv`

Contains validated assembled candidates before final selection and balancing.

It is an intermediate artifact, not the final training/evaluation dataset.

#### `pair_index.csv`

Canonical master index for selected final pairs.

This is the authoritative final pair dataset.

It contains full pair records according to the approved pair schema.

#### `splits/train.csv`, `validation.csv`, `test.csv`

Split index files contain `pair_id` references to the canonical master pair index.

They do not duplicate the full pair records.

### 7.2 Output Consistency Rules

- The master pair index is authoritative.
- Split files are indexes into the master pair index.
- Every selected pair belongs to exactly one split.
- Split files must not contain pair IDs absent from the master index.
- Intermediate candidates must not be confused with final selected pairs.
- Previous design output paths must be reconciled to this layout during implementation.

---

## 8. Validation Preflight & Pilot Requirements

Full-scale generation must not begin until preflight and pilot checks pass.

### 8.1 Environment Preflight

Verify:

- Python environment.
- Required dependencies.
- Tree-sitter C++ parser availability.
- Clang availability.
- Compiler version.
- Compiler flags.
- C++ language standard.
- Input dataset integrity.
- Metadata consistency.
- Split registry consistency.
- Output directory permissions.
- Config validity.

If required tooling is unavailable, the run must stop before batch generation.

Environment errors must not be classified as source syntax failures.

### 8.2 Pilot Sample

Pilot generation should use a reproducible sample covering:

- Multiple problem IDs.
- Short source files.
- Long source files.
- Sources with comments.
- Sources with minimal formatting.
- Sources with unusual but valid structures.
- Sources previously identified as outliers where feasible.

Pilot must measure:

- Variant generation success rate.
- Transformation distribution.
- Validation pass/reject rate.
- Parser compatibility.
- Compiler compatibility.
- Runtime per transformation.
- Runtime per validation stage.
- Timeout rate.
- Negative screening distribution.
- Negative candidate rejection rate.
- Pair candidate shortage.
- Duplicate detection effectiveness.

### 8.3 Pilot Acceptance

Pilot acceptance criteria:

- No original source modified.
- Variants have valid lineage.
- Split inheritance is correct.
- Required validators operate successfully.
- Environment failures are distinguishable from source failures.
- Transformation-specific validators detect invalid output.
- Generation is deterministic under the same seed/config/tool versions.
- Reports contain sufficient information to audit.
- Runtime is measured and practical for full-scale processing.

Threshold calibration must be reviewed before the full negative candidate generation run.

---

## 9. Implementation Dependency Order

Implementation should follow dependency order.

### Stage 1 — Shared contracts and configuration

- Pair schema.
- Variant schema.
- Split schema.
- IDs and canonical identity.
- Config loader.
- Path definitions.
- Seed management.
- Version metadata.

### Stage 2 — Source splitting and duplicate groups

- Load original metadata.
- Load verified duplicate groups.
- Construct atomic split groups.
- Deterministic stratified assignment.
- Persist split assignments.
- Validate leakage and distribution.

### Stage 3 — Variant generation and validation

- Transformation implementations.
- Eligibility checks.
- Retry logic.
- Variant registry.
- Structural validators.
- Transformation validators.
- Parser and compiler validators.
- Rejection logging.

### Stage 4 — Positive pair generation

- Original–accepted variant pairing.
- Lineage checks.
- Split inheritance.
- Canonical identity.
- Candidate output.

### Stage 5 — Negative candidate generation

- Cross-problem source sampling.
- Per-anchor negative target.
- Duplicate checks.
- Similarity screening.
- Bounded retries.
- Rejection reports.

### Stage 6 — Candidate assembly

- Load positive and negative pools.
- Schema validation.
- Pair canonicalization.
- Duplicate consolidation.
- Conflict detection.
- Split validation.

### Stage 7 — Selection and balancing

- Independent selection per split.
- Label balancing.
- Endpoint diversity preference.
- Problem distribution reporting.
- Shortage handling.

### Stage 8 — Final validation and export

- Validate final master index.
- Validate split references.
- Generate reports.
- Export canonical artifacts.
- Record run metadata.

### Stage 9 — Orchestration

- Integrate all stages.
- Stage contracts.
- Run status.
- Fail-safe behavior.
- Reproducibility.
- End-to-end tests.

Implementation checkpoints must remain small enough for independent testing and user verification.

---

## 10. Implementation Readiness Checklist

### Design consistency

- [x] Source split is source-level.
- [x] Split occurs before variant and pair generation.
- [x] Variants inherit original split.
- [x] Exact duplicate groups cannot cross splits.
- [x] Positive pair definition is consistent.
- [x] Negative pair definition is consistent.
- [x] Pair identity is canonical.
- [x] Selection cannot generate new candidates.
- [x] Balancing is independent per split.
- [x] Quota shortage does not bypass integrity rules.
- [x] Output artifacts have defined roles.
- [x] Reproducibility is required.

### Implementation prerequisites

- [ ] Source split algorithm implemented.
- [ ] Duplicate group input verified.
- [ ] Configuration schema finalized.
- [ ] Tokenizer behavior specified and tested.
- [ ] Tree-sitter parser installed and verified.
- [ ] Clang preflight completed.
- [ ] GNU C++17 compatibility pilot completed.
- [ ] Timeout behavior tested.
- [ ] Pilot generation completed.
- [ ] Pilot screening calibration reviewed.
- [ ] Canonical output layout adopted in code.

---

## 11. Readiness Criteria

The project is ready to begin implementation when:

1. All approved Phase 2 design decisions are represented in this document or their authoritative design documents.
2. No unresolved design conflict blocks implementation.
3. Proposed reconciliation rules are reviewed and approved.
4. Configuration and output contracts are finalized.
5. Validation tooling can be preflighted.
6. Pilot requirements are defined.
7. Implementation checkpoints and tests are planned.

The project is not yet ready for full-scale pair generation until pilot validation, threshold calibration, and runtime assessment have been completed.

---

## 12. Status Summary

### Locked design decisions

- Source split strategy: 80/10/10 stratified source-level split.
- Exact duplicate groups remain together.
- Two accepted variants per original target.
- Five attempts per variant target.
- Uniform baseline transformation distribution.
- Token Jaccard screening, initial threshold 0.85.
- Flexible quota policy.
- Per-split balancing.
- Layered validation V1–V3 required.
- Tree-sitter and Clang syntax-only validation.
- Fail-closed validation.

### Proposed reconciliation rules

- Deterministic group-aware stratified source assignment.
- C++-aware tokenization for negative screening.
- Canonical final pair index and split reference files.
- Environment preflight before generation.
- Pilot calibration before full-scale execution.

### Pilot-required parameters

- GNU C++17 compatibility.
- Parser and compiler runtime.
- Parser timeout.
- Compiler timeout.
- Negative screening threshold calibration.
- Transformation success and rejection rates.
- Full-scale runtime estimation.

---

**Document status:** Design Closure Draft  
**Next action:** Review and approve reconciliation rules before implementation planning is finalized.