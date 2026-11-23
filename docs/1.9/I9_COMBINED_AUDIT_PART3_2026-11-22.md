# CodeSimilarityResearch — Project Handoff / Checkpoint

**Checkpoint date:** 2026-11-21  
**Project:** `D:\University\NCKH\fullstack\CodeSimilarityResearch`  
**Working style:** one checkpoint at a time; user edits files manually; assistant provides exact commands/snippets and waits for results. No claims of editing the user's local repo.

## 1. Project context

Similarity research pipeline for source-code similarity dataset generation. This handoff is intended to restore the agreed decisions, progress, audit findings, and next step if conversation context is lost.


## 2. Phase I progress

- I.1 Config foundation — **Done**
- I.2 Source split & duplicate grouping — **Done**
- I.3 Variant generation & validation — **Done**
- I.4 Positive pair generation — **Done**
- I.5 Negative pair generation & screening — **Done**
- I.6 Pair assembly & candidate validation — **Done**
- I.7 Pair selection & balancing — **Done**
- I.8 Final validation & export — **Done**
- I.9 Pipeline orchestration & E2E — **In progress**

## 3. Latest verified test status

- I.8 final dataset validator module: **36 passed**.
- Full repository test suite: **542 passed in 34.86s**.
- I.8 is officially closed.

## 4. I.9 agreed timeline

1. I.9.1 Pipeline architecture audit — **Closed: PASS WITH GAPS**
2. I.9.2 Pipeline config & execution contract — **In progress (audit/design; no code yet)**
   - I.9.2.1 Config schema & authority audit — **Done: PASS WITH GAPS**
   - I.9.2.2 Pipeline input contract — **Next checkpoint**
   - I.9.2.3 Execution order & stage contract
   - I.9.2.4 Runtime policy
   - I.9.2.5 Output & execution contract
   - I.9.2.6 Design closure
3. I.9.3 Pipeline result/report model
4. I.9.4 Stage orchestration
5. I.9.5 Error handling & failure propagation
6. I.9.6 Artifact/export integration
7. I.9.7 Reproducibility/execution trace
8. I.9.8 Orchestrator unit tests
9. I.9.9 E2E tests
10. I.9.10 Regression & integration audit
11. I.9.11 Acceptance & closure

Timeline can be adjusted after audit evidence. Do not jump ahead of the current checkpoint.

## 5. I.9.1 Architecture audit — findings

Repo tree showed many stage modules under `src/data/`, including split, variant, positive/negative pair generation, assembly, selection, validation. Transformations and validation submodules also exist.

Key findings:
- No evidence of a full end-to-end pipeline orchestrator or root CLI.
- Existing `variant_pipeline_orchestrator.py`, `variant_generation_runner.py`, and `variant_generation_cli.py` are variant-generation-only, not the full dataset pipeline.
- Variant CLI uses factory injection and errors when factories are not configured.
- `tests/test_pair_selection_pipeline.py` tests manually assembled selection subpipeline, not full orchestrator.
- README has overview/setup/environment test guidance, but no full pipeline run instructions evident.
- Individual modules/tests exist; existence alone does not prove all design baseline contracts are implemented.
- No code changes were made during audit.

**I.9.1 status: PASS WITH GAPS; closed.**

## 6. I.9.2.1 Config schema & authority audit

`src/data/pair_generation_config.py` observations:
- Loads JSON via absolute config path; checks file existence/file type; catches JSON decoding errors; root must be a dict.
- `raw` exposes the underlying mutable config dict; `get(*keys)` nested lookup raises `KeyError`.
- Relative path resolution is based on the config directory's parent (assumes config under project-root `config/`).
- `seed`, `dataset_name` properties; validates at initialization.
- Validates required section existence; dataset name nonempty string; seed integer (bool rejected).
- Split train/validation/test numeric values (bool rejected), each between 0 and 1, sum exactly 1.
- Transform enabled list nonempty/no duplicates; probabilities required for enabled transforms, numeric (bool rejected), in [0,1], sum to 1; sampling must be `without_replacement`.
- Variant target/max/attempts positive integers (bool rejected), target <= max; chaining must be exactly False.
- Negative pair quota/attempts positive integers; same problem/lineage disallowed; originals only required.
- Negative screening threshold in [0,1], metric `token_jaccard`, fail_closed True.
- Selection oversampling False, cross-split transfer False, count policy `min_class_count`, target ratio positive numeric.
- Validation fail_closed True; parser/compiler timeouts positive numeric.

### Config audit gaps (backlog; not fixed yet)
- G1: section types are not comprehensively validated; malformed section shapes may cause raw errors later.
- G2: unknown keys are not rejected; typoed keys may be ignored.
- G3: schema coverage incomplete (dataset paths/language, deterministic setting, split strategy/group policies, duplicate policy, partial quotas/status, supported transforms, screening tokenization/mode, selection flags, tool names/language/std/syntax_only, output paths, etc.).
- G4: mutable `raw` may allow config to change after validation.
- G5: no run-level config snapshot/fingerprint/version freezing yet.
- G6: relative path resolution assumes config is located in project-root `config/`; behavior for alternate config paths needs explicit contract.

**I.9.2.1 status: PASS WITH GAPS; closed for audit.** Keep these gaps in implementation backlog.

### Config authority design agreed (provisional contract)
- One authoritative config for each run.
- Load and validate before any stage begins.
- No stage independently reloads config.
- Orchestrator passes config to stages.
- Config immutable during run.
- Record config snapshot, seed, version, fingerprint.
- Invalid config prevents pipeline start.
- Any CLI overrides must be merged before validation and snapshot creation.

## 7. I.9.2.2 Pipeline input contract — current checkpoint

**Not yet audited.** Assistant asked the user to inspect and paste these files:

```powershell
Get-Content src/data/variant_source_loader.py
Get-Content src/data/metadata_generator.py
Get-Content src/data/duplicate_detector.py
```

Next assistant action: wait for outputs; analyze these three modules only; document findings and compare them against the design baseline. Do not implement code yet. After I.9.2.2 is closed, move to I.9.2.3.

## 8. Design baseline (from `design_closure_and_implementation_readiness.md`)

### Data splitting
- Split at source level, stratified by problem; 80/10/10; fixed seed.
- Split before variant/pair generation; variants inherit source split; pair endpoints must share split.
- For POJ-104, ~500 sources/problem gives indicative 400/50/50; expected pair counts 41,600/5,200/5,200; duplicate groups can cause deviations.
- Duplicate groups stay atomic across splits (including across problems); originals remain. Exact duplicates grouped; near-duplicates not automatically grouped. Duplicate grouping is only for split integrity, not positive-pair creation.
- Proposed `source_splits.csv`: sample_id, problem_id, split, seed, method, duplicate_group_id, split_version.

### Variants
- Target 2 accepted variants/original; max 2; 5 attempts; originals only; no chaining; reject duplicates and failed validation; partial output allowed; no bypass.
- Baseline transformation mix: whitespace/formatting/comments roughly one-third each; prefer distinct transformation types; uniform among eligible, without replacement; no adaptive weighting.
- Accepted variants pass V1 structural, V2 transformation, V3 syntax checks. V4 semantic evidence optional/baseline.
- Tree-sitter C++; Clang syntax-only GNU C++17. Parser timeout 3 sec, compiler timeout 10 sec; never execute source. Tool/environment failures must be distinguishable from syntax failures.

### Negative pair screening
- Token Jaccard threshold 0.85; score >= 0.85 rejected; below threshold passes screening only (not proof of a negative).
- Tokenizer failure is fail-closed. C++-aware tokenizer removes comments and formatting effects but preserves identifiers, literals, operators, unique tokens.
- Reports retain pair IDs, metric, score, threshold, status, implementation version, and errors.

### Pair quotas / selection
- Flexible quotas: retain valid candidates; no oversampling; no bypass; no cross-split compensation; balance independently per split; selected count is min available label count.
- Shortages become warnings; split missing a label is a quality failure.
- Priority: integrity > label validity > leakage > diversity > problem balance > quantity.
- Selection is independently per split. Q_s = min(P_s, N_s).

### Pair integrity and final checks
- Positive: original + variant, label 1, same split; no variant-variant positives; at most one positive per variant.
- Negative: originals only; different problems and lineages; same split; no exact duplicate; screening and validation pass; keep provenance.
- Assembly: pools, schema/source refs, split membership, canonical pair identity (sort endpoints), no self-pairs, deduplicate; label conflict is critical.
- Final validation: schema/source refs, self-pairs, duplicates/conflicts, type-label consistency, split/leakage, positive lineage, negative cross-problem/screening/provenance; split indexes/master counts.

### Outputs (proposed baseline layout)

```text
data/processed/poj104/
  source/
  variants/
  metadata/
    samples.csv
    source_splits.csv
    variants.csv
    variant_validation.csv

data/pairs/
  candidates/assembled_candidates.csv
  pair_index.csv
  splits/
    train.csv
    validation.csv
    test.csv
  reports/
    generation_report.json
    split_report.json
    variant_report.json
    screening_report.json
    assembly_report.json
    selection_report.json
    final_validation_report.json

configs/pair_generation_config.json
```

- `pair_index.csv` is master; split files contain pair IDs/refs. Master is authoritative; paths must be harmonized.
- Preflight checks tools/versions/dependencies/inputs/config/permissions; missing required tools stop pipeline; environment failures separated from source syntax failures.
- Pilot run and calibration before full generation; representative sources; runtime and screening calibration; reproducibility with same seed/config/tool versions.

## 9. Working rules for the next chat

- Keep Vietnamese and informal/cooperative tone; concise, stepwise.
- One checkpoint at a time. User executes commands and shares outputs.
- Provide exact PowerShell commands. Do not ask the user to rerun checks without reason.
- During audit/design checkpoints: inspect and document only; **do not ask for code edits or implement prematurely**.
- Clearly distinguish: confirmed decisions, audit evidence, inferred gaps, and proposals.
- Wait for test/output before advancing.
- No web browsing needed for this repo work.



---

# 3.4.4 — Preflight Output Readiness Audit

**Project:** CodeSimilarityResearch  
**Phase:** I.9 — Pipeline Orchestration & E2E  
**Branch:** 3.4 — Preflight Output Readiness  
**Status:** DESIGN CLOSED — PASS WITH GAPS  
**Implementation Status:** UNVERIFIED  
**Verification Status:** OPEN

---

## 1. Purpose

This document consolidates the design audit and acceptance contract for the Preflight Output Readiness subsystem.

It serves as the implementation handoff baseline for subsequent engineering work.

The objective of preflight is to ensure that the pipeline is allowed to begin execution only when its configuration, inputs, outputs, runtime dependencies, integrity assumptions, and execution context satisfy the required safety contract.

Preflight is not merely a directory-existence check.

It must establish that the pipeline can execute safely within the approved configuration and artifact boundaries.

### Audit scope

- Preflight responsibility and existing capability inventory.
- Preflight acceptance contract.
- Input and metadata readiness.
- Output path canonicalization and containment.
- Directory readiness and write capability.
- Collision, overwrite, and existing artifact policy.
- Run isolation and temporary file safety.
- Critical checks and blocking conditions.
- Warning, optional, and deferred conditions.
- Decision aggregation and state derivation.
- Result integrity, consistency, and invariants.
- Acceptance matrix and traceability.
- Final design reconciliation and closure.

---

## 2. Audit Methodology

### 2.1 Carry-forward Audit — Reuse Evidence, Audit Only Gaps

Previously verified evidence must be reused where relevant.

Do not re-audit closed checkpoints unless:

- New implementation contradicts previous evidence.
- A requirement has changed.
- New integration introduces a boundary violation.
- Existing evidence is insufficient for the current acceptance decision.

### 2.2 Evidence classification

| Level | Evidence | Meaning |
|---|---|---|
| E0 | No evidence | Unverified |
| E1 | Design contract | Requirement is defined |
| E2 | Source implementation | Implementation exists |
| E3 | Unit/integration tests | Behavior is verified at component boundaries |
| E4 | End-to-end evidence | Integrated execution verified |

Current 3.4.4 design closure is primarily E1.

Implementation and verification evidence must be established separately.

### 2.3 Audit constraints

- Do not implement code without approval.
- Do not treat design contracts as code evidence.
- Do not silently downgrade critical conditions.
- Do not bypass integrity checks to achieve quantity targets.
- Do not repeat already closed evidence without justification.
- Preserve all gaps for carry-forward.

---

## 3. Authority & Design Baseline

The following authority hierarchy remains applicable:

1. Approved design decisions.
2. Consolidated pipeline contract.
3. Module contracts.
4. Verified implementation evidence.
5. Defaults.

Implementation must not override approved design decisions without explicit reconciliation.

### Existing pipeline baseline

- Dataset: POJ-104.
- Language: C++.
- Config version: 1.0.0.
- Pipeline version: 1.0.0.
- Seed: 42.
- Deterministic execution policy.
- Source-level stratified split: 80/10/10.
- Duplicate groups remain atomic across splits.
- Variants inherit source split.
- Pair endpoints must belong to the same split.
- Required V1–V3 validation.
- Optional V4 semantic validation according to approved policy.
- C++ Tree-sitter and Clang syntax-only validation.
- No generated source code execution.
- Existing generation, screening, selection and balancing contracts remain authoritative.

Preflight must not modify these existing scientific/research decisions.

---

# 4. Checkpoint Summary

## 3.4.4.1 — Preflight Responsibility & Existing Capability Inventory

**Status: CLOSED — PASS WITH GAPS**

Findings:

- No centralized preflight coordinator was confirmed.
- Existing environment tests provide basic import/smoke evidence.
- Existing CLI tests cover partial config/input validation.
- Existing tests do not establish comprehensive output readiness.
- Directory existence does not establish safe ownership, permission, collision safety or write readiness.

Implementation requirement:

Introduce a centralized preflight responsibility without duplicating existing module validation unnecessarily.

---

## 3.4.4.2 — Preflight Acceptance Contract

**Status: CLOSED — APPROVED**

### Required preflight state

- READY
- READY_WITH_WARNINGS
- BLOCKED

### Required result properties

- `status`
- `can_run`
- `checks`
- `errors`
- `warnings`
- `checked_at`
- `config_fingerprint`
- `summary`

Additional finalized identity, optional, deferred and traceability fields are specified in later checkpoints.

### Critical policy

- Critical failure blocks.
- Missing critical results block.
- Skipped critical results block.
- Unknown critical results block.
- Invalid classifications fail closed.
- Warnings cannot bypass critical conditions.

### Existing output inventory

Expected outputs include:

- Candidate directory.
- Selected pair directory.
- Split output directory.
- Config snapshot directory.
- Variants root.
- Variant registry.
- Reports.

Existing partial mechanisms were identified, but they do not constitute centralized output readiness.

---

## 3.4.4.3 — Input & Metadata Readiness

**Status: CLOSED — PASS WITH GAPS**

### Evidence carried forward

- `samples.csv`: 52,000 rows.
- `source_splits.csv`: 52,000 rows.
- `duplicate_groups.csv`: 5 groups.
- Samples/splits ID uniqueness verified.
- Missing split IDs: 0.
- Orphan split rows: 0.
- Problem mismatch: 0.
- Duplicate groups: 5, with 2 members per group.
- Duplicate group hash matching evidence available.

### Source loader findings

Existing source loader verifies:

- Required metadata/split columns.
- Unique IDs.
- Successful sample status.
- Missing/extra split checks.
- Valid split values.
- Source containment.
- Source file existence.
- Metadata file size is nonnegative integer.

Not yet established:

- Actual source file size comparison.
- Raw source SHA-256 fingerprint.
- Fingerprint of exact bytes consumed.
- Mutation detection.
- Immutable input snapshot.
- Run linkage and input provenance.
- Exact duplicate member ID reconciliation, previously identified as a gap.

### Mandatory input requirements

- Schema integrity.
- Unique sample identity.
- Split integrity.
- Cross-artifact reconciliation.
- Problem attribution consistency.
- Duplicate group integrity.
- Source containment.
- Actual source byte size.
- Source fingerprint.
- Source mutation detection.
- Immutable run input snapshot.
- Reproducible input provenance.

---

## 3.4.4.4 — Output Readiness Audit

**Status: DESIGN CLOSED — PASS WITH GAPS**

### 3.4.4.4.1 — Scope & Existing Evidence Inventory

Existing mechanisms provide partial protections, but no centralized output readiness enforcement was confirmed.

Preflight and runtime protections are both required.

### 3.4.4.4.2 — Output Path Canonicalization & Containment

Mandatory requirements:

- Explicit canonical root authority.
- CWD-independent resolution.
- Canonicalized paths.
- Containment checks.
- Path escape rejection.
- Source/output separation.
- Symlink policy.
- Preflight/writer path consistency.
- Safe handling of nonexistent destinations.
- Documented TOCTOU threat model.

### 3.4.4.4.3 — Write Permission & Directory Readiness

Mandatory requirements:

- Required directory inventory.
- Directory classification.
- Containment before directory creation.
- Controlled creation policy.
- Critical directory failure blocks.
- Actual write capability verification.
- Temporary write/commit capability.
- Runtime failure propagation.
- Partial artifact handling.
- Idempotent readiness checks.
- Storage/read-only/filesystem error classification.
- No silent fallback.
- Cleanup and failure reporting.

### 3.4.4.4.4 — Collision, Overwrite & Existing Artifact Policy

Existing artifact states:

- ABSENT
- VALID_EXISTING
- STALE
- INCOMPLETE
- CONFLICT
- CORRUPTED

Default collision mode:

`FAIL`

Resume:

- Explicit opt-in.
- Run identity required.
- Config compatibility required.
- Input fingerprint compatibility required.
- Artifact integrity required.
- Checkpoint compatibility required.

Overwrite:

- Explicit opt-in.
- Bounded scope.
- No accidental overwrite of another run.
- Must preserve run ownership boundaries.

### 3.4.4.4.5 — Run Isolation & Temporary File Safety

Isolation applies to:

- Candidate variants.
- Selected pairs.
- Splits.
- Reports.
- Config snapshots.
- Run summaries.
- Temporary files.
- Registry.
- Logs.

Temporary file lifecycle:

`CREATE → WRITE → VALIDATE → COMMIT`

Failure lifecycle:

`ABORT → CLEANUP / RECOVERY`

Requirements:

- Unique temp names.
- Exclusive creation.
- Explicit ownership.
- Allowed-root containment.
- Temp never treated as final artifact.
- Cleanup limited to owned temp files.
- Stale temp detection.
- Atomic commit.
- Commit failure propagation.
- Run completion distinguished from individual file commit.
- Crash recovery and reconciliation.
- Cleanup failures recorded.

### Cross-stage artifact provenance

Artifact metadata should carry as applicable:

- `run_id`
- `stage_id`
- `artifact_id`
- `config_fingerprint`
- `input_fingerprint`
- `artifact_fingerprint`
- `status`
- `created_at`
- `schema_version`

Downstream stages must consume committed artifacts and validate provenance and compatibility.

File existence alone is not sufficient evidence for reuse.

---

# 5. Preflight Decision Contract

## 3.4.4.6.1 — Scope & Reconciliation

**Status: CLOSED — DESIGN CONTRACT**

All output readiness checks, blocking rules, warning boundaries, result integrity and execution gate requirements belong to the preflight contract.

Preflight must evaluate readiness before generation begins.

It is not authorized to silently repair integrity failures or modify the approved effective configuration.

---

## 3.4.4.6.2 — Critical Checks & Blocking Conditions

**Status: CLOSED — DESIGN CONTRACT**

Critical checks:

### CC-01 Config readiness

Config exists, readable, valid and internally consistent.

### CC-02 Dataset & metadata integrity

Required data and metadata are valid and reconciled.

### CC-03 Source path integrity

Canonicalization, containment, source authorization and readability.

### CC-04 Source snapshot & fingerprint

Actual bytes, identity, fingerprint and mutation guarantees.

### CC-05 Output canonicalization & containment

All output destinations are canonical, permitted and safe.

### CC-06 Output directory & write capability

Required directories and actual write/commit capability.

### CC-07 Collision & existing artifact safety

Existing outputs classified; overwrite/resume policy enforced.

### CC-08 Run isolation

Run-scoped output, temp ownership and concurrency boundaries.

### CC-09 Registry readiness

Registry schema, consistency, identity and concurrency safety.

### CC-10 Dependency & toolchain readiness

Required dependencies, actual parser capability and compiler validation capability.

### CC-11 Config snapshot & reproducibility

Effective config snapshot, fingerprint, seed and persistence.

### CC-12 Preflight-to-execution consistency

Execution context must match the validated preflight context.

### Blocking rules

- Any critical failure → BLOCKED.
- Critical skipped/unknown/error → BLOCKED.
- Missing critical result → BLOCKED.
- Invalid classification → fail closed.
- Unclassified failure → fail closed.
- Warnings cannot downgrade critical failures.
- No bypass through CLI flags, retry, fallback or runtime override.
- Aggregate all safely executable checks.
- Generation requires a validated READY or READY_WITH_WARNINGS result.

---

## 3.4.4.6.3 — Warning, Optional & Deferred Conditions

**Status: CLOSED — DESIGN CONTRACT**

### Warning conditions

- Non-critical sample shortage.
- Pair quota shortage.
- Quality degradation within hard contract.
- Non-critical report limitation.
- Recoverable stage failure with explicit safe recovery contract.

Warnings must:

- Be structured.
- Be preserved.
- Include context and impact.
- Not hide integrity failure.
- Not silently disappear.

### Optional conditions

Examples:

- Optional V4 semantic validation.
- Additional diagnostic reports.
- Extended visualization.
- Non-essential metrics.
- Debug metadata.

Optional capability must not affect required integrity, provenance or required artifacts.

### Deferred conditions

- Full TOCTOU protection.
- Filesystem durability guarantees.
- Cross-process coordination.
- Crash recovery completeness.

Deferred does not mean passed.

Each deferred risk must retain:

- Risk ID.
- Description.
- Reason deferred.
- Scope.
- Impact.
- Mitigation.
- Responsible area.
- Status.
- Review trigger.

---

## 3.4.4.6.4 — Preflight Decision Aggregation & State Derivation

**Status: CLOSED — DESIGN CONTRACT**

Normalized check states:

- PASS
- FAIL
- WARN
- SKIPPED
- UNKNOWN
- ERROR

### Decision rules

`BLOCKED`:

- Any critical check is non-PASS.
- Critical check is missing.
- Invalid classification/status.
- Aggregate result is invalid or incomplete.

`READY_WITH_WARNINGS`:

- All critical checks PASS.
- At least one active warning exists.
- Result is valid.

`READY`:

- All critical checks PASS.
- No active warnings.
- Result is valid.

### Precedence

`BLOCKED > READY_WITH_WARNINGS > READY`

Decision must be deterministic and independent of check iteration order.

### can_run

`can_run` is derived-only:

| Status | can_run |
|---|---|
| READY | true |
| READY_WITH_WARNINGS | true |
| BLOCKED | false |

No caller may override `can_run`.

---

## 3.4.444.6.5 — Preflight Result Integrity, Consistency & Invariants

