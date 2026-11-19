# 2.7.4.3 — Pair Generation Pipeline Integration & Orchestration Design

## 1. Purpose

This document defines the orchestration strategy for integrating the previously designed pair generation, candidate assembly, validation, selection, and balancing components into a unified Pair Generation Pipeline.

The pipeline must:

- Execute pair generation stages in a controlled order.
- Enforce stage dependencies.
- Maintain data integrity between stages.
- Prevent invalid intermediate results from reaching final dataset export.
- Support reproducible pipeline runs.
- Track execution status and failures.
- Preserve intermediate artifacts for auditing.
- Produce a final dataset and pipeline run report.

This checkpoint focuses exclusively on pipeline integration and orchestration design.

It does not implement the pipeline or modify the algorithms defined in previous checkpoints.

---

## 2. Pipeline Overview

The Pair Generation Pipeline consists of the following stages:

1. Load input data and configuration.
2. Verify metadata and source split assignments.
3. Generate positive pair candidates.
4. Generate negative pair candidates.
5. Assemble pair candidates.
6. Validate assembled candidates.
7. Perform final pair selection and balancing.
8. Validate the final selected dataset.
9. Export the final dataset and split indexes.
10. Generate the pipeline run report.

The pipeline must execute stages in the defined order and ensure that each stage receives valid inputs from its required dependencies.

---

## 3. Pipeline Stage Definitions

| Stage | Responsibility | Expected Output |
|---|---|---|
| Input Preparation | Load inputs and configuration | Loaded input artifacts |
| Metadata & Split Verification | Validate metadata and split consistency | Verification result |
| Positive Generation | Generate positive pair candidates | Positive candidate pool |
| Negative Generation | Generate negative pair candidates | Negative candidate pool |
| Candidate Assembly | Combine and normalize candidates | Assembled candidate pool |
| Candidate Validation | Validate candidate integrity | Validation report and valid pool |
| Final Selection | Select pairs and apply balancing | Selected pair dataset |
| Final Validation | Independently validate final dataset | Final validation report |
| Export | Export final dataset and split indexes | Final artifacts |
| Run Reporting | Summarize pipeline execution | Pipeline run report |

Each stage must have a clearly defined responsibility and must not silently perform the responsibilities of another stage.

---

## 4. Stage Dependency Strategy

The pipeline must respect stage dependencies.

### 4.1 Execution Dependencies

- Input preparation must complete before metadata and split verification.
- Metadata and split verification must pass before pair generation.
- Positive and negative generation must use the same approved split assignments.
- Candidate assembly must receive positive and negative candidate outputs.
- Candidate validation must pass before final selection.
- Final selection must operate only on validated assembled candidates.
- Final validation must pass before final export.
- Run reporting must record the results of all executed stages.

### 4.2 Dependency Integrity

A stage must not execute when its required upstream stage has failed or produced invalid output.

The pipeline must not:

- Perform final selection on an invalid candidate pool.
- Export an invalid final dataset.
- Reassign pairs or sources between splits.
- Modify pair labels during orchestration.
- Bypass validation stages to force pipeline completion.

---

## 5. Stage Contract

Every pipeline stage must define the following components.

### 5.1 Input Contract

Defines the required inputs, metadata, configuration, and upstream artifacts needed for execution.

### 5.2 Processing Responsibility

Defines the operations that the stage is permitted to perform.

Each stage must remain within its designated scope.

### 5.3 Output Contract

Defines the expected output artifacts, structure, and status.

Downstream stages must rely only on outputs that satisfy the relevant contract.

### 5.4 Failure Conditions

Defines the conditions under which a stage is considered unsuccessful.

A failed stage must not be treated as a successful stage merely because some intermediate files were created.

---

## 6. Failure Handling Strategy

The pipeline follows a fail-safe execution strategy.

### 6.1 Failure Classification

| Failure Type | Handling |
|---|---|
| Missing input | Stop pipeline |
| Invalid metadata | Stop pipeline |
| Invalid split assignments | Stop pipeline |
| Generation stage failure | Mark run as failed |
| Candidate-level rejection | Reject candidate and record statistics |
| Assembly integrity failure | Stop pipeline |
| Selection failure | Stop finalization |
| Final validation failure | Prohibit final export |
| Report generation failure | Record incomplete run |

### 6.2 Critical Failures

Critical failures invalidate the pipeline run.

The pipeline must not silently ignore critical errors or continue exporting a final dataset when its integrity is no longer guaranteed.

Candidate-level rejection is different from pipeline-level failure. Individual invalid candidates may be rejected while the stage continues, provided the stage itself completes according to its validation rules.

---

## 7. Pipeline Run Management

Each execution must be treated as an independent pipeline run.

### 7.1 Run Metadata

Each run must record:

- `run_id`
- `created_at`
- `seed`
- `config_version`
- `pipeline_version`
- Input artifact references
- Run status

### 7.2 Run Status

The pipeline uses the following run states:

| Status | Description |
|---|---|
| `PENDING` | Run initialized but not started |
| `RUNNING` | Pipeline stages are executing |
| `COMPLETED` | All required stages completed successfully and final artifacts passed validation |
| `FAILED` | Pipeline terminated due to a critical failure |

A run must not be marked `COMPLETED` if required stages failed, final validation failed, or final artifacts were not successfully produced.

The existence of intermediate artifacts alone does not indicate successful completion.

---

## 8. Intermediate Artifacts and Final Artifacts

Pipeline artifacts must be divided into two categories.

### 8.1 Intermediate Artifacts

Intermediate artifacts may include:

- Positive candidate pool.
- Negative candidate pool.
- Assembled candidate pool.
- Candidate validation results.
- Selection statistics.
- Intermediate stage reports.

