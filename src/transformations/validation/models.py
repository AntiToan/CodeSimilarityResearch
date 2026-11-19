from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ValidationResult:
    validator_name: str
    status: ValidationStatus
    reason_codes: tuple[str, ...] = ()
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class VariantValidationReport:
    variant_id: str
    overall_status: ValidationStatus
    v1: ValidationResult
    v2: ValidationResult
    v3: ValidationResult

    @property
    def accepted(self) -> bool:
        return self.overall_status == ValidationStatus.PASS