**Status: CLOSED — DESIGN CONTRACT**

### Required result fields

- `preflight_id`
- `run_id`
- `status`
- `can_run`
- `checks`
- `errors`
- `warnings`
- `optional_results`
- `deferred_risks`
- `checked_at`
- `config_fingerprint`
- `summary`

### Check identity

Each check:

- `check_id`
- `category`
- `classification`
- `status`
- `message`
- `path` (optional)
- `details`

### Invariants

- Check IDs unique within result.
- Classification and status belong to allowed enums.
- No missing critical check.
- Aggregate state matches detailed checks.
- `can_run` matches final state.
- Errors match blocking conditions.
- Warnings match active warnings.
- Config fingerprint belongs to assessed config.
- Run ID remains consistent.
- Deferred risks are preserved.
- Contradictory results are rejected.
- Finalized results cannot silently mutate.

### Serialization

Serialization/deserialization must preserve decision semantics.

Missing fields must not default to PASS.

Downstream consumers must validate the result and context before using it as execution authorization.

---

## 3.4.4.6.6 — Preflight Acceptance Matrix & Traceability

**Status: CLOSED — MATRIX ESTABLISHED**

### Requirement coverage

| Range | Domain |
|---|---|
| PF-AC-01–15 | Config, dataset, metadata, source integrity |
| PF-AC-16–30 | Output readiness, collisions, isolation, registry |
| PF-AC-31–38 | Dependencies, toolchain, reproducibility |
| PF-AC-39–56 | Decision aggregation, result integrity, execution gate |
| PF-AC-57–69 | Warnings, optional capabilities, deferred risks |

### Traceability chain

`Requirement → Preflight Check/Decision → Implementation → Unit/Integration Test → E2E Evidence → Acceptance`

A critical requirement with an incomplete traceability chain cannot be considered implementation-verified.

---

## 3.4.444.6.7 — Preflight Design Closure & Final Reconciliation

**Status: DESIGN CLOSED — PASS WITH GAPS**

### Conflicts reconciled

1. Critical vs Warning classification.
2. Optional capability vs required integrity.
3. Deferred risk vs mandatory blocking boundary.
4. Preflight pass vs runtime context mutation.
5. Atomic write vs run isolation.
6. `status` vs `can_run`.
7. Structured warning persistence vs console logging.
8. Existing artifacts vs explicit resume.

### Final decision contract

BLOCKED:

- Any critical failure, skipped, unknown, error, missing or invalid result.
- `can_run = false`.
- Generation prohibited.

READY_WITH_WARNINGS:

- All critical checks PASS.
- Active warnings exist.
- Result valid.
- `can_run = true`.

READY:

- All critical checks PASS.
- No active warnings.
- Result valid.
- `can_run = true`.

### Final design acceptance

- Output readiness domains covered.
- Critical boundary defined.
- Warning boundary defined.
- Optional policy defined.
- Deferred risks identified.
- Aggregation defined.
- Result invariants defined.
- Execution gate defined.
- Traceability established.
- No unresolved design contradiction identified during final reconciliation.

Design phase is closed.

Implementation and runtime verification remain open.

---

# 6. Consolidated Acceptance Requirements

## A. Config & input integrity

- PF-AC-01 Config validity.
- PF-AC-02 Config authority consistency.
- PF-AC-03 Dataset readiness.
- PF-AC-04 Metadata schema.
- PF-AC-05 Sample ID integrity.
- PF-AC-06 Split integrity.
- PF-AC-07 Samples/splits reconciliation.
- PF-AC-08 Problem attribution.
- PF-AC-09 Duplicate group integrity.
- PF-AC-10 Exact duplicate membership.
- PF-AC-11 Source containment.
- PF-AC-12 Source readability.
- PF-AC-13 Actual byte size.
- PF-AC-14 Source fingerprint.
- PF-AC-15 Source mutation detection.

## B. Output readiness & isolation

- PF-AC-16 Output canonicalization.
- PF-AC-17 Output containment.
- PF-AC-18 Source/output separation.
- PF-AC-19 Directory readiness.
- PF-AC-20 Write capability.
- PF-AC-21 Temporary write capability.
- PF-AC-22 Existing artifact classification.
- PF-AC-23 Collision policy.
- PF-AC-24 Overwrite policy.
- PF-AC-25 Resume compatibility.
- PF-AC-26 Run isolation.
- PF-AC-27 Temporary file safety.
- PF-AC-28 Registry readiness.
- PF-AC-29 Registry concurrency safety.
- PF-AC-30 Run identity readiness.

## C. Dependency & reproducibility

- PF-AC-31 Python dependencies.
- PF-AC-32 Tree-sitter capability.
- PF-AC-33 Compiler capability.
- PF-AC-34 Toolchain/config compatibility.
- PF-AC-35 Config snapshot persistence.
- PF-AC-36 Effective config identity.
- PF-AC-37 Deterministic seed readiness.
- PF-AC-38 Preflight/execution consistency.

## D. Decision & result integrity

- PF-AC-39 Critical check completeness.
- PF-AC-40 Critical PASS enforcement.
- PF-AC-41 Unknown classification fail-closed.
- PF-AC-42 Unknown status fail-closed.
- PF-AC-43 Warning aggregation.
- PF-AC-44 Optional isolation.
- PF-AC-45 Deferred preservation.
- PF-AC-46 Deterministic aggregation.
- PF-AC-47 State precedence.
- PF-AC-48 `can_run` derivation.
- PF-AC-49 Result structural validity.
- PF-AC-50 Cross-field consistency.
- PF-AC-51 Error consistency.
- PF-AC-52 Warning consistency.
- PF-AC-53 Result immutability.
- PF-AC-54 Serialization preservation.
- PF-AC-55 Downstream validation.
- PF-AC-56 Execution gate enforcement.

## E. Warning & deferred

- PF-AC-57 Sample shortage.
- PF-AC-58 Pair quota shortage.
- PF-AC-59 Quality degradation.
- PF-AC-60 Optional report failure.
- PF-AC-61 Optional V4 unavailable.
- PF-AC-62 Recoverable stage failure.
- PF-AC-63 Warning persistence.
- PF-AC-64 Deferred risk recording.
- PF-AC-65 Deferred risk review triggers.
- PF-AC-66 TOCTOU threat model.
- PF-AC-67 Filesystem durability.
- PF-AC-68 Crash recovery completeness.
- PF-AC-69 Cross-process coordination.

---

# 7. Implementation Gap Register

These gaps remain open and must be carried into implementation and verification.

## G1 — Centralized Preflight Coordinator

Verify or implement:

- Central coordinator.
- Check registration/execution.
- Structured check results.
- Aggregation.
- Final decision.
- No scattered independent readiness decisions.

## G2 — Filesystem & Output Safety

Verify:

- Canonicalization.
- Containment.
- Symlink policy.
- Directory creation.
- Actual write capability.
- Temp lifecycle.
- Collision detection.
- Overwrite/resume enforcement.
- Runtime path consistency.
- Run isolation.

## G3 — Source Snapshot Integrity

Verify:

- Actual byte size.
- SHA-256.
- Exact consumed bytes fingerprint.
- Mutation detection.
- Immutable input snapshot.
- Provenance.
- Split and duplicate reconciliation.

## G4 — Registry & Concurrency Safety

Verify:

- Registry schema.
- Unique identity.
- Safe transaction.
- Concurrency handling.
- Lost-update prevention.
- Ownership.
- Crash reconciliation.

## G5 — Dependency & Toolchain Verification

Verify:

- Required Python imports.
- Tree-sitter grammar loading.
- Parser capability.
- Compiler identity.
- Actual syntax-validation capability.
- Required flags.
- Timeout behavior.
- Config compatibility.

## G6 — Preflight Result Integrity

Verify:

- Result schema.
- Check IDs.
- Allowed classification/status.
- Cross-field invariants.
- Immutability.
- Serialization round-trip.
- Contradiction rejection.

## G7 — Execution Gate

Verify:

- BLOCKED cannot execute.
- Invalid result cannot execute.
- Missing critical checks cannot execute.
- Context mismatch cannot execute.
- `can_run` cannot be manually overridden.
- Gate is enforced before generation.

## G8 — E2E Acceptance

Verify:

- Preflight.
- Execution.
- Stage results.
- Artifacts.
- Reports.
- Config snapshot.
- Run identity.
- Provenance.
- Failure propagation.
- Warning persistence.
- Final run state.

## G9 — Residual Risk Closure

Explicitly address:

- TOCTOU.
- Filesystem durability.
- Crash recovery.
- Cross-process coordination.
- Threat model.
- Recovery strategy.

---

# 8. Recommended Implementation Order

Implementation should follow dependency boundaries rather than simply following document numbering.

## Phase A — Shared foundations

1. Canonical path/root resolver.
2. Run identity and run-scoped output model.
3. Config snapshot and fingerprint model.
4. Structured result/check schema.
5. Stable enums and identity rules.

## Phase B — Safety primitives

6. Source integrity/snapshot service.
7. Output containment service.
8. Directory readiness and write probe.
9. Collision/ownership policy.
10. Safe temporary file lifecycle.
11. Registry concurrency/transaction policy.

## Phase C — Preflight check modules

12. Config readiness.
13. Input/metadata reconciliation.
14. Source integrity.
15. Output path readiness.
16. Directory/write readiness.
17. Collision/resume/overwrite checks.
18. Registry readiness.
19. Dependency/toolchain checks.
20. Config snapshot readiness.
21. Run isolation checks.

## Phase D — Decision engine

22. Critical/warning/optional/deferred classification.
23. Missing check detection.
24. Aggregation.
25. State derivation.
26. `can_run` derivation.
27. Result invariants.
28. Serialization validation.

## Phase E — Runtime enforcement

29. Preflight-to-execution context validation.
30. Execution gate.
31. Runtime failure propagation.
32. Artifact ownership enforcement.
33. Run completion reconciliation.

## Phase F — Verification

34. Unit tests.
35. Integration tests.
36. Failure injection.
37. Concurrency tests.
38. Crash/recovery tests.
39. E2E tests.
40. Regression audit.
41. Acceptance closure.

Do not implement every layer in one large step. Each layer should have contract, implementation, targeted verification and closure before dependent layers advance.

---

# 9. Minimum Verification Matrix

| Test domain | Minimum acceptance evidence |
|---|---|
| Config | Invalid/missing/ambiguous config blocks |
| Metadata | Missing/orphan/duplicate records block |
| Source integrity | Missing, escape, size mismatch, mutation block |
| Path containment | Escaping output path blocks |
| Directory readiness | Critical mkdir/write failure blocks |
| Temp lifecycle | Partial write/commit failure safely handled |
| Collision | Existing unclassified artifact blocks |
| Resume | Incompatible run/config/input rejected |
| Isolation | Run A cannot overwrite Run B |
| Registry | Concurrent updates do not silently lose data |
| Dependency | Missing required package blocks |
| Parser | Actual grammar/parser capability verified |
| Compiler | Actual required syntax validation capability verified |
| Snapshot | Failure to persist effective config blocks |
| Aggregation | Same checks yield deterministic decision |
| Critical | FAIL/WARN/SKIP/UNKNOWN/ERROR/missing all block |
| Warning | Valid warning permits READY_WITH_WARNINGS |
| Optional | Optional failure does not block core run |
| Deferred | Unresolved risks preserved |
| Result | Contradictory fields rejected |
| Serialization | Round-trip preserves state and evidence |
| Gate | BLOCKED/invalid result cannot start generation |
| E2E | Successful and failing runs produce correct artifacts/reports |

---

# 10. Definition of Done

3.4.4 design is already closed.

Implementation acceptance is not complete until:

- [ ] Every critical requirement maps to an implementation component.
- [ ] Every critical requirement maps to tests.
- [ ] Missing critical results block.
- [ ] Invalid results fail closed.
- [ ] Output containment is enforced by actual writers.
- [ ] Run isolation is verified.
- [ ] Collision/resume/overwrite policy is enforced.
- [ ] Source integrity and fingerprint requirements are met.
- [ ] Registry concurrency safety is verified.
- [ ] Toolchain capability is tested.
- [ ] Config snapshot is persisted and validated.
- [ ] Preflight/execution consistency is enforced.
- [ ] Execution gate is enforced.
- [ ] Warning and deferred records survive serialization/reporting.
- [ ] E2E acceptance passes.
- [ ] Regression audit passes.
- [ ] Residual risks are explicitly documented.

---

# 11. Closure Status

| Area | Design | Implementation | Verification |
|---|---|---|---|
| Preflight scope | CLOSED | OPEN | OPEN |
| Critical blocking | CLOSED | OPEN | OPEN |
| Warning policy | CLOSED | OPEN | OPEN |
| Optional policy | CLOSED | OPEN | OPEN |
| Deferred risk | IDENTIFIED | OPEN | OPEN |
| Aggregation | CLOSED | OPEN | OPEN |
| Result invariants | CLOSED | OPEN | OPEN |
| Acceptance matrix | CLOSED | OPEN | OPEN |
| Traceability | ESTABLISHED | OPEN | OPEN |
| Execution gate | CONTRACT CLOSED | OPEN | OPEN |
| E2E acceptance | CONTRACT DEFINED | OPEN | OPEN |

### Final audit decision

**3.4.4 — Preflight Output Readiness Audit**

`DESIGN CLOSED — PASS WITH GAPS`

No unresolved design-level blocker was identified during final reconciliation.

Implementation safety, runtime enforcement, tests and E2E acceptance remain open.

---

# 12. Handoff Instruction for Future Implementation Sessions

When continuing implementation:

1. Read this document first.
2. Reuse approved contracts.
3. Do not reopen closed design checkpoints without evidence of conflict.
4. Inspect the current implementation before proposing code changes.
5. Audit only the gaps relevant to the current implementation checkpoint.
6. Map findings to PF-AC IDs and G1–G9.
7. Implement incrementally.
8. Test before closing each implementation checkpoint.
9. Preserve unresolved gaps.
10. Never claim implementation PASS from design evidence alone.

**This document is the consolidated design baseline and implementation handoff for 3.4.4.**


---

# 3.4.4 — Output Readiness Audit

**Project:** CodeSimilarityResearch  
**Phase:** I.9 — Pipeline Orchestration & E2E  
**Audit Method:** Carry-forward Audit — Reuse Evidence, Audit Only Gaps  
**Status:** Closed — PASS WITH GAPS  
**Scope:** Output readiness, path canonicalization, write permission, collision policy, run isolation, temporary files, atomic commit, crash recovery và cross-stage artifact ownership.

---

## 1. Purpose & Scope

Checkpoint 3.4.4 thực hiện audit khả năng sẵn sàng của toàn bộ output destinations trước và trong quá trình pipeline execution.

Mục tiêu là đảm bảo pipeline:

- Không ghi output ra path ngoài phạm vi cho phép.
- Không ghi khi destination chưa sẵn sàng.
- Không overwrite artifact ngoài policy.
- Không để các run ảnh hưởng lẫn nhau.
- Không coi partial hoặc stale artifacts là output hợp lệ.
- Có thể xác định ownership, integrity và lifecycle của artifacts.
- Propagate output-related failures đúng stage và run.

Audit này là **design/evidence audit**, không phải implementation verification. Các cơ chế đã tồn tại được ghi nhận nhưng không tự động được xem là đáp ứng toàn bộ acceptance requirements.

### Checkpoint overview

| Checkpoint | Title | Status |
|---|---|---|
| 3.4.4.1 | Output Readiness Scope & Existing Evidence Inventory | Closed — PASS WITH GAPS |
| 3.4.4.2 | Output Path Canonicalization & Containment | Closed — PASS WITH GAPS |
| 3.4.4.3 | Write Permission & Directory Readiness | Closed — PASS WITH GAPS |
| 3.4.4.4 | Collision, Overwrite & Existing Artifact Policy | Closed — PASS WITH GAPS |
| 3.4.4.5 | Run Isolation & Temporary File Safety | Closed — PASS WITH GAPS |

---

## 2. Existing Evidence Inventory

| Component | Existing evidence | Remaining gap |
|---|---|---|
| Variant output writer | Exclusive create (`xb`), containment | End-to-end run isolation chưa xác minh |
| Variant registry | Unique temp file + atomic `os.replace` | Shared registry, lost-update/concurrency risk |
| Report exporter | Atomic replacement | Overwrite và artifact ownership chưa centralized |
| Run summary | Fixed `.tmp` path | Temp collision giữa runs |
| Preprocessing | Direct writes | Chưa có unified output safety policy |
| Pair/candidate/selected/split outputs | Shared output directories | Run ownership, stale artifact detection chưa xác minh |
| Config snapshot | Có output location trong config | Immutable, unique run linkage chưa xác minh |
| Preflight | Chưa có centralized preflight coordinator/result | Output readiness chưa được kiểm tra thống nhất |

**Audit conclusion:** Existing local write protections are useful but insufficient to establish pipeline-wide output safety.

---

## 3. 3.4.4.1 — Output Readiness Scope & Existing Evidence Inventory

### Status: CLOSED — PASS WITH GAPS

Đã xác định các output-producing components và partial write protections hiện có.

Các gap chính:

- Chưa centralized output readiness coordinator.
- Chưa inventory/validate thống nhất toàn bộ critical destinations.
- Directory existence không đồng nghĩa write readiness.
- Chưa chứng minh preflight output checks bao phủ tất cả writers.
- Chưa có runtime output safeguards được xác minh xuyên pipeline.

### Mandatory requirements

- Inventory critical và optional outputs.
- Classify output directories và destinations.
- Validate path, containment, directory readiness và collision state.
- Centralize preflight output readiness checks.
- Giữ runtime write protection kể cả khi preflight pass.

---

## 4. 3.4.4.2 — Output Path Canonicalization & Containment

### Status: CLOSED — PASS WITH GAPS

### Evidence

- Path resolution còn phụ thuộc CWD/config-parent assumptions.
- Path traversal thông qua `..` là risk.
- Variant writer và source loader có local containment protection.
- End-to-end root authority chưa được xác minh.
- Symlink escape và TOCTOU risk chưa được xử lý đầy đủ.
- Chưa xác nhận toàn bộ components dùng cùng canonical path policy.

### Mandatory requirements — OP-R1..OP-R9

1. Explicit project/output root authority.
2. CWD-independent path resolution.
3. Unified path canonicalization.
4. Path-aware containment, không dùng string-prefix check.
5. Symlink escape protection.
6. Preflight path phải giống destination thực tế của writer.
7. Defense-in-depth giữa pipeline và writer.
8. Safe handling cho destinations chưa tồn tại.
9. TOCTOU mitigation và residual threat-model documentation.

**Closure note:** Design closure đã đạt; implementation-level path safety chưa được xác minh toàn diện.

---

## 5. 3.4.4.3 — Write Permission & Directory Readiness

### Status: CLOSED — PASS WITH GAPS

### Evidence

- Một số writers có directory creation và temp/replace hoặc exclusive-create mechanisms.
- Runtime permission validation chưa được chứng minh centralized.
- Parent-directory readiness, containment-before-mkdir và recursive creation policy chưa xác minh.
- Read-only filesystem, disk-full, unavailable filesystem, temp failure, lock/retry và cleanup handling chưa có runtime evidence đầy đủ.

### DR-R1..DR-R8 — Directory readiness

- Inventory và classify output directories.
- Validate readiness của critical destinations.
- Enforce containment trước khi mkdir.
- Define nested-parent creation policy.
- Critical directory failure phải block preflight.
- Controlled/documented preflight side effects.
- Centralized directory policy.
- Idempotent directory creation.

### WP-R1..WP-R10 — Write permission

- Validate actual write capability khi cần.
- Validate temp-write và commit readiness.
- Safe write probes có kiểm soát nếu cần.
- Critical write failure phải block.
- Runtime write failure phải propagate.
- Partial artifacts phải được classify.
- Không coi directory existence là write readiness.
- Permission failure phải report rõ và có context.

### ENV-R1..ENV-R10 — Filesystem/environment failures

- Handle read-only, storage exhaustion, unavailable filesystem và temp failures.
- Bounded retry chỉ khi operation safe.
- Không unsafe fallback destination.
- Temp cleanup và cleanup-failure reporting.
- Run status phản ánh environment failure.
- Preserve artifact integrity và failure context.

### Write-readiness contract

- Critical output failure → BLOCKED.
- Critical check skipped/unverified → BLOCKED.
- Optional safe failure → READY_WITH_WARNINGS.
- Không generation trước execution gate.
- Atomicity không đồng nghĩa isolation.
- Runtime failures vẫn phải propagate.

---

## 6. 3.4.4.4 — Collision, Overwrite & Existing Artifact Policy

### Status: CLOSED — PASS WITH GAPS

### 6.1 Existing artifact classification

| State | Meaning | Default action |
|---|---|---|
| `ABSENT` | Destination chưa tồn tại | Có thể tạo |
| `VALID_EXISTING` | Artifact có provenance/integrity hợp lệ | Không overwrite/reuse mặc định |
| `STALE` | Không khớp config/input hiện tại | Block reuse |
| `INCOMPLETE` | Artifact của run chưa hoàn tất | Block mặc định |
| `CONFLICT` | Ownership xung đột/không xác định | Block |
| `CORRUPTED` | Integrity/schema failure | Block reuse |

### 6.2 Collision modes

| Mode | Contract |
|---|---|
| `FAIL` | Default; collision bất ngờ phải block |
| `RESUME` | Explicit opt-in; yêu cầu run identity, fingerprint compatibility, integrity và checkpoint hợp lệ |
| `OVERWRITE` | Explicit opt-in; bounded scope và ownership; không được ảnh hưởng artifacts ngoài phạm vi |

### 6.3 Mandatory CO-R1..CO-R15

- Inventory output destinations.
- Detect existing files/directories.
- Determine artifact ownership/run identity.
- Detect stale/incomplete artifacts.
- `FAIL` là default.
- `RESUME` explicit và integrity-verified.
- `OVERWRITE` explicit và scope-controlled.
- Run-scoped output isolation.
- Registry concurrency safety.
- Unique/collision-safe temporary paths.
- Runtime collision propagation.
- No silent overwrite.
- Crash/recovery classification.
- Collision policy được ghi vào execution trace.
- Preflight và writers áp dụng cùng policy.

### 6.4 Concurrent run & shared output

Risks identified:

- Concurrent runs ghi shared reports.
- Registry lost update.
- Fixed temporary path collisions.
- Concurrent generation cùng artifact.
- Preflight-to-write TOCTOU.
- Shared overwrite conflict.
- Incomplete artifact bị run khác hiểu nhầm là valid.

Mandatory CR-R1..CR-R12:

1. Unique `run_id`.
2. Run-scoped critical outputs.
3. Shared artifact concurrency control.
4. Registry lost-update prevention.
5. Collision-safe temp paths.
6. Không dựa preflight đơn lẻ để đảm bảo write safety.
7. Atomicity/conflict detection phù hợp.
8. Run A không overwrite Run B.
9. Concurrency violation fail-closed.
10. Runtime collision được record và propagate.
11. Lock lifecycle/stale-lock/cleanup policy nếu sử dụng.
12. Crash-safe isolation.

