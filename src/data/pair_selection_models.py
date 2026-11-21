
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class PairSelectionStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class PairSelectionConfig:
    seed: int = 42
    balance_labels: bool = True
    prefer_endpoint_diversity: bool = True
    prefer_problem_balance: bool = True
    selector_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")

        if not isinstance(self.balance_labels, bool):
            raise TypeError("balance_labels must be a boolean")

        if not isinstance(self.prefer_endpoint_diversity, bool):
            raise TypeError(
                "prefer_endpoint_diversity must be a boolean"
            )

        if not isinstance(self.prefer_problem_balance, bool):
            raise TypeError(
                "prefer_problem_balance must be a boolean"
            )

        if not self.selector_version.strip():
            raise ValueError("selector_version must not be empty")


@dataclass(frozen=True)
class PairSelectionResult:
    selected_pairs: tuple[Any, ...]
    positive_count: int
    negative_count: int
    total_count: int
    selection_status: PairSelectionStatus

    def __post_init__(self) -> None:
        if not isinstance(self.selected_pairs, tuple):
            raise TypeError("selected_pairs must be a tuple")

        if self.positive_count < 0:
            raise ValueError("positive_count cannot be negative")

        if self.negative_count < 0:
            raise ValueError("negative_count cannot be negative")

        if self.total_count < 0:
            raise ValueError("total_count cannot be negative")

        if self.total_count != len(self.selected_pairs):
            raise ValueError(
                "total_count must equal the number of selected pairs"
            )

        if self.positive_count + self.negative_count != self.total_count:
            raise ValueError(
                "positive_count + negative_count must equal total_count"
            )

        if not isinstance(self.selection_status, PairSelectionStatus):
            raise TypeError(
                "selection_status must be PairSelectionStatus"
            )


@dataclass(frozen=True)
class SplitSelectionStats:
    split: str
    candidate_positive_count: int
    candidate_negative_count: int
    target_positive_count: int
    target_negative_count: int
    selected_positive_count: int
    selected_negative_count: int
    unmet_positive_quota: int
    unmet_negative_quota: int

    def __post_init__(self) -> None:
        if not self.split.strip():
            raise ValueError("split must not be empty")

        count_fields = (
            self.candidate_positive_count,
            self.candidate_negative_count,
            self.target_positive_count,
            self.target_negative_count,
            self.selected_positive_count,
            self.selected_negative_count,
            self.unmet_positive_quota,
            self.unmet_negative_quota,
        )

        if any(count < 0 for count in count_fields):
            raise ValueError("selection counts cannot be negative")

        if self.target_positive_count > self.candidate_positive_count:
            raise ValueError(
                "target_positive_count cannot exceed candidate positives"
            )

        if self.target_negative_count > self.candidate_negative_count:
            raise ValueError(
                "target_negative_count cannot exceed candidate negatives"
            )

        if self.selected_positive_count > self.target_positive_count:
            raise ValueError(
                "selected_positive_count cannot exceed target_positive_count"
            )

        if self.selected_negative_count > self.target_negative_count:
            raise ValueError(
                "selected_negative_count cannot exceed target_negative_count"
            )

        if self.unmet_positive_quota != max(
            0, self.target_positive_count - self.selected_positive_count
        ):
            raise ValueError(
                "unmet_positive_quota does not match target and selected counts"
            )

        if self.unmet_negative_quota != max(
            0, self.target_negative_count - self.selected_negative_count
        ):
            raise ValueError(
                "unmet_negative_quota does not match target and selected counts"
            )

    @property
    def candidate_count(self) -> int:
        return (
            self.candidate_positive_count
            + self.candidate_negative_count
        )

    @property
    def selected_count(self) -> int:
        return (
            self.selected_positive_count
            + self.selected_negative_count
        )

    @property
    def unmet_quota_count(self) -> int:
        return (
            self.unmet_positive_quota
            + self.unmet_negative_quota
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "candidate_positive_count": self.candidate_positive_count,
            "candidate_negative_count": self.candidate_negative_count,
            "candidate_count": self.candidate_count,
            "target_positive_count": self.target_positive_count,
            "target_negative_count": self.target_negative_count,
            "selected_positive_count": self.selected_positive_count,
            "selected_negative_count": self.selected_negative_count,
            "selected_count": self.selected_count,
            "unmet_positive_quota": self.unmet_positive_quota,
            "unmet_negative_quota": self.unmet_negative_quota,
            "unmet_quota_count": self.unmet_quota_count,
        }


@dataclass(frozen=True)
class PairSelectionReport:
    selector_version: str
    seed: int
    split_stats: tuple[SplitSelectionStats, ...]

    def __post_init__(self) -> None:
        if not self.selector_version.strip():
            raise ValueError("selector_version must not be empty")

        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")

        if not isinstance(self.split_stats, tuple):
            raise TypeError("split_stats must be a tuple")

        for stats in self.split_stats:
            if not isinstance(stats, SplitSelectionStats):
                raise TypeError(
                    "split_stats must contain SplitSelectionStats instances"
                )

        splits = [stats.split for stats in self.split_stats]

        if len(splits) != len(set(splits)):
            raise ValueError("split_stats contain duplicate split names")

    @classmethod
    def from_stats(
        cls,
        stats: Iterable[SplitSelectionStats],
        seed: int,
        selector_version: str = "1.0.0",
    ) -> PairSelectionReport:
        ordered_stats = tuple(sorted(stats, key=lambda item: item.split))

        return cls(
            selector_version=selector_version,
            seed=seed,
            split_stats=ordered_stats,
        )

    @property
    def total_candidate_count(self) -> int:
        return sum(stats.candidate_count for stats in self.split_stats)

    @property
    def total_selected_count(self) -> int:
        return sum(stats.selected_count for stats in self.split_stats)

    @property
    def total_unmet_quota_count(self) -> int:
        return sum(stats.unmet_quota_count for stats in self.split_stats)

    @property
    def status(self) -> PairSelectionStatus:
        if self.total_unmet_quota_count > 0:
            return PairSelectionStatus.WARNING

        return PairSelectionStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "selector_version": self.selector_version,
            "seed": self.seed,
            "status": self.status.value,
            "total_candidate_count": self.total_candidate_count,
            "total_selected_count": self.total_selected_count,
            "total_unmet_quota_count": self.total_unmet_quota_count,
            "split_stats": [
                stats.to_dict()
                for stats in self.split_stats
            ],
        }
