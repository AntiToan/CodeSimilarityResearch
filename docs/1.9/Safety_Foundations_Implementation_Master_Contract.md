# Safety Foundations — Implementation Master Contract

**Project:** CodeSimilarityResearch  
**Research phase:** I.9 — Pipeline Preflight, Orchestration & Execution Readiness  
**Subsystem:** I.9.3 → 3.4.6 Shared Safety Foundations  
**Checkpoint:** SF03.5.9.9 — Implementation Readiness & Approval  
**Document version:** 1.0.0  
**Status:** READY WITH CONDITIONS — PENDING IMPLEMENTATION APPROVAL  
**Implementation status:** NOT STARTED

---

## 1. Purpose

This document consolidates all investigation, design contracts, technical findings, safety policies, integration boundaries, implementation plans, and acceptance criteria established before implementing the Shared Safety Foundations subsystem.

Its purposes are to:

- Preserve all safety decisions before implementation.
- Prevent undocumented architectural changes during coding.
- Establish authoritative contracts for safety-critical operations.
- Separate approved design decisions from unverified technical assumptions.
- Define implementation sequencing and dependency boundaries.
- Define test and acceptance requirements.
- Preserve unresolved technical risks and deferred scope.
- Establish an implementation approval boundary.

This document is the implementation reference for the Shared Safety Foundations subsystem.

It does not authorize implementation by itself.

---

## 2. Project Context

### 2.1 Repository

Project:

`CodeSimilarityResearch`

Repository:

`D:\University\NCKH\fullstack\CodeSimilarityResearch`

Environment:

- Windows
- Python
- PowerShell
- Virtual environment
- Filesystem-based artifact and registry persistence

### 2.2 Phase

Phase I.9:

**Pipeline Preflight, Orchestration & Execution Readiness**

Current subsystem:

**I.9.3 — Pipeline Result/Report Model**

Current work area:

**3.4.6 — Shared Safety Foundations**

### 2.3 Implementation objective

Introduce a shared safety layer supporting:

- Canonical path resolution.
- Path containment.
- Source integrity.
- Output collision protection.
- Safe persistence.
- Registry transaction safety.
- Run identity and directory ownership.
- Failure classification and propagation.
- Preflight execution gating.
- Artifact integrity and recovery.
- Pipeline integration without bypassing safety boundaries.

---

# 3. Timeline and Checkpoint History

## 3.1 I.9 overview

### Closed

- I.9.1 — Pipeline Architecture Audit
- I.9.2 — Pipeline Config & Execution Contract

### Current phase

- I.9.3 — Pipeline Result/Report Model

### Remaining

- I.9.4 — Stage Orchestration
- I.9.5 — Error Handling & Failure Propagation
- I.9.6 — Artifact/Export Integration
- I.9.7 — Reproducibility/Execution Trace
- I.9.8 — Orchestrator Unit Tests
- I.9.9 — E2E Tests
- I.9.10 — Regression & Integration Audit
- I.9.11 — Acceptance & Closure

---

## 3.2 I.9.3 progress

### 3.4.1 — Preflight Responsibility & Capability Inventory

Status:

CLOSED — PASS WITH GAPS

Responsibilities and missing capabilities identified.

### 3.4.2 — Preflight Acceptance Contract

Status:

CLOSED — DESIGN APPROVED

Critical checks, blocking rules, and readiness semantics established.

### 3.4.3 — Input & Metadata Readiness

Status:

CLOSED — PASS WITH GAPS

Input, source, metadata, encoding and readiness requirements audited.

### 3.4.4 — Output Readiness Audit

Checkpoints 3.4.4.1 through 3.4.4.6.7:

CLOSED — DESIGN APPROVED

Output readiness, path authority, collisions, reports, registries, and persistence considerations established.

### 3.4.5 — Preflight Result Model & Schema

Checkpoints 3.4.5.1 through 3.4.5.4:

CLOSED — APPROVED

Result model, statuses, serialization, schema versioning, and consumer trust boundary established.

### 3.4.6 — Shared Safety Foundations

Safety investigations and design consolidation completed through SF03.5.9.9.

Implementation not started.

---

# 4. Authority Baseline

## 4.1 Mandatory decisions

### M-1 — Canonical Root Authority & Containment

- Paths must have explicit base authority.
- Relative path resolution must not depend on hidden CWD assumptions.
- Path escapes must be rejected.
- Source and output roots must remain distinct.
- Canonical paths are the authority for containment.
- Prefix-based containment checks are prohibited.

### M-2 — Source Snapshot Integrity

- Source identity must reflect the actual bytes consumed.
- Actual byte size must be measured.
- SHA-256 must be calculated where required.
- Fingerprints must represent exact consumed content.
- Source mutation must be detected where integrity is required.
- Integrity failure must fail closed.

### M-3 — Run-Scoped Outputs

- Outputs must be scoped to a run.
- Collision policy must be explicit.
- Default immutable artifact behavior is fail-if-exists.
- Resume must be explicit.
- Overwrite must be explicitly authorized.
- Temporary files must be uniquely owned.
- Artifacts from different runs must not be mixed.

### M-4 — Registry Transaction Safety

- Registry updates require single-writer transaction semantics.
- Read-modify-write must be protected.
- Duplicate checking must occur within the protected transaction.
- Lost updates must be prevented.

