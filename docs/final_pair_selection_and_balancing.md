# 2.7.4.2 — Final Pair Selection & Balancing Integration

## 1. Purpose

This document defines the strategy for selecting the final pair dataset from the assembled pair candidate pool.

The selection process integrates the previously defined pair generation, validation, sampling, and balancing strategies to produce a final dataset suitable for subsequent model training and evaluation.

The selection process must:

- Operate only on assembled and validated pair candidates.
- Preserve pair labels and pair identities.
- Maintain source-level split isolation.
- Balance positive and negative pairs where possible.
- Improve problem distribution and endpoint diversity.
- Ensure deterministic selection under a fixed configuration and seed.
- Report selection results and limitations transparently.

This checkpoint focuses exclusively on final pair selection and balancing integration.

It does not implement pair generation, variant generation, model training, or evaluation.

---

## 2. Input Data

The final selection process receives the following inputs:

| Input | Description |
|---|---|
| Assembled candidate pool | Validated positive and negative pair candidates |
| Pair schema | Approved pair record structure |
| Sample metadata | Sample IDs, problem IDs, source paths and related metadata |
| Source split assignments | Train, validation, and test assignments at source level |
| Label information | Positive and negative labels |
| Sampling configuration | Selection parameters and diversity preferences |
| Balancing configuration | Label balance and problem distribution preferences |
| Random seed | Seed used for deterministic selection |

The candidate pool must have passed the candidate assembly and validation checkpoint before selection begins.

The selection process must not generate new pairs or modify existing pair labels.

---

## 3. Split-wise Selection

Selection must be performed independently for each dataset split:

- Train
- Validation
- Test

Candidates belonging to one split must never be transferred to another split to improve balance.

The selection process must preserve the source-level split assignments established before pair generation.

For every selected pair:

- Both endpoints must belong to the same split.
- The pair must remain in its original split.
- Variants must inherit the split of their original source.
- No source may cross dataset splits through pair selection.

Selection must not reassign samples or pairs between splits.

---

## 4. Label Balancing Strategy

Positive and negative pair counts should be balanced independently within each split.

For split \(s\), let:

- \(P_s\): number of valid positive pair candidates.
- \(N_s\): number of valid negative pair candidates.

The target number of selected pairs per label is:

\[
Q_s = \min(P_s, N_s)
\]

Therefore:

\[
P_s^{selected} = N_s^{selected} = Q_s
\]

when sufficient valid candidates are available.

### 4.1 Selection Rules

- Select equal numbers of positive and negative pairs whenever feasible.
- Do not oversample existing pairs.
- Do not duplicate pairs to achieve balance.
- Do not create artificial pairs during balancing.
- Do not move candidates between splits.
- Preserve excess candidates in the assembled candidate pool.
- If a split lacks sufficient candidates for one label, select the maximum feasible number and report the resulting imbalance.

Label balance is a target, not a reason to violate pair validity.

---

## 5. Problem Distribution Balancing

Problem distribution should be improved where possible without imposing hard quotas.

The selection process should prefer:

- Relatively balanced representation of problem IDs.
- Reduced dominance by frequently occurring problems.
- Diverse problem combinations among negative pairs.
- Better coverage of available problems.

However, problem distribution is a soft optimization objective.

The selection process must not force the inclusion of invalid candidates or candidates that violate negative pair rules.

If the candidate pool does not provide sufficient diversity, the selection process should preserve pair integrity and report the limitation.

---

## 6. Endpoint Diversity

Endpoint diversity aims to reduce excessive usage of a small number of source samples.

The selection process should prefer candidates that:

- Use samples with lower pair-selection frequency.
- Introduce different endpoints when equivalent candidates are available.
- Reduce excessive concentration of pairs around a small number of samples.
- Improve endpoint coverage across the selected dataset.

### 6.1 Endpoint Usage

Endpoint usage frequency should be calculated for each source sample.

For a sample \(x\):

\[
F(x) = \text{number of selected pairs containing } x
\]

Selection should prefer lower-frequency endpoints when competing candidates have equivalent validity and priority.

No strict endpoint cap is imposed at this stage.

A hard cap may unnecessarily discard valid candidates and reduce dataset size. Endpoint frequency should instead be monitored and reported for empirical analysis.

---

## 7. Selection Priority

When selection objectives conflict, the following priority order must be respected:

1. Pair integrity and validity
2. Endpoint and pair diversity
3. Label balance
4. Problem distribution refinement

Higher-priority requirements must never be violated to satisfy a lower-priority objective.

For example, label balancing must not introduce invalid negative pairs, and problem balancing must not cause split leakage.

---

## 8. Selection Workflow

The final selection pipeline follows these steps:

1. Load the assembled candidate pool.
2. Verify input schema and metadata.
3. Verify source-level split assignments.
4. Partition candidates by split.
5. Evaluate positive and negative candidate counts per split.
6. Apply label balancing targets.
7. Apply endpoint diversity preferences.
8. Refine problem distribution where feasible.
9. Select final pairs using deterministic selection rules.
10. Normalize final pair records.
11. Validate the selected dataset.
12. Generate selection reports.
13. Export final selected pairs and split indexes.

Candidate selection and final validation must remain separate stages.

Selection must not silently modify candidate metadata or labels.

---

## 9. Determinism and Reproducibility

The selection process must be reproducible under the same inputs and configuration.

Determinism requirements:

- Fixed random seed.
- Fixed selection configuration.
- Stable candidate ordering.
- Stable priority rules.
- Seeded random tie-breaking only when necessary.
- No dependence on filesystem ordering.
- No dependence on input arrival order.
- No uncontrolled randomness.