### 6.5 Collision acceptance

Critical destinations phải được inventory và phân loại trước execution.

Unclassified collisions block execution.

Preflight states:

- `READY`
- `READY_WITH_WARNINGS`
- `BLOCKED`

Runtime collision protection vẫn bắt buộc. Atomic replace không tự ngăn overwrite hoặc lost updates.

---

## 7. 3.4.4.5 — Run Isolation & Temporary File Safety

### Status: CLOSED — PASS WITH GAPS

### 7.1 Run isolation scope

Isolation targets:

- Candidate variants.
- Selected pairs.
- Split outputs.
- Reports.
- Config snapshot.
- Run summary.
- Temporary files.
- Shared registry.
- Logs/execution trace.

### 7.2 Temporary file lifecycle

Required lifecycle:

`CREATE → WRITE → VALIDATE → COMMIT`

Failure path:

`FAILURE → ABORT → CLEANUP / RECOVERY RECORD`

Requirements:

- Unique name per run/operation.
- Exclusive creation where appropriate.
- Owner identity.
- Temp file nằm trong allowed root.
- Temp file không phải final artifact.
- Cleanup chỉ xóa files thuộc operation hiện tại.
- Detect/classify stale temporary files.
- Temp collision không gây silent overwrite.

### 7.3 Atomic commit & partial artifacts

- Validate before commit.
- Temp và final path phải thỏa atomicity constraints của filesystem.
- Commit failure phải propagate.
- Không overwrite artifacts ngoài authorized scope.
- File-level commit tách biệt run-level completion.
- Partial artifacts được classify và không silently reuse.
- Crash recovery reconcile ownership, integrity và commit state.
- Cleanup failure được report riêng.
- Durability expectations/limitations phải document; atomic replace tự nó không bảo đảm durability khi power loss.

### 7.4 Crash recovery scenarios

| Crash point | Required handling |
|---|---|
| Before temp creation | Không có artifact; run mới có thể bắt đầu |
| During temp write | Detect stale/incomplete temp; safe cleanup/quarantine |
| After validation, before commit | Không auto-commit/reuse |
| During commit | Reconcile commit state và final integrity |
| After commit, before stage report | Artifact có thể committed nhưng run incomplete; reconcile |
| Between stages | Run incomplete; không fallback sang stale outputs |
| During cleanup | Report cleanup residue/failure; không xóa artifact ngoài ownership |

### 7.5 Cross-stage artifact ownership

Artifact ownership/provenance phải verifiable, thông qua metadata hoặc manifest, bao gồm khi phù hợp:

- `run_id`
- `stage_id`
- `artifact_id`
- `config_fingerprint`
- `input_fingerprint`
- `artifact_fingerprint`
- `status`
- `created_at`
- `schema_version`

Không nhất thiết phải duplicate mọi field trong từng artifact nếu central manifest cung cấp linkage an toàn.

Downstream stages:

- Consume committed artifacts only.
- Verify ownership và compatibility.
- Không chọn artifact chỉ dựa path/existence.
- Reject incomplete, stale, cross-run hoặc altered artifacts.
- Reconcile final outputs với upstream committed artifacts.

### 7.6 Mandatory requirements

- Unique run identity và propagation.
- Run-scoped namespace và artifact ownership.
- Temporary naming/lifecycle/cleanup/recovery safety.
- Atomic commit cho artifacts phù hợp.
- Partial/crash artifact classification.
- Shared registry concurrency safety.
- Cross-stage ownership/lineage.
- Committed artifact consumption only.
- Runtime failure propagation.
- Run completion reconciled với committed required artifacts.
- Isolation policy captured trong execution trace.
- Cleanup/recovery observability.
- Integrity và compatibility validation khi handoff.
- Không run nào được overwrite/damage artifact của run khác.

---

## 8. Consolidated Preflight vs Runtime Responsibilities

### 8.1 Preflight — critical checks block trước generation

- Root authority, canonical path, containment, symlink policy.
- Existing artifact inventory và ownership/collision classification.
- Output isolation capability.
- Directory readiness và critical write capability.
- Collision mode (`FAIL` default, explicit `RESUME`/`OVERWRITE`).
- Registry/shared-resource concurrency readiness.
- Temporary path safety.
- Required commit readiness.
- Required config snapshot destinations.
- Critical checks không được skip hoặc để unverified.

### 8.2 Runtime — safeguards luôn hoạt động

- Re-check collision-sensitive writes.
- Exclusive create hoặc equivalent conflict protection.
- Atomic commit khi cần.
- Registry lock/transaction/conflict detection.
- Temp uniqueness và ownership.
- Integrity validation và cross-stage ownership checks.
- Failure propagation và artifact-state recording.
- Safe cleanup/recovery observability.
- Final reconciliation run status/artifacts.

**Preflight pass không đảm bảo runtime collision/failure không thể xảy ra.**

---

## 9. Output Readiness State Contract

| State | Acceptance meaning |
|---|---|
| `READY` | All critical checks pass; không unresolved critical collision |
| `READY_WITH_WARNINGS` | Critical checks pass; chỉ còn non-critical warnings đã phân loại |
| `BLOCKED` | Critical failure, skipped/unverified critical check, hoặc unresolved collision/readiness issue |

Critical checks skipped/unverified không thể yield `READY` hay `READY_WITH_WARNINGS`.

Generation chỉ được phép sau khi execution gate pass. Runtime failure vẫn có thể invalidate execution và phải propagate đúng stage/run.

---

## 10. Mandatory Implementation Backlog

Audit closure **không đồng nghĩa implementation completion**. Các requirements sau vẫn phải implement/test:

1. Centralized run context và unique `run_id`.
2. Canonical project/output roots, CWD-independent resolution.
3. Path canonicalization, containment và symlink handling thống nhất.
4. Central output readiness coordinator/result.
5. Directory/write readiness validation, controlled side effects.
6. Unified collision policy (`FAIL` default; safe explicit `RESUME`/`OVERWRITE`).
7. Existing artifact ownership, stale/incomplete/integrity detection.
8. Run-scoped output namespace/isolation.
9. Unique temporary naming, lifecycle, cleanup và recovery.
10. Atomic commit khi phù hợp và durability limitations.
11. Registry concurrency-safe updates.
12. Cross-stage artifact ownership/provenance/lineage.
13. Committed-artifact handoff và compatibility validation.
14. Runtime collision/failure propagation.
15. Run completion reconciliation và execution trace.
16. Unit, concurrency, crash/recovery, preflight và integration/E2E acceptance tests.

---

## 11. Final Verdict

**3.4.4 — Output Readiness Audit: CLOSED — PASS WITH GAPS**

All five audit checkpoints are closed at the design/evidence-audit level. Consolidated acceptance contract and mandatory implementation backlog have been established.

Implementation coverage remains unverified for the gaps above. No code changes were made during this audit.

### Next checkpoint

**3.4.4.6 — Output Readiness Acceptance Contract**

Reconcile output readiness requirements into the final preflight contract, critical/warning classifications, `READY / READY_WITH_WARNINGS / BLOCKED` execution gate and runtime safeguards.

---

*Audit principle: Confirmed evidence is carried forward. Gaps remain explicit. Design closure is not implementation proof.*


---

# DDR-3.4.5.2 — Preflight Result Model Contract & Schema Design

- **Project:** CodeSimilarityResearch
- **Phase:** I.9 — Pipeline Orchestration & E2E
- **Checkpoint:** 3.4.5.2
- **Decision status:** APPROVED
- **Decision type:** Design contract — implementation not started
- **Date:** 2026-11-22

## 1. Context

Existing code has domain-level generation, validation, pair-selection, sample/batch and persistence result models, but no centralized Preflight Result Model.

Preflight must provide auditable check-level outcomes, an aggregate readiness decision, diagnostics, identity/context and a reliable consumer contract.

## 2. Decision

Adopt a three-layer contract:

1. `PreflightCheckResult` — outcome of an individual readiness check.
2. `PreflightResult` — immutable finalized aggregate containing check records and the readiness decision.
3. Consumer contract — validate the result before consuming readiness; execution permission is derived, never trusted as an arbitrary field.

This checkpoint defines the contract only. No implementation, evaluator, filesystem checker or runtime gate is authorized by this decision.

## 3. Enums

### 3.1 Overall `PreflightStatus`

- `READY` — all critical checks pass; no warnings.
- `READY_WITH_WARNINGS` — all critical checks pass; one or more non-blocking warnings exist.
- `BLOCKED` — a critical check is not PASS, a required check is missing, or the result is invalid/incomplete.

### 3.2 Check-level `PreflightCheckStatus`

- `PASS`
- `FAIL`
- `WARN`
- `SKIPPED`
- `UNKNOWN`
- `ERROR`

### 3.3 `PreflightCheckClassification`

- `CRITICAL` — mandatory readiness condition.
- `WARNING` — issue is recorded but does not independently block.
- `OPTIONAL` — supplemental check; does not affect readiness.
- `DEFERRED` — explicitly deferred risk/capability under policy.

Classification describes importance/policy; status describes observed outcome.

## 4. `PreflightCheckResult` contract

Required fields:

| Field | Type | Required | Contract |
|---|---|---|---|
| `check_id` | string | Yes | Unique within a preflight result |
| `category` | string | Yes | Non-empty category |
| `classification` | enum | Yes | Check criticality |
| `status` | enum | Yes | Check outcome |
| `message` | string | Yes | Non-empty human-readable result |
| `path` | string or null | No | Context path, if applicable |
| `details` | dict | No | Structured JSON-compatible diagnostics |

Rules:

- IDs must be unique in a preflight.
- Category and message must be non-empty.
- Enum values must be valid.
- Details must be JSON-compatible.
- Finalized results must not be mutated.
- A path is contextual data; the model does not itself establish path safety.

## 5. `PreflightResult` contract

Required fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `preflight_id` | string | Yes | Identity of this preflight attempt |
| `run_id` | string | Yes | Intended pipeline run identity |
| `status` | enum | Yes | Aggregate readiness |
| `can_run` | boolean | Yes | Derived execution permission |
| `checks` | tuple of check results | Yes | Check-level evidence |
| `errors` | tuple of structured diagnostics | Yes | Blocking/fatal diagnostics |
| `warnings` | tuple of structured diagnostics | Yes | Non-blocking diagnostics |
| `optional_results` | tuple | Yes | Optional check outcomes |
| `deferred_risks` | tuple | Yes | Explicitly accepted/deferred risks |
| `checked_at` | ISO-8601 UTC string | Yes | Check timestamp |
| `config_fingerprint` | string | Yes | Configuration identity |
| `summary` | dict | Yes | Aggregate counts/explanation |

`preflight_id` and `run_id` are distinct: multiple preflight attempts may assess the same intended run.

## 6. Structured diagnostic contract

Errors and warnings are structured records, not plain strings.

Proposed fields:

- `code` — stable machine-readable code.
- `message` — human-readable explanation.
- `check_id` — related check ID or null.
- `details` — JSON-compatible context.

Separate collections:

- **Errors:** blocking/fatal diagnostics according to policy.
- **Warnings:** non-blocking diagnostics.
- **Optional results:** outcomes of supplemental checks.
- **Deferred risks:** risks accepted for deferral; never substitutes for a critical check that is missing, skipped, unknown, or errored.

## 7. Aggregation and readiness rules

- A critical check passes readiness only when `classification == CRITICAL` and `status == PASS`.
- A critical check with `FAIL`, `WARN`, `SKIPPED`, `UNKNOWN`, or `ERROR` does not pass readiness.
- Missing required critical checks, duplicate IDs, invalid status, or inconsistent aggregation must fail closed.
- All critical checks PASS and no warnings → `READY`.
- All critical checks PASS and warnings exist → `READY_WITH_WARNINGS`.
- Any critical check not PASS, required check missing, or invalid/incomplete result → `BLOCKED`.

