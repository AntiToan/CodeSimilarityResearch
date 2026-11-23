# I.9.2.5 — Output & Execution Contract Audit
**Project:** CodeSimilarityResearch  
**Date:** 2026-11-21  
**Checkpoint:** I.9.2.5  
**Audit status:** PASS WITH GAPS  
**Scope:** Audit of output/execution contracts against approved design documents and previously inspected repository evidence.  
**Code changes:** None. Audit only.

## 1. Scope and evidence reviewed

### Design sources
- `docs/pair_generation_output_and_reproducibility.md` (uploaded and read): defines master pair index, pair-ID split indexes, generation/validation/sampling/distribution reports, config retention, reproducibility metadata, candidate-retention policy, and run tracking.
- `docs/pair_generation_pipeline_orchestration.md` (uploaded and read): defines stage order/dependencies, failure handling, run status, intermediate vs final artifacts, independent runs/reruns, run reporting, consistency, and final-validation export gate.
- `docs/final_pair_selection_and_balancing.md` (uploaded and read): defines candidate/selected artifacts, per-split selection, independent final validation, split-index outputs, selection reporting, and shortage policy.
- `docs/design_closure_and_implementation_readiness.md` (uploaded and read): reconciles canonical layout and roles; establishes `pair_index.csv` as authoritative selected final index, `assembled_candidates.csv` as intermediate, split files as pair-ID references, and implementation prerequisites/pilot requirements.

### Repository evidence from prior terminal searches
- Source scan for writer/export/manifest/atomic-write patterns found variant-oriented report/summary exporters, `variant_output_writer.py`, `variant_registry.py`, and preprocessing-related writers. No full-pipeline pair dataset CSV exporter or full-pipeline manifest was identified in the scanned source.
- Broader repository search (excluding virtualenv, cache, and Git directories) found design references in docs and source references mainly in `final_dataset_validator.py`, `source_splitter.py`, `variant_registry.py`; no implementation evidence was located for `pair_index.csv`, `assembled_candidates.csv`, pair split-index export, or a full pipeline finalizer.
- Existing code evidence previously reviewed: variant source writing is exclusive-create but not atomic; variant registry and variant reports use temporary files plus replace-style atomic writes; run summary is variant-only. This is partial artifact atomicity, not proof of atomic final dataset finalization.
- Searches are evidence of what was found, not absolute proof that no implementation exists elsewhere.

## 2. Approved output design baseline

### Canonical layout and artifact roles
- `data/pairs/candidates/assembled_candidates.csv`: intermediate assembled candidate pool before selection.
- `data/pairs/pair_index.csv`: canonical, authoritative full records for selected final pairs.
- `data/pairs/splits/train.csv`, `validation.csv`, `test.csv`: pair-ID reference files into the master index; no full pair duplication.
- `data/pairs/reports/`: generation, split, variant, screening, assembly, selection, final-validation reports.
- `configs/pair_generation_config.json`: configuration retained with outputs.
- The selection-design document also proposes `selected_pairs.csv`; the design-closure document reconciles this to canonical `pair_index.csv` as final authority. This is a design reconciliation, not implementation evidence.

### Run/reproducibility requirements
- Unique `run_id`, status, timestamps, seed, configuration and pipeline versions, input references, stage status/output/error/warnings, counts, validation/export results.
- Independent run isolation; reruns must not silently overwrite prior completed runs.
- Finalization is gated by final validation PASS and successful final artifact production.
- Cross-artifact consistency: selected pairs, master index, pair-ID split files, reports, labels, source references, source splits, and counts must agree.
- Deterministic ordering and controlled randomness; retain inputs/config/dependencies/version details sufficient for reproduction.
- Intermediate/partial outputs must not be mistaken for final valid dataset.
- Preserve diagnostics; failure/incomplete reports must not falsely mark a dataset valid.

## 3. O-01 through O-10 audit

| ID | Requirement | Status | Evidence / rationale |
|---|---|---|---|
| O-01 | One authoritative final dataset; no competing final artifacts | NOT VERIFIED / GAP | Canonical design says `pair_index.csv` is authoritative. Implementation of full-pair export not found in searched repository evidence. Selection design's `selected_pairs.csv` was reconciled in design closure, but no source implementation evidence. |
| O-02 | Run isolation | PARTIAL / GAP | Design requires independent runs and no overwrite. Variant writers use safe/exclusive writing for variant files, but full pair-pipeline run directory isolation and collision policy were not evidenced. |
| O-03 | Atomic finalization | PARTIAL / GAP | Atomic temp-write/replace exists for variant registry/reports. Variant source writer is direct exclusive-create, not atomic. No final selected-pair dataset atomic publication/finalizer was found. |
| O-04 | Cross-artifact consistency | NOT VERIFIED / GAP | Design specifies reconciliation among pair master, split indexes, reports/counts, labels, references, and selection results. Full-pipeline consistency/final export implementation not found. |
| O-05 | Run/config/seed/source traceability | PARTIAL / GAP | Variant registry/report/summary preserve some provenance and seed details. Full run ID, config/pipeline/input fingerprints and source-to-final-pair trace across all artifacts were not established. |
| O-06 | Failure diagnostics without false-valid implication | PARTIAL / GAP | Variant generation has per-sample result/error diagnostics and variant reports. Full pipeline run-level diagnostic contract and artifact-validity signaling were not found. |
| O-07 | Final validation PASS gate before export | NOT VERIFIED / GAP | `FinalDatasetValidator` exists and is tested; orchestration/export gate that blocks publication on non-PASS validation was not evidenced. |
| O-08 | Naming/versioning | PARTIAL / GAP | Canonical naming and schema roles are defined in design closure. Full implementation adoption, versioning and collision-safe run-specific names were not verified. |
| O-09 | Intermediate/partial/final distinction | PARTIAL / GAP | Variant outputs and reports distinguish variant-stage artifacts. Pair pipeline artifact lifecycle, final dataset marking and partial-run handling not evidenced in source. |
| O-10 | Sufficient reproducibility metadata | PARTIAL / GAP | Deterministic seed-based behavior exists in inspected split/variant-related modules, but full run-level input snapshots/fingerprints, config freeze, pipeline/dependency versions, and complete stage trace were not evidenced. |

