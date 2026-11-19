# Balance Constraints & Trade-offs

## 1. Objective

This checkpoint defines the constraints, priorities, and trade-offs applied during pair dataset balancing.

The goal is to preserve pair validity, dataset integrity, and diversity while maintaining reasonable label and problem distributions.

## 2. Priority Order

Pair selection follows this priority order:

1. Pair validity and dataset integrity.
2. Pair diversity.
3. Label balance.
4. Problem distribution balance.

Higher-priority constraints must not be violated to satisfy lower-priority balancing objectives.

## 3. Mandatory Constraints

The following conditions are mandatory:

- Positive and negative pairs must follow their respective generation rules.
- Negative pairs must come from different problems.
- Negative pairs must not share source lineage.
- Duplicate pairs must not be included.
- No pair may cross train, validation, or test splits.
- Original source files and candidate records must not be modified or deleted by balancing.
- Pair validity must not be compromised to achieve a target dataset size.

## 4. Soft Constraints

The following objectives are soft constraints:

- Positive-to-negative ratio of 1:1.
- Relatively uniform distribution across the 104 problems.
- Source appearance frequency.
- Negative endpoint diversity.

These objectives should be pursued whenever feasible but must not override mandatory constraints.

## 5. Source Frequency Control

A source may appear in multiple valid pairs. However, excessive source reuse can reduce dataset diversity and increase the risk of source-specific bias.

The balancing process must:

- Track pair appearances per sample ID.
- Monitor sources with unusually high appearance frequencies.
- Prefer less frequently used sources when competing candidates are equally valid.
- Avoid setting a hard source appearance cap before actual pair distribution is audited.

A source frequency cap may be considered in a future experiment if empirical evidence justifies it.

## 6. Insufficient Candidate Handling

When the available valid candidates cannot satisfy a balancing target:

1. Search remaining valid candidates within the defined sampling constraints.
2. Perform bounded resampling if applicable.
3. Record the unmet quota and its reason.
4. Accept a smaller dataset when valid candidates remain insufficient.

Invalid candidates must not be introduced to meet a quota.

## 7. Balancing Trade-offs

The project accepts the following trade-offs:

- A smaller dataset is acceptable when valid candidates are insufficient.
- Imperfect label balance is acceptable when the available valid pairs are limited.
- Imperfect problem balance is acceptable when a problem has insufficient valid candidates.
- Pair diversity is preferred over excessive reuse of the same source.
- Pair validity and integrity take priority over all balancing objectives.

## 8. Audit and Reporting

The balancing process must report:

- Pair counts before and after filtering.
- Pair counts before and after balancing.
- Positive and negative counts.
- Duplicate pairs removed.
- Problem-level distribution.
- Source appearance frequency.
- Sampling seed and configuration.
- Unmet quotas.
- Reasons for constraints or targets not being satisfied.

## 9. Reproducibility

Balancing must be reproducible using the recorded candidate pool, configuration, and random seed.

All sampling and balancing decisions must be traceable through the generated reports.

## 10. Expected Outcome

The final pair dataset should prioritize validity, integrity, and diversity while maintaining a balanced label distribution and broad problem coverage where feasible.

This checkpoint defines constraints and trade-offs only. Implementation will be performed in a later checkpoint.
