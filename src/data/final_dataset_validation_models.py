from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FinalDatasetValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class FinalDatasetValidationIssue:
    code: str
    message: str
    severity: FinalDatasetValidationStatus


@dataclass(frozen=True)
class FinalDatasetValidationReport:
    status: FinalDatasetValidationStatus
    total_pairs: int
    positive_count: int
    negative_count: int
    issues: tuple[FinalDatasetValidationIssue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.status, FinalDatasetValidationStatus):
            raise TypeError("status must be a FinalDatasetValidationStatus")

        if type(self.total_pairs) is not int or self.total_pairs < 0:
            raise ValueError("total_pairs must be a non-negative integer")

        if type(self.positive_count) is not int or self.positive_count < 0:
            raise ValueError("positive_count must be a non-negative integer")

        if type(self.negative_count) is not int or self.negative_count < 0:
            raise ValueError("negative_count must be a non-negative integer")

        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")

        if any(
            not isinstance(issue, FinalDatasetValidationIssue)
            for issue in self.issues
        ):
            raise TypeError(
                "issues must contain FinalDatasetValidationIssue instances"
            )