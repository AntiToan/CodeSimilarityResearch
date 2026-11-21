
from __future__ import annotations

import random
from typing import Iterable

from src.data.pair_models import PairRecord


class PairProblemDistributionSelector:
    def select(
        self,
        pairs: Iterable[PairRecord],
        target_count: int,
        seed: int = 42,
    ) -> tuple[PairRecord, ...]:
        candidates = tuple(pairs)

        if not isinstance(target_count, int) or isinstance(target_count, bool):
            raise TypeError("target_count must be an integer")

        if target_count < 0:
            raise ValueError("target_count cannot be negative")

        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("seed must be an integer")

        if target_count > len(candidates):
            raise ValueError("target_count cannot exceed candidate count")

        for pair in candidates:
            if not isinstance(pair, PairRecord):
                raise TypeError("candidates must contain PairRecord instances")

        if target_count == 0:
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

        problem_usage: dict[str, int] = {}
        remaining = list(ordered_candidates)
        selected: list[PairRecord] = []

        while len(selected) < target_count:
            def get_problems(pair: PairRecord) -> tuple[str, ...]:
                return tuple(
                    sorted(
                        {
                            pair.problem_a_id,
                            pair.problem_b_id,
                        }
                    )
                )

            def selection_key(pair: PairRecord) -> tuple:
                problems = get_problems(pair)
                usages = tuple(
                    problem_usage.get(problem_id, 0)
                    for problem_id in problems
                )

                return (
                    sum(usages),
                    max(usages, default=0),
                    tie_breakers[pair.pair_id],
                    pair.pair_id,
                )

            best_pair = min(remaining, key=selection_key)

            selected.append(best_pair)
            remaining.remove(best_pair)

            for problem_id in get_problems(best_pair):
                problem_usage[problem_id] = (
                    problem_usage.get(problem_id, 0) + 1
                )

        return tuple(selected)
