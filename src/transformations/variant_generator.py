
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from src.transformations.base import Transformation
from src.transformations.selection import TransformationSelector


@dataclass(frozen=True)
class VariantValidationOutcome:
    """Normalized validation result consumed by the generator."""

    passed: bool
    reason: str | None = None


@dataclass(frozen=True)
class VariantAttempt:
    """Record of one generation attempt."""

    variant_index: int
    attempt_index: int
    transformation_type: str
    seed: int
    accepted: bool
    rejection_reason: str | None = None
    transformed_text: str | None = None


@dataclass(frozen=True)
class GeneratedVariant:
    """An accepted variant kept in memory."""

    variant_id: str
    original_sample_id: str
    variant_index: int
    transformation_type: str
    generation_seed: int
    source_text: str
    transformed_text: str


@dataclass
class VariantGenerationResult:
    """Complete result for generating variants from one original."""

    original_sample_id: str
    seed: int
    target_variants: int
    accepted_variants: list[GeneratedVariant] = field(
        default_factory=list
    )
    attempts: list[VariantAttempt] = field(default_factory=list)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_variants)

    @property
    def rejected_count(self) -> int:
        return sum(not attempt.accepted for attempt in self.attempts)

    @property
    def quota_reached(self) -> bool:
        return self.accepted_count >= self.target_variants

    @property
    def status(self) -> str:
        if self.quota_reached:
            return "COMPLETED"
        if self.accepted_count > 0:
            return "PARTIAL"
        return "FAILED"


Validator = Callable[
    [str, str, str],
    VariantValidationOutcome,
]


class VariantGenerationError(Exception):
    """Base exception for variant generation errors."""


class VariantGenerator:
    """Generate validated variants from an immutable original source."""

    def __init__(
        self,
        transformations: list[Transformation],
        probabilities: dict[str, float],
        validator: Validator,
        target_variants: int = 2,
        max_attempts_per_variant: int = 5,
    ) -> None:
        if target_variants <= 0:
            raise ValueError("target_variants must be positive.")

        if max_attempts_per_variant <= 0:
            raise ValueError(
                "max_attempts_per_variant must be positive."
            )

        if not transformations:
            raise ValueError("At least one transformation is required.")

        names = [transformation.name for transformation in transformations]

        if len(names) != len(set(names)):
            raise ValueError("Transformation names must be unique.")

        if set(names) != set(probabilities):
            raise ValueError(
                "Probability keys must match transformation names."
            )

        self.transformations = {
            transformation.name: transformation
            for transformation in transformations
        }
        self.probabilities = dict(probabilities)
        self.validator = validator
        self.target_variants = target_variants
        self.max_attempts_per_variant = max_attempts_per_variant
        self.selector = TransformationSelector()

    def generate(
        self,
        original_sample_id: str,
        original_source: str,
        seed: int,
    ) -> VariantGenerationResult:
        """Generate variants from original source only."""

        result = VariantGenerationResult(
            original_sample_id=original_sample_id,
            seed=seed,
            target_variants=self.target_variants,
        )

        available_names = [
            name
            for name, weight in self.probabilities.items()
            if weight > 0
        ]

        if not available_names:
            raise VariantGenerationError(
                "No transformation has positive probability."
            )

        # Create a deterministic weighted permutation of transformation
        # names. This gives the generator a reproducible candidate order.
        selection = self.selector.select(
            transformations=list(self.transformations.values()),
            probabilities=self.probabilities,
            count=len(available_names),
            seed=seed,
        )
        transformation_order = list(selection.selected)

        for variant_index in range(1, self.target_variants + 1):
            accepted = False

            # Rotate the order to prefer different transformation types
            # for different variants when possible.
            offset = (variant_index - 1) % len(transformation_order)
            candidate_order = (
                transformation_order[offset:]
                + transformation_order[:offset]
            )

            for attempt_index in range(
                1,
                self.max_attempts_per_variant + 1,
            ):
                transformation_name = candidate_order[
                    (attempt_index - 1) % len(candidate_order)
                ]

                # Derive a deterministic seed for each attempt.
                attempt_seed = (
                    seed
                    + variant_index * 100_000
                    + attempt_index
                )

                transformation = self.transformations[
                    transformation_name
                ]

                try:
                    transform_result = transformation.transform(
                        original_source,
                        seed=attempt_seed,
                    )
                except Exception as exc:
                    result.attempts.append(
                        VariantAttempt(
                            variant_index=variant_index,
                            attempt_index=attempt_index,
                            transformation_type=transformation_name,
                            seed=attempt_seed,
                            accepted=False,
                            rejection_reason=(
                                f"TRANSFORMATION_ERROR: "
                                f"{type(exc).__name__}: {exc}"
                            ),
                        )
                    )
                    continue

                transformed_source = transform_result.transformed_text

                if not transform_result.changed:
                    result.attempts.append(
                        VariantAttempt(
                            variant_index=variant_index,
                            attempt_index=attempt_index,
                            transformation_type=transformation_name,
                            seed=attempt_seed,
                            accepted=False,
                            rejection_reason="NO_CHANGE",
                        )
                    )
                    continue

                if transformed_source == original_source:
                    result.attempts.append(
                        VariantAttempt(
                            variant_index=variant_index,
                            attempt_index=attempt_index,
                            transformation_type=transformation_name,
                            seed=attempt_seed,
                            accepted=False,
                            rejection_reason="SOURCE_IDENTICAL",
                        )
                    )
                    continue

                try:
                    validation = self.validator(
                        original_source,
                        transformed_source,
                        transformation_name,
                    )
                except Exception as exc:
                    result.attempts.append(
                        VariantAttempt(
                            variant_index=variant_index,
                            attempt_index=attempt_index,
                            transformation_type=transformation_name,
                            seed=attempt_seed,
                            accepted=False,
                            rejection_reason=(
                                f"VALIDATOR_ERROR: "
                                f"{type(exc).__name__}: {exc}"
                            ),
                        )
                    )
                    continue

                if not validation.passed:
                    result.attempts.append(
                        VariantAttempt(
                            variant_index=variant_index,
                            attempt_index=attempt_index,
                            transformation_type=transformation_name,
                            seed=attempt_seed,
                            accepted=False,
                            rejection_reason=(
                                validation.reason
                                or "VALIDATION_FAILED"
                            ),
                        )
                    )
                    continue

                variant_id = (
                    f"{original_sample_id}_v{variant_index:03d}"
                )

                generated_variant = GeneratedVariant(
                    variant_id=variant_id,
                    original_sample_id=original_sample_id,
                    variant_index=variant_index,
                    transformation_type=transformation_name,
                    generation_seed=attempt_seed,
                    source_text=original_source,
                    transformed_text=transformed_source,
                )

                result.accepted_variants.append(generated_variant)

                result.attempts.append(
                    VariantAttempt(
                        variant_index=variant_index,
                        attempt_index=attempt_index,
                        transformation_type=transformation_name,
                        seed=attempt_seed,
                        accepted=True,
                        transformed_text=transformed_source,
                    )
                )

                accepted = True
                break

            if not accepted:
                # Partial quota is permitted. Do not oversample,
                # bypass validation, or generate from another variant.
                continue

        return result
