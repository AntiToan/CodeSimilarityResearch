
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.data.pair_models import PairRecord, PairSplit, PairType


@dataclass(frozen=True)
class PairCandidatePartition:
    train_pairs: tuple[PairRecord, ...]
    validation_pairs: tuple[PairRecord, ...]
    test_pairs: tuple[PairRecord, ...]
    total_count: int
    train_positive_count: int
    train_negative_count: int
    validation_positive_count: int
    validation_negative_count: int
    test_positive_count: int
    test_negative_count: int

    def __post_init__(self) -> None:
        pair_groups = (
            self.train_pairs,
            self.validation_pairs,
            self.test_pairs,
        )

        for group in pair_groups:
            if not isinstance(group, tuple):
                raise TypeError("partition pair groups must be tuples")

            for pair in group:
                if not isinstance(pair, PairRecord):
                    raise TypeError(
                        "partition groups must contain PairRecord instances"
                    )

        actual_total = sum(len(group) for group in pair_groups)

        if self.total_count != actual_total:
            raise ValueError(
                "total_count must equal the number of partitioned pairs"
            )

        count_fields = (
            self.train_positive_count,
            self.train_negative_count,
            self.validation_positive_count,
            self.validation_negative_count,
            self.test_positive_count,
            self.test_negative_count,
        )

        if any(count < 0 for count in count_fields):
            raise ValueError("pair counts cannot be negative")

        expected_counts = (
            (self.train_pairs, self.train_positive_count, self.train_negative_count),
            (
                self.validation_pairs,
                self.validation_positive_count,
                self.validation_negative_count,
            ),
            (self.test_pairs, self.test_positive_count, self.test_negative_count),
        )

        for pairs, positive_count, negative_count in expected_counts:
            actual_positive = sum(
                pair.pair_type == PairType.POSITIVE for pair in pairs
            )
            actual_negative = sum(
                pair.pair_type == PairType.NEGATIVE for pair in pairs
            )

            if positive_count != actual_positive:
                raise ValueError(
                    "positive count does not match partition contents"
                )

            if negative_count != actual_negative:
                raise ValueError(
                    "negative count does not match partition contents"
                )

        all_pair_ids = [
            pair.pair_id
            for group in pair_groups
            for pair in group
        ]

        if len(all_pair_ids) != len(set(all_pair_ids)):
            raise ValueError(
                "partition contains duplicate pair_id values"
            )

        all_canonical_keys = [
            pair.canonical_key
            for group in pair_groups
            for pair in group
        ]

        if len(all_canonical_keys) != len(set(all_canonical_keys)):
            raise ValueError(
                "partition contains duplicate sample pairs"
            )

        split_expectations = (
            (self.train_pairs, PairSplit.TRAIN),
            (self.validation_pairs, PairSplit.VALIDATION),
            (self.test_pairs, PairSplit.TEST),
        )

        for pairs, expected_split in split_expectations:
            for pair in pairs:
                if pair.split != expected_split:
                    raise ValueError(
                        "pair was assigned to the wrong split partition"
                    )


class PairCandidatePartitioner:
    def partition(
        self,
        pairs: Iterable[PairRecord],
    ) -> PairCandidatePartition:
        pair_list = tuple(pairs)

        for pair in pair_list:
            if not isinstance(pair, PairRecord):
                raise TypeError(
                    "pairs must contain PairRecord instances"
                )

        train_pairs = tuple(
            sorted(
                (pair for pair in pair_list if pair.split == PairSplit.TRAIN),
                key=lambda pair: pair.pair_id,
                )
        )

        validation_pairs = tuple(
            sorted(
                (
                    pair
                    for pair in pair_list
                    if pair.split == PairSplit.VALIDATION
                ),
                key=lambda pair: pair.pair_id,
            )
        )

        test_pairs = tuple(
            sorted(
                (pair for pair in pair_list if pair.split == PairSplit.TEST),
                key=lambda pair: pair.pair_id,
            )
        )

        return PairCandidatePartition(
            train_pairs=train_pairs,
            validation_pairs=validation_pairs,
            test_pairs=test_pairs,
            total_count=len(pair_list),
            train_positive_count=self._count_type(
                train_pairs, PairType.POSITIVE
            ),
            train_negative_count=self._count_type(
                train_pairs, PairType.NEGATIVE
            ),
            validation_positive_count=self._count_type(
                validation_pairs, PairType.POSITIVE
            ),
            validation_negative_count=self._count_type(
                validation_pairs, PairType.NEGATIVE
            ),
            test_positive_count=self._count_type(
                test_pairs, PairType.POSITIVE
            ),
            test_negative_count=self._count_type(
                test_pairs, PairType.NEGATIVE
            ),
        )

    @staticmethod
    def _count_type(
        pairs: tuple[PairRecord, ...],
        pair_type: PairType,
    ) -> int:
        return sum(pair.pair_type == pair_type for pair in pairs)
