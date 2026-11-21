
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.data.pair_models import (
    PairRecord,
    PairSplit,
    PairType,
)

@dataclass(frozen=True)
class PositivePairRejection:
    variant_id: str
    reason: str


@dataclass
class PositivePairGenerationResult:
    pairs: list[PairRecord] = field(default_factory=list)
    variants_seen: int = 0
    variants_eligible: int = 0
    variants_rejected: int = 0
    rejections: list[PositivePairRejection] = field(default_factory=list)

    @property
    def pairs_generated(self) -> int:
        return len(self.pairs)


class PositivePairGenerator:
    """Generate synthetic positive pairs from originals and validated variants."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def create_pair_id(
        sample_a_id: str,
        sample_b_id: str,
    ) -> str:
        canonical_ids = sorted((sample_a_id, sample_b_id))
        payload = "\x1f".join(canonical_ids).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return f"pair_{digest}"

    @staticmethod
    def _reject(
        result: PositivePairGenerationResult,
        variant_id: str,
        reason: str,
    ) -> None:
        result.variants_rejected += 1
        result.rejections.append(
            PositivePairRejection(
                variant_id=variant_id,
                reason=reason,
            )
        )

    def generate(
        self,
        original_samples: Iterable[Any],
        variant_records: Iterable[Any],
    ) -> PositivePairGenerationResult:
        result = PositivePairGenerationResult()

        originals_by_id = {
            sample.sample_id: sample
            for sample in original_samples
        }

        seen_pair_keys: set[tuple[str, str]] = set()

        for variant in variant_records:
            result.variants_seen += 1

            variant_id = variant.variant_id
            original_sample_id = variant.original_sample_id

            # Registry should contain validated variants.
            validation_status = str(
                variant.validation_status
            ).strip().upper()

            if validation_status != "PASS":
                self._reject(
                    result,
                    variant_id,
                    f"Variant validation status is {validation_status!r}, not PASS.",
                )
                continue

            original = originals_by_id.get(original_sample_id)

            if original is None:
                self._reject(
                    result,
                    variant_id,
                    "Original sample is missing from the loaded source set.",
                )
                continue

            if variant_id == original_sample_id:
                self._reject(
                    result,
                    variant_id,
                    "Variant ID must differ from original sample ID.",
                )
                continue

            if str(variant.problem_id) != str(original.problem_id):
                self._reject(
                    result,
                    variant_id,
                    "Variant problem ID does not match original sample.",
                )
                continue

            if str(variant.split) != str(original.split):
                self._reject(
                    result,
                    variant_id,
                    "Variant split does not match original sample split.",
                )
                continue

            canonical_key = tuple(
                sorted((original_sample_id, variant_id))
            )

            if canonical_key in seen_pair_keys:
                self._reject(
                    result,
                    variant_id,
                    "Duplicate positive pair detected.",
                )
                continue

            seen_pair_keys.add(canonical_key)
            result.variants_eligible += 1

            pair_id = self.create_pair_id(*canonical_key)

            pair = PairRecord.create_canonical(
                pair_id=pair_id,
                sample_a_id=original_sample_id,
                sample_b_id=variant_id,
                label=1,
                pair_type=PairType.POSITIVE,
                split=PairSplit(str(original.split)),
                source_a_id=original_sample_id,
                source_b_id=original_sample_id,
                problem_a_id=str(original.problem_id),
                problem_b_id=str(original.problem_id),
                generation_method=f"transformation:{variant.transformation_type}",
                created_seed=variant.generation_seed,
            )

            result.pairs.append(pair)

        return result
