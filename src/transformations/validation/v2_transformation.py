
from __future__ import annotations

from src.transformations.base import Transformation
from src.transformations.validation.models import (
    ValidationResult,
    ValidationStatus,
)


class TransformationValidator:
    @property
    def name(self) -> str:
        return "V2_TRANSFORMATION"

    def validate(
        self,
        original: str,
        candidate: str,
        transformation: Transformation,
        seed: int | None = None,
    ) -> ValidationResult:
        try:
            replay = transformation.transform(
                original,
                seed=seed,
            )
        except Exception as exc:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.ERROR,
                reason_codes=("TRANSFORMATION_REPLAY_ERROR",),
                message="Transformation replay failed.",
                details={
                    "exception_type": type(exc).__name__,
                },
            )

        if not replay.changed:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                reason_codes=("TRANSFORMATION_NO_CHANGE",),
                message="Transformation produced no changes.",
            )

        if replay.transformed_text != candidate:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                reason_codes=("TRANSFORMATION_OUTPUT_MISMATCH",),
                message="Candidate does not match replayed output.",
            )

        if replay.source_text != original:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                reason_codes=("TRANSFORMATION_SOURCE_MISMATCH",),
                message="Transformation result references a different source.",
            )

        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.PASS,
            message="Transformation-specific validation passed.",
        )
