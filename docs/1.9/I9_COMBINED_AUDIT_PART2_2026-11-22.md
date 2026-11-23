# CodeSimilarityResearch — Checkpoint Ledger

**Project:** `D:\University\NCKH\fullstack\CodeSimilarityResearch`  
**Checkpoint date:** 2026-11-21  
**Current phase:** Phase I — Dataset pipeline, I.9 Pipeline orchestration & E2E  
**Working mode:** audit/design checkpoints first; no code changes unless explicitly approved.

---

## 1. Working agreement

- Work one checkpoint at a time and wait for user approval before moving forward.
- Vietnamese, concise, friendly explanations; provide exact PowerShell commands when needed.
- User edits the local repo; assistant must not claim to have changed it.
- During audit checkpoints, inspect only: no implementation changes.
- Distinguish evidence-confirmed implementation, gaps, proposals, and not-verified areas.
- Do not use web unless explicitly requested or needed; project work is repo-local.
- At milestone closure, provide a checkpoint document for handoff.


## 2. Phase I progress

| Milestone | Status |
|---|---|
| I.1 Config foundation | Done |
| I.2 Source split & duplicate grouping | Done |
| I.3 Variant generation & validation | Done |
| I.4 Positive pair generation | Done |
| I.5 Negative pair generation & screening | Done |
| I.6 Pair assembly & candidate validation | Done |
| I.7 Pair selection & balancing | Done |
| I.8 Final validation & export | Done |
| I.9 Pipeline orchestration & E2E | In progress — audit/design |

### I.8 verified tests
- I.8 module tests: **36 passed**
- Full repo tests: **542 passed in 34.86s**
- I.8 officially closed.

## 3. I.9 agreed timeline
1. I.9.1 Pipeline architecture audit — closed PASS WITH GAPS
2. I.9.2 Pipeline config & execution contract
   - I.9.2.1 Config schema & authority audit — closed PASS WITH GAPS
   - I.9.2.2 Pipeline input contract — closed PASS WITH GAPS
   - I.9.2.3 Execution order & stage contract — closed PASS WITH GAPS
   - I.9.2.4 Runtime Policy — closed PASS WITH GAPS
   - I.9.2.5 Output & execution contract — audit/design in progress
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

## 4. Design baseline previously agreed
- Source-level stratified split target 80/10/10 with fixed seed; split originals before variants/pairs; variants inherit source split; pair endpoints same split.
- Duplicate groups atomic for split integrity; exact duplicates retained as source records, not automatically positive pairs. Near duplicates not automatically grouped.
- Variants: target 2 accepted/original, max 2, up to 5 attempts; originals only; no chaining; reject duplicates/validation failures; partial generation allowed; no bypass.
- Transform baseline roughly 1/3 whitespace/formatting, 1/3 comments, 1/3 structural; prefer diverse transformations; uniform eligible selection without replacement; no adaptive probability.
- Validation baseline V1 structural, V2 transformation, V3 syntax; V4 semantic evidence optional; accepted variants require V1–V3.
- C++ validation uses Tree-sitter C++ and Clang syntax-only GNU C++17; parser timeout 3s, compiler timeout 10s; never execute source. Tool/env failures separate from syntax failures.
- Negative screening token Jaccard threshold 0.85; score >= threshold reject, below threshold only passes screening (not proof negative); fail closed on tokenizer errors. C++ aware tokenization strips comments, ignores formatting, preserves identifiers/literals/operators; record provenance, metric, score, threshold, status, version/errors.
- Flexible pair quotas: keep valid candidates, no oversampling, no bypass screening/validation, no cross-split compensation; balance each split independently using min available class count. Shortages reported; split lacking label is quality failure.
- Priority: integrity > label validity > leakage > diversity > problem distribution > balance > quantity.
- Pilot/calibration before full generation.

## 5. I.9.1 — Pipeline architecture audit (closed PASS WITH GAPS)
Evidence-backed architecture components exist for duplicate detection, split, variants/validation, positive/negative pairs, assembly, selection, final validation, registry, reports/writers.
- Variant orchestrator/CLI are variant-only.
- Full dataset pipeline orchestrator/root CLI not evidenced in inspected files.
- Full E2E orchestration evidence not found at audit time.
- No code edits during audit.

## 6. I.9.2.1 — Config schema & authority audit (closed PASS WITH GAPS)
Audited `src/data/pair_generation_config.py`:
- Resolves config path, reads JSON, requires object root/sections, dataset name, seed int rejecting bool, split ratios, enabled transforms/probabilities, variant target/max/attempts/no chaining, negative config, screening threshold/metric/fail-closed, selection oversampling/cross-split/count policy/ratio, validation fail-closed/timeouts.
- Partial validation: section/type, unknown keys, dataset paths/language, split strategy/group flags, duplicate policies, partial quota/status, transform names, screening tokenization, selection, tool config/output path not fully validated.
- `raw` mutable; no immutable snapshot/fingerprint/version freeze.
- Relative paths assume config in `config/` under project root.
- Proposed authority: one validated config/run, validate before stages, pass config into stages, no independent reload, freeze and record snapshot/seed/versions/fingerprint; CLI overrides before validation/snapshot.
- Gaps G1–G6: section types; unknown keys; complete schema; mutability; snapshot/fingerprint/version; path root resolution.

