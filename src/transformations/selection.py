
from __future__ import annotations

import random
from dataclasses import dataclass

from src.transformations.base import Transformation


class TransformationSelectionError(Exception):
    """Raised when transformation selection cannot be completed."""


@dataclass(frozen=True)
class TransformationSelectionResult:
    selected: tuple[str, ...]
    seed: int
    requested_count: int
    available_count: int
    probabilities: dict[str, float]


class TransformationSelector:
    """Select transformations using weighted sampling without replacement."""

    def select(
        self,
        transformations: list[Transformation],
        probabilities: dict[str, float],
        count: int,
        seed: int,
    ) -> TransformationSelectionResult:
        # if count not in (1, 2):
        #     raise TransformationSelectionError(
        #         "count must be 1 or 2 for V1."
        #     )

        if count < 1:
            raise TransformationSelectionError(
                "count must be at least 1."
            )

        if not transformations:
            raise TransformationSelectionError(
                "No transformations provided."
            )

        names = [transformation.name for transformation in transformations]

        if len(names) != len(set(names)):
            raise TransformationSelectionError(
                "Transformation names must be unique."
            )

        if set(names) != set(probabilities):
            raise TransformationSelectionError(
                "Probability keys must match transformation names exactly."
            )

        for name, weight in probabilities.items():
            if not isinstance(weight, (int, float)):
                raise TransformationSelectionError(
                    f"Probability for {name!r} must be numeric."
                )

            if weight < 0:
                raise TransformationSelectionError(
                    f"Probability for {name!r} cannot be negative."
                )

        available = [
            (transformation.name, float(probabilities[transformation.name]))
            for transformation in transformations
            if probabilities[transformation.name] > 0
        ]

        if count > len(available):
            raise TransformationSelectionError(
                "Requested count exceeds the number of transformations "
                "with positive probability."
            )

        if sum(weight for _, weight in available) <= 0:
            raise TransformationSelectionError(
                "Total probability weight must be positive."
            )

        rng = random.Random(seed)
        pool = list(available)
        selected: list[str] = []

        for _ in range(count):
            total_weight = sum(weight for _, weight in pool)
            draw = rng.random() * total_weight

            cumulative = 0.0
            selected_index = len(pool) - 1

            for index, (_, weight) in enumerate(pool):
                cumulative += weight

                if draw < cumulative:
                    selected_index = index
                    break

            selected_name, _ = pool.pop(selected_index)
            selected.append(selected_name)

        return TransformationSelectionResult(
            selected=tuple(selected),
            seed=seed,
            requested_count=count,
            available_count=len(available),
            probabilities=dict(probabilities),
        )