## 4. Confirmed implementation vs design-only

### Confirmed or partially evidenced in inspected source
- Variant output writing and registry.
- Atomic replacement patterns for variant registry and variant reports.
- Variant generation report and variant-only run summary.
- Final dataset validation component exists.
- Source splitting component exists.
- Deterministic seed behavior in variant runner (with previously noted gaps).

### Not evidenced in the searched source
- Full pair-generation orchestrator/finalizer.
- Canonical final `pair_index.csv` writer.
- `assembled_candidates.csv` persistence as canonical pipeline artifact.
- Pair split index CSV export.
- Full run manifest/fingerprint system.
- Atomic final dataset publication.
- Cross-artifact consistency verification during final export.
- Final validation PASS export gate at pipeline level.
- Independent run directories/collision policy for full pair runs.

## 5. Audit conclusion

**I.9.2.5 is closed as PASS WITH GAPS.**

The output/execution contract is sufficiently specified at design level and reconciled by the design-closure document. However, the implementation evidence currently remains variant-stage-centric. The full pair-pipeline output and execution-contract capabilities listed O-01 through O-10 are not implemented or not verified in the searched source.

This checkpoint is an audit closure only. No source files were edited.

## 6. Remaining gaps to carry forward
- Full-pipeline output/export implementation and canonical final artifact.
- Run isolation, run IDs, manifest and artifact inventory.
- Atomic final dataset finalization.
- Cross-artifact consistency checks.
- Full traceability/fingerprints/version/dependency metadata.
- Run-level error and warning diagnostics.
- Final-validation PASS gate enforced by export.
- Explicit intermediate/partial/final lifecycle and naming/version policy.
- End-to-end reproducibility trace.

## 7. Next checkpoint
**I.9.2.6 — Design Closure:** reconcile and formally close config, input, execution-order, runtime-policy, and output/execution-contract findings into a single approved implementation-ready contract. Do not start implementation until that closure checkpoint is reviewed and approved.

## 8. Audit commands/evidence boundary
The audit relied on the user-provided terminal search outputs from the repository and the four design files listed above. No repository changes or local code execution were performed during this closure.


---

# I.9.2.6 — Step 3.1 Config Contract Closure Audit

**Date:** 2026-11-21  
**Scope:** Read-only audit of `src/data/pair_generation_config.py` supplied by user.  
**Status:** PASS WITH GAPS  
**Code changes:** None.

## 1. Confirmed implementation

- Resolves config path; checks exists and is a file.
- Reads UTF-8 JSON and converts JSON parse errors into `PairGenerationConfigError`.
- Validates root is a dict.
- Requires the eleven top-level sections.
- Validates nonempty dataset name and integer seed (explicitly excludes bool).
- Validates exact split ratio keys, numeric values in `(0,1)`, sum within tolerance.
- Validates transformation enabled list nonempty, duplicate names, probability entries for enabled names, probability range and sum, and `without_replacement` sampling.
- Validates variant target/maximum/attempt counts as positive integers, target <= maximum, chaining disabled.
- Validates negative-pair quota/attempt counts, disallows same-problem and same-lineage pairs, requires originals-only.
- Validates negative screening threshold, `token_jaccard`, fail-closed.
- Validates selection oversampling/cross-split transfer disabled, selection strategy `min_class_count`, and positive target ratio.
- Validates fail-closed validation and positive parser/compiler timeout values.
- Provides nested `get`, convenience `seed` and `dataset_name`, and repository-root-relative path resolution (root inferred as parent of config directory).

## 2. Gaps / limitations

- **CFG-01 Section types:** required sections are checked for presence but not each being an object; malformed sections may cause `AttributeError` instead of config-domain error.
- **CFG-02 Unknown keys:** unknown root and nested keys are accepted; no strict schema/version handling.
- **CFG-03 Incomplete field validation:** sections including `split`, `duplicate_detection`, and `output` lack comprehensive schema validation; other sections permit unvalidated extras.
- **CFG-04 Transformation names/types:** enabled item types and allowed transformation names are not explicitly validated; probability keys beyond enabled list are accepted; unhashable entries may raise native exceptions during `set()`.
- **CFG-05 Numeric edge cases:** positive selection target ratio and timeout validation do not explicitly reject non-finite float values (e.g., infinity); other numeric validation is mostly bounded and catches NaN through comparisons.
- **CFG-06 Mutable authority:** `raw` returns the internal dict directly; `get()` returns mutable nested references; config can be changed after validation and during a run.
- **CFG-07 Snapshot/fingerprint/version:** no immutable validated snapshot, config fingerprint/hash, schema version, or pipeline config version shown.
- **CFG-08 Path semantics:** root inferred from config path's parent-parent; this is an assumption. No centralized path validation, containment policy, or config-relative-vs-repository-relative distinction for every path field shown.
- **CFG-09 Defaults/normalization:** no explicit normalized config model or documented default-merging layer evidenced in this file.
- **CFG-10 Validation error consistency:** missing nested keys through `get()` raise `KeyError`; some malformed values may raise Python-native exceptions instead of `PairGenerationConfigError`.
- **CFG-11 Revalidation and run isolation:** no evidence in this class of freeze-after-validation behavior, safe run-level snapshot capture, or prevention of post-validation mutation.

## 3. Closure contract proposed from approved D-06

