from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PairAssemblyResult:
    pairs: tuple[Any, ...]
    positive_count: int
    negative_count: int
    total_count: int
    duplicate_pair_count: int
    assembly_status: str

    def __post_init__(self) -> None:
        if self.total_count != len(self.pairs):
            raise ValueError(
                "total_count must equal the number of assembled pairs."
            )

        if self.positive_count < 0:
            raise ValueError("positive_count cannot be negative.")

        if self.negative_count < 0:
            raise ValueError("negative_count cannot be negative.")

        if self.duplicate_pair_count < 0:
            raise ValueError("duplicate_pair_count cannot be negative.")

        if self.positive_count + self.negative_count != self.total_count:
            raise ValueError(
                "positive_count + negative_count must equal total_count."
            )

        if self.assembly_status not in {"PASS", "FAIL"}:
            raise ValueError(
                "assembly_status must be either 'PASS' or 'FAIL'."
            )