# SafePersistence 1.9 — Security Pause & Resume Notes

**Project:** CodeSimilarityResearch  
**Workstream:** SafePersistence 1.9 / Phase B — Adversarial Testing & Remediation (B2.6.5)  
**Status:** SECURITY WORK PAUSED — prioritize completing runnable pipeline phases first  
**Pause checkpoint:** R1.26.5 — Registry concurrency remediation implemented and targeted regression tests reported PASS  
**Date paused:** 2026-11-24

---

## 1. Decision / Scope

Temporarily pause further security hardening so the project can proceed with the remaining pipeline phases and become runnable end-to-end.

Do **not** delete or revert security-related code, tests, or findings already completed. Keep this work as-is unless a later phase is blocked by a concrete bug or unsafe behavior that must be addressed to proceed.

This is a deliberate deferral, **not a security closure or sign-off**. SafePersistence remains partially hardened and must not be described as fully secure.

## 2. Current project roadmap status

### SafePersistence 1.9
- Phase B: SafePersistence development — in progress; B2.6.5 adversarial testing/remediation was the current focus.
- B2.6.6 audit closure — not completed.
- B2.7 cleanup & recovery — not completed.
- B2.8 durability/platform behavior — not completed.
- B2.9 SafePersistence closure — not completed.

### Later phases (not started)
- Phase C — RegistryTransaction
- Phase D — Preflight
- Phase E — FailurePolicy
- Phase F — Pipeline Integration
- Phase G — E2E Closure

**Next priority:** resume the roadmap at Phase C (RegistryTransaction), unless the current project roadmap/checkpoint notes specify a prerequisite or blocker that changes this order.

## 3. Security work completed / verified so far

Source under active work:
- `src/safety/persistence_temp.py`

Test file:
- `tests/safety/persistence/test_atomic_commit.py`

### R1 — Trusted transaction ownership / registry lifecycle (partial)
Implemented in the current source:
- Registry stores a `TempOwnershipRegistryRecord` rather than only ownership metadata.
- Registry authorization checks that the registered ownership is the exact genuine object (`registered.ownership is ownership`), not a clone.
- Lifecycle states exist: `ACTIVE`, `CONSUMED`, `REVOKED`.
- Successful commit transitions lifecycle to `CONSUMED`.
- Sequential replay after successful commit is rejected.

Reported test results:
- Forged ownership regression — PASS.
- Cloned genuine ownership regression — PASS.
- `FAIL_IF_EXISTS` successful commit regression — PASS.
- `REPLACE` successful commit regression — PASS.
- Replay after successful commit (`FAIL_IF_EXISTS`) — PASS.
- Replay after successful commit (`REPLACE`) — PASS.

### R1.26 — Concurrent replay vulnerability (reproduced and remediated, targeted coverage only)
- An adversarial test was added: `test_r1_concurrent_commit_same_ownership`.
- Before the lock remediation, the test reproduced the bug: **two concurrent calls both returned `COMMITTED` (2 successes instead of the expected 1)**.
- A registry lock was introduced: `_TEMP_OWNERSHIP_REGISTRY_LOCK = threading.Lock()`.
- `commit_owned_temp_file()` now uses `with _TEMP_OWNERSHIP_REGISTRY_LOCK:` to protect the registry authorization/lifecycle check, commit operation, and lifecycle transition.
- This avoids the manual `acquire()` / `release()` approach; lock release is guaranteed through the context manager even on early return/exception.

Reported checks after change:
- `python -m py_compile src/safety/persistence_temp.py` — PASS.
- Concurrent replay regression — PASS (user-reported).
- Regression subset: `commit_succeeds or registry_rejects_replay or concurrent_commit_same_ownership` — PASS (user-reported).

**Important:** these are targeted test reports, not a full-suite run, formal proof, or complete security audit.

## 4. Security findings / incomplete items — DO NOT FORGET

Security is paused with known open issues. Track these as unfinished, not resolved.

### High-priority resume items
1. **PreCommitGate authenticity and binding**
   - Existing gate is a `PreCommitGateResult` with `PASSED`/`DENIED` state and denial reason.
   - Adversarial tests previously exposed issues including forged/passed gates, stale gate reuse, gate reuse for a different temp ownership, caller-claimed sync/write completion, and passed state combined with denial reason.
   - Gate must eventually be cryptographically/structurally bound to the specific ownership, temp identity/content state, write completion, and sync evidence. A caller-constructible “passed” state is not a trustworthy authorization boundary.
   - Revisit tests before redesigning. Do not assume current gate is secure.