1. Load config, validate strictly and report config errors consistently.
2. Validate section/object types and all mandatory fields; define allowed keys and explicit schema/version policy.
3. Normalize config into a canonical representation.
4. Freeze or deep-copy canonical config for the run; prevent mutable references from altering the run config.
5. Compute and persist a config fingerprint/hash and schema/config version.
6. Define path resolution authority (repository-root vs config-relative), validate all configured paths consistently, and make root explicit or deterministic.
7. Keep unsupported or invalid settings fail-fast; do not silently ignore unknown keys unless an explicit compatibility policy allows it.

## 4. Acceptance criteria for implementation readiness

- Malformed sections and nested types produce domain-specific config errors.
- Schema/unknown-key policy is explicit and tested.
- Every consumed setting is validated, including finite numeric constraints and enum/name allowlists.
- Canonical validated snapshot is immutable for the duration of a run.
- Fingerprint and schema/config version are available to run manifest/report.
- Path resolution behavior is documented and tested independent of current working directory.
- Validation failures block pipeline execution before any stage writes output.

## 5. Decision/status

**PASS WITH GAPS.** Existing config validation covers many algorithm-level constraints, but config is not yet closed as a strict, immutable, versioned run authority. D-06 requires the immutable run snapshot; strict schema, fingerprint/version, path policy, and comprehensive section validation remain implementation requirements or explicit decisions to reconcile in design closure.

Audit is read-only. No code changed.


---

# I.9.2.6 — Step 3.2.1: Variant Source Loader Audit

**Date:** 2026-11-21  
**Checkpoint:** Input & Metadata Contract — Loader  
**Status:** PASS WITH GAPS  
**Scope:** Audit-only. No repository code modified.

## 1. Audited source
`src/data/variant_source_loader.py` as provided in the conversation.

## 2. Confirmed implementation
- Reads metadata and split CSVs with UTF-8-SIG and `csv.DictReader`.
- Reports missing CSV files and catches `OSError`, `UnicodeError`, and `csv.Error` during CSV reading.
- Checks required column sets.
- Rejects duplicate sample IDs separately in metadata and split records.
- Includes only metadata records whose status, after strip/lower, equals `success`.
- Requires successful metadata IDs and split IDs to match exactly (missing and extra split IDs rejected).
- Validates split values against train/validation/test.
- Resolves source paths and checks containment within resolved source root.
- Requires source file existence and reads UTF-8 source text, catching filesystem/Unicode errors.
- Parses metadata size as integer and rejects negative values.
- Sorts returned samples by `(problem_id, sample_id)` for deterministic order.

## 3. Audit table
| Area | Status | Evidence / note |
|---|---|---|
| CSV existence/read | PASS | `_read_csv` uses `is_file`; catches read errors |
| Required columns | PASS WITH GAPS | Header set checked from first DictReader row |
| Metadata ID uniqueness | PASS | Duplicate sample IDs rejected |
| Split ID uniqueness | PASS | Duplicate split sample IDs rejected |
| Success filtering | PASS | Only `status == success` after strip/lower |
| Metadata/split coverage | PASS | Missing and extra split IDs rejected |
| Split values | PASS | Allowed split set enforced |
| Path containment | PASS | resolved path must remain under source root |
| Source existence | PASS | `is_file()` |
| Source readability | PASS WITH GAPS | UTF-8 read and exception handling; content constraints absent |
| Empty source | GAP | Empty or whitespace-only text accepted |
| Size metadata | PASS WITH GAPS | Integer/nonnegative only; not compared to actual file size |
| Language | GAP | Loaded without validation/allowlist/config check |
| Filename/path consistency | GAP | Filename not compared with path basename |
| Stable output order | PASS | Sort by problem ID and sample ID |

## 4. Gaps
- **IN-01 Required values:** IDs and other required fields are not checked for blank/whitespace-only values.
- **IN-02 File size consistency:** CSV size is not compared against actual source file size.
- **IN-03 Empty content:** empty or whitespace-only source is accepted.
- **IN-04 Language contract:** language is not checked against configured/allowed languages.
- **IN-05 Filename consistency:** `filename` is not checked against source path basename.
- **IN-06 Filtered-status split policy:** split IDs for non-success metadata are rejected as extra IDs; policy for pre-filtered samples is not explicitly documented.
- **IN-07 Strict CSV schema:** duplicate headers, blank headers and row/schema irregularities are not explicitly validated beyond required column names.
- **IN-08 ID canonicalization:** metadata/split IDs are compared without normalization; whitespace can cause mismatch. Canonical-ID policy is not established.
- **IN-09 Path policy:** containment is enforced, but absolute paths, symlink policy and root authority are not fully specified.

## 5. Contract recommendations (design, not implementation)
- Validate required fields as nonblank strings.
- Define canonical sample-ID handling (prefer strict canonical values over silent trimming that could hide collisions).
- Decide whether split records may include failed/filtered samples; make loader behavior consistent with that policy.
- Validate supported language values and file extension mapping against the project/config contract.
- Validate filename/path agreement if both are authoritative fields.
- Compare declared byte size with actual file byte size, using a clearly defined encoding/storage convention.
- Reject empty/whitespace-only sources if empty code is not an eligible sample.
- Add strict CSV header/schema checks.
- Document path policy for relative/absolute paths and symlinks; preserve resolved containment checks.

## 6. Closure
**PASS WITH GAPS.** The loader has useful integrity controls—unique IDs, split coverage, allowed split labels, path containment, source existence, and stable ordering. It is not yet a fully closed input contract because field-value, content, metadata consistency, language, and path-policy validation remain incomplete.

No code was changed. Next planned subcheckpoint: 3.2.2 metadata generator/metadata integrity audit.


---

# I.9.2.6 — Step 3.2.2: Metadata Generator & Metadata Integrity Audit

**Date:** 2026-11-21  
**Checkpoint status:** PASS WITH GAPS  
**Scope:** Audit-only; no repository code changed.

## 1. Audited source

`src/data/metadata_generator.py`

## 2. Confirmed implementation