Derive `can_run` solely from validated overall status:

- `READY` → `can_run = true`
- `READY_WITH_WARNINGS` → `can_run = true`
- `BLOCKED` → `can_run = false`

A consumer must reject contradictory data rather than choosing whichever field seems authoritative.

## 8. Result invariants

| ID | Invariant |
|---|---|
| PRI-01 | `preflight_id` is non-empty |
| PRI-02 | `run_id` is non-empty |
| PRI-03 | `config_fingerprint` is non-empty and conforms to the later fingerprint contract |
| PRI-04 | `checked_at` is valid |
| PRI-05 | Every check has the correct model/type |
| PRI-06 | Check IDs are unique |
| PRI-07 | Required critical checks are present |
| PRI-08 | Overall status agrees with aggregation rules |
| PRI-09 | `can_run` agrees with status |
| PRI-10 | Errors agree with critical failure/error policy |
| PRI-11 | Warnings agree with warning policy |
| PRI-12 | Optional results cannot falsely satisfy critical readiness |
| PRI-13 | Deferred risks cannot substitute for critical checks |
| PRI-14 | Summary counts agree with check records |
| PRI-15 | Finalized result is immutable |
| PRI-16 | Serialization round-trip preserves semantic equivalence |
| PRI-17 | Consumers validate before using execution permission |

Distinguish:

- **Invalid model:** schema/invariant violation; reject the model.
- **Valid blocked result:** internally valid result that correctly reports `BLOCKED`, with `can_run=false`.

A valid BLOCKED result must remain persistable and reportable.

## 9. Separation of concerns

The result model:

- does not execute checks;
- does not access the filesystem;
- does not implement evaluator policy;
- does not perform runtime enforcement;
- represents finalized evidence and derived readiness.

## 10. Serialization boundary / next checkpoint

Serialization is required but implementation details are deferred to **3.4.5.3 — Serialization & Schema Versioning Contract**.

Requirements carried forward:

- JSON-compatible values.
- Enum values serialized as stable strings.
- UTC ISO-8601 timestamps.
- Deterministic ordering for checks and diagnostics.
- No mutable references in serialized result.
- `details` contains only JSON-compatible values.
- Preserve checks, diagnostics, optional results, deferred risks, summary and identity fields.
- Validate deserialized payload before consumers use it.

## 11. Acceptance criteria

| ID | Criterion |
|---|---|
| RM-01 | Check-level model is independent |
| RM-02 | Root result model is independent |
| RM-03 | Status and classification are distinct |
| RM-04 | Diagnostics are structured |
| RM-05 | Optional results and deferred risks are distinct |
| RM-06 | Overall readiness is fail-closed |
| RM-07 | `can_run` is derived |
| RM-08 | Run and configuration context included |
| RM-09 | Result invariants are defined |
| RM-10 | Finalized result is immutable |
| RM-11 | Model does not depend on evaluator/filesystem |
| RM-12 | Contract is serialization-ready |

## 12. Scope boundaries and carry-forward

- This design does not claim existing repository code implements the contract.
- Checkpoint 3.4.5.1 inventory is closed as PASS WITH GAPS.
- Existing generation report is generation-scoped; report updates before persistence are not deemed a bug based on current evidence.
- Existing result models/exporters are reuse references only; no refactor is authorized.
- Implementations, evaluator checks, execution gate, E2E and residual risk closure remain open.
- 3.4.5.3 must refine schema/versioning/round-trip and compatibility contracts.

## 13. Approval record

Approved conversationally by the user on 2026-11-22. This document records the design contract; implementation requires a separate explicit approval.


---

# DDR-3.4.5.3 — Serialization & Schema Versioning Contract

- Project: CodeSimilarityResearch
- Phase: I.9 — Pipeline Orchestration & E2E
- Checkpoint: 3.4.5.3
- Decision status: PROPOSED — Pending user approval
- Decision type: Design contract — implementation not started
- Date: 2026-11-22

## 1. Context

PreflightResult requires persistent, auditable JSON representation.

JSON parse success alone does not guarantee schema compatibility, semantic preservation, result integrity, or safe consumer behavior.

## 2. Decision

Adopt explicit schema identity, versioning, deterministic serialization, semantic round-trip validation, compatibility policy and fail-closed payload rejection.

Serialization, deserialization, export and consumer authorization are separate responsibilities.

## 3. Schema Identity

- schema_name: `preflight_result`
- schema_version: `1.0.0` initial proposed version

Schema version is independent of:

- config_version
- pipeline_version
- validator_version
- report_version

## 4. Versioning Policy

Semantic versioning:

- MAJOR: breaking schema or semantic changes.
- MINOR: backward-compatible schema extensions.
- PATCH: compatible corrections without semantic change.

Version changes must reflect compatibility and semantics, not merely field count.

## 5. Canonical Root Contract

Required fields:

- schema_name
- schema_version
- preflight_id
- run_id
- status
- can_run
- checked_at
- config_fingerprint
- checks
- errors
- warnings
- optional_results
- deferred_risks
- summary

All required fields must be present. Missing fields must not receive readiness defaults.

## 6. Serialization Rules

- UTF-8 JSON.
- Enums encoded as stable strings.
- No integer enum ordinals.
- Deterministic field/key ordering.
- Deterministic check and diagnostic ordering.
- JSON-compatible nested details.
- Reject NaN and Infinity.
- UTC ISO-8601 timestamps.
- Stable human-readable formatting for persisted artifacts.
- No runtime objects in payload.

## 7. Nested Records

Check, diagnostic, optional-result and deferred-risk records must have explicit schemas.

- Required fields must be preserved.
- IDs and references must be preserved.
- Optional fields use a consistent representation.
- Enum values are stable strings.
- Nested details must be JSON-compatible.
- Deferred risks are not PASS checks.
- Optional results cannot satisfy critical readiness.

## 8. Semantic Round-Trip

Serialize → Deserialize → Validate must preserve semantic equivalence.

Preserve:

- Identity/context.
- Status and can_run.
- All check records.
- Errors and warnings.
- Optional results.
- Deferred risks.
- Summary.
- Classification/status distinctions.
- Details and contextual paths.

Successful JSON parsing is not sufficient.

Deserialization must reconstruct a validated immutable model, not expose raw mutable dictionaries as trusted results.

## 9. Compatibility Policy

- Same supported schema version: read and validate.
- Supported older compatible minor version: read and validate.
- Unsupported major version: reject by default.
- Unsupported newer minor: reject unless explicit extension compatibility is guaranteed.
- Missing schema version: reject.
- Malformed version: reject.
- Unknown enum: reject.
- Missing required field: reject.

Unknown fields are rejected by default for schema 1.0.0. Explicit future compatibility rules may permit safe extensions.

## 10. Migration Policy

Migration is explicit only.

- Explicit source → target versions.
- Deterministic.
- No implicit major-version migration.
- No guessed values.
- No critical semantics loss.
- Migration output validates fully.
- Migration failures reject.
- Original artifacts remain unchanged.

Migration audit must preserve source/target versions, migration identity, outcome and original artifact identity when migration is implemented.

## 11. Invalid Payload Handling

Reject:

- Invalid JSON.
- Wrong root type/schema identity.
- Unsupported version.
- Missing required fields.
- Invalid field types.
- Invalid enum.
- Duplicate checks.
- Inconsistent status/can_run.
- Inconsistent summary.
- Missing critical evidence.
- Invalid timestamp.
- Non-JSON-compatible details.
- NaN/Infinity.

No automatic repair or fail-open behavior.

## 12. Filesystem Boundary

Serialization does not establish file safety.

- Serialization/schema: 3.4.5.3.
- Path containment/output isolation/collision/temp safety: 3.4.4.
- Exporter must comply with 3.4.4 output contract.
- Serialization success does not imply export success.
- Export success does not imply preflight readiness.

## 13. Acceptance Criteria

- Schema identity defined.
- Schema version independent of pipeline/config versions.
- Versioning policy defined.
- Root fields canonicalized.
- Stable enum encoding.
- Nested record serialization defined.
- JSON-compatible details defined.
- Deterministic output defined.
- Semantic round-trip defined.
- Deserialization validates invariants.
- Compatibility policy defined.
- Unknown field policy defined.
- Explicit migration policy defined.
- Invalid payload behavior fail-closed.
- Filesystem safety separated.
- No implementation performed.

## 14. Scope & Carry-Forward

- Design only.
- No implementation authorized.
- Model implementation must satisfy 3.4.5.2.
- Invariant and consumer enforcement must satisfy 3.4.5.4.
- Export safety must satisfy 3.4.4.
- Consumer execution gate remains a later checkpoint.
- Migration engine is not required for baseline schema 1.0.0.

## 15. Approval Record

Pending explicit user approval.


---

# DDR-3.4.5.4 — Result Invariants & Consumer Contract

- **Project:** CodeSimilarityResearch
- **Phase:** I.9 — Pipeline Orchestration & E2E
- **Checkpoint:** 3.4.5.4
- **Decision status:** PROPOSED — Pending user approval
- **Decision type:** Design contract — implementation not started
- **Date:** 2026-11-22

## 1. Context

A valid PreflightResult must not only represent readiness but also be trustworthy at the execution boundary.

Correct serialization alone does not guarantee correct aggregation, identity matching, freshness, or safe consumer behavior.

## 2. Decision

Adopt explicit result invariants and a fail-closed consumer contract.

Consumers must validate the preflight result before using it to authorize pipeline execution.

## 3. Invariant groups

### RI-A — Identity & Context

- Preflight ID and run ID are non-empty and valid.
- Config fingerprint conforms to its contract.
- Timestamp is valid and timezone-aware per UTC contract.
- Result identity and context must match the intended execution.
- Results cannot be reused to authorize a different run.

### RI-B — Check Collection

- All records have valid model/type, classification and status.
- Check IDs are unique.
- Category and message are non-empty.
- Required critical checks must be present.
- Ordering is deterministic.
- Logical duplicate checks cannot bypass required-check policy.

### RI-C — Aggregation

- Overall status must agree with check outcomes.
- Critical readiness requires exact status PASS.
- Critical WARN, FAIL, SKIPPED, UNKNOWN and ERROR do not pass readiness.
- Missing required critical checks block.
- READY requires no warnings.
- READY_WITH_WARNINGS requires all critical checks PASS.
- BLOCKED must have can_run=false.
- can_run is derived from validated status.
- Invalid/incomplete results cannot authorize execution.

### RI-D — Diagnostics

- Diagnostic code and message are non-empty.
- Referenced check IDs must be valid.
- Errors and warnings must reconcile with policy.
- Contradictory diagnostics are invalid.
- Optional results cannot satisfy critical checks.
- Deferred risks cannot substitute for required checks.
- Diagnostic ordering is deterministic.

### RI-E — Summary & Serialization

- Summary values must match actual check records.
- Caller cannot override derived summary values.
- Serialized data preserves identities, checks and diagnostics.
- Deserialization requires revalidation.
- Missing fields cannot default to READY.
- Unknown enums are rejected.
- Incompatible schemas require rejection or explicit migration.

### RI-F — Immutability & Lifecycle

- Finalized result is immutable.
- Nested collections/details cannot expose mutable references.
- No checks may be appended after finalization.
- Builders/evaluators cannot mutate finalized results.
- Consumers cannot alter readiness to bypass policy.

## 4. Valid BLOCKED vs Invalid Result

### Valid BLOCKED