## 7. I.9.2.2 — Pipeline input contract (closed PASS WITH GAPS)
Audited `variant_source_loader.py`, `metadata_generator.py`, `duplicate_detector.py`, `source_splitter.py`.
- Loader validates CSV/read failures, required columns, unique sample IDs, successful metadata filtering, metadata/split coverage, valid split values, path containment, source existence/read, sorted samples.
- Loader gaps: empty fields, language, metadata-vs-source file-size mismatch, empty source policy, failed-status behavior, path convention consistency.
- Metadata generator: sorted recursive TXT discovery, relative processed-file matching, status success/failed, file-size metadata. Gaps: ID collision (problem+stem), duplicate IDs not checked, empty file/content/encoding, debug print, processed dir validation, path convention inconsistency, language hardcoded cpp.
- Duplicate detector: SHA256 streaming 1MB, path containment, file existence, deterministic hash groups/member IDs. Gaps: input schema/duplicate IDs/malformed rows/empty-file policy; failures raise.
- Source splitter: rejects empty samples, validates split names/positive ratios/sum, duplicate sample IDs, duplicate groups atomic, unknown group members/multiple memberships rejected, singleton retained, seeded tie-break, global/per-problem ratio cost optimization, assignment coverage, actual ratio/count/target reporting. Gaps: sample/group schema, ratio type/finite validation (bool/NaN/Inf), seed, duplicate group IDs/empty IDs/empty members/single member, split quality not guaranteed.
- Contract decisions: stable IDs and valid metadata; metadata/splits coverage consistent; paths inside root; duplicate groups atomic; each sample exactly one split; targets and actual split counts reported; validate before generation.
- Input gap IDs: G-IN-01 metadata field validation; G-IN-02 sample ID collision; G-IN-03 file size mismatch; G-IN-04 empty source policy; G-IN-05 path convention; G-IN-06 language/config contract; G-IN-07 duplicate detector input schema; G-IN-08 failed sample policy.

## 8. I.9.2.3 — Execution order & stage contract (closed PASS WITH GAPS)
Proposed pipeline order:
0 Preflight/config → 1 Input load/validation → 2 Duplicate detection → 3 Source split → 4 Variant generation → 5 Positive pair generation → 6 Negative pair generation → 7 Pair assembly/candidate validation → 8 Pair selection/balancing → 9 Final dataset validation → 10 Export/artifacts.
Dependencies: split before variants/pairs; variants inherit split; positive/negative pools feed assembly; final validation gates final export.
- Fatal proposed: config/input integrity, split integrity/leakage, critical candidate integrity, final validation failure.
- Recoverable proposed: per-sample variant errors and persistence errors only when policy permits.
- Quality warnings: shortages, minor balance/diversity issues.
- Never bypass screening/split/validation/quota to force quantity.
- Variant batch COMPLETED is not full pipeline SUCCESS.
- Audited `variant_pipeline_orchestrator.py`: per-sample generator, report aggregation, accepted variants persistence, output-file existence, SHA256 registry provenance (source refs/problem/split/index/transformation/seed/validator version/status/hash/time); persistence error captured in `VariantPersistenceResult`; possible orphan file if registry registration fails. Not full pipeline.
- Audited `variant_generation_runner.py`: sequential samples, deterministic sample seed SHA256(master seed + sample_id), isolates sample exceptions, batch status COMPLETED/PARTIAL/FAILED. G-EXEC-01 bool seed accepted; G-EXEC-02 sample success may mask persistence failure; G-EXEC-03 persistence errors absent from batch errors; G-EXEC-04 no stage statuses; G-EXEC-05 no run ID/fingerprint/trace/recovery.
- Audited `variant_generation_run_summary.py`: dataset/split/master seed/status, sample/variant counters, success rate, errors, timestamps, JSON export temp+replace. G-EXEC-06 variant-only summary; G-EXEC-07 missing reproducibility metadata (config/input/tool/pipeline fingerprints/version); G-EXEC-08 status ignores persistence failure; G-EXEC-09 stage timings absent.
- No code changes.

## 9. I.9.2.4 — Runtime Policy (closed PASS WITH GAPS)
User approved baseline R1–R6:
- R1 Determinism: fixed master seed; sample seed derived deterministically from master seed + sample ID; no implicit random seeds; record actual seed/config.
- R2 Timeout: task-specific timeouts; parser/compiler timeout distinct from syntax errors; clean subprocess; no infinite retry.
- R3 Resources: cap concurrency; time/file/external-tool resources; sequential baseline first; no concurrency to compensate for shortage.
- R4 Error isolation: isolate sample-local errors only if integrity unaffected; integrity/leakage/label/source-pair errors fatal; do not swallow errors.
- R5 Retry: no retry deterministic failures (validation/syntax/duplicate); limited retry only transient infrastructure failures; record retries; don't alter policy/seed.
- R6 Fail-safe: fatal stops; recoverable isolated and recorded; quality warning remains warning; final validation non-PASS blocks valid final export.

Runtime evidence from inspected files:
- `VariantGenerationRunner.__init__` checks `isinstance(master_seed, int)` so bool accepted (G-EXEC-01).
- `derive_sample_seed` uses SHA256 of `f"{master_seed}:{sample_id}"`, first 4 bytes unsigned; sequential loop.
- Runner catches exceptions per sample and records `SampleRunError`; then continues.
- Runner increments sample success on any returned result, even when result contains failed persistence items. Thus persistence errors may be hidden from batch status/errors (G-EXEC-02/03/08; also G-RT-03).
- Orchestrator persistence catches exception per variant and returns persistence result with error; it doesn't raise that failure to runner.
- No retries visible in these files.
- Run summary reports variant-only counters, status, errors, start/end timestamps; no full pipeline stage status, run ID, fingerprints, timing per stage.
- G-EXEC-01..09: 01 bool seed accepted; 02 sample success can mask persistence; 03 persistence errors not batch errors; 04 no stage-level statuses; 05 no run ID/recovery/trace; 06 variant-only report; 07 missing config/input/tool/pipeline fingerprints; 08 status doesn't reflect persistence failures; 09 stage timing absent.
- Runtime gaps: G-RT-01 full runtime timeout policy not verified; G-RT-02 resource budgets not established/verified; G-RT-03 persistence failure propagation; G-RT-04 cancellation policy not verified; G-RT-05 retry policy not yet implemented/verified across runtime; G-RT-06 fatal propagation/export gate not verified full pipeline.
- I.9.2.4 closure: **PASS WITH GAPS**. No code edits.