### M-5 — Preflight Execution Gate

Preflight must validate:

- Configuration.
- Run identity.
- Path safety.
- Input readiness.
- Output readiness.
- Registry readiness.
- Execution capabilities.

Critical failures must block execution.

---

## 4.2 Approved design decisions

### D-02 — Failure propagation

Fatal integrity errors must propagate.

Recoverable failures may be structured and recorded according to policy.

### D-04 — Export gate

Export and artifact publication must follow transaction-like validation and commit semantics.

### D-09 — Consumer trust boundary

Consumers must independently validate preflight results and safety context.

A preflight result must not be treated as permanently valid authorization.

### D-10 through D-17

Schema/versioning, canonical serialization, deterministic representation, and strict validation requirements are preserved from the approved result-model contract.

### TOCTOU

Time-of-check/time-of-use residual risk is deferred.

Canonicalization and boundary revalidation mitigate risk but do not eliminate it universally.

---

# 5. Symlink, Junction & Reparse-Point Policy

Policy SYM-01 through SYM-10:

### SYM-01

Links resolving within an authorized root may be permitted.

### SYM-02

Links escaping authorized roots must be rejected.

### SYM-03

Dangling required links must be rejected.

### SYM-04

Nested links must be resolved and checked against the final target.

### SYM-05

Loops and unresolved link states must fail closed.

### SYM-06

Source links are permitted only within the authorized source root.

### SYM-07

Output links are permitted only within the authorized output/run root.

### SYM-08

Junctions and reparse points must not bypass containment.

### SYM-09

Critical resolution failures block or abort.

### SYM-10

TOCTOU residual risk must remain documented.

---

# 6. Output & Persistence Policy

## C-01 — Collision policy

Default:

FAIL-IF-EXISTS for immutable artifacts.

Resume and overwrite are explicit modes.

Collision checks must remain race-safe.

## C-02 — Persistence method

Use:

Temporary artifact → Validate → Commit

Atomic replacement is required where supported and appropriate.

Direct writes to final destinations should be replaced where feasible.

## C-03 — Resume policy

Resume is explicit.

Reuse is allowed only after verifying:

- Run identity.
- Artifact identity.
- Compatibility.
- Integrity.
- Ownership.

Partial or unknown state is not automatically reusable.

## C-04 — Cleanup policy

- Cleanup failure is secondary.
- Primary failure must be preserved.
- File fsync is required for critical persistence.
- Directory durability is platform-dependent.
- Stale temporary artifacts require safe reconciliation.

---

# 7. Preflight Result Model

## 7.1 Models

Immutable aggregate:

`PreflightResult`

Individual result:

`PreflightCheckResult`

## 7.2 Overall status

`PreflightStatus`:

- READY
- READY_WITH_WARNINGS
- BLOCKED

## 7.3 Check status

`CheckStatus`:

- PASS
- FAIL
- WARN
- SKIPPED
- UNKNOWN
- ERROR

## 7.4 Classification

`CheckClassification`:

- CRITICAL
- WARNING
- OPTIONAL
- DEFERRED

## 7.5 Check fields

- check_id
- category
- classification
- status
- message
- path
- details

## 7.6 Aggregate fields

- preflight_id
- run_id
- status
- can_run
- checks
- errors
- warnings
- optional_results
- deferred_risks
- checked_at
- config_fingerprint
- summary

## 7.7 Gate invariants

- All required critical checks must exist.
- Every critical check must PASS.
- Missing critical checks block.
- SKIPPED critical checks block.
- UNKNOWN critical checks block.
- ERROR critical checks block.
- Invalid or incomplete aggregate state fails closed.
- `can_run` is derived from status and check invariants.

`can_run=True` only for:

- READY
- READY_WITH_WARNINGS

## 7.8 Schema

- Schema name: `preflight_result`
- Version: `1.0.0`
- Strict enum validation.
- Canonical JSON representation.
- Reject NaN and Infinity.
- Strict deserialization.
- Explicit migrations.
- Reject unknown fields by default.

## 7.9 Consumer trust

Consumers validate:

- Schema/version.
- Required checks.
- Status aggregation.
- Run identity.
- Configuration fingerprint.
- Source identity.
- Output context.
- `can_run` invariants.

Preflight is context-bound.

No universal fixed TTL is imposed.

Changes to relevant context invalidate readiness.

---

# 8. Shared Safety Foundations

## 8.1 SF-01 — Error & Failure Classification

Status:

AUDIT COMPLETE — PASS WITH GAPS

Evidence examined:

- `variant_generation_runner.py`
- `variant_pipeline_orchestrator.py`

### Findings

- Catch-all exception handling may swallow fatal errors.
- Recoverable and fatal failures are not consistently distinguished.
- Continuation is not severity-aware.
- Generation and persistence success are not unified.
- Failure diagnostics are insufficient.

### Gaps

- G1: Fatal/recoverable classification missing.
- G2: Catch-all handling insufficiently controlled.
- G3: Continuation is not severity-aware.
- G4: Generation/persistence success not unified.
- G5: Diagnostics insufficient.

Shared FailurePolicy is required.

---

## 8.2 SF-02 — Path Canonicalization & Containment