- Model/schema is valid.
- Checks are represented.
- Critical failures are recorded.
- Aggregation is consistent.
- can_run=false.

A valid BLOCKED result is persistable and auditable.

### Invalid/Rejected

Examples:

- Invalid schema.
- Missing identities.
- Duplicate check IDs.
- Contradictory aggregation.
- Summary mismatch.
- Unknown enum values.
- Missing critical evidence without explicit representation.

Invalid results must not authorize execution.

If a required check is missing, the aggregator should materialize an explicit UNKNOWN check with diagnostic context when possible. A completely absent required record makes the result incomplete and subject to rejection.

## 5. Consumer MUST

- Validate schema and invariants.
- Match run ID.
- Match config fingerprint.
- Match intended input/source identity.
- Match output context and policy.
- Verify overall status and derived readiness.
- Reject invalid, incomplete, stale or mismatched results.
- Fail-closed on validation exceptions.
- Enforce the gate at execution boundary.

## 6. Consumer MUST NOT

- Trust can_run alone.
- Trust status without validation.
- Reuse results from another run.
- Ignore critical failures.
- Treat critical WARN as PASS.
- Fabricate missing checks as PASS.
- Alter status/summary to authorize execution.
- Substitute optional results or deferred risks for critical checks.
- Fail open on exceptions.

## 7. Consumer validation sequence

1. Receive result.
2. Validate schema.
3. Validate invariants.
4. Verify required checks.
5. Match run ID.
6. Match config fingerprint.
7. Match input/source identity.
8. Match output context.
9. Reconcile status and checks.
10. Verify can_run.
11. Authorize or block.

## 8. Freshness

- Timestamp is mandatory.
- Identity/config/input/output context must match.
- TTL is not hardcoded in this checkpoint.
- Any TTL/freshness policy must be explicit.
- TTL does not replace revalidation of mutable filesystem/toolchain state.
- State changes after preflight may invalidate readiness.

## 9. Error taxonomy proposal

Result rejection:

- PFR_INVALID_SCHEMA
- PFR_INVALID_INVARIANT
- PFR_DUPLICATE_CHECK
- PFR_MISSING_REQUIRED_CHECK
- PFR_INVALID_AGGREGATION

Context rejection:

- PFR_RUN_ID_MISMATCH
- PFR_CONFIG_MISMATCH
- PFR_INPUT_MISMATCH
- PFR_OUTPUT_CONTEXT_MISMATCH
- PFR_STALE_RESULT

Readiness rejection:

- PFR_BLOCKED
- PFR_CRITICAL_CHECK_FAILED
- PFR_CRITICAL_CHECK_UNKNOWN
- PFR_CRITICAL_CHECK_ERROR
- PFR_CRITICAL_CHECK_SKIPPED

Codes are proposed identifiers and must be reconciled with existing error conventions before implementation.

## 10. Security & Integrity Boundary

- Schema validation and invariant validation are mandatory.
- Context matching is mandatory.
- Cryptographic signing is not part of the current local research pipeline baseline.
- Validation does not prove authenticity against malicious in-memory tampering.
- TOCTOU remains a documented residual risk.
- Re-evaluate the trust model if remote/untrusted execution is introduced.

## 11. Acceptance Criteria

- Identity invariants defined.
- Check collection invariants defined.
- Aggregation invariants defined.
- Diagnostic consistency defined.
- Summary consistency defined.
- Immutability lifecycle defined.
- Valid BLOCKED distinguished from invalid.
- Consumer trust boundary defined.
- Consumer MUST/MUST NOT defined.
- Context matching defined.
- Fail-closed behavior defined.
- Freshness policy boundary defined.
- Error taxonomy proposed.
- Residual limitations documented.
- No implementation performed.

## 12. Scope & Carry-Forward

- Design only; no code changes authorized.
- Serialization/versioning implementation belongs to checkpoint 3.4.5.3.
- Execution gate implementation belongs to later runtime enforcement checkpoint.
- Required-check inventory must be authoritative.
- Every execution entrypoint must enforce the consumer contract.
- Freshness and state revalidation remain subject to later runtime design.
- This checkpoint does not claim current repository implementation satisfies the contract.

## 13. Approval Record

Pending explicit user approval.


---

# SF03.4 — Policy Reconciliation: Clarifications to Confirm

**Project:** CodeSimilarityResearch  
**Phase:** I.9 — Pipeline Preflight, Orchestration & Execution Readiness  
**Checkpoint:** 3.4.6 — Shared Safety Foundations  
**Status:** Pending user confirmation  
**Scope:** Operational clarifications C-01 through C-04. No implementation has started.

---

## 1. Context

SF03.2 and SF03.3 evidence audits identified persistence, cleanup, collision, overwrite, concurrency, and incomplete-artifact gaps.

SF03.4 reconciliation found that the existing approved authorities are sufficient; no new major policy is required:

- **M-1:** Canonical path authority, containment, root separation, reject escapes.
- **M-3:** Run-scoped outputs, collision safety, explicit fail/resume/overwrite policy.
- **M-4:** Registry single-writer/transaction and lost-update prevention.
- **M-5:** Preflight readiness and critical safety blocking.
- **D-02:** Fatal integrity errors propagate; recoverable errors are structured.
- **D-04:** Transaction-like artifact/export behavior.
- **D-09:** Consumer trust boundary and artifact validation.

The following clarifications make these existing policies implementable consistently.

---

## 2. C-01 — Default Collision Mode

### Proposed decision

**FAIL-IF-EXISTS is the default for immutable artifacts.**

- Existing destination files are not overwritten by default.
- Resume and overwrite must be explicitly authorized by policy/configuration.
- Permission to reuse an artifact must not be inferred merely because a file exists.
- Collision checks must be race-safe; check-then-write alone is insufficient.

### Scope / notes

Artifact types may impose stricter constraints. Immutable variant source files should remain fail-if-exists unless an explicitly approved lifecycle permits otherwise.

**Confirmation:** ☐ Approve  ☐ Reject / revise

---

## 3. C-02 — Atomic Persistence Baseline

### Proposed decision

Use a **temp-first → validate → commit** persistence lifecycle for artifacts that support atomic replacement.

1. Prepare and validate destination path, containment, parent directory, ownership, and collision policy.
2. Write into a uniquely created temporary file in the destination directory/filesystem.
3. Flush and validate the temporary artifact as appropriate.
4. Commit using an atomic filesystem operation where supported and permitted by destination policy.
5. Verify the committed artifact when required.
6. Do not treat pre-commit temporary files as completed artifacts.

Direct-to-destination writes should be replaced with this safe commit pattern where feasible.

### Limitations

Atomicity and durability guarantees depend on filesystem and platform behavior. The implementation must not claim guarantees it cannot verify.

**Confirmation:** ☐ Approve  ☐ Reject / revise

---

## 4. C-03 — Resume Semantics

### Proposed decision

**Resume may reuse only verified artifacts.**

Before reuse, validate at minimum:

- Run identity/context.
- Artifact identity and expected destination.
- Schema/version compatibility where applicable.
- Completion and integrity status.
- Provenance/hash requirements for that artifact type.

Filename existence alone is not sufficient evidence for reuse. Incomplete or partial artifacts are not reusable as completed outputs.

Resume must be an explicit mode/authorization; it must not silently become overwrite.

**Confirmation:** ☐ Approve  ☐ Reject / revise

---

## 5. C-04 — Cleanup & Durability

### Proposed decision

- Cleanup is attempted on failure paths.
- Cleanup failure is recorded as a secondary failure and must not mask the primary failure.
- File-level flush/fsync is required for critical persistence paths according to the agreed durability level.
- Parent-directory durability and crash recovery are treated explicitly according to filesystem/platform capabilities.
- Stale temporary files left by process crashes must be safely detectable/reconcilable; they must never be assumed to be committed artifacts.

### Limitations

Durability behavior is filesystem/platform-dependent. Directory fsync and crash-recovery guarantees may not be universally available.

**Confirmation:** ☐ Approve  ☐ Reject / revise

---

## 6. Proposed Combined Baseline

If all four clarifications are approved:

1. **Default:** Fail-if-exists for immutable outputs.
2. **Persistence:** Temp-first, validate, commit, verify as required.
3. **Resume:** Explicit and identity/integrity-verified; never filename-only.
4. **Cleanup:** Preserve primary errors; record cleanup failures separately.
5. **Durability:** Apply critical file flush requirements; document platform-dependent guarantees.
6. **No implicit overwrite:** Replacement only under explicit authorization and compatible artifact policy.

---

## 7. Approval Record

| Clarification | Decision | Notes |
|---|---|---|
| C-01 — Default Collision Mode | Pending | |
| C-02 — Atomic Persistence Baseline | Pending | |
| C-03 — Resume Semantics | Pending | |
| C-04 — Cleanup & Durability | Pending | |

**Overall checkpoint:** SF03.4 Policy Reconciliation — PASS, existing authorities sufficient; operational clarification approval pending.

**Next checkpoint after confirmation:** SF03.5 — Implementation Contract & Design.

**Implementation status:** Not started. No code changes are authorized by this document.


---

# I.9.3 — 3.4.6 Shared Safety Foundations
## SF03.5.8 — Full Safety Design Review & Approval

**Checkpoint status:** REVIEW COMPLETE — PENDING APPROVAL  
**Implementation status:** NOT STARTED  
**Scope:** Reconcile SF03.5.1–SF03.5.7 as a unified safety architecture.  
**Project:** CodeSimilarityResearch / I.9 Pipeline Preflight, Orchestration & Execution Readiness

---

## 1. Purpose

Review all seven preceding safety design checkpoints as one system, identify conflicts or overlapping responsibilities, refine interfaces and ownership, identify unresolved technical decisions, and define approval/acceptance gates before implementation.

This checkpoint is design review only. It does not authorize code changes or imply approval.

## 2. Review of seven checkpoints

| Checkpoint | Topic | Review outcome |
|---|---|---|
| SF03.5.1 | Persistence result & failure state | Keep; normalize states and derive status |
| SF03.5.2 | Path safety interface | Keep; foundational path authority |
| SF03.5.3 | Safe persistence & commit semantics | Keep; clarify collision and commit semantics |
| SF03.5.4 | Registry transaction & concurrency | Keep; lock must cover full logical transaction |
| SF03.5.5 | Failure policy & propagation | Keep; reconcile with persistence truth |
| SF03.5.6 | Preflight integration | Keep; readiness assessment only |
| SF03.5.7 | Component integration & dependency | Keep 4 services; avoid redundant modules |

**Overall:** No severe architectural contradiction was identified. Several contracts require normalization before approval and implementation.

---

## 3. Reconciliation decisions proposed

### R-01 — Persistence status and commit state

Persistence state dimensions:

- `CommitState`: `NOT_COMMITTED`, `COMMITTED`, `OUTCOME_UNKNOWN`
- `VerificationState`: `NOT_REQUIRED`, `NOT_RUN`, `PASSED`, `FAILED`
- `CleanupState`: `NOT_NEEDED`, `PENDING`, `SUCCEEDED`, `FAILED`

Status must be derived from these dimensions; callers must not independently assign contradictory values.

Proposed statuses:

- `COMMITTED`: commit confirmed, verification acceptable, cleanup succeeded
- `COMMITTED_WITH_WARNINGS`: commit confirmed, integrity acceptable, cleanup failed
- `VERIFY_FAILED`: commit confirmed but post-commit verification failed
- `REJECTED`: pre-commit policy rejection (e.g., FAIL_IF_EXISTS collision)
- `FAILED`: confirmed failure before commit
- `COMMIT_UNKNOWN`: outcome cannot yet be determined

`REJECTED` is a policy outcome, not a generic filesystem error.

