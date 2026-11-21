
from __future__ import annotations

import random
from typing import Iterable

from src.data.pair_models import PairRecord


class PairEndpointDiversitySelector:
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

        endpoint_usage: dict[str, int] = {}
        remaining = list(ordered_candidates)
        selected: list[PairRecord] = []

        while len(selected) < target_count:
            best_pair = min(
                remaining,
                key=lambda pair: (
                    endpoint_usage.get(pair.sample_a_id, 0)
                    + endpoint_usage.get(pair.sample_b_id, 0),
                    max(
                        endpoint_usage.get(pair.sample_a_id, 0),
                        endpoint_usage.get(pair.sample_b_id, 0),
                    ),
                    tie_breakers[pair.pair_id],
                    pair.pair_id,
                ),
            )

            selected.append(best_pair)
            remaining.remove(best_pair)

            endpoint_usage[best_pair.sample_a_id] = (
                endpoint_usage.get(best_pair.sample_a_id, 0) + 1
            )
            endpoint_usage[best_pair.sample_b_id] = (
                endpoint_usage.get(best_pair.sample_b_id, 0) + 1
            )

        return tuple(selected)