## 10. I.9.2.5 — Output & Execution Contract (in progress)
User approved audit-only start. O-01 through O-10 are baseline principles:
- O-01 Output authority: identify authoritative final dataset; avoid multiple competing “final” files.
- O-02 Run isolation: run outputs separate or managed to avoid overwriting previous runs.
- O-03 Atomic finalization: final dataset must not be half-written yet appear valid.
- O-04 Artifact consistency: report/manifest/counts/registry/validation must agree.
- O-05 Traceability: artifact trace to run/config/seed/source.
- O-06 Failure artifacts: preserve diagnostic reports on failure but never imply failed run produced valid final data.
- O-07 Export gate: only final validation PASS can promote/export final dataset.
- O-08 Naming/versioning: file/folder/run/version names unambiguous.
- O-09 Partial output: intermediate/partial/final clearly distinguished.
- O-10 Reproducibility: enough metadata to rerun/compare.

### Audit evidence — first output/provenance group
Files read:
- `src/data/variant_output_writer.py`
- `src/data/variant_registry.py`
- `src/data/variant_generation_report.py`
- `src/data/variant_generation_run_summary.py`

Findings:
- VariantOutputWriter: safe ID regex; variant ID must match original sample; containment check; normalize CRLF/CR to LF; exclusive `xb` creation prevents overwrites; writes UTF-8 bytes directly (no temp/atomic file write).
- VariantRegistry: CSV schema columns; record validation; split/index/seed/source hash checks; checks file exists and recomputes SHA256; rejects duplicate variant IDs; writes registry via temp file, flush+fsync, `os.replace` (atomic replacement on same filesystem).
- VariantGenerationReport: detailed per-original counts/status/attempts/rejection reasons/transformation stats/split distribution; JSON export temp file, flush+fsync, `os.replace`.
- VariantGenerationRunSummary: dataset/split/master seed/status/counts/success-rate/errors/timestamps; JSON export via `.tmp` and replace, but no explicit fsync in shown implementation.
- Confirmed partials: artifact-specific atomic report/registry; variant source direct-write; variant provenance/checksum; variant-only report/summary.
- Not evidenced in this group: run-level output directory isolation, final dataset writer, final manifest, artifact inventory/manifest, full pipeline export gate, cross-artifact consistency, run/config/input fingerprints.

### Audit evidence — second final-dataset group
Files read:
- `src/data/final_dataset_validator.py`
- `src/data/final_dataset_validation_models.py`
- `src/data/final_dataset_validation_config.py`
- `src/data/pair_models.py`
- `src/data/pair_selection_models.py`

Findings:
- `FinalDatasetValidator` validates in-memory iterable of PairRecord: non-empty (configurable), duplicate pair IDs, duplicate sample-pair keys, both labels, split leakage, selection result integrity and count/status mismatch. Produces report status PASS/WARNING/FAIL, counts, issues.
- Validation report/model/config are typed and frozen report/config; config checks booleans strictly.
- `PairRecord` validates field strings, exact int label 0/1, PairType/PairSplit enums, positive semantics (same source lineage, label 1), negative semantics (label 0, different problem and source lineage), no self-pairs, canonical sample ordering. `created_seed` type checked but bool technically accepted? `type(created_seed) is int` means bool rejected.
- `PairSelectionResult` validates tuple, non-negative counts, count consistency, status type. It does not in this model verify selected item PairRecord types; validator does if selection integrity enabled.
- `PairSelectionReport` carries selector version/seed/split counts/shortages; status WARNING if unmet quotas else PASS.
- Important scope: validator validates pairs in memory; no final dataset file exporter, manifest, checksums, artifact inventory or atomic final dataset promotion was shown in these modules.
- Observed implementation quirk: validator contains duplicate imports of `Counter` and `PairRecord`; does not affect output-contract audit but cleanup note only, not a contract gap.

### Current O-contract status (provisional until export search)
- O-01 Output authority: Not verified (no final dataset exporter identified yet).
- O-02 Run isolation: Partial for variant naming/path; run-level isolation not evidenced.
- O-03 Atomic finalization: Partial (registry/report atomic replace; variant file direct write; final dataset atomic export not verified).
- O-04 Artifact consistency: Partial (registry hash validates individual variant file; final dataset/report/manifest consistency not shown).
- O-05 Traceability: Partial (variant provenance present; final dataset-to-run trace not verified).
- O-06 Failure artifacts: Partial (variant reports/errors exist; full pipeline failure artifact not verified).
- O-07 Export gate: Not verified (validator exists, but no export/promote path shown).
- O-08 Naming/versioning: Partial (variant IDs, registry columns, report version 1.0; run-level naming/versioning not verified).
- O-09 Partial output: Partial (variant generation statuses exist; final partial/intermediate/final artifact contract not verified).
- O-10 Reproducibility: Partial for variant seed/provenance; full config/input/tool/pipeline fingerprints and final dataset reproducibility not verified.

**I.9.2.5 remains open.** Need inspect repository-wide output/export references with full path/line evidence, and if needed CLI/config paths. Do not close checkpoint until evidence review completes.

## 11. Gap backlog (cumulative)
- Config: G1–G6.
- Inputs: G-IN-01–08.
- Execution: G-EXEC-01–09.
- Runtime policy: G-RT-01–06.
- Output/execution contract: O-01–O-10 statuses provisional pending export-path audit.

## 12. Immediate next action
Continue I.9.2.5 audit-only. Search repository for final dataset writer/export path and output configuration, with PowerShell commands that preserve full path and line text, e.g.:
```powershell
Get-ChildItem src -Recurse -File | Select-String -Pattern "to_csv|csv\.writer|write_text|write_bytes|json\.dump|export|output_path|final_dataset|manifest|os\.replace|\.replace\(" | Format-List Path,LineNumber,Line
```
If output is too large, narrow to `src/data` and the CLI/config files. Then finalize O-01–O-10 evidence and decide checkpoint status.


---