2. **TOCTOU / temp path substitution**
   - Adversarial coverage has exposed pathname substitution and path-based race concerns (including substitution after verification, symlink/hardlink scenarios, and temp content mutation).
   - Current verification followed by pathname-based `os.link()` / `os.replace()` may still have race exposure depending on platform/filesystem behavior.
   - Reassess commit design and platform-specific primitives when returning to security.

3. **`OUTCOME_UNKNOWN` lifecycle policy**
   - Current generic `OSError` handling conservatively returns `OUTCOME_UNKNOWN`.
   - The lifecycle may remain `ACTIVE` when an operation outcome is unknown, which could allow retry/replay of a transaction whose first mutation may have happened.
   - Define a safe policy for unknown outcome (e.g. quarantine/revoke/consume state, reconciliation, or explicit recovery design) before enabling retries/recovery.

4. **Registry lifecycle, cleanup, and resource handling**
   - Registry is currently in-memory and unbounded; cleanup/revocation semantics are incomplete.
   - `REVOKED` lifecycle exists but behavior/API has not been fully wired/audited.
   - Review temp FD closure, temp-file cleanup, registry record cleanup, stale entries, and crash/restart behavior.

5. **Atomic commit platform behavior and durability**
   - Audit `FAIL_IF_EXISTS` (`os.link`) and `REPLACE` (`os.replace`) semantics on supported Windows/filesystems.
   - Clarify atomicity vs durability guarantees; test failure cases and destination-parent disappearance/races.
   - Review whether directory sync/durability behavior is required and feasible on supported platforms.

6. **Concurrency scope**
   - Current registry lock is global and protects the tested commit critical section. It may serialize unrelated commits.
   - Confirm lock protects all relevant registry mutations (registration, lifecycle transitions, revocation/cleanup) and check lock ordering/deadlock potential once cleanup/recovery APIs exist.
   - Do not optimize to per-transaction locks until correctness is demonstrated and tests cover it.

## 5. Historical adversarial test context

The AT-01 through AT-44 adversarial series identified or characterized risks such as:
- forged ownership and cloned ownership;
- replay and second-destination replay;
- stale/forged gates and cross-ownership gate reuse;
- claimed-but-not-actual write/sync evidence;
- temp-content mutation after sync/gate;
- path substitution / TOCTOU;
- symlink and hardlink substitution;
- atomic commit boundary races and ambiguous outcomes.

Not every adversarial test PASS meant the system was secure: some tests were characterization tests demonstrating that a vulnerability existed or behavior was unsafe. When resuming, inspect the test assertion and result meaning before interpreting a historical PASS as remediation.

## 6. Resume sequence — suggested security order

When pipeline phases are complete and security work resumes:

1. Re-open this note and the current `persistence_temp.py` / `test_atomic_commit.py`.
2. Run targeted existing security tests and the relevant test subset to establish a fresh baseline.
3. Revisit **PreCommitGate authenticity/binding** and redesign the trust boundary test-first.
4. Revisit **TOCTOU/path substitution** and define safe platform primitives or redesign limitations.
5. Define **`OUTCOME_UNKNOWN` lifecycle/recovery policy**; prevent blind retry.
6. Audit registry lifecycle, revoke, cleanup, FD/temp resource lifecycle.
7. Add/finish atomicity, durability, and Windows/platform behavior coverage.
8. Finish B2.6.6 audit closure, B2.7 cleanup & recovery, B2.8 durability/platform behavior, and B2.9 SafePersistence closure.
9. Run full regression and adversarial suites; document any residual limitations.
10. Only then mark security hardening complete.

## 7. Instructions for future ChatGPT continuation

- The user prefers **one step at a time**: give one command/edit/test per response, wait for `ok` or test output before advancing.
- Do not bundle multiple edits/tests into one instruction.
- Do not claim tests were run by the assistant; the user executes tests locally and reports output.
- Preserve the user's Windows PowerShell workflow and repository paths.
- Do not redo completed checkpoints unless a new failure or audit requires it.
- Keep security tasks paused while the user advances pipeline phases, unless a concrete issue blocks progress or the user explicitly asks to resume security.
- Treat this note as a handoff snapshot. Re-read the source and test files before making future security changes; code may have changed since this note was written.
- No security closure claim is justified by this snapshot.

## 8. Current immediate next step

**Return to Phase C — RegistryTransaction** and continue the main pipeline roadmap, using the project's existing checkpoint/timeline notes as the source of truth for the exact next task.

---

*This file records deferred security work and a continuation plan. It is not a vulnerability-free declaration or a substitute for a future audit.*