Status:

AUDIT COMPLETE — PASS WITH GAPS

### Findings

- CWD-dependent configuration paths.
- `..` escape potential.
- Inconsistent canonicalization.
- Registry path ambiguity.
- Missing write-boundary revalidation.
- Symlink/Junction concerns.
- TOCTOU residual risk.

### Approved policy

Existing path authority is sufficient.

No additional major policy is required.

Implementation must centralize:

- Canonicalization.
- Containment.
- Root separation.
- Link handling.
- Write-boundary enforcement.
- Path failure classification.

---

## 8.3 SF-03 — File, Persistence, Collision & Registry Safety

### SF03.1 — File & Directory Safety Inventory

Closed.

### SF03.2 — Persistence Failure, Cleanup & Partial Artifact Audit

Audit complete.

Evidence:

#### `variant_generation_run_summary.py`

Observed:

- Parent directory creation.
- Fixed `.tmp` filename.
- Non-exclusive temp write.
- JSON serialization.
- Replacement.
- Cleanup.

Gaps:

- Temp collision.
- Race.
- Concurrent writes.
- Destination replacement.
- Cleanup masking.
- Crash orphan.
- No postcommit verification.
- No structured persistence result.
- No containment enforcement.

#### `variant_generation_report.py`

Observed:

- `NamedTemporaryFile`.
- Unique temp.
- Same-directory temp.
- Flush/fsync.
- `os.replace`.
- Cleanup.

Strengths:

- Unique temp.
- Flush/fsync.
- Temp-first.

Gaps:

- Uncontrolled replacement.
- Concurrent last-writer-wins.
- Cleanup masking.
- Crash orphan.
- No postcommit verification.
- No parent directory fsync.
- No structured errors.
- No containment.

#### `variant_registry.py`

Observed:

- Record validation.
- Source existence/hash.
- Header validation.
- Unique temporary file.
- Flush/fsync.
- Atomic replacement.

Gaps:

- Lost-update race.
- Duplicate registration race.
- Cleanup masking.
- Crash orphan.
- No verification.
- No directory fsync.
- Insufficient semantic validation.
- Source TOCTOU.
- No containment.

### SF03.3 — Overwrite & Collision Semantics

Audit complete.

#### `variant_writer.py`

Strengths:

- Canonical output root.
- Regex ID validation.
- Resolved containment.
- Exclusive `xb` create.

Gaps:

- Direct write can expose partial artifacts.
- No rollback.
- No fsync.
- No post-write verification.
- TOCTOU.
- Run ownership not established.

#### `batch_processor.py`

Gaps:

- Input path not resolved.
- Output may overwrite.
- Direct `write_text`.
- No atomic persistence.
- No containment.
- No root-overlap protection.
- Report overwrite/race.
- Report failure after processing is not structured.
- No fsync.
- No explicit resume/ownership.

#### `source_reader.py`

Strengths:

- `read_bytes`.
- Structured `SourceReadError`.
- Encoding fallback:
  - UTF-8 BOM.
  - UTF-8.
  - CP1252.
- BOM handling.
- Newline normalization.
- Actual raw byte size.
- Processed UTF-8 byte size.

Gaps:

- No SHA-256 snapshot.
- No mutation detection.
- No maximum file size.
- No canonicalization.
- No symlink policy.

### SF03.4 — Policy Reconciliation

Status:

CLOSED — PASS, EXISTING AUTHORITY SUFFICIENT

No new major policy required.

---

# 9. SF03.5 — Shared Safety Design

## 9.1 SF03.5.1 — Persistence Result & Failure State Contract

### State dimensions

`CommitState`:

- NOT_COMMITTED
- COMMITTED
- OUTCOME_UNKNOWN

`VerificationState`:

- NOT_REQUIRED
- NOT_RUN
- PASSED
- FAILED

`CleanupState`:

- NOT_NEEDED
- PENDING
- SUCCEEDED
- FAILED

`PersistenceStatus`:

- COMMITTED
- COMMITTED_WITH_WARNINGS
- REJECTED
- FAILED
- VERIFY_FAILED
- COMMIT_UNKNOWN

### Error model

`PersistenceErrorRecord`:

- error_type
- message
- phase
- severity

Errors:

- primary_error
- secondary_errors

### PersistenceResult

Immutable model:

- status
- destination
- temp_path
- commit_state
- verification_state
- cleanup_state
- bytes_written
- verified
- primary_error
- secondary_errors

### Status derivation

COMMITTED:

- Commit confirmed.
- Verification acceptable.
- Cleanup successful/not required.

COMMITTED_WITH_WARNINGS:

- Commit confirmed.
- Integrity acceptable.
- Cleanup failed or secondary warning exists.

VERIFY_FAILED:

- Commit confirmed.
- Verification failed.

REJECTED:

- Precommit policy rejection.

FAILED:

- Precommit failure.
- Confirmed not committed.

COMMIT_UNKNOWN:

- Outcome cannot be established.

### Invariants

- No contradictory state.
- Verification failure does not reverse commit.
- Cleanup failure does not overwrite primary failure.
- `bytes_written` represents temp bytes written, not necessarily committed bytes.

---

## 9.2 SF03.5.2 — PathSafety Contract

Proposed module:

