from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class PairType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

class PairSplit(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"

@dataclass(frozen=True)
class PairRecord:
    pair_id: str 
    sample_a_id: str 
    sample_b_id: str 
    label: int 
    pair_type: PairType
    split: PairSplit
    source_a_id: str 
    source_b_id: str 
    problem_a_id: str 
    problem_b_id: str 
    generation_method: str 
    created_seed: int | None = None

    def __post_init__(self) -> None:
        self._validate_fields()
        self._validate_pair_semantics()
        self._validate_canonical_order()

    def _validate_fields(self) -> None:
        string_fields = (
            "pair_id",
            "sample_a_id",
            "sample_b_id",
            "source_a_id",
            "source_b_id",
            "problem_a_id",
            "problem_b_id",
            "generation_method",
        )

        for field_name in string_fields:
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty."
                )

        if type(self.label) is not int:
            raise TypeError("label must be an integer.")

        if self.label not in (0, 1):
            raise ValueError("label must be 0 or 1.")

        if not isinstance(self.pair_type, PairType):
            raise TypeError(
                "pair_type must be a PairType"
            )

        if not isinstance(self.split, PairSplit):
            raise TypeError(
                "split must be a PairSplit."
            )

        if self.created_seed is not None:
            if type(self.created_seed) is not int:
                raise TypeError(
                    "created_seed must be an integer or None."
                )

    def _validate_pair_semantics(self) -> None:
        if self.sample_a_id == self.sample_b_id:
            raise ValueError(
                "Self-pairs are not allowed."
            )

        if self.pair_type == PairType.POSITIVE:
            if self.label != 1:
                raise ValueError(
                    "Positive pairs must have label=1."
                )

            if self.source_a_id != self.source_b_id:
                raise ValueError(
                    "Positive pairs must share the same source lineage."
                )

        elif self.pair_type == PairType.NEGATIVE:
            if self.label != 0:
                raise ValueError(
                    "Negative pairs must have label=0."
                )

            if self.problem_a_id == self.problem_b_id:
                raise ValueError(
                    "Negative pairs must have different problem IDs."
                )

            if self.source_a_id == self.source_b_id:
                raise ValueError(
                    "Negative pairs must have different source lineages."
                )

    def _validate_canonical_order(self) -> None:
        if self.sample_a_id > self.sample_b_id:
            raise ValueError(
                "sample_a_id must be lexicographically <= sample_b_id."
            )

    @property
    def canonical_key(self) -> tuple[str, str]:
        return (self.sample_a_id, self.sample_b_id)

    
    @classmethod
    def create_canonical(
        cls,
        *,
        pair_id: str,
        sample_a_id: str,
        sample_b_id: str,
        label: int,
        pair_type: PairType,
        split: PairSplit,
        source_a_id: str,
        source_b_id: str,
        problem_a_id: str,
        problem_b_id: str,
        generation_method: str,
        created_seed: int | None = None,
    ) -> PairRecord:
        if sample_a_id > sample_b_id:
            sample_a_id, sample_b_id = sample_b_id, sample_a_id
            source_a_id, source_b_id = source_b_id, source_a_id
            problem_a_id, problem_b_id = problem_b_id, problem_a_id

        return cls(
            pair_id=pair_id,
            sample_a_id=sample_a_id,
            sample_b_id=sample_b_id,
            label=label,
            pair_type=pair_type,
            split=split,
            source_a_id=source_a_id,
            source_b_id=source_b_id,
            problem_a_id=problem_a_id,
            problem_b_id=problem_b_id,
            generation_method=generation_method,
            created_seed=created_seed,
        )