# CodeSimilarityResearch — Phase I Checkpoint Ledger

**Last updated:** 2026-11-21  
**Project:** `D:\University\NCKH\fullstack\CodeSimilarityResearch`  
**Phase:** I — Data Pipeline  
**Working mode:** audit/design first; no implementation until the relevant design checkpoint is closed and explicitly approved.

## Working agreement
- Work one checkpoint at a time; do not advance without the user's confirmation.
- Give concise Vietnamese explanations and exact PowerShell commands when inspection is needed.
- User edits code manually; assistant does not claim to have edited local repository files.
- During audit/design checkpoints, do not request code changes.
- Distinguish confirmed implementation facts from design proposals and gaps.
- Wait for user test output before proceeding after implementation steps.

## Phase I progress
| Stage | Status |
|---|---|
| I.1 Config foundation | Done |
| I.2 Source split & duplicate grouping | Done |
| I.3 Variant generation & validation | Done |
| I.4 Positive pair generation | Done |
| I.5 Negative pair generation & screening | Done |
| I.6 Pair assembly & candidate validation | Done |
| I.7 Pair selection & balancing | Done |
| I.8 Final validation & export | Done |
| I.9 Pipeline orchestration & E2E | In progress; audit/design underway |

## Verified test checkpoint
- I.8 module tests: **36 passed**.
- Whole repository: **542 passed in 34.86s**.
- I.8 is closed.

## I.9 agreed timeline
1. I.9.1 Pipeline architecture audit — **closed: PASS WITH GAPS**
2. I.9.2 Pipeline config & execution contract — in progress
   - I.9.2.1 Config schema & authority audit — **closed: PASS WITH GAPS**
   - I.9.2.2 Pipeline input contract — **closed: PASS WITH GAPS**
   - I.9.2.3 Execution order & stage contract — **audit complete, awaiting user approval to close**
   - I.9.2.4 Runtime policy — next after I.9.2.3 approval
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

## Design baseline (confirmed earlier)
- Source-level stratified split target 80/10/10, fixed seed; split originals before variants/pairs; variants inherit split; pair endpoints must be in the same split.
- Duplicate groups are indivisible for split integrity; exact duplicates retained as source records, not automatically positive pairs. Near duplicates are not automatically grouped.
- Variants: target 2 accepted per original, maximum 2; up to 5 attempts; original-only input, no chaining; reject duplicates and failed validation; partial generation allowed; no bypass.
- Transformation baseline: whitespace/formatting/comments roughly one-third each; prefer distinct type; uniformly sample eligible transformations without replacement; no adaptive probabilities.
- Validation baseline: V1 structural, V2 transformation, V3 syntax; optional V4 semantic evidence. Accepted variants require V1–V3.
- C++ validation baseline: Tree-sitter C++ and Clang syntax-only GNU C++17; parser timeout 3s, compiler timeout 10s; no execution. Tool/environment failures distinct from syntax failures.
- Negative screening: token Jaccard threshold 0.85; score >= threshold rejected; score below threshold passes screening only (not proof of negative). Fail closed on tokenizer errors. C++-aware tokenization strips comments and ignores formatting while retaining identifiers/literals/operators. Report sample/pair provenance, metric, score, threshold, status, implementation version/errors.
- Pair quotas flexible: keep valid candidates, no oversampling, no screening/validation bypass, no cross-split compensation; balance independently per split using minimum available label count. Shortages are reported; split lacking a label is a quality failure.
- Priority: integrity > label validity > leakage > diversity > problem distribution > balance > quantity.
- Full generation requires a pilot/calibration before scale-up.

## I.9.1 Architecture audit — closed, PASS WITH GAPS
Observed repository architecture (user-provided tree):
- Components exist for duplicate detection, source split, variant generation/validation, positive/negative generation, assembly, selection, final validation, registry, reporting and writers.
- Variant-specific orchestrator and CLI exist; no evidence of full dataset pipeline entry point/orchestrator in inspected tree.
- `variant_pipeline_orchestrator.py` is limited to generating variants, reporting, writing and registry persistence.
- `variant_generation_runner.py` runs variants over samples; not full-pipeline orchestration.
- Full E2E orchestration evidence was not found in architecture audit.
- No code changes during audit.

## I.9.2.1 Config schema & authority audit — closed, PASS WITH GAPS
Audited `src/data/pair_generation_config.py` (user-supplied source):
- Resolves config path, reads JSON, requires object root, checks required sections, validates dataset name, integer seed (bool rejected), split ratios, enabled transforms/probabilities, variant limits/attempts/no chaining, negative generation policy, screening threshold/metric/fail-closed, selection oversampling/cross-split/count policy/ratio, validator fail-closed/timeouts.
- Partial coverage: sections/types, unknown keys, dataset paths/language, split strategy/group flags, duplicate policy, partial quota/status, transform names, screening tokenization settings, selection settings, tool config, output paths not all validated.
- `raw` exposes mutable config; no immutable snapshot/fingerprint/version freeze.
- Relative path resolution assumes config location under project `config/`.
- Proposed authority contract: one validated authoritative config per run; validate before stages; orchestrator passes config to stages; no stage independently reloads it; freeze config for run; record snapshot, seed, versions, fingerprint; CLI overrides merge before validation/snapshot.
- Gaps backlog: G1 section type; G2 unknown keys; G3 full validation; G4 mutability; G5 snapshot/fingerprint/version; G6 path-root contract.

## I.9.2.2 Pipeline Input Contract — closed, PASS WITH GAPS
Files inspected:
- `src/data/variant_source_loader.py`
- `src/data/metadata_generator.py`
- `src/data/duplicate_detector.py`
- `src/data/source_splitter.py`