`src/safety/path_safety.py`

### Responsibilities

- Canonicalize paths.
- Resolve relative paths using explicit base.
- Validate containment.
- Validate root separation.
- Validate write target.
- Enforce symlink/junction/reparse policy.

### Proposed API

```python
@dataclass(frozen=True)
class PathSafetyResult:
    path: Path
    root: Path
    relative_path: Path


class PathSafety:
    def canonicalize(
        path: Path,
        *,
        base_dir: Path | None = None,
    ) -> Path:
        ...

    def validate_containment(
        path: Path,
        root: Path,
    ) -> PathSafetyResult:
        ...

    def validate_distinct_roots(
        source_root: Path,
        output_root: Path,
    ) -> tuple[Path, Path]:
        ...

    def validate_write_target(
        path: Path,
        output_root: Path,
    ) -> PathSafetyResult:
        ...
```

### Exceptions

- PathSafetyError
- PathResolutionError
- PathContainmentError
- RootConfigurationError
- SymlinkPolicyError
- WriteTargetValidationError

### Requirements

- Component-aware containment.
- No string-prefix containment.
- Explicit base authority.
- Source/output root separation.
- Link policy enforcement.
- Writer-boundary revalidation.
- Fail-closed critical resolution.

---

## 9.3 SF03.5.3 — SafePersistence Contract

Proposed module:

`src/safety/safe_persistence.py`

### Responsibilities

- Temp lifecycle.
- Temp ownership.
- Writing.
- Flush.
- Critical fsync.
- Validation.
- Commit.
- Verification.
- Cleanup.
- PersistenceResult generation.

No generation logic.

### Proposed API

```python
class SafePersistence:
    def persist_bytes(
        *,
        destination: Path,
        payload: bytes,
        authorized_root: Path,
        collision_mode: CollisionMode,
        validator: ArtifactValidator | None = None,
        verification_required: bool = False,
    ) -> PersistenceResult:
        ...
```

### Collision modes

- `FAIL_IF_EXISTS` — default immutable artifact policy.
- `REPLACE_AUTHORIZED` — explicit replacement authorization.

Resume is a separate workflow.

### Invariants

- Temp file is unique and exclusively owned.
- Temp is created in an appropriate same-directory context.
- Final destination is never written directly for temp-first operations.
- Validate before commit.
- Collision race-safe.
- No-overwrite primitive must be verified.
- No fallback to overwrite when no-overwrite fails.
- Replace semantics must be verified.
- Commit unknown must be reconciled.
- Cleanup only operation-owned temp files.
- Unknown state preserves evidence.

### Deferred

- Streaming.
- Generic persistence framework.
- Automatic stale-temp recovery.
- Universal filesystem abstraction.
- Full rollback framework.

---

## 9.4 SF03.5.4 — RegistryTransaction Contract

Proposed module:

`src/safety/registry_transaction.py`

### Problem

Atomic file replacement does not prevent lost updates.

Two processes can read the same registry state and publish conflicting versions.

### Proposed locking strategy

Persistent adjacent lock file with OS-level exclusive lock on opened handle.

Requirements:

- Stable lock identity.
- Lock spans complete read-modify-write transaction.
- Do not delete lock file.
- File existence is not lock authority.
- PID-only locking rejected.
- Bounded timeout.
- No bypass.
- Crash releases OS handle lock.
- Network filesystem caveats documented.

### Transaction scope

`Lock → Read → Validate → Duplicate Check → Verify Source → Build → Temp Write → Validate Temp → Commit → Verify → Release`

### RegistryTransactionResult

Proposed:

- status
- variant_id
- registry_path
- records_before
- records_after
- committed
- verified
- primary_error
- secondary_errors

### Requirements

- Duplicate checking under lock.
- Source integrity verification.
- No lost update.
- Race-safe commit.
- Structured result.
- Process-level concurrency tests.

---

## 9.5 SF03.5.5 — FailurePolicy Contract

Proposed module:

`src/safety/failure_policy.py`

### Dimensions

Severity:

- INFO
- WARNING
- ERROR
- FATAL

Recoverability:

- RECOVERABLE
- NON_RECOVERABLE
- UNKNOWN

Propagation:

- LOCAL
- STAGE
- RUN

Disposition:

- CONTINUE
- SKIP_ITEM
- STOP_STAGE
- ABORT_RUN

Unknown failure must fail closed.

### Failure mapping

| Category | Policy |
|---|---|
| INPUT_INVALID | Recoverable, skip item |
| SOURCE_READ_ERROR | Context-specific |
| SOURCE_INTEGRITY | Fatal, abort |
| CONFIG_INVALID | Fatal |
| PATH_UNSAFE | Fatal |
| OUTPUT_COLLISION | Context-specific rejection |
| TRANSFORM_FAILED | Recoverable |
| WRITE_FAILED | Unknown until commit state established |
| REGISTRY_INVALID | Fatal |
| REGISTRY_DUPLICATE | Reject item |
| REGISTRY_LOCK_TIMEOUT | Abort transaction/run |
| REGISTRY_COMMIT_UNKNOWN | Fatal |
| REPORT_WRITE_FAILED | Unknown/finalization failure |
| PREFLIGHT_BLOCKED | Fatal |
| CLEANUP_FAILED | Secondary warning |
| VERIFICATION_FAILED | Fatal for required artifact |
| INTERNAL_ERROR | Fatal, unknown |

