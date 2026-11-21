
from __future__ import annotations

from dataclasses import dataclass

from src.data.pair_candidate_partitioner import PairCandidatePartition
from src.data.pair_selection_models import PairSelectionConfig


@dataclass(frozen=True)
class PairLabelQuota:
    split: str
    candidate_positive_count: int
    candidate_negative_count: int
    target_positive_count: int
    target_negative_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.split, str) or not self.split.strip():
            raise ValueError("split must be a non-empty string")

        count_fields = (
            self.candidate_positive_count,
            self.candidate_negative_count,
            self.target_positive_count,
            self.target_negative_count,
        )

        if any(
            not isinstance(count, int) or isinstance(count, bool)
            for count in count_fields
        ):
            raise TypeError("quota counts must be integers")

        if any(count < 0 for count in count_fields):
            raise ValueError("quota counts cannot be negative")

        if self.target_positive_count > self.candidate_positive_count:
            raise ValueError(
                "target positive count cannot exceed candidates"
            )

        if self.target_negative_count > self.candidate_negative_count:
            raise ValueError(
                "target negative count cannot exceed candidates"
            )

    @property
    def target_count(self) -> int:
        return self.target_positive_count + self.target_negative_count

    @property
    def candidate_count(self) -> int:
        return (
            self.candidate_positive_count
            + self.candidate_negative_count
        )

    @property
    def unmet_positive_quota(self) -> int:
        return (
            self.candidate_positive_count
            - self.target_positive_count
        )

    @property
    def unmet_negative_quota(self) -> int:
        return (
            self.candidate_negative_count
            - self.target_negative_count
        )

    @property
    def is_balanced(self) -> bool:
        return (
            self.target_positive_count
            == self.target_negative_count
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "split": self.split,
            "candidate_positive_count": self.candidate_positive_count,
            "candidate_negative_count": self.candidate_negative_count,
            "target_positive_count": self.target_positive_count,
            "target_negative_count": self.target_negative_count,
            "target_count": self.target_count,
            "candidate_count": self.candidate_count,
            "unmet_positive_quota": self.unmet_positive_quota,
            "unmet_negative_quota": self.unmet_negative_quota,
            "is_balanced": self.is_balanced,
        }


class PairLabelQuotaPlanner:
    def plan(
        self,
        partition: PairCandidatePartition,
        config: PairSelectionConfig,
    ) -> tuple[PairLabelQuota, ...]:
        split_data = (
            (
                "train",
                partition.train_positive_count,
                partition.train_negative_count,
            ),
            (
                "validation",
                partition.validation_positive_count,
                partition.validation_negative_count,
            ),
            (
                "test",
                partition.test_positive_count,
                partition.test_negative_count,
            ),
        )

        quotas = []

        for split, positive_count, negative_count in split_data:
            if config.balance_labels:
                target_count = min(positive_count, negative_count)

                target_positive = target_count
                target_negative = target_count
            else:
                target_positive = positive_count
                target_negative = negative_count

            quotas.append(
                PairLabelQuota(
                    split=split,
                    candidate_positive_count=positive_count,
                    candidate_negative_count=negative_count,
                    target_positive_count=target_positive,
                    target_negative_count=target_negative,
                )
            )

        return tuple(quotas)