These artifacts support auditing, debugging, and reproducibility.

They must not be mistaken for the final training dataset.

### 8.2 Final Artifacts

Final artifacts may include:

- Final selected pair dataset.
- Train split index.
- Validation split index.
- Test split index.
- Final validation report.
- Pipeline run report.

Final artifacts are considered valid only after the final validation stage passes.

Artifact paths and naming conventions must remain consistent with the previously approved Phase 2.5 and Phase 2.7.4.2 output designs.

This checkpoint does not introduce a competing output schema or split structure.

---

## 9. Re-run and Reproducibility Strategy

The pipeline must support controlled reruns without affecting previous completed runs.

### 9.1 Reproducibility Requirements

- Use a fixed seed recorded for each run.
- Record the pipeline and configuration versions.
- Use stable ordering for inputs and candidates.
- Avoid filesystem-order-dependent behavior.
- Avoid uncontrolled randomness.
- Use seeded random tie-breaking only when required.
- Ensure identical inputs, configuration, seed, and pipeline version can reproduce the same outputs.

### 9.2 Rerun Policy

Each rerun must create an independent run record.

The pipeline must not silently overwrite artifacts belonging to a previously completed run.

By default, a failed run should be rerun from the beginning rather than resumed from an arbitrary stage.

Stage-level resume is deferred because reusing intermediate artifacts without complete dependency verification may compromise reproducibility and data integrity.

---

## 10. Pipeline Run Report

Each pipeline execution must generate a report describing its actual execution.

### 10.1 Run Information

- Run ID.
- Creation time.
- Seed.
- Configuration version.
- Pipeline version.
- Final status.

### 10.2 Input Information

- Input metadata references.
- Split assignments.
- Input artifact references.
- Input verification results.

### 10.3 Stage Information

- Stage name.
- Execution status.
- Stage output references.
- Error information, if applicable.
- Warnings.
- Candidate counts where applicable.

### 10.4 Generation Information

- Positive candidate statistics.
- Negative candidate statistics.
- Accepted and rejected candidate counts.
- Rejection statistics.

### 10.5 Assembly and Selection Information

- Assembled candidate counts.
- Duplicate statistics.
- Invalid candidate counts.
- Selected and unselected pair counts.
- Label balance.
- Problem distribution.
- Endpoint diversity statistics.

### 10.6 Final Validation and Export

- Final validation status.
- Pair counts by split.
- Positive and negative counts per split.
- Exported artifact paths.
- Export status.

The report must reflect actual execution results rather than target values or expected counts.

---

## 11. Pipeline Execution Workflow

The complete pipeline follows this workflow:

1. Initialize a new pipeline run.
2. Load configuration and input artifacts.
3. Validate input metadata and split assignments.
4. Generate positive pair candidates.
5. Generate negative pair candidates.
6. Assemble positive and negative candidates.
7. Validate the assembled candidate pool.
8. Perform final pair selection and balancing.
9. Validate the final selected pair dataset.
10. Export final dataset artifacts.
11. Generate the pipeline run report.
12. Mark the run as completed only if all required stages succeed.

If a critical stage fails, the pipeline must stop the dependent stages and mark the run as failed.

Candidate-level rejection does not necessarily invalidate the entire pipeline run if the candidate processing stage completes successfully and the resulting pool satisfies the required integrity conditions.

---

## 12. Output Consistency

The pipeline must maintain consistency between:

- Assembled candidate pool.
- Selected pair records.
- Pair IDs.
- Train, validation, and test indexes.
- Pair labels.
- Sample references.
- Source split assignments.
- Selection reports.
- Pipeline run reports.

The final split indexes must reference the selected pair dataset correctly.

The pipeline must not create inconsistent pair IDs, missing references, duplicate records, or conflicting split assignments during orchestration.

Output path conventions will be consolidated with the previously approved pair generation output design before implementation.

---

## 13. Scope Boundary

This checkpoint defines the orchestration strategy for the Pair Generation Pipeline.

It does not define or implement:

- Variant generation algorithms.
- Positive pair generation algorithms.
- Negative pair generation algorithms.
- Pair sampling algorithms.
- Candidate assembly implementation.
- Validation implementation.
- Final selection implementation.
- Python package architecture.
- Model architecture.
- Model training.
- Model evaluation.
- Inference.

These responsibilities belong to their respective checkpoints or later implementation phases.

---

## 14. Acceptance Criteria

This checkpoint is considered complete when the pipeline orchestration design satisfies the following criteria:

- [ ] All required pipeline stages are identified.
- [ ] Stage execution order is defined.
- [ ] Stage dependencies are defined.
- [ ] Input and output contracts are specified.
- [ ] Stage responsibilities are clearly separated.
- [ ] Critical failure handling is defined.
- [ ] Candidate-level rejection is distinguished from pipeline-level failure.
- [ ] Run status management is defined.
- [ ] Intermediate and final artifacts are distinguished.
- [ ] Reproducibility requirements are defined.
- [ ] Rerun policy is defined.
- [ ] Pipeline reporting requirements are defined.
- [ ] Final export is protected by validation.
- [ ] Output conventions remain consistent with previous checkpoints.

---

## 15. Conclusion

The Pair Generation Pipeline Orchestration stage integrates the previously designed pair generation, candidate assembly, validation, selection, and balancing components into a single controlled workflow.

The pipeline must prioritize integrity, reproducibility, stage dependency enforcement, and transparent reporting.

A pipeline run is considered successful only when all required stages complete correctly, final validation passes, and final artifacts are successfully produced.

This design establishes the orchestration foundation for the future implementation of the Pair Generation Pipeline.