### Lifecycle

`PENDING → GENERATED → VALIDATED → PERSISTED → REGISTERED → COMPLETE`

Stages are distinct.

Generation success does not imply persistence success.

### Retry

- Bounded.
- Operation-specific.
- Explicit.
- No blind retry on commit unknown.

### Run states

- CREATED
- PREFLIGHT
- READY
- RUNNING
- COMPLETED
- COMPLETED_WITH_WARNINGS
- FAILED
- ABORTED
- FINALIZATION_FAILED

Execution and finalization are separate.

---

## 9.6 SF03.5.6 — Preflight Integration Contract

### Required checks

- PFC-01 Config
- PFC-02 Run Identity
- PFC-03 Path Safety
- PFC-04 Input Readiness
- PFC-05 Output Readiness
- PFC-06 Registry Readiness
- PFC-07 Execution Capabilities

### Preflight is read-only by default

Preflight does not:

- Generate variants.
- Write final artifacts.
- Register variants.
- Repair data.
- Overwrite outputs.
- Reserve permanent execution authority.

Optional write probe must be explicit and controlled.

### Order

Config → Run Identity → Path Safety → Root Separation → Capabilities → Input → Output → Registry → Aggregate → Result → Gate

Dependent checks may be skipped if prerequisites fail.

Skipped critical checks block.

### Gate

READY:

All critical checks pass without warnings.

READY_WITH_WARNINGS:

All critical checks pass with permitted warnings.

BLOCKED:

Any critical FAIL, ERROR, UNKNOWN, SKIPPED, or missing result.

### Freshness

Context-bound.

No fixed universal TTL.

Execution must revalidate relevant conditions.

---

## 9.7 SF03.5.7 — Integration & Dependencies

### Safety modules

```text
src/safety/
    __init__.py
    path_safety.py
    safe_persistence.py
    failure_policy.py
    registry_transaction.py
```

### Existing modules

```text
src/data/
    variant_registry.py
    variant_generation_report.py
    variant_generation_run_summary.py
    [existing preflight owner]

src/transformations/
    variant_writer.py
    variant_generator.py
    variant_generation_runner.py

src/preprocessing/
    batch_processor.py
    source_reader.py

[existing orchestrator]
```

### Dependency graph

PathSafety:

- Foundation.
- No persistence.
- No business logic.

SafePersistence:

- Depends on PathSafety.
- No generation logic.

RegistryTransaction:

- Depends on PathSafety and SafePersistence.
- Registry-specific transaction.

FailurePolicy:

- Classification and policy only.
- No orchestrator.
- No retry engine.

Preflight:

- Consumes shared safety services.
- Owns readiness aggregation only.

Orchestrator:

- Single run authority.
- Consumes Preflight and FailurePolicy.
- Owns stage/run lifecycle.

Artifact serialization remains owned by artifact modules.

### Deferred scope

- Generic transaction engine.
- Persistence plugins.
- Async.
- Distributed locks.
- Automatic stale temp cleanup.
- Automatic lock cleanup.
- Corruption repair.
- Universal retries.
- Multiple backends.
- Full rollback framework.

---

## 9.7 SF03.5.8 — Full Safety Design Review

Status:

REVIEW COMPLETE — DESIGN CONSOLIDATED

### Review decisions

R-01:

Persistence state derives from commit, verification, and cleanup truth.

R-02:

PathSafety is sole path policy authority.

R-03:

Preflight is context-bound, not permanent authorization.

R-04:

SafePersistence owns file transaction; RegistryTransaction owns logical registry transaction.

R-05:

FailurePolicy cannot alter persistence truth.

R-06:

Dependency graph reviewed; no major architectural conflict.

R-07:

Four shared services retained.

### Unresolved

U-01 through U-12 technical issues remain documented.

Architecture review did not substitute for filesystem prototypes.

---

# 10. SF03.5.9 — Technical Decision Resolution

Goal:

Resolve Windows-specific technical blockers before implementation claims rely on them.

---

## 10.1 SF03.5.9.1 — Technical Decision Prioritization

Priority:

1. U-01 — Atomic no-overwrite commit.
2. U-02 — Atomic replacement.
3. U-03 — Registry OS-level locking.
4. U-07 — Windows path canonicalization.
5. U-08 — Run identity & ownership.
6. U-10 — Run directory reservation.

Tier B:

- U-04
- U-05
- U-06
- U-11

Tier C:

- U-09
- U-12

---

## 10.2 SF03.5.9.2 — Atomic No-Overwrite Commit

Status:

INVESTIGATION COMPLETE — OPEN TECHNICAL DECISION

### Problem

Commit must not overwrite an existing destination.

An existence check followed by write is race-unsafe.

### Candidate strategies

A. Direct exclusive destination creation.

Advantages:

- Race-safe create-if-absent.

Limitations:

- Partial destination may be visible.
- Crash may leave incomplete artifact.

B. Temp + no-overwrite rename/move.

Advantages:

- Temp-first.

Limitations:

- Primitive semantics must be verified on Windows/filesystem.

C. Temp + hard-link create destination.

Candidate for atomic destination creation.