### R-02 — PathSafety and SafePersistence responsibility

**PathSafety**

- Canonicalize paths.
- Validate root containment.
- Validate source/output-root relationships.
- Enforce symlink/junction/reparse policy.
- Validate write targets.

**SafePersistence**

- Invoke PathSafety at the write boundary.
- Do not trust an earlier preflight check as permanent authorization.
- Do not implement a second, divergent containment policy.

Proposed: PathSafety is the single authority for path policy; SafePersistence rechecks relevant conditions at the write boundary.

### R-03 — Preflight is not permanent authorization

Preflight evaluates a context at a point in time.

Contract:

- Result is bound to run ID, config fingerprint, input identity, canonical paths, output context, and mode.
- Context changes invalidate the result.
- Execution still revalidates safety-critical conditions.
- `READY` is not a token that bypasses filesystem checks.

Proposed: preflight is a context-bound readiness snapshot, not a security authorization token.

### R-04 — SafePersistence vs RegistryTransaction

**SafePersistence — file-level transaction**

`Temp → Write → Flush → Validate → Commit → Verify → Cleanup`

**RegistryTransaction — logical registry transaction**

`Lock → Read → Validate → Check Duplicate → Build Snapshot → Persist → Verify → Unlock`

RegistryTransaction uses SafePersistence to commit the registry file. SafePersistence remains unaware of registry schema, variant IDs, sample identity, and domain-specific duplicate rules.

Proposed: RegistryTransaction owns logical transaction/concurrency; SafePersistence owns file commit.

### R-05 — FailurePolicy must not override persistence truth

Separate:

- **Operation truth:** Was the file committed?
- **Pipeline disposition:** Continue, skip, stop stage, or abort run?

A cleanup failure after confirmed commit must not convert commit state to `NOT_COMMITTED` or `FAILED`.

Proposed: FailurePolicy decides disposition, not the underlying commit truth.

### R-06 — Generation is not persistence

Sample lifecycle:

`PENDING → GENERATED → VALIDATED → PERSISTED → REGISTERED → COMPLETE`

- `GENERATED`: transformation produced output.
- `VALIDATED`: output passed validation.
- `PERSISTED`: file commit is confirmed.
- `REGISTERED`: registry transaction confirmed.
- `COMPLETE`: lifecycle requirements all satisfied.

Uncertain states (e.g., `COMMIT_UNKNOWN`, registry commit unknown, finalization failure) must remain explicit. Do not collapse all outcomes into a single success boolean.

---

## 4. Reconciled dependency architecture

```mermaid
flowchart TD
    PS[PathSafety]
    SP[SafePersistence]
    FP[FailurePolicy]
    RT[RegistryTransaction]
    PF[Existing Preflight]
    VW[VariantWriter]
    VR[VariantRegistry]
    BR[Batch Runner]
    OR[Pipeline Orchestrator]

    PS --> SP
    PS --> RT
    SP --> RT
    PS --> PF
    FP --> BR
    FP --> OR
    RT --> VR
    PS --> VW
    SP --> VW
    VR --> BR
    VW --> BR
    PF --> OR
    BR --> OR

5. Single-owner responsibility table
Responsibility	Single authority
Canonical path & containment	PathSafety
Symlink/junction/reparse policy	PathSafety
File temp lifecycle	SafePersistence
File commit semantics	SafePersistence
Commit/verification/cleanup state	SafePersistence
Failure classification	FailurePolicy
Failure disposition	FailurePolicy + scope-owning orchestrator
Registry lock	RegistryTransaction
Registry logical transaction	RegistryTransaction
Registry schema/domain validation	VariantRegistry
Preflight aggregation	Existing preflight owner
Variant serialization	Artifact/business owner
Per-item continuation	Batch runner
Run state & abort decision	Orchestrator
Final report serialization	Existing report owner
Run summary serialization	Existing summary owner

No module should duplicate another module's safety policy for convenience.

6. Failure classification and propagation
Severity
- INFO
- WARNING
- ERROR
- FATAL
Recoverability
- RECOVERABLE
- NON_RECOVERABLE
- UNKNOWN (fail-closed)
Propagation scope
- LOCAL
- ITEM
- STAGE
- RUN
Disposition
- CONTINUE
- SKIP_ITEM
- STOP_STAGE
- ABORT_RUN
Keep these as separate dimensions rather than a single flattened enum.
Exception-boundary contract
- Safety services raise typed errors with cause context.
- Domain layer classifies operation failures.
- Runner continues only for policy-approved recoverable failures.
- Orchestrator owns run-level disposition.
- Catch-all except Exception cannot downgrade failures to recoverable.
- Fatal failures are not catch-and-continue.
- Cleanup failure is secondary if a primary failure already exists.
- COMMIT_UNKNOWN is not directly retryable.

7. Collision, resume, and overwrite
These are separate mechanisms:
Mode	Meaning	Rule
FAIL_IF_EXISTS	Destination already exists	Reject; preserve existing artifact
REPLACE_AUTHORIZED	Explicitly authorized replacement	Only when policy/context permit
RESUME	Continue an earlier run	Verify run/artifact identity and compatibility

Rules:
- Default immutable-artifact mode is FAIL_IF_EXISTS.
- Collision never silently becomes replacement.
- Resume is not overwrite.
- Partial artifacts are not reusable unless verified.
- Immutable variant outputs cannot be replaced contrary to policy.
- Run directory ownership/identity must be explicit.
- Collision races require a race-safe commit primitive; pre-check alone is insufficient.

8. Preflight and execution boundary
Preflight evaluates seven groups:
1. Config validation
2. Run identity
3. Path safety
4. Input readiness
5. Output readiness
6. Registry readiness
7. Execution capabilities
Aggregate result
Condition	Status
All critical checks PASS, no warnings	READY
Critical checks PASS, warnings exist	READY_WITH_WARNINGS
Critical FAIL/ERROR/UNKNOWN	BLOCKED
Critical SKIPPED or missing	BLOCKED

Execution gate validates schema, required checks, run identity, config fingerprint, canonical path/output context, input identity, mode, and aggregate consistency. No normal-execution bypass of preflight.

Preflight does not reserve registry locks or guarantee later filesystem availability. Execution still revalidates safety-critical conditions.

9. Minimal safety-service layout
Keep four initial services:
src/safety/
  __init__.py
  path_safety.py
  safe_persistence.py
  failure_policy.py
  registry_transaction.py


- Merge persistence models/types with safe_persistence.py for initial implementation.
- Do not create safety_preflight.py; integrate with existing preflight owner (confirm exact file during implementation).
- No generic transaction framework.
- No universal retry framework.
- No multi-backend filesystem abstraction.
- No async persistence.
- No streaming until a demonstrated need.
- No automatic stale-temp deletion.
- No automatic lock-file deletion.
- No automatic registry repair.
- No distributed locking.

10. Unresolved technical decisions
ID	Decision	Resolution method
U-01	Windows atomic no-overwrite commit primitive	Prototype and race tests
U-02	Atomic replacement guarantees per filesystem	Verify actual semantics
U-03	OS-level lock implementation/dependency	Prototype and process tests
U-04	Lock behavior local vs network filesystems	Document capability/limits
U-05	Parent-directory durability on Windows	Verify platform support
U-06	Post-commit verification by artifact type	Define artifact-specific policy
U-07	COMMIT_UNKNOWN reconciliation	Destination/fingerprint inspection
U-08	Windows canonicalization: drive, UNC, case, junction	Target-platform tests
U-09	Stale temp recovery	Design reconciliation; no auto-delete yet
U-10	Run-directory ownership/reuse	Define identity/create/resume rules
U-11	Source mutation between hash and read/use	Snapshot or fail-on-change strategy
U-12	File-size/resource limits	Dataset/config requirements

Must resolve before implementation planning is finalized
U-01, U-02, U-03, U-07, U-08, U-10

The remaining items can be resolved during component verification only if they do not weaken a safety guarantee. Resolve before acceptance of the affected component.

11. Full design acceptance criteria
Architecture
- [ ] Each safety responsibility has one authority owner.
- [ ] No circular dependencies.
- [ ] No duplicate safety policy.
- [ ] Preflight and execution enforcement are separate.
- [ ] Registry logical transaction and file transaction are separate.
- [ ] Orchestrator is the sole run-state authority.
State and failure
- [ ] Persistence states cannot contradict.
- [ ] Commit truth survives verification/cleanup failure.
- [ ] COMMIT_UNKNOWN fails closed.
- [ ] Fatal errors cannot be downgraded to recoverable.
- [ ] Cleanup failure does not erase primary error.
- [ ] Generated/validated/persisted/registered/complete are distinct.
Filesystem and transaction
- [ ] Canonical paths and containment are consistent.
- [ ] Symlink/junction/reparse policy is enforced.
- [ ] Temp lifecycle has clear ownership.
- [ ] Collision defaults to fail-if-exists.
- [ ] Replacement requires explicit authorization.
- [ ] Registry lock spans complete read-modify-write transaction.
- [ ] Process-level concurrency tests are included.
- [ ] Silent overwrite is prevented.
Preflight
- [ ] Critical checks are complete.
- [ ] UNKNOWN, ERROR, SKIPPED, or missing critical checks block.
- [ ] Result is context-bound.
- [ ] Context mismatch invalidates the result.
- [ ] Execution revalidates safety-critical conditions.

12. Proposed implementation order (after approval)
Phase A — Foundation
PathSafety → SafePersistence → FailurePolicy
Phase B — Transactions
RegistryTransaction → VariantRegistry integration
Phase C — Preflight
Integrate shared safety services with existing preflight owner.
Phase D — Writers and artifacts
VariantWriter → reports → run summary → preprocessing outputs
Phase E — Pipeline
Source integrity → runner → orchestrator → failure propagation
Phase F — Acceptance
Unit tests → concurrency/process tests → cross-component tests → E2E → regression → acceptance/closure

Each phase requires review, test evidence, and closure before advancing.

13. Review conclusion
Review outcome: No severe architectural contradiction identified.
Design status: Review complete; approval pending.
Implementation: Not started.

Reconciled:
- Four safety services are sufficient for the initial architecture.
- Persistence state is the authority for file commit truth.
- FailurePolicy owns policy/disposition, not operation truth.
- PathSafety is the single path-policy authority.
- SafePersistence is the single file-commit authority.
- RegistryTransaction owns logical registry concurrency.
- Preflight does not replace execution enforcement.
- Runner must not equate generation with persistence success.
- Orchestrator owns run lifecycle and run-level decisions.
- Platform/filesystem-dependent technical decisions remain unresolved.

14. Timeline status
| I.9 section | Status |
|---|---|
| I.9.1 Pipeline Architecture Audit | CLOSED |
| I.9.2 Config & Execution Contract | CLOSED |
| I.9.3 Result/Report Model | IN PROGRESS |
| 3.4.1–3.4.5 | CLOSED |
| 3.4.6 SF03.5.1–.7 | Design drafts complete |
| 3.4.6 SF03.5.8 | Review complete, pending approval |
| I.9.4 Stage Orchestration | NOT STARTED |
| I.9.5 Failure Propagation | NOT STARTED |
| I.9.6 Artifact/Export Integration | NOT STARTED |
| I.9.7 Reproducibility & Execution Trace | NOT STARTED |
| I.9.8–I.9.11 | Tests, regression, acceptance & closure | NOT STARTED |

15. Next checkpoint
After explicit approval of this full design:

SF03.5.9 — Safety Implementation Plan & Technical Decision Resolution

Resolve required technical decisions, verify Windows commit/locking behavior, finalize implementation-level contracts, and then begin coding.

Approval note: User approval is still required. “Review complete” does not mean “design approved.”