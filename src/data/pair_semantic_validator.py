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


APPROVED_TRANSFORMATIONS = {
    "formatting",
    "whitespace",
    "comments",
    "scope_aware_local_variable_renaming",
    "safe_function_local_identifier_renaming",
}

TRANSFORMATION_ALIASES = {
    "format": "formatting",
    "formatting": "formatting",
    "whitespace": "whitespace",
    "comment": "comments",
    "comments": "comments",
    "scope_aware_local_variable_renaming":
        "scope_aware_local_variable_renaming",
    "safe_function_local_identifier_renaming":
        "safe_function_local_identifier_renaming",
}

PASS_STATUSES = {"PASS", "PASSED", "SUCCESS", "ACCEPTED"}


@dataclass(frozen=True)
class PairSemanticValidationConfig:
    validator_version: str = "1.0.0"


class PairSemanticValidator:
    """
    Semantic validation for positive and negative pairs.

    Positive:
      - same lineage
      - original + validated variant
      - approved transformation
      - matching split

    Negative:
      - originals only
      - cross-problem
      - cross-lineage
      - no known duplicate group
      - successful screening evidence
      - matching split

    This validator does not perform similarity calculations itself.
    """

    def __init__(
        self,
        config: PairSemanticValidationConfig | None = None,
    ) -> None:
        self.config = config or PairSemanticValidationConfig()

    @staticmethod
    def _get(record: Any, key: str, default=None):
        if isinstance(record, Mapping):
            return record.get(key, default)
        return getattr(record, key, default)

    @classmethod
    def _text(cls, record: Any, key: str):
        value = cls._get(record, key)
        return value if isinstance(value, str) else None

    @classmethod
    def _split(cls, record: Any):
        value = cls._get(record, "split")
        if hasattr(value, "value"):
            value = value.value
        return value

    @classmethod
    def _source_id(cls, sample: Any, sample_id: str):
        source_id = cls._get(sample, "source_id")
        if source_id is not None:
            return source_id

        original_id = cls._get(sample, "original_sample_id")
        if original_id is not None:
            return original_id

        return sample_id

    @classmethod
    def _is_variant(cls, sample: Any, sample_id: str, variants: Mapping):
        if sample_id in variants:
            return True

        original_sample_id = cls._get(sample, "original_sample_id")
        if original_sample_id is not None:
            return True

        sample_type = cls._get(sample, "sample_type")
        if isinstance(sample_type, str) and sample_type.lower() == "variant":
            return True

        return False

    @classmethod
    def _variant_record(cls, variants: Mapping, sample_id: str):
        return variants.get(sample_id)

    @staticmethod
    def _canonical_pair_key(sample_a_id: str, sample_b_id: str):
        return tuple(sorted((sample_a_id, sample_b_id)))

    @staticmethod
    def _issue(
        rule_id: str,
        message: str,
        pair_id: str,
        field: str | None = None,
        details: tuple[tuple[str, str], ...] = (),
    ):
        return PairValidationIssue(
            rule_id=rule_id,
            severity=ValidationSeverity.ERROR,
            message=message,
            pair_id=pair_id,
            field=field,
            details=details,
        )

    # ---------------------------------------------------------
    # Positive validation
    # ---------------------------------------------------------

    def _validate_positive(
        self,
        pair: Any,
        pair_id: str,
        samples: Mapping,
        variants: Mapping,
    ) -> list[PairValidationIssue]:
        issues = []

        sample_a_id = self._text(pair, "sample_a_id")
        sample_b_id = self._text(pair, "sample_b_id")

        if not sample_a_id or not sample_b_id:
            return issues

        sample_a = samples.get(sample_a_id)
        sample_b = samples.get(sample_b_id)

        if sample_a is None or sample_b is None:
            return issues

        variant_a = self._is_variant(sample_a, sample_a_id, variants)
        variant_b = self._is_variant(sample_b, sample_b_id, variants)

        if variant_a == variant_b:
            issues.append(
                self._issue(
                    "POSITIVE_ORIGINAL_VARIANT_ROLE",
                    "Positive pair must contain exactly one original and one variant",
                    pair_id,
                )
            )
            return issues

        original_id = sample_b_id if variant_a else sample_a_id
        variant_id = sample_a_id if variant_a else sample_b_id

        original_sample = sample_b if variant_a else sample_a
        variant_sample = sample_a if variant_a else sample_b

        original_source = self._source_id(original_sample, original_id)
        variant_source = self._source_id(variant_sample, variant_id)

        if original_source != variant_source:
            issues.append(
                self._issue(
                    "POSITIVE_LINEAGE_MISMATCH",
                    "Positive pair samples do not share the same source lineage",
                    pair_id,
                )
            )

        variant_record = self._variant_record(variants, variant_id)

        if variant_record is None:
            issues.append(
                self._issue(
                    "POSITIVE_VARIANT_RECORD_MISSING",
                    "Variant registry record is missing",
                    pair_id,
                )
            )
            return issues

        registry_original_id = self._get(
            variant_record, "original_sample_id"
        )

        if registry_original_id != original_id:
            issues.append(
                self._issue(
                    "POSITIVE_VARIANT_ORIGINAL_MISMATCH",
                    "Variant registry does not point to the paired original sample",
                    pair_id,
                )
            )

        # Transformation metadata validation
        transformation = self._get(
            variant_record, "transformation_type"
        )

        if not isinstance(transformation, str) or not transformation.strip():
            issues.append(
                self._issue(
                    "POSITIVE_TRANSFORMATION_MISSING",
                    "Variant transformation metadata is missing",
                    pair_id,
                )
            )
        else:
            normalized_transformation = TRANSFORMATION_ALIASES.get(
                transformation.strip().lower()
            )

            if normalized_transformation not in APPROVED_TRANSFORMATIONS:
                issues.append(
                    self._issue(
                        "POSITIVE_TRANSFORMATION_UNAPPROVED",
                        f"Unapproved transformation: {transformation}",
                        pair_id,
                    )
                )

        # Validation status: must have passed variant validation
        validation_status = self._get(
            variant_record, "validation_status"
        )

        if validation_status is None:
            validation_status = self._get(
                variant_record, "status"
            )

        if isinstance(validation_status, str):
            validation_status = validation_status.upper()

        if validation_status not in PASS_STATUSES:
            issues.append(
                self._issue(
                    "POSITIVE_VARIANT_VALIDATION_FAILED",
                    "Variant does not have a successful validation status",
                    pair_id,
                )
            )

        # Variant and original must belong to the same split
        original_split = self._split(original_sample)
        variant_split = self._split(variant_sample)
        pair_split = self._split(pair)

        if (
            original_split is not None
            and variant_split is not None
            and original_split != variant_split
        ):
            issues.append(
                self._issue(
                    "POSITIVE_SPLIT_MISMATCH",
                    "Original and variant belong to different splits",
                    pair_id,
                )
            )

        if (
            pair_split is not None
            and original_split is not None
            and pair_split != original_split
        ):
            issues.append(
                self._issue(
                    "POSITIVE_PAIR_SPLIT_MISMATCH",
                    "Positive pair split does not match its original source",
                    pair_id,
                )
            )

        return issues

    # ---------------------------------------------------------
    # Negative validation
    # ---------------------------------------------------------

    def _validate_negative(
        self,
        pair: Any,
        pair_id: str,
        samples: Mapping,
        variants: Mapping,
        screening_records: Mapping,
        duplicate_groups: Mapping,
    ) -> list[PairValidationIssue]:
        issues = []

        sample_a_id = self._text(pair, "sample_a_id")
        sample_b_id = self._text(pair, "sample_b_id")

        if not sample_a_id or not sample_b_id:
            return issues

        sample_a = samples.get(sample_a_id)
        sample_b = samples.get(sample_b_id)

        if sample_a is None or sample_b is None:
            return issues

        # Must use originals only
        if self._is_variant(sample_a, sample_a_id, variants):
            issues.append(
                self._issue(
                    "NEGATIVE_VARIANT_ENDPOINT",
                    "Negative pair cannot contain generated variants",
                    pair_id,
                    "sample_a_id",
                )
            )

        if self._is_variant(sample_b, sample_b_id, variants):
            issues.append(
                self._issue(
                    "NEGATIVE_VARIANT_ENDPOINT",
                    "Negative pair cannot contain generated variants",
                    pair_id,
                    "sample_b_id",
                )
            )

        problem_a = self._get(sample_a, "problem_id")
        problem_b = self._get(sample_b, "problem_id")

        if problem_a is not None and problem_b is not None:
            if str(problem_a) == str(problem_b):
                issues.append(
                    self._issue(
                        "NEGATIVE_SAME_PROBLEM",
                        "Negative pair samples must belong to different problems",
                        pair_id,
                    )
                )

        source_a = self._source_id(sample_a, sample_a_id)
        source_b = self._source_id(sample_b, sample_b_id)

        if source_a == source_b:
            issues.append(
                self._issue(
                    "NEGATIVE_SAME_LINEAGE",
                    "Negative pair samples belong to the same source lineage",
                    pair_id,
                )
            )

        # Duplicate group lookup supports sample -> group mapping
        duplicate_group_a = duplicate_groups.get(sample_a_id)
        duplicate_group_b = duplicate_groups.get(sample_b_id)

        if (
            duplicate_group_a is not None
            and duplicate_group_a == duplicate_group_b
        ):
            issues.append(
                self._issue(
                    "NEGATIVE_KNOWN_DUPLICATE",
                    "Negative pair endpoints belong to the same known duplicate group",
                    pair_id,
                )
            )

        # Screening evidence is keyed by canonical sample pair
        canonical_key = self._canonical_pair_key(
            sample_a_id, sample_b_id
        )

        screening_record = screening_records.get(canonical_key)

        if screening_record is None:
            # Also support a pair_id-keyed screening record.
            screening_record = screening_records.get(pair_id)

        if screening_record is None:
            issues.append(
                self._issue(
                    "NEGATIVE_SCREENING_RECORD_MISSING",
                    "Negative pair has no traceable similarity screening record",
                    pair_id,
                )
            )
        else:
            screening_status = self._get(
                screening_record, "status"
            )

            if screening_status is None:
                screening_status = self._get(
                    screening_record, "screening_status"
            )

            if isinstance(screening_status, str):
                screening_status = screening_status.upper()

            if screening_status not in PASS_STATUSES:
                issues.append(
                    self._issue(
                        "NEGATIVE_SCREENING_NOT_PASSED",
                        "Similarity screening was not successful",
                        pair_id,
                    )
                )

            # Require screening traceability
            screening_method = self._get(
                screening_record, "method"
            )

            if screening_method is None:
                screening_method = self._get(
                    screening_record, "screening_method"
                )

            if not isinstance(screening_method, str) or not screening_method.strip():
                issues.append(
                    self._issue(
                        "NEGATIVE_SCREENING_METHOD_MISSING",
                        "Screening record does not identify its screening method",
                        pair_id,
                    )
                )

        # Both samples must be in the same split, and pair must match it
        split_a = self._split(sample_a)
        split_b = self._split(sample_b)
        pair_split = self._split(pair)

        if (
            split_a is not None
            and split_b is not None
            and split_a != split_b
        ):
            issues.append(
                self._issue(
                    "NEGATIVE_SPLIT_MISMATCH",
                    "Negative pair endpoints belong to different splits",
                    pair_id,
                )
            )

        if (
            pair_split is not None
            and split_a is not None
            and pair_split != split_a
        ):
            issues.append(
                self._issue(
                    "NEGATIVE_PAIR_SPLIT_MISMATCH",
                    "Negative pair split does not match sample metadata",
                    pair_id,
                )
            )

        return issues

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def validate_pair(
        self,
        pair: Any,
        samples: Mapping,
        variants: Mapping,
        screening_records: Mapping | None = None,
        duplicate_groups: Mapping | None = None,
    ) -> PairValidationResult:
        screening_records = screening_records or {}
        duplicate_groups = duplicate_groups or {}

        pair_id = self._text(pair, "pair_id") or "__invalid_pair_id__"
        pair_type = self._text(pair, "pair_type")

        issues = []

        if pair_type == "positive":
            issues.extend(
                self._validate_positive(
                    pair,
                pair_id,
                    samples,
                    variants,
                )
            )
        elif pair_type == "negative":
            issues.extend(
                self._validate_negative(
                    pair,
                pair_id,
                samples,
                variants,
                screening_records,
                duplicate_groups,
            )
            )
        else:
            issues.append(
                self._issue(
                    "SEMANTIC_UNKNOWN_PAIR_TYPE",
                    "Cannot perform semantic validation for unknown pair_type",
                    pair_id,
                    "pair_type",
                )
            )

        return PairValidationResult(
            pair_id=pair_id,
            issues=tuple(issues),
        )

    def validate_batch(
        self,
        pairs: Sequence,
        samples: Mapping,
        variants: Mapping,
        screening_records: Mapping | None = None,
        duplicate_groups: Mapping | None = None,
    ) -> PairValidationReport:
        screening_records = screening_records or {}
        duplicate_groups = duplicate_groups or {}

        aggregated: dict[str, list[PairValidationIssue]] = defaultdict(list)
        seen_pair_ids: set[str] = set()

        for pair in pairs:
            result = self.validate_pair(
                pair,
                samples,
                variants,
                screening_records,
                duplicate_groups,
            )

            aggregated[result.pair_id].extend(result.issues)

            if result.pair_id in seen_pair_ids:
                aggregated[result.pair_id].append(
                    self._issue(
                        "SEMANTIC_DUPLICATE_PAIR_ID",
                        "Duplicate pair_id in semantic validation batch",
                        result.pair_id,
                    )
                )

            seen_pair_ids.add(result.pair_id)

        results = [
            PairValidationResult(
                pair_id=pair_id,
                issues=tuple(issues),
            )
            for pair_id, issues in aggregated.items()
        ]

        return PairValidationReport.from_results(
            results,
            validator_version=self.config.validator_version,
        )