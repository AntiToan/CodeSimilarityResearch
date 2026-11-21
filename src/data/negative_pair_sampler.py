
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.data.negative_pair_generator import NegativePairGenerator
from src.data.pair_models import PairRecord


@dataclass
class NegativePairSamplingResult:
    pairs: list[PairRecord] = field(default_factory=list)

    candidates_seen: int = 0
    candidates_eligible: int = 0
    candidates_rejected: int = 0

    quota_target: int = 3
    quota_reached: bool = False

    unique_problem_count: int = 0
    problem_ids_selected: list[str] = field(default_factory=list)

    rejections: list[Any] = field(default_factory=list)

    @property
    def sampled_count(self) -> int:
        return len(self.pairs)

    @property
    def quota_remaining(self) -> int:
        return max(0, self.quota_target - self.sampled_count)


class NegativePairSampler:
    """Deterministic, problem-diverse negative sampling for one anchor."""

    def __init__(
        self,
        generator: NegativePairGenerator,
        quota_per_anchor: int = 3,
    ) -> None:
        if type(quota_per_anchor) is not int:
            raise TypeError("quota_per_anchor must be an integer.")

        if quota_per_anchor < 1:
            raise ValueError("quota_per_anchor must be >= 1.")

        self.generator = generator
        self.quota_per_anchor = quota_per_anchor

    @staticmethod
    def _stable_shuffle(
        items: list[PairRecord],
        rng: random.Random,
    ) -> list[PairRecord]:
        items = sorted(items, key=lambda pair: pair.pair_id)
        rng.shuffle(items)
        return items

    def sample(
        self,
        anchor: Any,
        candidates: Iterable[Any],
        *,
        duplicate_groups: dict[str, str] | None = None,
        seed: int = 42,
    ) -> NegativePairSamplingResult:
        generation_result = self.generator.generate(
            anchor,
            candidates,
            duplicate_groups=duplicate_groups,
            seed=seed,
        )

        result = NegativePairSamplingResult(
            candidates_seen=generation_result.candidates_seen,
            candidates_eligible=generation_result.candidates_eligible,
            candidates_rejected=generation_result.candidates_rejected,
            quota_target=self.quota_per_anchor,
            rejections=list(generation_result.rejections),
        )

        eligible_pairs = list(generation_result.pairs)

        rng = random.Random(seed)

        # Group candidates by their opposing problem ID.
        by_problem: dict[str, list[PairRecord]] = {}

        for pair in eligible_pairs:
            opposing_problem_id = self._opposing_problem_id(
                pair,
                str(anchor.problem_id),
            )

            by_problem.setdefault(
                opposing_problem_id, []
            ).append(pair)

        # Shuffle problems deterministically.
        problem_ids = sorted(by_problem)
        rng.shuffle(problem_ids)

        # Phase 1: select one pair from each distinct problem.
        selected: list[PairRecord] = []
        selected_keys: set[tuple[str, str]] = set()

        for problem_id in problem_ids:
            if len(selected) >= self.quota_per_anchor:
                break

            problem_candidates = self._stable_shuffle(
                by_problem[problem_id],
                rng,
            )

            chosen = problem_candidates[0]
            selected.append(chosen)
            selected_keys.add(chosen.canonical_key)

        # Phase 2: fill remaining quota with eligible pairs.
        if len(selected) < self.quota_per_anchor:
            remaining = [
                pair
                for pair in eligible_pairs
                if pair.canonical_key not in selected_keys
            ]

            remaining = self._stable_shuffle(remaining, rng)

            for pair in remaining:
                if len(selected) >= self.quota_per_anchor:
                    break

                selected.append(pair)
                selected_keys.add(pair.canonical_key)

        result.pairs = selected
        result.problem_ids_selected = list(
            dict.fromkeys(
                self._opposing_problem_id(pair, str(anchor.problem_id))
                for pair in selected
            )
        )
        result.unique_problem_count = len(
            result.problem_ids_selected
        )
        result.quota_reached = (
            len(selected) >= self.quota_per_anchor
        )

        return result

    @staticmethod
    def _opposing_problem_id(
        pair: PairRecord,
        anchor_problem_id: str,
    ) -> str:
        if pair.problem_a_id == anchor_problem_id:
            return pair.problem_b_id
        return pair.problem_a_id