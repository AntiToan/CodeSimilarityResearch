from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from src.data.pair_assembly_models import PairAssemblyResult


@dataclass(frozen=True)
class PairAssemblyConfig:
    validate_pair_type_label_consistency: bool = True
    check_duplicate_pair_ids: bool = True
    check_duplicate_sample_pairs: bool = True


class PairAssembler:
    """Merge positive and negative pairs into a deterministic assembled dataset."""

    def __init__(
        self,
        config: PairAssemblyConfig | None = None,
    ) -> None:
        self.config = config or PairAssemblyConfig()

    @staticmethod
    def _get(record: Any, key: str, default: Any = None) -> Any:
        if isinstance(record, Mapping):
            return record.get(key, default)

        return getattr(record, key, default)

    @staticmethod
    def _value(value: Any) -> str:
        return str(value.value if hasattr(value, "value") else value)

    @classmethod
    def _pair_key(cls, pair: Any) -> tuple[str, str]:
        sample_a_id = str(cls._get(pair, "sample_a_id", ""))
        sample_b_id = str(cls._get(pair, "sample_b_id", ""))

        return tuple(sorted((sample_a_id, sample_b_id)))

    @classmethod
    def _pair_id(cls, pair: Any) -> str:
        return str(cls._get(pair, "pair_id", ""))

    @classmethod
    def _label(cls, pair: Any) -> int:
        value = cls._get(pair, "label")
        return int(value)

    @classmethod
    def _pair_type(cls, pair: Any) -> str:
        return cls._value(cls._get(pair, "pair_type", "")).lower()

    @classmethod
    def _stable_key(cls, pair: Any) -> tuple[str, ...]:
        """Stable ordering key independent of input order."""
        return (
            cls._pair_id(pair),
            *cls._pair_key(pair),
            str(cls._label(pair)),
            cls._pair_type(pair),
            cls._value(cls._get(pair, "split", "")),
            str(cls._get(pair, "source_a_id", "")),
            str(cls._get(pair, "source_b_id", "")),
            str(cls._get(pair, "problem_a_id", "")),
            str(cls._get(pair, "problem_b_id", "")),
            str(cls._get(pair, "generation_method", "")),
            str(cls._get(pair, "created_seed", "")),
        )

    def _validate_record(self, pair: Any, expected_label: int) -> None:
        pair_id = self._pair_id(pair)
        sample_a_id = str(self._get(pair, "sample_a_id", ""))
        sample_b_id = str(self._get(pair, "sample_b_id", ""))

        if not pair_id:
            raise ValueError("Pair ID must not be empty.")

        if not sample_a_id or not sample_b_id:
            raise ValueError("Sample IDs must not be empty.")

        if sample_a_id == sample_b_id:
            raise ValueError("Self-pairs are not allowed.")

        label = self._label(pair)
        pair_type = self._pair_type(pair)

        if label != expected_label:
            raise ValueError(
                f"Expected label {expected_label}, got {label} "
                f"for pair {pair_id}."
            )

        if self.config.validate_pair_type_label_consistency:
            expected_type = "positive" if expected_label == 1 else "negative"

            if not pair_type.endswith(expected_type):
                raise ValueError(
                    f"Expected pair_type '{expected_type}', "
                    f"got '{pair_type}' for pair {pair_id}."
                )

    def assemble(
        self,
        positive_pairs: Iterable[Any],
        negative_pairs: Iterable[Any],
    ) -> PairAssemblyResult:
        positive_list = list(positive_pairs)
        negative_list = list(negative_pairs)

        for pair in positive_list:
            self._validate_record(pair, expected_label=1)

        for pair in negative_list:
            self._validate_record(pair, expected_label=0)

        candidates = positive_list + negative_list

        # Deterministic processing order regardless of input order.
        candidates.sort(key=self._stable_key)

        retained: list[Any] = []
        pair_id_to_key: dict[str, tuple[str, str]] = {}
        pair_key_to_label: dict[tuple[str, str], int] = {}

        duplicate_count = 0

        for pair in candidates:
            pair_id = self._pair_id(pair)
            pair_key = self._pair_key(pair)
            label = self._label(pair)

            # A sample pair cannot have conflicting labels.
            existing_label = pair_key_to_label.get(pair_key)

            if existing_label is not None and existing_label != label:
                raise ValueError(
                    "Conflicting labels for sample pair "
                    f"{pair_key}: {existing_label} vs {label}."
                )

            # A Pair ID cannot point to different sample pairs.
            existing_key = pair_id_to_key.get(pair_id)

            if (
                self.config.check_duplicate_pair_ids
                and existing_key is not None
                and existing_key != pair_key
            ):
                raise ValueError(
                    f"Pair ID collision detected: {pair_id}."
                )

            # Duplicate unordered sample pair.
            if (
                self.config.check_duplicate_sample_pairs
                and pair_key in pair_key_to_label
            ):
                duplicate_count += 1
                continue

            # Duplicate Pair ID for an already represented sample pair.
            if (
                self.config.check_duplicate_pair_ids
                and pair_id in pair_id_to_key
            ):
                duplicate_count += 1
                continue

            retained.append(pair)
            pair_key_to_label[pair_key] = label
            pair_id_to_key[pair_id] = pair_key

        # Final deterministic output ordering.
        retained.sort(key=self._stable_key)

        positive_count = sum(self._label(pair) == 1 for pair in retained)
        negative_count = sum(self._label(pair) == 0 for pair in retained)

        return PairAssemblyResult(
            pairs=tuple(retained),
            positive_count=positive_count,
            negative_count=negative_count,
            total_count=len(retained),
            duplicate_pair_count=duplicate_count,
            assembly_status="PASS",
        )