Limitations:

- Filesystem compatibility.
- Same-volume requirements.
- Hard-link semantics.
- SMB limitations.
- Temp cleanup.
- NTFS-specific assumptions must be verified.

### Proposed prototype

Temp-first + hard-link create.

Alternative:

Verified no-replace move/rename primitive.

### Acceptance

- Existing destination preserved.
- Exactly one winner in concurrent race.
- No partial final artifact.
- Temp ownership.
- Commit truth.
- Crash behavior.
- Filesystem compatibility.
- Unsupported capability fail closed.

---

## 10.3 SF03.5.9.3 — Atomic Replacement

Status:

INVESTIGATION COMPLETE — OPEN TECHNICAL DECISION

### Candidate primitives

- `ReplaceFileW`
- `MoveFileExW` with replacement flags.
- Python `os.replace` where appropriate.

### Contract

- Temp-first.
- Flush.
- Close.
- Validate.
- Commit.
- Verify.

### Important distinction

Atomic visibility, old-file preservation, and crash durability are separate guarantees.

Do not overclaim universal crash durability.

### Requirements

- Precommit failure must preserve old artifact.
- Commit failure requires investigation/reconciliation.
- Verification failure does not reverse commit.
- Backup policy must be explicit.
- Metadata/ACL policy must be explicit.
- Cross-volume copy/delete is not accepted as atomic publication.

---

## 10.4 SF03.5.9.4 — Registry OS-Level Locking

Status:

INVESTIGATION COMPLETE — OPEN TECHNICAL DECISION

### Proposed strategy

Persistent adjacent lock file + OS-level exclusive handle lock.

### Requirements

- Lock spans entire transaction.
- Stable canonical registry lock identity.
- No lock-file deletion.
- No PID-only lock.
- Bounded timeout.
- No bypass.
- Crash release.
- Network filesystem caveats.

### Tests

- Separate process writers.
- Two/ten writer stress.
- Duplicate race.
- Lost update.
- Process termination.
- Lock timeout.
- Failure injection.
- Windows behavior.

---

## 10.4 SF03.5.9.5 — Commit-Unknown Reconciliation

Status:

INVESTIGATION COMPLETE — OPEN TECHNICAL DECISION

### Problem

Commit may succeed while caller loses confirmation.

Blind retry may overwrite or duplicate.

### Evidence

- Destination identity.
- Expected artifact identity.
- Expected content fingerprint.
- Actual content fingerprint.
- Temp state.
- Old destination fingerprint.
- Backup state if used.
- Run identity.

### State decisions

Expected destination identity and hash verified:

COMMITTED.

Destination absent and protocol evidence proves no commit:

NOT_COMMITTED.

Mismatch, ambiguity, or unreadable state:

OUTCOME_UNKNOWN.

### Requirements

- Read-only reconciliation.
- Idempotent.
- No blind retry.
- No automatic rollback.
- No generation.
- No overwrite.
- Preserve evidence.

---

## 10.5 SF03.5.9.6 — Windows Path Canonicalization

Status:

INVESTIGATION COMPLETE — OPEN TECHNICAL DECISION

### Path layers

1. Raw path.
2. Absolute path.
3. Lexically normalized path.
4. Resolved filesystem path.
5. Filesystem object identity.

### Path forms

- Drive-absolute.
- Drive-relative.
- Rooted-no-drive.
- UNC.
- Extended-length path.
- Symlink/Junction.
- Hardlink aliases.

### Rules

- Explicit base authority.
- No hidden CWD.
- Reject ambiguous path forms by default.
- Component-aware containment.
- Do not lowercase paths as identity authority.
- `samefile` supplementary for object identity.
- Revalidate at writer/commit boundary.
- Source/output roots distinct and non-overlapping.
- Alias ambiguity may require rejection.

### Tests

PC01–PC36:

Lexical paths, drive forms, UNC, case behavior, aliases, links, containment, root overlap, write boundary, race, and resolution failures.

---

## 10.6 SF03.5.9.7 — Run Identity & Directory Ownership

Status:

INVESTIGATION COMPLETE — DESIGN NOT APPROVED

### Identity dimensions

Run identity:

Specific execution.

Config identity:

Canonical config fingerprint.

Artifact identity:

Specific output artifact and content.

### Proposed RunIdentity fields

- run_id
- created_at
- config_fingerprint
- source_snapshot_id
- pipeline_version
- schema_version
- validator_version
- generation_seed
- execution_mode
- identity_version

### Ownership manifest

Each run directory should have a versioned ownership manifest.

Manifest does not independently prove integrity.

### Fresh run

- Generate identity.
- Canonicalize root.
- Validate containment.
- Allocate directory atomically.
- Establish ownership.
- Verify.
- Begin execution.

### Resume

Must verify:

- Run identity.
- Manifest.
- Canonical directory.
- Config compatibility.
- Source identity.
- Version compatibility.
- Artifact integrity.
- Registry state.
- Ownership.

### Orphan/incomplete state

- Do not take over.
- Do not delete automatically.
- Do not overwrite.
- Do not repair silently.
- Reconcile separately.
- Preserve evidence.

### Concurrency

Exactly one winner in same-directory allocation race.

### Ownership limitation

Directory ownership does not imply artifact integrity.

