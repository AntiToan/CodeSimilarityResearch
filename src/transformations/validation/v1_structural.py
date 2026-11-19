
from __future__ import annotations

from src.transformations.validation.models import (
    ValidationResult,
    ValidationStatus,
)


class StructuralValidator:
    @property
    def name(self) -> str:
        return "V1_STRUCTURAL"

    def validate(
        self,
        original: str,
        candidate: str,
        variant_id: str,
        original_sample_id: str,
        transformation_type: str,
    ) -> ValidationResult:
        errors: list[str] = []

        if not isinstance(original, str):
            errors.append("ORIGINAL_INVALID_TYPE")

        if not isinstance(candidate, str):
            errors.append("CANDIDATE_INVALID_TYPE")

        if not isinstance(variant_id, str) or not variant_id.strip():
            errors.append("VARIANT_ID_INVALID")

        if (
            not isinstance(original_sample_id, str)
            or not original_sample_id.strip()
        ):
            errors.append("ORIGINAL_SAMPLE_ID_INVALID")

        if (
            not isinstance(transformation_type, str)
            or not transformation_type.strip()
        ):
            errors.append("TRANSFORMATION_TYPE_INVALID")

        if errors:
            return self._fail(errors, "Invalid input metadata or types.")

        if not original.strip():
            errors.append("ORIGINAL_EMPTY")

        if not candidate.strip():
            errors.append("CANDIDATE_EMPTY")

        if candidate == original:
            errors.append("CANDIDATE_UNCHANGED")

        if "\x00" in original:
            errors.append("ORIGINAL_CONTAINS_NUL")

        if "\x00" in candidate:
            errors.append("CANDIDATE_CONTAINS_NUL")

        if original.endswith(("\n", "\r")) and not candidate.endswith(
            ("\n", "\r")
        ):
            errors.append("FINAL_NEWLINE_REMOVED")

        if self._contains_surrogate(original):
            errors.append("ORIGINAL_INVALID_UNICODE")

        if self._contains_surrogate(candidate):
            errors.append("CANDIDATE_INVALID_UNICODE")

        if errors:
            return self._fail(
                errors,
                "Structural validation failed.",
            )

        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.PASS,
            message="Structural validation passed.",
        )

    @staticmethod
    def _contains_surrogate(text: str) -> bool:
        return any(
            0xD800 <= ord(char) <= 0xDFFF
            for char in text
        )

    def _fail(
        self,
        errors: list[str],
        message: str,
    ) -> ValidationResult:
        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.FAIL,
            reason_codes=tuple(errors),
            message=message,
        )