| Item | Status | Evidence |
|---|---|---|
| Raw directory existence | PASS | `raw_path.exists()` |
| Raw directory type | PASS | `raw_path.is_dir()` |
| Deterministic file discovery | PASS | `sorted(raw_path.rglob("*.txt"))` |
| Processed source existence | PASS | `processed_file.is_file()` |
| Success/failed classification | PASS | Status derived from processed file existence |
| File size metadata | PASS WITH GAPS | `stat().st_size` for success, zero for failed |
| Sample ID generation | PASS WITH GAPS | Deterministic ID from problem ID and file stem, no collision check |
| Problem ID extraction | PASS WITH GAPS | First component of relative path |
| Language metadata | PASS WITH GAPS | Hardcoded `cpp` |
| CSV output schema | PASS | `METADATA_FIELDS` and `DictWriter` |
| Output parent creation | PASS | `mkdir(parents=True, exist_ok=True)` |
| Encoding | PASS WITH GAPS | Metadata CSV UTF-8; source content is not read/validated here |

## 3. Gaps

- **MD-01 Sample ID collision:** ID uses `problem_id` and `file_stem`; distinct nested files with the same stem may collide. No collision validation exists.
- **MD-02 Processed directory preflight:** `processed_dir` existence/type is not validated before iteration. Missing processed directory leads to samples marked failed rather than a clear preflight error.
- **MD-03 Status semantics:** success is based only on `is_file()`, not readability, non-empty content, parse validity, or language validity.
- **MD-04 Empty sources:** zero-byte processed source can be marked successful; no empty-source policy is enforced.
- **MD-05 Language is hardcoded:** all rows receive `cpp`, without configuration or content/extension validation.
- **MD-06 Path convention:** `source_path` is relative to `processed_path.parent`, not `processed_path`; reconcile with loader `source_root` contract to avoid incorrect resolution.
- **MD-07 Non-atomic output:** output CSV is opened in write mode directly. A mid-run failure can leave truncated/partial metadata without a completeness marker.
- **MD-08 Debug print:** path diagnostics are printed for the first sample instead of being returned as structured diagnostics/logging.
- **MD-09 Error reporting/isolation:** filesystem/stat/write errors can terminate generation; there is no structured per-sample failure reason report.
- **MD-10 Empty discovery:** no discovered TXT files can produce a header-only CSV and zero counts; empty dataset acceptance is unspecified.

## 4. Integrity implications

- Metadata `sample_id` uniqueness is not guaranteed by this generator, though the source loader later rejects duplicate IDs.
- `status=success` is a presence signal only; it does not certify that source content is valid or usable.
- Metadata path root and loader source-root assumptions must be reconciled.
- The direct CSV write is not crash-safe/atomic and can expose partial output.

## 5. Closure recommendations (design, not implementation)

1. Define sample ID uniqueness/collision policy, preferably incorporating a canonical relative path or explicit collision rejection.
2. Validate processed directory upfront and define whether empty files are invalid.
3. Define the exact meaning of `success` (existence vs readable/non-empty/validated).
4. Establish language authority and supported-language validation.
5. Reconcile source path root convention with `VariantSourceLoader`.
6. Publish metadata atomically or explicitly mark generation incomplete on failure.
7. Replace ad hoc debug prints with structured report/logging.
8. Define behavior for no discovered source files and filesystem errors.

## 6. Conclusion

**PASS WITH GAPS.** The generator deterministically discovers raw `.txt` files, writes a fixed metadata schema, checks whether corresponding processed files exist, and reports counts. It does not currently guarantee sample-ID uniqueness, source usability, strict path-root consistency, or atomic output. Audit only; no code changes made.


---

# I.9.2.6 — 3.4.3 Input & Metadata Readiness

**Status:** CLOSED — PASS WITH GAPS  
**Checkpoint:** 3.4.3.5 Input Readiness Acceptance & Closure  
**Project:** CodeSimilarityResearch  
**Scope:** Input metadata, source mapping, split mapping, source integrity, and input snapshot readiness.

---

## 1. Purpose

Assess whether the pipeline inputs and metadata are structurally ready for pipeline orchestration, identify integrity and reproducibility gaps, and carry confirmed evidence forward without re-auditing previously validated modules.

This checkpoint is an audit/design record. It does **not** implement the identified controls.

## 2. Audit approach

- Carry forward evidence from previous checkpoints where no contradiction or regression is present.
- Focus on unresolved input acceptance gaps.
- Avoid repeated full-dataset scans and unnecessary terminal commands.
- Distinguish verified evidence from requirements not yet implemented or fully demonstrated.
- Treat integrity gaps as implementation/acceptance requirements; do not claim full input integrity.

## 3. Confirmed evidence

### 3.1 Metadata and split artifacts

Previously observed metadata files under `data/processed/poj104/metadata`:

- `samples.csv`
- `source_splits.csv`
- `duplicate_groups.csv`

Observed row counts and schemas:

| Artifact | Rows | Columns |
|---|---:|---:|
| `samples.csv` | 52,000 | 8 |
| `source_splits.csv` | 52,000 | 8 |
| `duplicate_groups.csv` | 5 | 4 |

No malformed rows were reported in the prior schema/count check.

### 3.2 Samples ↔ splits reconciliation

Audit output:

| Check | Result |
|---|---:|
| Samples rows | 52,000 |
| Split rows | 52,000 |
| Unique sample IDs | 52,000 |
| Unique split IDs | 52,000 |
| Duplicate sample IDs | 0 |
| Duplicate split IDs | 0 |
| Missing split IDs | 0 |
| Orphan split IDs | 0 |
| Problem ID mismatch | 0 |

**Conclusion:** samples and split records have complete ID coverage and uniqueness, with no detected problem-ID mismatch in the executed reconciliation.

### 3.3 Duplicate-group evidence

There are five duplicate groups. Each has metadata `sample_count = 2`, two split-manifest records associated with the group, and matching content hashes reported by the focused diagnostic.

