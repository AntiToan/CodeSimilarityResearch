# Label Balance Strategy

## 1. Objective

This checkpoint defines the label balancing strategy for the code similarity pair dataset. The objective is to reduce class imbalance between positive and negative pairs while preserving pair validity, diversity, and reproducibility.

## 2. Label Definition

- Label 1: Positive pair — two code samples considered similar according to the defined positive pair generation strategy.
- Label 0: Negative pair — two code samples considered dissimilar according to the defined negative pair generation strategy.

## 3. Target Label Ratio

The primary dataset targets a 1:1 ratio between positive and negative pairs.

| Label | Target proportion |
|---|---:|
| Positive (1) | 50% |
| Negative (0) | 50% |

This ratio is the target for the balanced dataset, not a requirement to generate invalid pairs to achieve it.

## 4. Balancing Rule

Let:

- P = number of valid positive pairs available.
- N = number of valid negative pairs available.

The balancing quota is:

Q = min(P, N)

The final balanced dataset will contain:

- Q positive pairs
- Q negative pairs

The total dataset size will therefore be 2Q.

## 5. Excess Pair Handling

When one class contains more valid pairs than the other:

- The excess pairs will not be deleted from the original candidate pool.
- Only the required quota will be selected for the primary balanced dataset.
- Excess pairs may be retained for future experiments involving alternative sampling or balancing strategies.

## 6. Insufficient Pair Handling

If one class does not contain enough valid pairs:

- The final dataset size will be reduced according to the smaller class.
- No invalid pairs will be introduced to meet the target quota.
- No default oversampling will be applied.
- Pair validity and quality take priority over dataset size.

## 7. Reproducibility

Balancing must be deterministic and reproducible.

- A fixed random seed will be used when selecting pairs from an excess class.
- The selected pairs must be reproducible using the same candidate pool and seed.
- Balancing statistics must be recorded.

## 8. Reporting Requirements

The balancing process must report:

- Positive pair count before balancing.
- Negative pair count before balancing.
- Number of positive pairs selected.
- Number of negative pairs selected.
- Number of excess pairs retained outside the balanced dataset.
- Final label distribution.
- Random seed used for selection.

## 9. Constraints

- Pair validity must not be compromised for balancing.
- No pair may cross train, validation, or test splits.
- Duplicate pairs must not be introduced.
- Balancing must not modify or delete original source code or candidate records.
- The balanced dataset must maintain a 1:1 label ratio whenever both classes contain valid candidates.

## 10. Expected Outcome

The primary pair dataset will have equal positive and negative pair counts, reducing label imbalance and providing a consistent baseline for model training and evaluation.

This checkpoint defines the strategy only. Pair selection and balancing implementation will be conducted in a later checkpoint.