---

## 10.7 SF03.5.9.8 — Implementation Contract Consolidation

Status:

CONSOLIDATION REVIEW COMPLETE

### Consolidated architecture

Four shared safety services retained.

### Conflict review

Resolved:

- Preflight PASS vs later path change.
- Directory ownership vs artifact integrity.
- Commit success vs verification failure.
- Cleanup failure vs primary failure.
- Atomic registry write vs concurrent transaction.
- Resume identity mismatch.
- Collision vs replacement authorization.
- Fatal error swallowed by runner.
- Commit unknown and blind retry.
- Path safety vs symlink escape.

### API contracts

Consolidated for:

- PathSafety.
- SafePersistence.
- FailurePolicy.
- RegistryTransaction.
- Run Identity & Ownership.

### Implementation order

A. PathSafety.

B. SafePersistence.

C. FailurePolicy.

D. RegistryTransaction and Run Ownership.

E. Preflight Integration.

F. Existing Pipeline Integration.

G. Tests & Acceptance.

### Review

No major architecture conflict discovered.

Technical primitives still require verification.

---

## 10.8 SF03.5.9.9 — Implementation Readiness & Approval

Status:

COMPLETED

Verdict:

READY WITH CONDITIONS

### Ready

- Architecture.
- Component boundaries.
- Shared safety contracts.
- Path policy.
- Persistence result model.
- Failure policy.
- Preflight integration.
- Registry transaction design.
- Run identity/ownership design.
- Implementation order.
- Acceptance gates.

### Conditions

- Windows filesystem prototypes.
- No-overwrite proof.
- Replacement proof.
- OS-level locking proof.
- Run reservation proof.
- Commit reconciliation validation.
- Concurrency evidence.
- Integration regression evidence.

### Approval boundary

This readiness assessment does not authorize implementation.

Implementation requires explicit user approval after reviewing the master contract.

---

# 11. Final Architecture

## 11.1 Safety services

### PathSafety

Responsibilities:

- Canonicalization.
- Containment.
- Root separation.
- Link policy.
- Write-target validation.

### SafePersistence

Responsibilities:

- Temp creation.
- Write/flush/fsync.
- Validation.
- Commit.
- Verification.
- Cleanup.
- Persistence result.

### FailurePolicy

Responsibilities:

- Classification.
- Recoverability.
- Propagation.
- Disposition.

### RegistryTransaction

Responsibilities:

- Registry locking.
- Read-modify-write transaction.
- Duplicate protection.
- Registry validation.
- Commit verification.

### Run Identity & Ownership

Responsibilities:

- Run identity.
- Directory reservation.
- Ownership establishment.
- Identity verification.
- Resume compatibility.

### Preflight

Responsibilities:

- Readiness checks.
- Safety aggregation.
- Execution gate.

### Orchestrator

Responsibilities:

- Single run authority.
- Stage lifecycle.
- Execution.
- Failure propagation.
- Finalization.

---

# 12. Implementation Roadmap

## Phase A — PathSafety

- Implement canonicalization.
- Explicit base authority.
- Containment.
- Root separation.
- Symlink/Junction/reparse policy.
- Write-boundary validation.
- Typed exceptions.
- Unit tests.
- Windows tests.

Exit gate:

Path safety acceptance tests pass.

---

## Phase B — SafePersistence

### B1

Prototype no-overwrite primitive.

### B2

Prototype replacement primitive.

### B3

Implement persistence state models.

### B4

Implement SafePersistence.

### B5

Implement commit reconciliation.

### B6

Failure injection tests.

Exit gate:

Commit semantics proven for supported target environment.

---

## Phase C — Transactional Ownership

### C1

Registry lock prototype.

### C2

RegistryTransaction.

### C3

Run ID generation.

### C4

Run directory reservation.

### C5

Ownership manifest.

### C6

Resume validation.

### C7

Concurrency tests.

Exit gate:

Process-level race tests pass; no lost update; no cross-run ownership.

---

## Phase D — Preflight Integration

- Config validation.
- Run identity.
- PathSafety.
- Input readiness.
- Output readiness.
- Registry readiness.
- Execution capabilities.
- Aggregate result.
- Gate.
- Context invalidation.

Exit gate:

Blocked preflight produces zero execution side effects.

---

## Phase E — Existing Pipeline Integration

### E1

VariantWriter.

### E2

Source integrity.

### E3

Generation runner.

### E4

Registry.

### E5

Generation report.

### E6

Run summary.

### E7

Orchestrator.

Exit gate:

All existing persistence and execution paths use the shared safety contracts where required.

---

## Phase F — Verification

- Unit tests.
- Integration tests.
- Process concurrency.
- Failure injection.
- Crash/interruption.
- E2E.
- Regression.
- Acceptance.

Exit gate:

All critical safety acceptance criteria pass.

---

# 13. Implementation Rules

## Rule 1 — Incremental implementation

Each component:

Design → Implement → Unit Tests → Review → Integrate → Acceptance

Do not implement the whole subsystem in one pass.

## Rule 2 — No silent contract changes

If a contract is infeasible:

1. Stop.
2. Record evidence.
3. Reopen decision.
4. Reconcile design.
5. Obtain approval where needed.
6. Continue.

## Rule 3 — No safety bypass