The metadata `sample_ids` field is JSON-array text, for example:

```json
["poj104_26_345", "poj104_62_593"]
```

An earlier membership-check script incorrectly assumed semicolon-separated IDs, then a subsequent JSON parsing/membership script still reported zero correct members. The exact member-ID-to-split-row reconciliation was therefore **not conclusively validated by that script**.

Verified observations:
- 5 groups exist.
- Metadata count is 2 per group.
- Split-group count is 2 per group.
- Group hashes matched in the focused output.

Do **not** mark exact member-ID reconciliation as fully passed based only on those counts/hashes.

## 4. Source loader audit

Reviewed `src/data/variant_source_loader.py`.

### Confirmed controls

- Reads metadata and split CSVs with UTF-8 CSV handling.
- Requires configured metadata and split columns.
- Enforces unique sample IDs in each artifact.
- Excludes metadata records not marked `success`.
- Checks missing split assignments and extra split IDs.
- Validates split labels against `train`, `validation`, and `test`.
- Resolves source paths canonically and rejects paths escaping the source root.
- Requires source files to exist.
- Reads source text as UTF-8 and wraps read errors.
- Parses metadata `file_size_bytes` as an integer and rejects negative values.
- Stores loaded text and metadata size in `LoadedSample`.

### Gaps

- Metadata file size is not compared against the actual on-disk byte size.
- No raw-source SHA-256 fingerprint is calculated by this loader.
- `LoadedSample.file_size_bytes` is the metadata value, not an independently measured byte size.
- No source mutation/change detection is implemented in this loader.
- No immutable input snapshot or run-level source fingerprint map is created here.

## 5. Split and snapshot consistency

Carry-forward design evidence:

- Source-level splitting occurs before variant and pair generation.
- Approved split ratio is 80/10/10 with a fixed seed.
- Duplicate groups are atomic across splits.
- Generated variants inherit the split of their original sample.
- Pair endpoints must belong to the same split.
- The split manifest is persisted and its ID mapping was reconciled.

No implementation evidence was established in this checkpoint for an immutable input snapshot attached to a pipeline run, source-fingerprint linkage inside that snapshot, or run-level enforcement preventing snapshot drift.

## 6. Acceptance matrix

| ID | Acceptance criterion | Status | Evidence / note |
|---|---|---|---|
| IR-01 | Metadata schema and required fields | PASS (carry-forward) | Loader schema checks previously reviewed |
| IR-02 | Sample ID uniqueness | PASS | 52,000 unique |
| IR-03 | Split ID uniqueness | PASS | 52,000 unique |
| IR-04 | Samples ↔ splits ID coverage | PASS | No missing or orphan IDs |
| IR-05 | Problem ID consistency | PASS | 0 mismatches in audit |
| IR-06 | Source path containment | PASS (code evidence) | Canonical path containment |
| IR-07 | Source existence/readability | PASS (code evidence) | Existence and UTF-8 read checks |
| IR-08 | Failed-sample exclusion | PASS (code evidence) | Only status `success` eligible |
| IR-09 | Duplicate-group counts and hashes | PASS (focused diagnostic) | 5 groups; count and hash observations match |
| IR-10 | Exact duplicate member IDs reconciled to split rows | GAP | Prior membership scripts did not conclusively validate |
| IR-11 | Metadata size matches actual source bytes | GAP | Not checked by loader |
| IR-12 | Raw source fingerprint | GAP | Not calculated at input boundary |
| IR-13 | Source mutation detection | GAP | Not established |
| IR-14 | Immutable input snapshot | GAP | Not implemented/evidenced |
| IR-15 | Snapshot-to-run traceability | GAP | Not implemented/evidenced |

## 7. Implementation requirements carried forward

| Requirement | Description | Priority |
|---|---|---|
| IR-R1 | Validate cross-artifact consistency across metadata, sources, and split assignments | Critical |
| IR-R2 | Measure actual source byte size and verify metadata size | Critical |
| IR-R3 | Calculate SHA-256 on raw source bytes | Critical |
| IR-R4 | Bind the fingerprint to the exact source bytes consumed by pipeline stages | Critical |
| IR-R5 | Define source mutation detection and fail-closed handling | Critical |
| IR-R6 | Create a run-associated input snapshot | Critical |
| IR-R7 | Snapshot records source identity, split, metadata provenance, and fingerprint | Critical |
| IR-R8 | Correctly reconcile exact duplicate-group member identities | High |
| IR-R9 | Enable input snapshot reproducibility and run-to-input traceability | High |

## 8. Decisions and constraints

- This checkpoint closes the audit; it does not authorize code changes by itself.
- Confirmed loader safeguards and samples/splits mapping are carried forward.
- Do not claim full source integrity based on path/existence/readability checks.
- Actual byte-size verification, source fingerprinting, mutation detection, and snapshot controls remain implementation requirements.
- Duplicate-group exact member identity is not marked fully verified; retain it as a gap.
- No full hash of all 52,000 source files was required during this audit checkpoint.

## 9. Closure

**Checkpoint result: PASS WITH GAPS — CLOSED.**

Structural input readiness is confirmed for the examined metadata/split mapping and source-loader controls. Full input integrity and reproducibility are not yet established because actual byte-size checks, raw content fingerprints, mutation detection, immutable snapshot, and run traceability remain outstanding.

This record should be used as the baseline for implementation and preflight acceptance. Reopen only if new evidence reveals contradiction, regression, or a material integration risk.

---

## 10. Traceability

- Previous path/source integrity audit: I.9.2.6 — 3.3 Path & Source Integrity.
- Preflight config/path readiness: I.9.2.6 — 3.4.2 Preflight Acceptance Contract.
- Current checkpoint: I.9.2.6 — 3.4.3 Input & Metadata Readiness.
- Next checkpoint: I.9.2.6 — 3.4.4 Output / Write Permission / Collision Checks.


---

