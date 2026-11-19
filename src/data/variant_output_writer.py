
from __future__ import annotations

import re
from pathlib import Path

from src.transformations.variant_generator import GeneratedVariant


_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_VARIANT_ID_PATTERN = re.compile(
    r"^(?P<original_id>[A-Za-z0-9_-]+)_v(?P<index>\d{3})$"
)


class VariantOutputError(Exception):
    """Base exception for variant output errors."""


class InvalidVariantPathError(VariantOutputError):
    """Raised when a variant path contains invalid components."""


class VariantFileExistsError(VariantOutputError):
    """Raised when a variant file already exists."""


class VariantOutputWriter:
    """Safely write accepted variants into the variants directory."""

    def __init__(self, variants_root: Path | str) -> None:
        self.variants_root = Path(variants_root).resolve()

    @staticmethod
    def _validate_component(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value:
            raise InvalidVariantPathError(
                f"{field_name} must be a non-empty string."
            )

        if not _SAFE_ID_PATTERN.fullmatch(value):
            raise InvalidVariantPathError(
                f"Invalid {field_name}: {value!r}"
            )

        if value in {".", ".."}:
            raise InvalidVariantPathError(
                f"Invalid {field_name}: {value!r}"
            )

        return value

    def build_path(
        self,
        problem_id: str,
        variant_id: str,
        original_sample_id: str,
    ) -> Path:
        problem_id = self._validate_component(
            problem_id, "problem_id"
        )
        variant_id = self._validate_component(
            variant_id, "variant_id"
        )
        original_sample_id = self._validate_component(
            original_sample_id, "original_sample_id"
        )

        match = _VARIANT_ID_PATTERN.fullmatch(variant_id)

        if match is None:
            raise InvalidVariantPathError(
                f"Invalid variant_id format: {variant_id!r}"
            )

        if match.group("original_id") != original_sample_id:
            raise InvalidVariantPathError(
                "variant_id does not belong to original_sample_id."
            )

        output_path = (
            self.variants_root
            / problem_id
            / f"{variant_id}.txt"
        ).resolve()

        # Defensive containment check.
        if not output_path.is_relative_to(self.variants_root):
            raise InvalidVariantPathError(
                "Resolved output path escapes variants_root."
            )

        return output_path

    @staticmethod
    def _normalize_text(text: str) -> str:
        # Normalize CRLF/CR to LF. Do not otherwise alter code.
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def write_variant(
        self,
        variant: GeneratedVariant,
        problem_id: str,
    ) -> Path:
        output_path = self.build_path(
            problem_id=problem_id,
            variant_id=variant.variant_id,
            original_sample_id=variant.original_sample_id,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        content = self._normalize_text(
            variant.transformed_text
        ).encode("utf-8")

        try:
            # Exclusive creation: an existing variant is never overwritten.
            with output_path.open("xb") as file:
                file.write(content)
        except FileExistsError as exc:
            raise VariantFileExistsError(
                f"Variant file already exists: {output_path}"
            ) from exc

        return output_path