Prohibited:

- Disabling containment to make tests pass.
- Falling back to overwrite after no-overwrite failure.
- Bypassing registry lock.
- Continuing with unknown ownership.
- Blind retry on commit unknown.
- Swallowing fatal errors.
- Treating partial artifacts as complete.

## Rule 4 — Truthful status

Statuses must reflect actual operations.

Examples:

- COMMITTED only if commit is confirmed.
- COMMIT_UNKNOWN remains unknown until reconciliation.
- VERIFY_FAILED cannot be counted as successful verified artifact.
- READY cannot exist with failing critical checks.
- COMPLETED cannot be reported if required finalization failed.

## Rule 5 — Preserve evidence

Fail closed without destroying evidence.

- Preserve primary failure.
- Preserve commit-unknown state.
- Preserve unowned directories.
- Preserve unknown artifacts.
- Do not auto-delete artifacts of uncertain ownership.
- Cleanup failures are separately recorded.

## Rule 6 — Failure tests

Every safety component tests:

- Happy path.
- Policy rejection.
- OS failure.
- Race.
- Partial state.
- Crash.
- Verification failure.
- Cleanup failure.

---

# 14. Acceptance Criteria

## Gate 1 — Path Safety

- Canonical path authority.
- Explicit base.
- Component-aware containment.
- Root separation.
- Link policy.
- Write boundary enforcement.
- Race/error fail-closed.

## Gate 2 — Persistence Truth

- No-overwrite.
- Authorized replacement.
- Temp-first.
- Validation.
- Commit state.
- Verification.
- Cleanup state.
- Commit unknown reconciliation.

## Gate 3 — Concurrency

- Multi-process registry writers.
- Duplicate races.
- Run directory reservation.
- Exactly-one-winner semantics.
- No lost update.
- Crash lock release.

## Gate 4 — Run Ownership

- Fresh allocation.
- Resume verification.
- Identity mismatch rejection.
- Orphan preservation.
- Manifest integrity.
- Directory alias/move/copy validation.

## Gate 5 — Failure Propagation

- Recoverable vs fatal.
- Unknown fails closed.
- No swallowed integrity failures.
- Correct stage/run propagation.
- Generation and persistence separate.

## Gate 6 — Preflight

- Critical checks required.
- Missing critical checks block.
- Skipped critical checks block.
- Invalid aggregate blocks.
- Context changes invalidate readiness.
- BLOCKED produces zero execution side effects.

## Gate 7 — Artifact Integrity

- Schema validation.
- Content fingerprint.
- Partial artifact rejection.
- Resume compatibility.
- External modification detection.

## Gate 8 — Regression

- Existing behavior reviewed.
- No bypass paths.
- Output compatibility.
- Integration tests.
- E2E tests.
- Full regression.

---

# 15. Residual Risks

| Risk | Severity | Mitigation |
|---|---|---|
| TOCTOU | High | Boundary revalidation, explicit residual threat model |
| Unsupported filesystem primitive | High | Capability check, fail closed |
| Network filesystem semantics | High | Deferred, no unsupported guarantees |
| Registry lock aliasing | High | Canonical lock identity, reject ambiguity |
| Commit crash window | High | Reconciliation |
| Reservation crash window | High | Orphan state handling |
| External modification | High | Fingerprint and artifact verification |
| Stale temp files | Medium | Preserve/reconcile |
| Legacy safety bypass | High | Integration audit and tests |
| Schema drift | Medium | Strict versioning and migrations |

---

# 16. Deferred Scope

Not part of initial implementation unless explicitly reopened:

- Distributed locking.
- Network filesystem guarantees.
- Streaming persistence.
- Async persistence.
- Generic transaction engine.
- Multiple persistence backends.
- Automatic orphan cleanup.
- Automatic stale-temp deletion.
- Automatic corruption repair.
- Universal retry framework.
- Full rollback engine.
- Generic filesystem abstraction.

---

# 17. Approval Checklist

Before implementation:

- [ ] Review architecture.
- [ ] Review shared contracts.
- [ ] Review technical blockers.
- [ ] Review Windows prototype requirements.
- [ ] Review implementation roadmap.
- [ ] Review acceptance criteria.
- [ ] Review residual risks.
- [ ] Confirm implementation scope.
- [ ] Explicitly approve implementation.

---

# 18. Final Status

**Checkpoint:** SF03.5.9.9  
**Investigation:** COMPLETE  
**Consolidation:** COMPLETE  
**Architecture review:** COMPLETE  
**Readiness:** READY WITH CONDITIONS  
**Implementation:** NOT STARTED  
**Prototype validation:** NOT STARTED  
**User implementation approval:** PENDING

The safety architecture and contracts are consolidated and ready to serve as the implementation baseline.

Implementation must remain incremental, evidence-driven, and contract-preserving.

No safety requirement may be silently weakened to accommodate implementation convenience.

---

# 19. Next Action

After this master contract is saved and reviewed:

1. Confirm implementation scope and approval.
2. Begin Phase A — PathSafety.
3. Implement one contract at a time.
4. Run its acceptance tests.
5. Record evidence and checkpoint status.
6. Proceed only after the component passes.

**Safety Foundations implementation must not begin before explicit approval.**

End of document.