# I.9.2.6 — Step 3.2.3 Duplicate Detector & Input Integrity Audit

**Checkpoint:** 3.2.3  
**Status:** PASS WITH GAPS  
**Scope:** `src/data/duplicate_detector.py`  
**Mode:** Audit only; no repository code changes.

## Confirmed implementation evidence
- Exact duplicate detection uses SHA-256.
- Hashing reads files in binary streaming chunks of 1 MiB.
- File-read `OSError` is wrapped in `DuplicateDetectionError`.
- Samples are grouped by content hash; groups with fewer than two samples are omitted.
- Hash group iteration is sorted; member sample IDs are sorted.
- Group IDs use `dup_` plus the first 16 hex characters of the content SHA-256.
- Source paths are resolved and checked for containment under the resolved source root.
- Source files must exist and be regular files before hashing.

## Audit matrix
| Area | Status | Evidence / gap |
|---|---|---|
| SHA-256 hashing | PASS | Binary file hashing |
| Streaming read | PASS | 1 MiB chunks |
| Exact duplicate detection | PASS | Grouped by content hash |
| Duplicate group size | PASS | Only groups with >=2 samples |
| Deterministic group order | PASS | Sorted hash entries |
| Deterministic member order | PASS | Sorted sample IDs |
| Group ID | PASS WITH GAPS | 16-hex prefix; no explicit collision guard |
| File existence | PASS | `is_file()` |
| Path containment | PASS | `resolve()` + `is_relative_to()` |
| Hash read failure | PASS | Wrapped as `DuplicateDetectionError` |
| Input schema | GAP | No upfront sample schema/type validation |
| Sample ID uniqueness | GAP | Duplicate IDs are not rejected; mapping may overwrite |
| Empty iterable | PASS WITH GAPS | Empty output possible; no explicit policy |
| Empty source file | PASS WITH GAPS | Hashable, but empty-source policy not enforced here |
| Symlink/path policy | GAP | Resolved escape is checked; no explicit symlink policy |
| Duplicate-group provenance | PASS WITH GAPS | Hash and IDs provided, no version/report provenance here |

## Gaps
- **DD-01 Sample ID uniqueness:** repeated IDs may overwrite entries in `sample_hashes` and create inconsistent group membership.
- **DD-02 Input schema:** missing keys or malformed record types can raise native exceptions.
- **DD-03 Empty source policy:** zero-byte files are hashable and not rejected at this layer.
- **DD-04 Source-root preflight:** root existence/type is not checked up front.
- **DD-05 Group-ID collision scope:** truncated hash group IDs have no explicit uniqueness check; full hash is retained as content authority.
- **DD-06 Metadata identity:** content hashing does not verify problem ID, filename, or other metadata consistency.
- **DD-07 Mutation race:** source files could change between hashing and later pipeline stages; no run-level source immutability/fingerprint mechanism is shown here.

## Research boundary
- Exact duplicates may be grouped atomically before source splitting.
- Near-duplicates are not automatically duplicate groups.
- Duplicate groups do not automatically become positive pairs.
- SHA-256 exact-content grouping is not semantic similarity detection.

## Conclusion
**PASS WITH GAPS.** Exact duplicate hashing and deterministic grouping are implemented with path containment and read-error handling. Input record validation, duplicate-ID protection, empty-source policy, root preflight, and source mutation/fingerprint guarantees remain open contract gaps.

No code changes were made.


---

# I.9.2.6 — Step 3.2.4 Input Contract Reconciliation & Closure

Date: 2026-11-22
Status: **APPROVED — DESIGN CLOSURE**

## Scope
Reconciled input contract findings from the audits of `variant_source_loader.py`, `metadata_generator.py`, and `duplicate_detector.py`. No code changes were made and no scientific baseline was altered.

## Approved classifications and policies

### Mandatory input integrity
- Reject empty/whitespace `sample_id` values.
- Reject duplicate `sample_id` values; loader and duplicate detector must independently guard their input.
- Validate metadata schema, required field presence, and types; malformed input is fatal with context.
- Metadata-to-split eligible sample identity must be exact: no missing, extra, or duplicate IDs.
- Reject source paths that escape the canonical source root.
- Source files must exist and be readable.
- Reject empty and whitespace-only source files.
- Metadata `file_size` must equal the exact on-disk byte size.
- Detect source mutation during a run using SHA-256 fingerprints; mutation is a fatal integrity condition.
- Duplicate detector rejects malformed records and duplicate IDs before hashing.

### Robustness requirements
- Validate CSV headers, duplicate header names, row shape, and required fields; diagnostics include context/row where available.
- Metadata generator publishes CSV atomically (temporary file then replace).
- Detect `sample_id` collisions, including collisions caused by nested paths sharing a filename stem.
- Full SHA-256 is authoritative; detect any truncated group-id collision.
- Remove ad hoc debug output and provide structured diagnostics.
- Empty eligible datasets fail preflight.

### Explicit policy decisions
- `status=failed` samples are excluded from eligible dataset but retained for diagnostics. A failed sample appearing in split files is a fatal contract violation.
- `source_path` is relative to a canonical source root; absolute paths are not accepted as metadata paths.
- Dataset v1 is C++ only (`cpp`), and language metadata must match the configured dataset language.
- Extra CSV columns are allowed, but required schema and fields are strict.
- Do not silently normalize valid IDs. Whitespace-only IDs are rejected; otherwise preserve the ID as given.
- `file_size` means exact file bytes, not character count.
- Empty or whitespace-only source text is rejected.
- Source SHA-256 fingerprints are captured and checked to detect mutation during the run; mutation fails closed.
- Input integrity failures are fatal; pipeline must not silently continue on incomplete or invalid input.
- Metadata generation is deterministic and atomic; ID collisions must be detected before export.

