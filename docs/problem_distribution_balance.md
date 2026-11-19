# Problem Distribution Balance

## 1. Objective

This checkpoint defines the strategy for balancing pair distributions across the 104 programming problems in POJ-104.

The objective is to reduce problem-level sampling bias, improve problem diversity, and avoid excessive representation of a small subset of problems in the pair dataset.

## 2. Dataset Context

- Total problems: 104
- Original samples per problem: 500
- Positive pairs are primarily generated from the same source and its controlled variants.
- Negative pairs are sampled from different problems.

Although the original dataset is balanced at the sample level, pair generation can introduce problem-level imbalance.

## 3. Selected Strategy

The project adopts hierarchical / stratified problem sampling with soft balancing.

Sampling is performed with problem distribution considered as a priority, while pair validity and availability remain the primary constraints.

## 4. Positive Pair Distribution

Positive pair sampling must:

- Prioritize relatively uniform representation across the 104 problems.
- Select valid positive pairs within each problem.
- Avoid allowing problems with many variants to dominate the positive pair dataset.
- Accept lower counts for problems with fewer valid positive candidates.

No invalid positive pairs will be created to satisfy problem-level quotas.

## 5. Negative Pair Distribution

Negative pair sampling must:

- Distribute anchors across the 104 problems.
- Select negative samples from different problems than the anchor.
- Prioritize distinct negative problem IDs for the negative pairs associated with an anchor.
- Avoid repeatedly selecting a small subset of problems as negative endpoints.
- Track problem appearances across both pair endpoints.

## 6. Soft Balance Policy

Problem-level balance is a priority, not a strict quota.

- No mandatory fixed pair count per problem.
- Problems with insufficient valid pairs may contribute fewer pairs.
- Excess candidates may be sampled using controlled selection.
- Invalid pairs must never be forced into the dataset.
- Pair validity and diversity take priority over perfect uniformity.

## 7. Distribution Audit

The pair generation and balancing process must record problem-level statistics, including:

- Positive pair counts per problem.
- Negative pair counts per anchor problem.
- Negative endpoint appearances per problem.
- Minimum, maximum, mean, and median problem representation.
- Problems with unusually low or high pair representation.
- Distribution imbalance observations.

Negative endpoint appearances count a problem each time it appears as either endpoint of a negative pair.

## 8. Reproducibility

Problem-level sampling must be reproducible using a fixed random seed.

The same candidate pool, configuration, and seed should produce the same selected pair distribution.

## 9. Constraints

- No hard quota requiring invalid pairs.
- No duplicate pairs.
- No same-problem negative pairs under the current negative sampling policy.
- No pair crossing train, validation, or test splits.
- Problem balancing must not modify original source code or candidate records.
- Candidate pairs that are not selected must remain available in the candidate pool when applicable.

## 10. Expected Outcome

The resulting dataset should maintain broad coverage across POJ-104 problems, reduce excessive problem concentration, and preserve pair validity and diversity.

This checkpoint defines the problem distribution balancing strategy only. Implementation and actual pair generation will occur in later checkpoints.