Findings:
- Loader: CSV reading, required-column check, unique sample IDs, successful-record filtering, metadata/split join coverage, valid split names, source-root containment, source existence/read, sort order are implemented.
- Metadata generator: deterministic recursive TXT discovery, processed-path matching, status, size and CSV writing are implemented; sample ID collisions not checked; debug prints; language hardcoded `cpp`; path conventions require harmonization; processed dir validation and source content validation incomplete.
- Duplicate detector: streaming SHA-256, source containment/existence, deterministic grouping by hash and sorted IDs; input schema/duplicate sample IDs/empty-file policy not fully validated.
- Source splitter: rejects empty input, checks split names/positive ratios/sum, unique sample IDs; builds duplicate groups plus singleton groups; rejects unknown group members and samples in multiple groups; seeded shuffle/tie-breaking and global/per-problem target deviation; report actual ratios/counts/targets.
- Split ratios are targets, not strict guarantees; group integrity may cause deviation.
- Input contract decisions: stable sample identity and valid metadata; metadata/splits coverage consistency; paths remain under source root; duplicate groups atomic; each sample assigned exactly one split; actual ratios reported; input validation must precede generation.
- Gap backlog: G-IN-01 metadata fields; G-IN-02 sample ID collisions; G-IN-03 metadata file size vs actual; G-IN-04 empty source policy; G-IN-05 path conventions; G-IN-06 language/config contract; G-IN-07 duplicate detector input schema; G-IN-08 failed sample policy.
- No code changes.

## I.9.2.3 Execution Order & Stage Contract — audit complete; awaiting closure confirmation
Proposed full pipeline order:
0. Preflight & config
1. Input loading & validation
2. Duplicate detection
3. Source split
4. Variant generation
5. Positive pair generation
6. Negative pair generation
7. Pair assembly & candidate validation
8. Pair selection & balancing
9. Final dataset validation
10. Export & artifacts
Dependencies: split before variants/pairs; variants inherit source split; positive and negative pools feed assembly; final validation must gate final export.

Proposed failure semantics (design, not yet verified implementation):
- Fatal: config/input integrity; split integrity/leakage; critical candidate integrity; final validation failure.
- Recoverable: per-sample variant failures and persistence failures only where policy permits.
- Quality warning: shortages, minor balance/diversity issues.
- Never bypass screening, split integrity, validation, or quota policy to force quantity.
- Batch COMPLETED must not automatically mean final dataset SUCCESS.

### Audited modules
`src/data/variant_pipeline_orchestrator.py`
- Per-sample variant generator invocation; report records generation result; only accepted variants persisted; writer file checked; SHA-256 computed; registry record includes source/original references, problem, split, index, transformation, seed, validator version, hash, UTC timestamp.
- Persistence exceptions captured into `VariantPersistenceResult`; may leave orphaned written file if registration fails.
- Not full pipeline orchestrator; no source splitting, positive/negative generation, assembly, selection, final validation or export.
- No explicit split validation or seed type validation in this module.

`src/data/variant_generation_runner.py`
- Sequential sample batch runner; deterministic per-sample seed derived from SHA-256 of master seed and sample ID; isolates exceptions per sample; tracks processed/succeeded/failed and written/registered counts; batch status COMPLETED/PARTIAL/FAILED.
- G-EXEC-01 bool master seed accepted due `isinstance(bool, int)`.
- G-EXEC-02 sample success may not imply persistence success.
- G-EXEC-03 persistence failures recorded in result but not batch errors.
- G-EXEC-04 no stage-level states.
- G-EXEC-05 no full run identity, fingerprints, stage trace or recovery state.

`src/data/variant_generation_run_summary.py`
- Summary has dataset/split/seed/status, sample/variant counters, success rate, errors, start/end UTC timestamps; JSON export uses temporary file then replace.
- G-EXEC-06 summary variant-specific, not full pipeline.
- G-EXEC-07 missing config/input/tool/pipeline fingerprints and versions.
- G-EXEC-08 persistence failures not represented in overall status semantics.
- G-EXEC-09 no stage timing.
- No code changes.

## Gap backlog (cumulative)
- Config: G1–G6 (see I.9.2.1 section).
- Input: G-IN-01 through G-IN-08 (see I.9.2.2 section).
- Execution: G-EXEC-01 through G-EXEC-09 (see I.9.2.3 section).

## Current next step
Await user confirmation to close I.9.2.3 as **PASS WITH GAPS**. After approval, start I.9.2.4 Runtime Policy audit/design (determinism, timeouts, resource limits, error isolation, retry policy, fail-safe behavior). Do not code yet.


---

# I.9.2.6 — Step 3.3.5: Source Mutation & TOCTOU Audit

**Date:** 2026-11-22  
**Scope:** `variant_source_loader.py`, `variant_generation_runner.py`, `batch_processor.py`  
**Status:** PASS WITH GAPS — audit only; no implementation changes


## 1. VariantSourceLoader

| Check | Evidence | Assessment |
|---|---|---|
| Canonical source root | `Path(source_root).resolve()` | PASS |
| Source path containment | resolved candidate + `is_relative_to(source_root)` | PASS |
| File existence | `source_path.is_file()` | PASS |
| Read source snapshot into memory | `read_text(encoding="utf-8")` | PASS |
| Parse metadata byte size | `int(row["file_size_bytes"])` | PASS |
| Verify actual bytes against metadata size | Not performed in shown code | GAP |
| SHA-256 fingerprint at load | Not performed | GAP |
| Detect changes after loading | Not performed | GAP |
| Guard against mutation during file read | No before/after identity/hash check | GAP |

The loader returns `source_text` as a memory snapshot and `source_path` as a resolved path, but the supplied `file_size_bytes` comes from metadata rather than an actual measured size. The code shown does not establish that the disk file remains identical after loading.

## 2. VariantGenerationRunner

| Check | Evidence | Assessment |
|---|---|---|
| Deterministic per-sample seed | SHA-256 of master seed and sample ID | PASS |
| Sequential processing | Iterates samples sequentially | PASS |
| Per-sample error isolation | Catches exceptions per sample | PASS |
| Verify source file before generation | Not performed | GAP |
| Verify source fingerprint against loaded snapshot | Not performed | GAP |
| Detect source mutation during batch | Not performed | GAP |