## Contract summary
1. Eligible inputs consist only of `status=success` records passing strict metadata, source, and integrity checks.
2. Split membership must be an exact one-to-one mapping over eligible IDs; failed records must not appear in split files.
3. IDs are nonempty, unique, and not silently normalized.
4. Sources are readable, nonempty, contained under the canonical root, and represented by relative paths.
5. File size and filename/path metadata are consistent with the actual source.
6. Language is configured and validated (`cpp` for current v1 baseline).
7. SHA-256 fingerprinting protects against within-run source mutation.
8. Duplicate detection only groups exact whole-file duplicates; it does not auto-create positive pairs or group near-duplicates.
9. CSV validation is strict for required structure while permitting non-conflicting extra columns.
10. Fail-closed input validation is mandatory.

## Scientific baseline unchanged
- Source-level stratified split remains 80/10/10 with fixed seed before variant and pair generation.
- Duplicate groups remain atomic across splits.
- Exact duplicates are not automatically converted into positive pairs.
- Near-duplicates are not automatically grouped.

## Next checkpoint
Proceed to **Step 3.3 — Path & Source Integrity Audit**. This is a design audit only; implementation is not authorized by this approval.


---

# I.9.2.6 — Step 3.3.2 Config Path & Root Resolution Audit
Date: 2026-11-22
Status: PASS WITH GAPS

## Scope
Audited source evidence supplied by user:
- `src/data/pair_generation_config.py`
- `src/data/variant_generation_cli.py`

## Confirmed findings

### Config path
- Default config path is relative: `config/pair_generation_config.json`.
- `Path(config_path).resolve()` resolves relative paths against the current working directory (CWD).
- Existence and file checks are performed after resolution.
- JSON parse errors are wrapped; root object is validated.

### Config-relative path resolution
- `resolve_path()` accepts absolute configured paths and resolves them directly.
- Relative configured paths are resolved from `self.config_path.parent.parent`, assuming the config is in a `config/` directory under the project root.
- No containment policy prevents relative traversal or absolute paths outside the inferred root.

### CLI paths
- CLI defaults for dataset, variants, registry, and report are relative to CWD.
- CLI validates only dataset-root existence and directory status.
- Metadata and splits paths are constructed under dataset root.
- `source_root` is assigned to `args.dataset_root`.
- Output paths are passed to the runner without canonicalization or collision/isolation validation in the audited CLI file.
- CLI does not import or use `PairGenerationConfig` in this file; path/seed configuration appears separately supplied here.
- CLI seed is passed independently to runner; config-seed alignment is not established by these two files.

## Gap classifications

### Mandatory contract gaps
- Root authority is not explicit/stable across invocation locations; CWD changes relative defaults.
- Config `resolve_path()` permits absolute paths and resolved relative paths outside inferred project root.
- CLI and config path semantics are separate authorities; consistency is not established.
- Output path containment/isolation and collision policy are not enforced by the CLI evidence audited.

### Robustness / policy gaps
- No canonicalization of CLI paths at argument-validation boundary.
- No explicit root identity or expected layout validation.
- Config root inference relies on config directory layout.
- Seed authority/alignment between CLI and config remains unresolved.

## Proposed closure policy
1. Define a single explicit project/root authority for pipeline execution; do not depend implicitly on CWD.
2. Canonicalize all CLI paths at the boundary.
3. Keep absolute paths allowed only where explicitly approved; document them and enforce output/input safety policy.
4. Resolve config-relative paths against the defined root, not a positional directory assumption.
5. Establish one authoritative seed source (CLI override policy vs config).
6. Enforce run output isolation and collision checks in orchestration/output contract.
7. Keep input source root distinct from output roots and verify all path roles.

## Status
PASS WITH GAPS. The existing config loader and CLI can resolve paths in predictable ways when launched from project root, but they do not yet establish a unified, CWD-independent root authority or safety policy. No implementation changes were made.


---

# I.9.2.6 — Step 3.3.3: Source Path Containment Audit

**Date:** 2026-11-22  
**Scope:** `src/data/variant_pipeline_orchestrator.py`, `src/data/variant_output_writer.py`  
**Status:** PASS WITH GAPS  
**Audit only:** No source code changes made.

## 1. Orchestrator findings

| Check | Evidence | Assessment |
|---|---|---|
| Resolve written variant path | `Path(source_path).resolve()` | PASS |
| Confirm written variant exists as file | `source_path.is_file()` | PASS |
| Hash variant file for registry | `registry.compute_sha256(source_path)` | PASS |
| Resolve original source path before registry storage | `Path(original_source_path).resolve()` | PASS WITH GAPS |
| Validate original source path containment under dataset root | Not present in this module | GAP; expected upstream validation/root authority must be confirmed |
| Validate source path freshness / detect mutation | Not visible in this module | GAP; deferred to source-mutation audit |

The orchestrator trusts the upstream `original_source_path` argument. Resolving it produces a canonical path but does not prove it belongs to an authorized source root.

## 2. Output writer findings

| Check | Evidence | Assessment |
|---|---|---|
| Canonicalize variants root | `Path(variants_root).resolve()` | PASS |
| Validate path components | `_SAFE_ID_PATTERN` | PASS |
| Validate variant ID shape | `_VARIANT_ID_PATTERN.fullmatch()` | PASS |
| Ensure variant ID maps to original sample ID | Regex captured ID comparison | PASS |
| Resolve output path | `.resolve()` | PASS |
| Check output containment | `output_path.is_relative_to(self.variants_root)` | PASS |
| Avoid overwriting existing output | Exclusive mode `open("xb")` | PASS |
| Create output directories | `mkdir(parents=True, exist_ok=True)` | PASS |
| Normalize newline characters | CRLF/CR normalized to LF | PASS |

## 3. Containment and symlink caveat

The resolved output path and containment check protect against path traversal and already-present symlink redirection that resolves outside `variants_root`. However, filesystem changes between the containment check, directory creation, and exclusive file opening may create a time-of-check/time-of-use race. This is a residual hardening concern, not evidence of a currently demonstrated exploit. The writer does not show a race-resistant directory/file creation strategy.