The same candidate pool, configuration, and seed must produce the same selected pair dataset.

The selection process must record enough information to reproduce a selection run.

---

## 10. Candidate Preservation

Selection must not destroy or overwrite the assembled candidate pool.

The candidate pool and selected dataset are distinct artifacts.

The assembled pool contains candidates that passed the assembly stage, while the selected dataset contains the subset chosen for downstream use.

Unselected candidates must remain available for:

- Future selection experiments.
- Alternative balancing configurations.
- Sampling strategy comparisons.
- Dataset analysis.

Selection should record selected and unselected candidate counts.

---

## 11. Final Dataset Validation

After selection, the resulting dataset must undergo independent validation.

### 11.1 Structural Validation

Verify:

- Required fields exist.
- Pair IDs are valid.
- Sample references exist.
- Pair records follow the approved schema.
- Pair identity is canonical.
- No self-pairs exist.

### 11.2 Label Validation

Verify:

- Positive pairs have label `1` and type `positive`.
- Negative pairs have label `0` and type `negative`.
- No conflicting labels exist for the same canonical pair.

### 11.3 Split Validation

Verify:

- Each pair belongs to exactly one split.
- Both endpoints belong to the same split.
- Source-level split assignments are preserved.
- No source-level leakage exists across train, validation, and test.

### 11.4 Selection Validation

Verify:

- Every selected pair belongs to the assembled candidate pool.
- No duplicate pairs exist in the selected dataset.
- No pairs were created during selection.
- No labels were modified.
- Selected pair counts match reported counts.

### 11.5 Balance and Diversity Validation

Report:

- Positive and negative pair counts.
- Label ratio for each split.
- Problem distribution.
- Endpoint frequency distribution.
- Number of unique endpoints.
- Duplicate pair count.
- Split distribution.

Integrity violations must cause the finalization process to fail.

Balance and diversity limitations should generate warnings rather than invalidate otherwise correct pairs.

---

## 12. Output Artifacts

The selection stage produces the following artifacts.

| Artifact | Purpose |
|---|---|
| `assembled_candidates.csv` | Intermediate assembled candidate pool |
| `selected_pairs.csv` | Final selected pair records |
| `train.csv` | Training split index |
| `validation.csv` | Validation split index |
| `test.csv` | Test split index |
| `selection_report.json` | Selection statistics and reproducibility information |

The proposed intermediate paths are:

```text
data/
└── pairs/
    ├── candidates/
    │   └── assembled_candidates.csv
    ├── selected/
    │   └── selected_pairs.csv
    ├── splits/
    │   ├── train.csv
    │   ├── validation.csv
    │   └── test.csv
    └── reports/
        └── selection_report.json
```

The canonical pair schema and split-index conventions must remain consistent with the previously approved Phase 2.5 output design.

The candidate and selected artifacts are intermediate/final selection products and must not introduce a conflicting pair schema or split structure.

---

## 13. Selection Report

The selection report should contain the following information.

### 13.1 Input Statistics

- Total assembled candidates.
- Positive candidates.
- Negative candidates.
- Candidate counts by split.
- Invalid candidates, if any were rejected during selection checks.

### 13.2 Selected Statistics

- Total selected pairs.
- Selected positive pairs.
- Selected negative pairs.
- Selected counts by split.
- Label balance per split.

### 13.3 Distribution Statistics

- Problem distribution.
- Endpoint usage frequency.
- Unique endpoint count.
- Pair diversity statistics.
- Duplicate count.

### 13.4 Reproducibility Metadata

- Selection seed.
- Configuration version.
- Selection strategy version.
- Input artifact reference.
- Run identifier.

The report must reflect actual selection results rather than target values.

---

## 14. Insufficient Candidate Handling

If the candidate pool does not contain enough valid candidates to achieve the desired selection targets:

- Do not generate additional pairs during selection.
- Do not oversample existing pairs.
- Do not transfer pairs between splits.
- Do not force invalid candidates into the final dataset.
- Select the maximum feasible number of valid pairs.
- Report shortages and resulting imbalance.

The selection stage must be conservative.

Dataset size may be reduced when candidate validity and split integrity require it.

---

## 15. Acceptance Criteria

This checkpoint is considered complete when the final pair selection strategy satisfies the following requirements:

- Selection operates exclusively on assembled candidate pairs.
- Pair labels and identities are preserved.
- Train, validation, and test are selected independently.
- Source-level split integrity is maintained.
- Label balance is applied per split where feasible.
- No oversampling or duplicate pairs are introduced.
- Problem distribution is improved where feasible.
- Endpoint diversity is considered.
- Pair integrity takes priority over balancing.
- Selection is reproducible with a fixed seed and configuration.
- Candidate pools remain preserved.
- Insufficient candidates are handled conservatively.
- A selection report is generated.
- The selected dataset undergoes independent final validation.

---

## 16. Scope Boundary

This checkpoint defines the strategy for integrating candidate assembly with final pair selection and balancing.

It does not define:

- Positive pair generation.
- Negative pair generation.
- Transformation generation.
- Source splitting implementation.
- Model architecture.
- Model training.
- Model evaluation.
- Similarity inference.

These topics belong to their respective checkpoints.

---

## 17. Conclusion

The final pair selection stage transforms a validated candidate pool into a usable pair dataset while preserving pair validity, label integrity, and source-level split isolation.

Balancing and diversity are optimization objectives rather than absolute requirements.

The final dataset must prioritize valid, reproducible, and leakage-free pairs over artificially satisfying numerical targets.

The resulting selected pair dataset will serve as the input artifact for subsequent dataset preparation and model training stages.