The runner passes both the in-memory `sample.source_text` and the on-disk `sample.source_path` to the orchestrator without reconciling them. Generation is based on the loaded text snapshot, while the registry stores the resolved original-source path. If that file changes after load, the provenance path may refer to content different from the content used for generation.

## 3. Preprocessing batch processor

| Check | Evidence | Assessment |
|---|---|---|
| Input directory existence/type | Explicit checks | PASS |
| Recursive source enumeration | `rglob("*.txt")` | PASS |
| Relative directory structure | `relative_to(input_path)` | PASS |
| Output directory creation | `mkdir(parents=True)` | PASS |
| Output path isolation | Not enforced in shown code | GAP |
| Existing destination protection | `write_text()` can overwrite | GAP |
| Atomic per-file output | Direct `write_text()` | GAP |
| Mutation detection | Not performed | GAP |
| Fixed report path isolation | `output_path.parent / "preprocessing_report.json"` | GAP |

The preprocessing implementation overwrites destinations and writes its report to a fixed sibling path. This may be intentional for repeatable preprocessing, but overwrite and run-isolation behavior need an explicit policy.

## 4. TOCTOU / mutation risk summary

- A source may change between loader read and later pipeline persistence.
- There is no source fingerprint captured at load and compared later.
- The source text snapshot and provenance path can diverge over a run.
- A source may also be modified while it is being read; the current code does not verify a stable read snapshot.
- Upstream preprocessing can overwrite source-derived output paths without collision protection or atomic writes.

## 5. Proposed contract closure requirements (not implementation)

1. Measure actual source bytes at load and validate exact metadata byte-size agreement.
2. Capture a SHA-256 source fingerprint associated with the loaded snapshot.
3. Ensure the fingerprint corresponds to the exact source text used for generation (define byte encoding/newline policy explicitly).
4. Verify the on-disk source fingerprint at the approved integrity boundary(s), or make the loaded snapshot authoritative and persist its fingerprint/provenance consistently.
5. Define policy for source mutation during reads (stable-read verification or fail-closed retry/reject).
6. Define preprocessing overwrite, collision, atomic-write, and per-run report path policy.
7. Treat a detected source mutation as an integrity failure; do not silently regenerate from mixed source versions.

## 6. Checkpoint decision

**PASS WITH GAPS.** Snapshot loading, path containment, and sequential execution are present. Source fingerprint consistency, metadata byte-size verification, mutation detection, and preprocessing output protection are not established by the audited code. No code was changed.


---

# I.9.2.6 — Step 3.3.6: Path & Source Integrity Reconciliation

**Date:** 2026-11-22  
**Status:** Reconciliation proposal — awaiting approval  
**Scope:** Evidence from 3.3.1–3.3.5; no implementation changes

## 1. Scope and evidence

This reconciliation consolidates the path/source audit evidence from:
- 3.3.1 Path usage inventory
- 3.3.2 Config path and root resolution
- 3.3.3 Source path containment
- 3.3.4 Output path isolation and collision
- 3.3.5 Source mutation and TOCTOU

Audited components include the config/CLI boundary, `VariantSourceLoader`, `VariantOutputWriter`, `VariantPipelineOrchestrator`, `VariantRegistry`, generation report and run-summary exporters, `VariantGenerationRunner`, and preprocessing batch processor.

## 2. Consolidated findings

| ID | Finding | Evidence / risk | Proposed disposition |
|---|---|---|---|
| P-01 | Path authority is inconsistent | Config paths and CLI defaults depend on CWD or inferred config location; config and CLI path/seed authority is not reconciled | Mandatory before implementation |
| P-02 | Source containment exists at loader boundary | Loader resolves paths and checks containment under source root; writer independently checks output containment | Already satisfied at these boundaries; retain as invariant |
| P-03 | Original-source containment is not revalidated by orchestrator | Orchestrator only resolves `original_source_path`; no source-root containment contract at persistence boundary | Mandatory contract; enforcement location to be decided |
| P-04 | Source metadata size is not checked against actual bytes | Loader parses metadata size but does not compare to `stat().st_size` | Mandatory; input contract already approved |
| P-05 | Source snapshot fingerprint/provenance is incomplete | Loader/runner do not capture source hash; registry stores variant hash but no original-source hash | Mandatory; preserve source identity for run and registry provenance |
| P-06 | Source mutation / TOCTOU is not detected across run | No before/after fingerprint strategy; path may refer to a changed source after load | Mandatory; fail-closed policy needed |
| P-07 | Output paths are not uniformly canonicalized at CLI/export boundaries | Writer resolves its root, while registry/report/summary and CLI paths are inconsistent | Mandatory path-boundary contract; canonicalize before use |
| P-08 | Per-run output isolation is not enforced | Shared paths can overwrite report/summary or mix outputs between runs | Mandatory; define run-scoped output layout or explicit overwrite policy |
| P-09 | Registry read-modify-write lacks concurrency protection | Atomic replace prevents partial-file replacement but does not prevent lost updates across concurrent writers | Mandatory decision: single-writer/run lock or concurrency-safe transaction |
| P-10 | Run-summary temp file uses fixed sibling name | Concurrent exporters targeting same output can collide on `.tmp` | Mandatory fix or guarantee single writer with isolated run paths |
| P-11 | Report exporter can overwrite a shared destination | Temp file is unique, replacement is atomic, but destination overwrite is allowed | Mandatory policy; unique run output or explicit overwrite permission |
| P-12 | Preprocessing outputs/report can collide and overwrite | Direct writes; no output containment guard, atomic file replacement, or run-specific report isolation | Deferred from core I.9 implementation unless preprocessing is part of the run; must be tracked as upstream integrity risk |
| P-13 | Atomic report/registry replacement is implemented in places | Same-directory temp + flush/fsync + replace in registry/report; registry read-modify-write still has race | Already partially satisfied; atomicity is not isolation/concurrency safety |

