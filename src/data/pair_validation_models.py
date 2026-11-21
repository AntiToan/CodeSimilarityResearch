from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class PairValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass(frozen=True)
class PairValidationIssue:
    rule_id: str
    severity: ValidationSeverity
    message: str
    pair_id: str | None = None
    field: str | None = None
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")

        if not self.message.strip():
            raise ValueError("message must not be empty")

        if self.pair_id is not None and not self.pair_id.strip():
            raise ValueError("pair_id must not be empty")

        if self.field is not None and not self.field.strip():
            raise ValueError("field must not be empty")

        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("severity must be ValidationSeverity")

        if not isinstance(self.details, tuple):
            raise TypeError("details must be a tuple")

    @property
    def is_error(self) -> bool:
        return self.severity == ValidationSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == ValidationSeverity.WARNING


@dataclass(frozen=True)
class PairValidationResult:
    pair_id: str
    issues: tuple[PairValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        if not self.pair_id.strip():
            raise ValueError("pair_id must not be empty")

        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")

        for issue in self.issues:
            if not isinstance(issue, PairValidationIssue):
                raise TypeError(
                    "issues must contain PairValidationIssue instances"
                )

            if issue.pair_id is not None and issue.pair_id != self.pair_id:
                raise ValueError(
                    "issue pair_id must match result pair_id"
                )

    @property
    def error_count(self) -> int:
        return sum(issue.is_error for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.is_warning for issue in self.issues)

    @property
    def status(self) -> PairValidationStatus:
        if self.error_count > 0:
            return PairValidationStatus.FAIL

        if self.warning_count > 0:
            return PairValidationStatus.WARNING

        return PairValidationStatus.PASS

    @property
    def is_valid(self) -> bool:
        return self.status != PairValidationStatus.FAIL


@dataclass(frozen=True)
class PairValidationReport:
    validator_version: str
    pair_results: tuple[PairValidationResult, ...]

    def __post_init__(self) -> None:
        if not self.validator_version.strip():
            raise ValueError("validator_version must not be empty")

        if not isinstance(self.pair_results, tuple):
            raise TypeError("pair_results must be a tuple")

        pair_ids = [
            result.pair_id
            for result in self.pair_results
        ]

        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("pair_results contain duplicate pair_id")

        for result in self.pair_results:
            if not isinstance(result, PairValidationResult):
                raise TypeError(
                    "pair_results must contain PairValidationResult instances"
                )

    @classmethod
    def from_results(
        cls,
        results: Iterable[PairValidationResult],
        validator_version: str = "1.0.0",
    ) -> PairValidationReport:
        # Stable ordering for reproducible report output.
        ordered_results = tuple(
            sorted(results, key=lambda result: result.pair_id)
        )

        return cls(
            validator_version=validator_version,
            pair_results=ordered_results,
        )

    @property
    def total_pair_count(self) -> int:
        return len(self.pair_results)

    @property
    def valid_pair_count(self) -> int:
        return sum(result.is_valid for result in self.pair_results)

    @property
    def invalid_pair_count(self) -> int:
        return sum(
            result.status == PairValidationStatus.FAIL
            for result in self.pair_results
        )

    @property
    def error_count(self) -> int:
        return sum(result.error_count for result in self.pair_results)

    @property
    def warning_count(self) -> int:
        return sum(result.warning_count for result in self.pair_results)

    @property
    def pass_pair_count(self) -> int:
        return sum(
            result.status == PairValidationStatus.PASS
            for result in self.pair_results
        )

    @property
    def warning_pair_count(self) -> int:
        return sum(
            result.status == PairValidationStatus.WARNING
            for result in self.pair_results
        )

    @property
    def status(self) -> PairValidationStatus:
        if self.invalid_pair_count > 0:
            return PairValidationStatus.FAIL

        if self.warning_count > 0:
            return PairValidationStatus.WARNING

        return PairValidationStatus.PASS

    def to_dict(self) -> dict:
        return {
            "validator_version": self.validator_version,
            "status": self.status.value,
            "total_pair_count": self.total_pair_count,
            "valid_pair_count": self.valid_pair_count,
            "invalid_pair_count": self.invalid_pair_count,
            "pass_pair_count": self.pass_pair_count,
            "warning_pair_count": self.warning_pair_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }