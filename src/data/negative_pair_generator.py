from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
from src.data.pair_models import PairRecord, PairSplit, PairType

SimilarityScreener = Callable[[Any, Any], bool]

@dataclass(frozen=True)
class NegativePairRejection:
    anchor_id: str
    candidate_id: str
    reason: str

@dataclass
class NegativePairGenerationResult:
    pairs: list[PairRecord] = field(default_factory=list)
    candidates_seen: int = 0
    candidates_eligible: int = 0
    candidates_rejected: int = 0
    rejections: list[NegativePairRejection] = field(default_factory=list)

    @property
    def pairs_generated(self) -> int:
        return len(self.pairs)

class NegativePairGenerator:
    """Generate eligible cross-problem negative pairs from original samples."""

    def __init__(
        self,
        similarity_screener: SimilarityScreener,
    ) -> None:
        if not callable(similarity_screener):
            raise TypeError("similarity_screener must be callable.")

        self.similarity_screener = similarity_screener

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
        result: NegativePairGenerationResult,
        anchor_id: str,
        candidate_id: str,
        reason: str,
    ) -> None:
        result.candidates_rejected += 1
        result.rejections.append(
            NegativePairRejection(
                anchor_id=anchor_id,
                candidate_id=candidate_id,
                reason=reason,
            )
        )

    @staticmethod
    def _duplicate_group(
        sample: Any,
        duplicate_groups: dict[str, str],
    ) -> str | None:
        return duplicate_groups.get(sample.sample_id)

    @staticmethod
    def _split_value(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)

    def generate(
        self,
        anchor: Any,
        candidates: Iterable[Any],
        *,
        duplicate_groups: dict[str, str] | None = None,
        seed: int | None = None,
    ) -> NegativePairGenerationResult:
        result = NegativePairGenerationResult()
        duplicate_groups = duplicate_groups or {}

        seen_pair_keys: set[tuple[str, str]] = set()

        anchor_id = anchor.sample_id
        anchor_problem = str(anchor.problem_id)
        anchor_lineage = str(
            getattr(anchor, "source_id", anchor.sample_id)
        )
        # anchor_split = str(anchor.split)
        anchor_split = self._split_value(anchor.split)

        for candidate in candidates:
            result.candidates_seen += 1

            candidate_id = candidate.sample_id
            candidate_problem = str(candidate.problem_id)
            candidate_lineage = str(
                getattr(candidate, "source_id", candidate.sample_id)
            )
            # candidate_split = str(candidate.split)
            candidate_split = self._split_value(candidate.split)

            if candidate_id == anchor_id:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Self-pair is not allowed.",
                )
                continue

            if candidate_problem == anchor_problem:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Same-problem negative candidate is excluded.",
                )
                continue

            if candidate_lineage == anchor_lineage:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Shared source lineage is excluded.",
                )
                continue

            if candidate_split != anchor_split:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Cross-split candidate is prohibited.",
                )
                continue

            anchor_group = self._duplicate_group(
                anchor, duplicate_groups
            )
            candidate_group = self._duplicate_group(
                candidate, duplicate_groups
            )

            if (
                anchor_group is not None
                and candidate_group is not None
                and anchor_group == candidate_group
            ):
                self._reject(
                    result, anchor_id, candidate_id,
                    "Known exact-duplicate group relationship.",
                )
                continue

            canonical_key = tuple(sorted((anchor_id, candidate_id)))

            if canonical_key in seen_pair_keys:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Duplicate pair candidate.",
                )
                continue

            try:
                passes_similarity = self.similarity_screener(
                    anchor, candidate
            )
            except Exception as exc:
                self._reject(
                    result, anchor_id, candidate_id,
                    f"Similarity screening error: {type(exc).__name__}: {exc}",
                )
                continue

            if passes_similarity is not True:
                self._reject(
                    result, anchor_id, candidate_id,
                    "Candidate rejected by similarity screening.",
                )
                continue

            seen_pair_keys.add(canonical_key)
            result.candidates_eligible += 1

            pair = PairRecord.create_canonical(
                pair_id=self.create_pair_id(*canonical_key),
                sample_a_id=anchor_id,
                sample_b_id=candidate_id,
                label=0,
                pair_type=PairType.NEGATIVE,
                split=PairSplit(anchor_split),
                source_a_id=anchor_lineage,
                source_b_id=candidate_lineage,
                problem_a_id=anchor_problem,
                problem_b_id=candidate_problem,
                generation_method="cross_problem_sampling",
                created_seed=seed,
            )

            result.pairs.append(pair)

        return result