## 3. Mandatory closure items proposed before implementation

### M-1 — Single path/root authority
- Define one explicit project/run root authority; do not infer authority from the current working directory.
- Establish exact CLI override rules for config values and seeds.
- Resolve config-relative paths against a documented root.
- Canonicalize paths at boundaries and reject disallowed escapes.
- Keep source roots separate from artifact/output roots.

### M-2 — Source identity and mutation integrity
- Verify actual file byte size against metadata.
- Capture SHA-256 of original source bytes/snapshot when loading.
- Establish what is hashed: source bytes read for generation, not a later reread only.
- Detect disk source mutation during run according to the approved policy and fail closed on integrity mismatch.
- Carry original-source fingerprint into variant provenance/registry records.

### M-3 — Output isolation and overwrite policy
- Define run identity and run-scoped output directories for variants, registry, reports, and summaries (or approve an equivalent isolation strategy).
- Prohibit accidental cross-run artifact reuse/overwrite.
- Define behavior when target artifacts already exist: fail, resume, or explicit overwrite; do not silently overwrite.
- Use collision-safe temporary files for exports.

### M-4 — Registry write safety
- Define concurrency policy: single writer with an enforceable run lock, or safe transactional update.
- Prevent lost updates from concurrent registry writers.
- Ensure registry location belongs to the intended run/output root under approved policy.

### M-5 — Preflight path/integrity readiness
- Before generation begins, verify all required input/output paths, containment, directory creation/write access, artifact collisions, and registry consistency.
- Fail before any variants are written if a mandatory integrity precondition fails.

## 4. Deferred / scoped items proposed

- Preprocessing batch processor hardening (destination containment, atomic writes, collision policy) can be deferred from core I.9 implementation only if preprocessing is treated as a separate upstream preparation tool. Record it as an upstream remediation item and do not claim the preprocessing path is fully integrity-hardened.
- Platform-specific TOCTOU hardening beyond canonicalization, source snapshot hashing, and mutation detection can be deferred if the first implementation documents its threat model and limitations. Avoid claiming symlink/race resistance stronger than the actual checks.

## 5. Already-satisfied controls to preserve

- Loader resolves source candidates and enforces containment under canonical source root.
- Variant output writer validates path components, canonicalizes output path, checks containment, and uses exclusive creation (`xb`) to avoid variant overwrite.
- Registry/report exporters use same-directory temporary replacement in their respective implementations; this provides atomic replacement at file level, not run isolation or full concurrency safety.
- Runner derives stable per-sample seeds from master seed and sample ID.
- Generation consumes the in-memory source text snapshot supplied by loader rather than reopening source text inside runner.

## 6. Proposed decision / acceptance criteria

3.3.6 should be accepted when the owner approves:
1. M-1 through M-5 as mandatory pre-implementation contract items;
2. P-12 as explicitly deferred/scoped (or elevated to mandatory);
3. concurrency strategy for registry writes and run-level output isolation;
4. the source snapshot/hash/mutation policy and failure behavior.

No code changes are authorized or performed by this audit.

## 7. Status

**PASS WITH GAPS — reconciliation prepared, approval pending.**  
The evidence is consolidated. Design closure is not yet final until the mandatory policies are approved and then carried into Step 3.3.7 and cross-contract reconciliation.


---

# I.9.2.6 — Step 3.3.7: Path & Source Integrity Closure

**Date:** 2026-11-22  
**Status:** CLOSED — APPROVED BASELINE  
**Approval basis:** User approval of Step 3.3.6 reconciliation

## Closure statement
Step 3.3 Path & Source Integrity Audit is closed. The approved mandatory requirements M-1 through M-5 are design-baseline requirements for the implementation phase. No repository code has been modified as part of this audit.


## Approved requirements

| ID | Requirement | Closure disposition |
|---|---|---|
| M-1 | Single path/root authority; canonicalize path boundaries; reject escapes; distinguish source and artifact roots | Mandatory implementation requirement |
| M-2 | Verify actual source byte size; capture SHA-256 for the loaded source snapshot; preserve provenance; detect source mutation and fail closed | Mandatory implementation requirement |
| M-3 | Run-scoped output isolation; explicit fail/resume/overwrite behavior; collision-safe temporary artifacts | Mandatory implementation requirement |
| M-4 | Registry write safety against concurrent read-modify-write/lost updates; single-writer lock or transaction policy | Mandatory implementation requirement |
| M-5 | Preflight validates path containment, readiness, permissions, collisions, and registry consistency before generation writes | Mandatory implementation requirement |

## Deferred / tracked risk

- P-12: preprocessing batch output hardening (containment, atomic writes, collision policy) is deferred from core I.9 if preprocessing remains a separate upstream preparation tool. This must remain documented as upstream risk and cannot be represented as fully hardened.
- Platform-specific TOCTOU hardening beyond snapshot hashing, mutation detection, and canonicalization may be deferred subject to a documented threat model. Do not claim race-proof symlink behavior.

## Existing controls to preserve

- Loader canonicalizes source candidates and checks containment within source root.
- Variant writer validates path components, checks output containment, and uses exclusive creation.
- Some registry/report writes use same-directory temporary files and atomic replacement.
- Per-sample deterministic seed derivation exists.
- Generation consumes loaded in-memory source text rather than reopening source during generation.

These controls are partial and do not satisfy all mandatory requirements by themselves.

## Final audit disposition

- Step 3.3.1 Path Usage Inventory: completed
- Step 3.3.2 Config Path & Root Resolution Audit: completed
- Step 3.3.3 Source Path Containment Audit: completed
- Step 3.3.4 Output Path Isolation & Collision Audit: completed
- Step 3.3.5 Source Mutation & TOCTOU Audit: completed
- Step 3.3.6 Path & Source Integrity Reconciliation: approved
- Step 3.3.7 Path & Source Integrity Closure: closed