## 4. Cross-module reconciliation

- The writer has a clear canonical output root and containment check.
- The orchestrator resolves the original source path but does not enforce source-root containment itself.
- The previously audited source loader and duplicate detector perform root containment checks at their respective boundaries; the pipeline still needs a single approved root-authority contract and end-to-end validation that those guarantees remain connected.

## 5. Gaps and policy recommendations

1. Define the authoritative dataset/source root explicitly and pass it through the pipeline contract.
2. Validate the canonical original source path is contained under that root at a trusted boundary; do not rely on `resolve()` alone.
3. Preserve source-path identity and provenance in the run record/registry, with a clear absolute-versus-relative storage policy.
4. Keep output containment and no-overwrite guards; consider race-resistant filesystem operations if threat-model hardening requires it.
5. Reconcile source path validation with source hash/fingerprint checks in the forthcoming source mutation/TOCTOU audit.

## 6. Conclusion

**PASS WITH GAPS.** Output path containment, component validation, canonicalization, and exclusive creation are implemented in the writer. The orchestrator canonicalizes the original source path for registry storage but does not itself prove source-root containment. Residual TOCTOU hardening and source freshness are not established by these files and remain for later audit steps.

No implementation changes were made.


---

# I.9.2.6 — Step 3.3.4: Output Path Isolation & Collision Audit

**Date:** 2026-11-22  
**Scope:** `variant_registry.py`, `variant_generation_report.py`, `variant_generation_run_summary.py`  
**Audit mode:** Read-only; no implementation changes  
**Status:** PASS WITH GAPS

## 1. Variant Registry (`variant_registry.py`)

| Area | Evidence | Assessment |
|---|---|---|
| Registry path canonicalization | Constructor stores `Path(registry_path)` without resolving | GAP |
| Parent directory creation | `_atomic_write()` uses `mkdir(parents=True, exist_ok=True)` | PASS |
| Atomic replacement | Temporary file in registry parent, flush + `os.fsync`, then `os.replace` | PASS |
| Same-filesystem temporary | Temp file created in destination parent | PASS |
| Duplicate ID check | Reads existing records and checks variant ID before write | PASS for single-writer flow |
| Concurrent writer safety | No locking across read/check/append/replace | GAP |
| Lost-update prevention | Whole read-modify-write sequence is not atomic | GAP |
| Schema validation | Header and row keys validated | PASS |
| Source file/hash validation | File existence and hash verified before registering | PASS |

### Concurrency risk

`register()` performs read → duplicate check → append → atomic file replacement. Two processes can read the same old registry and each write a new snapshot; the later replacement can discard the earlier process's new record. `os.replace()` makes the replacement operation atomic at the file level, but it does not make the entire read-modify-write transaction concurrency-safe.

## 2. Variant Generation Report (`variant_generation_report.py`)

| Area | Evidence | Assessment |
|---|---|---|
| Output path canonicalization | `Path(output_path)` without resolve | GAP |
| Directory creation | Parent directory created | PASS |
| Temporary file uniqueness | `NamedTemporaryFile` in destination directory | PASS |
| Flush and fsync | Explicit flush and `os.fsync` | PASS |
| Atomic replacement | `os.replace(temp_path, output_path)` | PASS |
| Existing destination policy | Replacement can overwrite existing report | GAP |
| Per-run isolation | No run-specific path or collision policy shown in exporter | GAP |

Atomic export protects against exposing a partially written report, but does not prevent different runs from overwriting a shared destination.

## 3. Run Summary (`variant_generation_run_summary.py`)

| Area | Evidence | Assessment |
|---|---|---|
| Output path canonicalization | `Path(output_path)` without resolve | GAP |
| Parent directory creation | `mkdir(parents=True, exist_ok=True)` | PASS |
| Temporary file uniqueness | Fixed `output_path + .tmp` name | GAP |
| Atomic replacement | `temporary_path.replace(output_path)` | PASS WITH GAPS |
| Existing destination policy | Destination can be replaced | GAP |
| Concurrent export safety | No lock; fixed temporary name can collide | GAP |
| Per-run isolation | Not enforced in exporter | GAP |

### Concurrency risk

The summary exporter uses a predictable shared temporary path (e.g. `run_summary.json.tmp`). Concurrent runs targeting the same output can interfere with the temporary file and/or replace one another's final summary. The exact failure mode depends on timing and filesystem behavior.

## 4. Consolidated findings

- **Atomic file replacement is not run isolation.** Report and summary exporters can replace a shared destination.
- **Registry atomicity is narrower than transaction safety.** A single replace does not protect the full read/check/append/write transaction from concurrent writers.
- **Summary temp naming is collision-prone.** Its fixed `.tmp` path is not unique per export.
- **Output roots are not canonicalized at these component boundaries.** They accept path values without resolving them here.
- **Run-specific output ownership is not enforced by these files.** A run-level policy must prevent accidental shared destinations or define explicit overwrite behavior.

## 5. Contract proposals for later reconciliation

1. Canonicalize output destinations at the pipeline boundary.
2. Define run ID / output ownership and explicit collision behavior for artifacts.
3. Use unique temporary files for summary export, in the target directory.
4. Define registry concurrency policy: single-writer guarantee, process lock, or another transaction-safe mechanism. Do not assume atomic replace is sufficient.
5. Define overwrite policy separately for reports, summaries, registry, and variant source files.
6. Ensure failure cleanup does not delete another concurrent run's temporary file.

These are design recommendations for contract closure; this audit does not prescribe implementation or make changes to the repository.

## 6. Checkpoint conclusion

**PASS WITH GAPS.** Individual exporters have useful atomic-write safeguards, but output isolation, collision policy, registry concurrent-writer safety, and canonicalization are not fully enforced by the audited files. Carry these gaps into I.9.2.6 Step 3.3 reconciliation and closure.
