from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.data.pair_validation_models import (
    PairValidationIssue,
    PairValidationReport,
    PairValidationResult,
    ValidationSeverity,
)


REQUIRED_FIELDS = (
    "pair_id",
    "sample_a_id",
    "sample_b_id",
    "label",
    "pair_type",
    "split",
    "source_a_id",
    "source_b_id",
    "problem_a_id",
    "problem_b_id",
    "generation_method",
    "created_seed",
)

VALID_LABELS = {0, 1}
VALID_PAIR_TYPES = {"positive", "negative"}
VALID_SPLITS = {"train", "validation", "test"}


@dataclass(frozen=True)
class PairSchemaReferenceValidationConfig:
    validator_version: str = "1.0.0"


class PairSchemaReferenceValidator:
    """
    Validates pair schema and sample references.

    This checkpoint intentionally does not validate positive/negative
    semantic constraints such as lineage or similarity screening.
    """

    def __init__(
        self,
        config: PairSchemaReferenceValidationConfig | None = None,
    ) -> None:
        self.config = config or PairSchemaReferenceValidationConfig()

    @staticmethod
    def _get(record: Any, field: str, default: Any = None) -> Any:
        if isinstance(record, Mapping):
            return record.get(field, default)

        return getattr(record, field, default)

    @staticmethod
    def _sample_metadata(samples: Mapping[str, Any], sample_id: str):
        return samples.get(sample_id)

    @classmethod
    def _metadata_value(cls, metadata: Any, field: str):
        return cls._get(metadata, field)

    @classmethod
    def _expected_source_id(cls, metadata: Any, sample_id: str):
        """
        Source lineage normalization:
        - source_id, if already normalized
        - original_sample_id, for generated variants
        - sample_id, for original samples
        """
        source_id = cls._metadata_value(metadata, "source_id")
        if source_id is not None:
            return source_id

        original_sample_id = cls._metadata_value(
            metadata, "original_sample_id"
        )
        if original_sample_id is not None:
            return original_sample_id

        return sample_id

    @staticmethod
    def _issue(
        rule_id: str,
        message: str,
        pair_id: str | None,
        field: str | None = None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> PairValidationIssue:
        return PairValidationIssue(
            rule_id=rule_id,
            severity=ValidationSeverity.ERROR,
            message=message,
            pair_id=pair_id,
            field=field,
            details=details,
        )

    def validate_pair(
        self,
        pair: Any,
        samples: Mapping[str, Any],
    ) -> PairValidationResult:
        issues: list[PairValidationIssue] = []

        raw_pair_id = self._get(pair, "pair_id")
        pair_id = (
            raw_pair_id
            if isinstance(raw_pair_id, str) and raw_pair_id.strip()
            else "__invalid_pair_id__"
        )

        # -------------------------
        # 1. Required fields
        # -------------------------
        for field in REQUIRED_FIELDS:
            if not (
                isinstance(pair, Mapping) and field in pair
            ) and not (
                not isinstance(pair, Mapping)
                and hasattr(pair, field)
            ):
                issues.append(
                    self._issue(
                        "SCHEMA_MISSING_FIELD",
                        f"Missing required field: {field}",
                        pair_id,
                        field,
                    )
                )

        # -------------------------
        # 2. String field validation
        # -------------------------
        string_fields = (
            "pair_id",
            "sample_a_id",
            "sample_b_id",
            "pair_type",
            "split",
            "source_a_id",
            "source_b_id",
            "problem_a_id",
            "problem_b_id",
            "generation_method",
        )

        for field in string_fields:
            value = self._get(pair, field)

            if not isinstance(value, str) or not value.strip():
                issues.append(
                    self._issue(
                        "SCHEMA_INVALID_STRING",
                        f"{field} must be a non-empty string",
                        pair_id,
                        field,
                    )
                )

        # -------------------------
        # 3. Label
        # -------------------------
        label = self._get(pair, "label")

        if isinstance(label, bool) or not isinstance(label, int):
            issues.append(
                self._issue(
                    "SCHEMA_INVALID_LABEL_TYPE",
                    "label must be an integer (0 or 1)",
                    pair_id,
                    "label",
                )
            )
        elif label not in VALID_LABELS:
            issues.append(
                self._issue(
                    "SCHEMA_INVALID_LABEL",
                    "label must be either 0 or 1",
                    pair_id,
                    "label",
                )
            )

        # -------------------------
        # 4. Pair type
        # -------------------------
        pair_type = self._get(pair, "pair_type")

        if isinstance(pair_type, str) and pair_type not in VALID_PAIR_TYPES:
            issues.append(
                self._issue(
                    "SCHEMA_INVALID_PAIR_TYPE",
                    "pair_type must be positive or negative",
                    pair_id,
                    "pair_type",
                )
            )

        # -------------------------
        # 5. Label/type consistency
        # -------------------------
        if (
            isinstance(label, int)
            and not isinstance(label, bool)
            and isinstance(pair_type, str)
        ):
            expected = {
                1: "positive",
                0: "negative",
            }.get(label)

            if expected is not None and pair_type != expected:
                issues.append(
                    self._issue(
                        "SCHEMA_LABEL_TYPE_MISMATCH",
                        "label does not match pair_type",
                        pair_id,
                        "label",
                    )
                )

        # -------------------------
        # 6. Split
        # -------------------------
        split = self._get(pair, "split")

        if isinstance(split, str) and split not in VALID_SPLITS:
            issues.append(
                self._issue(
                    "SCHEMA_INVALID_SPLIT",
                    "split must be train, validation, or test",
                    pair_id,
                    "split",
                )
            )

        # -------------------------
        # 7. Seed
        # -------------------------
        seed = self._get(pair, "created_seed")

        if seed is not None and (
            isinstance(seed, bool) or not isinstance(seed, int)
        ):
            issues.append(
                self._issue(
                    "SCHEMA_INVALID_SEED",
                    "created_seed must be an integer or None",
                    pair_id,
                    "created_seed",
                )
            )

        # -------------------------
        # 8. Sample IDs
        # -------------------------
        sample_a_id = self._get(pair, "sample_a_id")
        sample_b_id = self._get(pair, "sample_b_id")

        valid_a_id = isinstance(sample_a_id, str) and bool(sample_a_id.strip())
        valid_b_id = isinstance(sample_b_id, str) and bool(sample_b_id.strip())

        if valid_a_id and valid_b_id and sample_a_id == sample_b_id:
            issues.append(
                self._issue(
                    "REFERENCE_SELF_PAIR",
                    "A pair cannot reference the same sample twice",
                    pair_id,
                )
            )

        # -------------------------
        # 9. Sample existence
        # -------------------------
        metadata_a = None
        metadata_b = None

        if valid_a_id:
            metadata_a = self._sample_metadata(samples, sample_a_id)
            if metadata_a is None:
                issues.append(
                    self._issue(
                        "REFERENCE_SAMPLE_NOT_FOUND",
                        f"sample_a_id not found: {sample_a_id}",
                        pair_id,
                        "sample_a_id",
                    )
                )

        if valid_b_id:
            metadata_b = self._sample_metadata(samples, sample_b_id)
            if metadata_b is None:
                issues.append(
                    self._issue(
                        "REFERENCE_SAMPLE_NOT_FOUND",
                        f"sample_b_id not found: {sample_b_id}",
                        pair_id,
                        "sample_b_id",
                    )
                )

        # -------------------------
        # 10. Metadata consistency
        # -------------------------
        if metadata_a is not None:
            expected_source_a = self._expected_source_id(
                metadata_a, sample_a_id
            )
            expected_problem_a = self._metadata_value(
                metadata_a, "problem_id"
            )
            expected_split_a = self._metadata_value(
                metadata_a, "split"
            )

            actual_source_a = self._get(pair, "source_a_id")
            actual_problem_a = self._get(pair, "problem_a_id")

            if actual_source_a != expected_source_a:
                issues.append(
                    self._issue(
                        "REFERENCE_SOURCE_MISMATCH",
                        "source_a_id does not match sample metadata",
                        pair_id,
                        "source_a_id",
                    )
                )

            if actual_problem_a != expected_problem_a:
                issues.append(
                    self._issue(
                        "REFERENCE_PROBLEM_MISMATCH",
                        "problem_a_id does not match sample metadata",
                        pair_id,
                        "problem_a_id",
                    )
                )

            if (
                isinstance(split, str)
                and expected_split_a is not None
                and split != expected_split_a
            ):
                issues.append(
                    self._issue(
                        "REFERENCE_SPLIT_MISMATCH",
                        "Pair split does not match sample_a split",
                        pair_id,
                        "split",
                    )
                )

        if metadata_b is not None:
            expected_source_b = self._expected_source_id(
                metadata_b, sample_b_id
            )
            expected_problem_b = self._metadata_value(
                metadata_b, "problem_id"
            )
            expected_split_b = self._metadata_value(
                metadata_b, "split"
            )

            actual_source_b = self._get(pair, "source_b_id")
            actual_problem_b = self._get(pair, "problem_b_id")

            if actual_source_b != expected_source_b:
                issues.append(
                    self._issue(
                        "REFERENCE_SOURCE_MISMATCH",
                        "source_b_id does not match sample metadata",
                        pair_id,
                        "source_b_id",
                    )
                )

            if actual_problem_b != expected_problem_b:
                issues.append(
                    self._issue(
                        "REFERENCE_PROBLEM_MISMATCH",
                        "problem_b_id does not match sample metadata",
                        pair_id,
                        "problem_b_id",
                    )
                )

            if (
                isinstance(split, str)
                and expected_split_b is not None
                and split != expected_split_b
            ):
                issues.append(
                    self._issue(
                        "REFERENCE_SPLIT_MISMATCH",
                        "Pair split does not match sample_b split",
                        pair_id,
                        "split",
                    )
                )

        return PairValidationResult(
            pair_id=pair_id,
            issues=tuple(issues),
        )

    def validate_batch(
        self,
        pairs: Sequence[Any],
        samples: Mapping[str, Any],
    ) -> PairValidationReport:
        """
        Validate all pairs.

        Duplicate pair IDs are reported. Results are aggregated by pair_id
        because PairValidationReport requires unique result identifiers.
        """
        issues_by_pair_id: dict[str, list[PairValidationIssue]] = defaultdict(list)
        seen_pair_ids: set[str] = set()

        for index, pair in enumerate(pairs):
            result = self.validate_pair(pair, samples)
            pair_id = result.pair_id

            issues_by_pair_id[pair_id].extend(result.issues)

            if pair_id in seen_pair_ids:
                issues_by_pair_id[pair_id].append(
                    self._issue(
                        "SCHEMA_DUPLICATE_PAIR_ID",
                        "Duplicate pair_id detected in batch",
                        pair_id,
                        "pair_id",
                    )
                )

            seen_pair_ids.add(pair_id)

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