**Next:** I.9.2.6 Step 3.4 — Preflight Acceptance Contract.


---

# I.9.2.6 — Step 3.4.1 Preflight Responsibility & Existing Capability Inventory

**Status:** Audit completed — PASS WITH GAPS  
**Scope:** Inventory only; no code changes and no preflight design approval implied.

## Evidence reviewed
- `src/data/pair_generation_config.py` (user-provided source)
- `src/data/variant_generation_cli.py` (user-provided source)
- `src/data/variant_generation_runner.py` (user-provided source)
- `tests/test_environment.py` (user-provided source)
- `tests/test_variant_generation_cli.py` (user-provided source)
- Source search for `preflight|readiness|environment check|validate.*config|check.*path`; only config-validation matches were found in `pair_generation_config.py` after excluding `.pyc` artifacts.

## Existing capabilities

| Component | Existing checks / behavior | Category |
|---|---|---|
| `PairGenerationConfig` | Config existence, file type, JSON parse, object root, required sections and values/cross-field constraints | Configuration validation |
| CLI `validate_cli_args` | Nonnegative seed; dataset root exists and is a directory | CLI prechecks |
| CLI `run_cli` | Loads metadata/splits through loader; filters split; constructs runner and executes | Execution path, not consolidated preflight |
| `VariantSourceLoader` | Metadata/split schema and source checks, containment, sample eligibility (previous audit evidence) | Input validation during loading |
| Registry integrity checker | Registry integrity checks (previous audit evidence) | Integrity validation |
| Output writer | Output path containment and exclusive creation (previous audit evidence) | Write-time safeguards |
| Orchestrator | Per-sample/variant generation and validation steps (previous audit evidence) | Runtime validation |
| `VariantGenerationRunner.run` | Processes samples sequentially; captures per-sample exceptions and continues; reports completed/partial/failed according to counts | Runtime error isolation |
| `test_environment.py` | NumPy array sum; Pandas DataFrame construction; sklearn accuracy computation; Tree-sitter Parser instantiation | Dependency smoke tests |
| `test_variant_generation_cli.py` | CLI defaults/custom args/split parsing; negative seed, missing root, file-not-directory rejected; split filtering and all-split passthrough tested | CLI behavior tests |

## Boundaries and limitations confirmed
- No independent preflight coordinator/result contract was identified in the source inventory/search evidence.
- Config validation and CLI checks are separate and not shown as consolidated before-run checks.
- Loader validation occurs during loading; it is not demonstrated as an aggregated preflight readiness report.
- Environment tests are smoke checks only: no package-version compatibility check, C++ grammar loading check, Clang executable/version/flags verification, or full pipeline dependency readiness check was shown.
- CLI tests do not demonstrate checking write permissions, output collisions, registry readiness, path canonicalization/containment for every output, or output isolation before generation.
- Runner's sample-level exception handling is runtime recovery, not preflight fail-fast policy. The CLI's final return code depends on result status.

## Preliminary inventory conclusion
Existing checks are distributed across configuration, CLI, loader, integrity, writer, orchestrator, and runner. They provide useful local validation, but the reviewed evidence does not establish a unified preflight phase that checks mandatory readiness before generation side effects.

**Disposition:** 3.4.1 inventory can close as PASS WITH GAPS. Proceed to 3.4.2 Path / Config Readiness Checks. No implementation changes are authorized by this audit checkpoint.


---

# I.9.2.6 — Step 3.4.2.1 Config Readiness Audit

**Status:** PASS WITH GAPS — config readiness audit evidence reviewed
**Scope:** `config/pair_generation_config.json` and previously supplied `src/data/pair_generation_config.py`
**Mode:** Audit only; no repository code changes.

## Configured paths

| Key | Value | Role |
|---|---|---|
| dataset.raw_dir | `data/raw/poj104` | Raw dataset |
| dataset.processed_dir | `data/processed/poj104` | Processed dataset |
| dataset.metadata_dir | `data/processed/poj104/metadata` | Metadata directory |
| dataset.source_metadata_file | `data/processed/poj104/metadata/samples.csv` | Source metadata file |
| output.candidate_dir | `data/pairs/candidates` | Candidate pairs |
| output.selected_dir | `data/pairs/selected` | Selected pairs |
| output.pairs_dir | `data/pairs` | Pair artifact root |
| output.split_dir | `data/pairs/splits` | Pair splits |
| output.reports_dir | `data/pairs/reports` | Reports |
| output.config_snapshot_dir | `data/pairs/configs` | Config snapshots |

## Existing config checks evidenced in code
- Config file exists and is a file; JSON parse succeeds; root is a dict.
- Required sections exist.
- Dataset name is a non-empty string.
- Seed is integer (bool excluded).
- Split ratios, transformation probabilities and supported sampling behavior are validated.
- Variant and negative-pair parameters/constraints are validated.
- Negative-screening, pair-selection and parser/compiler timeout settings are validated.

## Gaps / risks
- No evidence yet of `config_version` or `pipeline_version` compatibility checks.
- No evidence yet that dataset language is validated against supported language or runtime capability.
- Configured path values are not centrally validated for type/empty values.
- `resolve_path()` resolves absolute paths as given and relative paths from inferred project root (`config_path.parent.parent`); no containment policy was evidenced in the supplied implementation.
- Config validation does not itself prove required input paths exist, are readable, or are of the correct type.
- Config validation does not preflight output directories for writability, collisions, overwrite policy, or run isolation.
- CLI's variant-generation path is a separate configuration surface and does not use this `PairGenerationConfig` directly, based on supplied CLI evidence; alignment remains an open cross-contract issue.

## Preliminary conclusion
Config schema/behavior validation exists and is fairly broad. It is not a readiness check: path resolution and config validity do not guarantee the pipeline can safely execute. Findings are preliminary to subsequent path/input/output/environment preflight checkpoints.

## Next checkpoint
3.4.2.2 — Dataset root and metadata path readiness evidence.
