
from __future__ import annotations

import random
from typing import Iterable

from src.data.pair_models import PairRecord, PairType
from src.data.pair_label_quota_planner import PairLabelQuota


class PairFinalSelector:
    def select(
        self,
        pairs: Iterable[PairRecord],
        quota: PairLabelQuota,
        seed: int = 42,
        prefer_endpoint_diversity: bool = True,
        prefer_problem_balance: bool = True,
    ) -> tuple[PairRecord, ...]:
        candidates = tuple(pairs)

        if not isinstance(quota, PairLabelQuota):
            raise TypeError("quota must be a PairLabelQuota instance")

        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("seed must be an integer")

        if not isinstance(prefer_endpoint_diversity, bool):
            raise TypeError(
                "prefer_endpoint_diversity must be a boolean"
            )

        if not isinstance(prefer_problem_balance, bool):
            raise TypeError(
                "prefer_problem_balance must be a boolean"
            )

        for pair in candidates:
            if not isinstance(pair, PairRecord):
                raise TypeError(
                    "candidates must contain PairRecord instances"
                )

        if len({pair.pair_id for pair in candidates}) != len(candidates):
            raise ValueError("duplicate pair_id values in candidates")

        if len({pair.canonical_key for pair in candidates}) != len(candidates):
            raise ValueError("duplicate sample pairs in candidates")

        expected_split = quota.split

        for pair in candidates:
            if pair.split.value != expected_split:
                raise ValueError(
                    "candidate split does not match quota split"
                )

        positive_candidates = [
            pair for pair in candidates
            if pair.pair_type == PairType.POSITIVE
        ]

        negative_candidates = [
            pair for pair in candidates
            if pair.pair_type == PairType.NEGATIVE
        ]

        if quota.target_positive_count > len(positive_candidates):
            raise ValueError("positive target exceeds available candidates")

        if quota.target_negative_count > len(negative_candidates):
            raise ValueError("negative target exceeds available candidates")

        if quota.target_count == 0:
            return ()

        ordered_candidates = sorted(
            candidates,
            key=lambda pair: pair.pair_id,
        )

        rng = random.Random(seed)

        tie_breakers = {
            pair.pair_id: rng.random()
            for pair in ordered_candidates
        }

        remaining_positive = list(positive_candidates)
        remaining_negative = list(negative_candidates)

        selected: list[PairRecord] = []

        endpoint_usage: dict[str, int] = {}
        problem_usage: dict[str, int] = {}

        selected_positive_count = 0
        selected_negative_count = 0

        while (
            selected_positive_count < quota.target_positive_count
            or selected_negative_count < quota.target_negative_count
        ):
            positive_progress = (
                selected_positive_count / quota.target_positive_count
                if quota.target_positive_count > 0
                else 1.0
            )

            negative_progress = (
                selected_negative_count / quota.target_negative_count
                if quota.target_negative_count > 0
                else 1.0
            )

            if (
                selected_positive_count < quota.target_positive_count
                and (
                    selected_negative_count >= quota.target_negative_count
                    or positive_progress <= negative_progress
                )
            ):
                current_candidates = remaining_positive
                selected_label = PairType.POSITIVE
            else:
                current_candidates = remaining_negative
                selected_label = PairType.NEGATIVE

            def score(pair: PairRecord) -> tuple:
                score_parts = []

                if prefer_endpoint_diversity:
                    endpoints = {
                        pair.sample_a_id,
                        pair.sample_b_id,
                    }

                    endpoint_counts = [
                        endpoint_usage.get(endpoint, 0)
                        for endpoint in endpoints
                    ]

                    score_parts.extend(
                        (
                            sum(endpoint_counts),
                            max(endpoint_counts, default=0),
                        )
                    )

                if prefer_problem_balance:
                    problems = {
                        pair.problem_a_id,
                        pair.problem_b_id,
                    }

                    problem_counts = [
                        problem_usage.get(problem, 0)
                        for problem in problems
                    ]

                    score_parts.extend(
                        (
                            sum(problem_counts),
                            max(problem_counts, default=0),
                        )
                    )

                score_parts.extend(
                    (
                        tie_breakers[pair.pair_id],
                        pair.pair_id,
                    )
                )

                return tuple(score_parts)

            best_pair = min(current_candidates, key=score)

            selected.append(best_pair)
            current_candidates.remove(best_pair)

            if selected_label == PairType.POSITIVE:
                selected_positive_count += 1
            else:
                selected_negative_count += 1

            for endpoint in {
                best_pair.sample_a_id,
                best_pair.sample_b_id,
            }:
                endpoint_usage[endpoint] = (
                    endpoint_usage.get(endpoint, 0) + 1
                )

            for problem in {
                best_pair.problem_a_id,
                best_pair.problem_b_id,
            }:
                problem_usage[problem] = (
                    problem_usage.get(problem, 0) + 1
                )

        return tuple(selected)
