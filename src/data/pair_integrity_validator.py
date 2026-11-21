
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from src.data.pair_validation_models import (
    PairValidationIssue,
    PairValidationReport,
    PairValidationResult,
    ValidationSeverity,
)


@dataclass(frozen=True)
class PairIntegrityValidationConfig:
    check_duplicate_pair_ids: bool = True
    check_duplicate_sample_pairs: bool = True
    check_pair_id_integrity: bool = True
    check_split_leakage: bool = True
    check_duplicate_group_leakage: bool = True
    validator_version: str = "1.0.0"


class PairIntegrityValidator:
    """Validate pair identity, duplication, split, and duplicate-group integrity."""

    def __init__(
        self,
        config: PairIntegrityValidationConfig | None = None,
    ) -> None:
        self.config = config or PairIntegrityValidationConfig()

    @staticmethod
    def compute_pair_id(
        sample_a_id: str,
        sample_b_id: str,
    ) -> str:
        from src.data.positive_pair_generator import PositivePairGenerator

        return PositivePairGenerator.create_pair_id(
            sample_a_id,
            sample_b_id,
        )

    @staticmethod
    def _value(value: Any) -> str:
        return str(value.value if hasattr(value, "value") else value)

    @staticmethod
    def _get(
        record: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(record, Mapping):
            return record.get(key, default)

        return getattr(record, key, default)

    @staticmethod
    def _canonical_key(
        sample_a_id: str,
        sample_b_id: str,
    ) -> tuple[str, str]:
        return tuple(sorted((sample_a_id, sample_b_id)))

    @staticmethod
    def _issue(
        rule_id: str,
        message: str,
        pair_id: str,
        *,
        field: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> PairValidationIssue:
        normalized_details = tuple(
            sorted(
                (str(key), str(value))
                for key, value in (details or {}).items()
            )
        )

        return PairValidationIssue(
            rule_id=rule_id,
            severity=ValidationSeverity.ERROR,
            message=message,
            pair_id=pair_id,
            field=field,
            details=normalized_details,
        )

    def validate_pair(
        self,
        pair: Any,
        samples: Mapping[str, Any],
        duplicate_groups: Mapping[str, str] | None = None,
    ) -> PairValidationResult:
        pair_id = str(self._get(pair, "pair_id", ""))
        issues: list[PairValidationIssue] = []

        sample_a_id = str(self._get(pair, "sample_a_id", ""))
        sample_b_id = str(self._get(pair, "sample_b_id", ""))

        # Pair ID integrity
        if self.config.check_pair_id_integrity:
            expected_pair_id = self.compute_pair_id(
                sample_a_id,
                sample_b_id,
            )

            if pair_id != expected_pair_id:
                issues.append(
                    self._issue(
                        "PAIR_ID_CONTENT_MISMATCH",
                        "Pair ID does not match the canonical sample pair.",
                        pair_id,
                        field="pair_id",
                        details={
                            "expected": expected_pair_id,
                            "actual": pair_id,
                        },
                    )
                )

        # Split integrity: metadata must exist before split comparison.
        if self.config.check_split_leakage:
            pair_split = self._value(self._get(pair, "split"))

            sample_a = samples.get(sample_a_id)
            sample_b = samples.get(sample_b_id)

            missing_sample_ids = []

            if sample_a is None:
                missing_sample_ids.append(sample_a_id)

            if sample_b is None:
                missing_sample_ids.append(sample_b_id)

            if missing_sample_ids:
                issues.append(
                    self._issue(
                        "PAIR_SAMPLE_METADATA_MISSING",
                        "Sample metadata is missing; split integrity cannot be verified.",
                        pair_id,
                        field="sample_reference",
                        details={
                            "missing_sample_ids": ",".join(
                                sorted(missing_sample_ids)
                            ),
                        },
                    )
                )
            else:
                split_a = self._value(self._get(sample_a, "split"))
                split_b = self._value(self._get(sample_b, "split"))

                if split_a != split_b or pair_split != split_a:
                    issues.append(
                        self._issue(
                            "PAIR_SPLIT_LEAKAGE",
                            "Pair split must match both endpoint sample splits.",
                            pair_id,
                            field="split",
                            details={
                                "pair_split": pair_split,
                                "sample_a_split": split_a,
                                "sample_b_split": split_b,
                            },
                        )
                    )

        # Known duplicate-group leakage is applicable to negative pairs.
        if self.config.check_duplicate_group_leakage:
            pair_type = self._value(self._get(pair, "pair_type")).upper()

            if pair_type.endswith("NEGATIVE"):
                duplicate_groups = duplicate_groups or {}

                group_a = duplicate_groups.get(sample_a_id)
                group_b = duplicate_groups.get(sample_b_id)

                if (
                    group_a is not None
                    and group_b is not None
                    and group_a == group_b
                ):
                    issues.append(
                        self._issue(
                            "DUPLICATE_GROUP_LEAKAGE",
                            "Negative pair endpoints belong to the same known duplicate group.",
                            pair_id,
                            details={
                                "sample_a_id": sample_a_id,
                                "sample_b_id": sample_b_id,
                                "duplicate_group_id": group_a,
                            },
                        )
                    )

        return PairValidationResult(
            pair_id=pair_id,
            issues=tuple(issues),
        )

    def validate_batch(
        self,
        pairs: Iterable[Any],
        samples: Mapping[str, Any],
        duplicate_groups: Mapping[str, str] | None = None,
    ) -> PairValidationReport:
        pair_list = list(pairs)

        # Keep per-record issues before aggregating by pair_id.
        issues_by_pair_id: dict[str, list[PairValidationIssue]] = {}
        pair_ids_by_key: dict[tuple[str, str], list[str]] = {}
        pair_ids_by_id: dict[str, list[str]] = {}

        for pair in pair_list:
            pair_id = str(self._get(pair, "pair_id", ""))

            result = self.validate_pair(
                pair,
                samples,
                duplicate_groups,
            )

            issues_by_pair_id.setdefault(pair_id, []).extend(result.issues)

            key = self._canonical_key(
                str(self._get(pair, "sample_a_id", "")),
                str(self._get(pair, "sample_b_id", "")),
            )

            pair_ids_by_key.setdefault(key, []).append(pair_id)
            pair_ids_by_id.setdefault(pair_id, []).append(pair_id)

        # Duplicate Pair IDs
        if self.config.check_duplicate_pair_ids:
            for pair_id, occurrences in pair_ids_by_id.items():
                if len(occurrences) > 1:
                    issues_by_pair_id.setdefault(pair_id, []).append(
                        self._issue(
                            "DUPLICATE_PAIR_ID",
                            "Pair ID occurs more than once in the batch.",
                            pair_id,
                            field="pair_id",
                            details={"occurrences": len(occurrences)},
                        )
                    )

        # Duplicate unordered sample pairs, including reversed orientation.
        if self.config.check_duplicate_sample_pairs:
            for key, pair_ids in pair_ids_by_key.items():
                if len(pair_ids) > 1:
                    for pair_id in set(pair_ids):
                        issues_by_pair_id.setdefault(pair_id, []).append(
                            self._issue(
                                "DUPLICATE_SAMPLE_PAIR",
                                "Sample pair occurs more than once in the batch, regardless of order.",
                                pair_id,
                                details={
                                    "sample_a_id": key[0],
                                    "sample_b_id": key[1],
                                    "occurrences": len(pair_ids),
                                },
                            )
                        )

        results = [
            PairValidationResult(
                pair_id=pair_id,
                issues=tuple(issues),
            )
            for pair_id, issues in issues_by_pair_id.items()
        ]

        return PairValidationReport.from_results(
            results,
            validator_version=self.config.validator_version,
        )
