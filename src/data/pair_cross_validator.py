from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.data.pair_validation_models import (
    PairValidationIssue,
    PairValidationReport,
    PairValidationResult,
)
from src.data.pair_schema_reference_validator import (
    PairSchemaReferenceValidator,
)
from src.data.pair_semantic_validator import (
    PairSemanticValidator,
)
from src.data.pair_integrity_validator import (
    PairIntegrityValidator,
)


@dataclass(frozen=True)
class PairCrossValidationConfig:
    validator_version: str = "1.0.0"


class PairCrossValidator:
    """
    Coordinates schema/reference, semantic, and integrity validation.

    This class only aggregates validation issues. It does not repair,
    filter, or mutate pairs.
    """

    def __init__(
        self,
        config: PairCrossValidationConfig | None = None,
        schema_validator: PairSchemaReferenceValidator | None = None,
        semantic_validator: PairSemanticValidator | None = None,
        integrity_validator: PairIntegrityValidator | None = None,
    ) -> None:
        self.config = config or PairCrossValidationConfig()

        self.schema_validator = (
            schema_validator or PairSchemaReferenceValidator()
        )
        self.semantic_validator = (
            semantic_validator or PairSemanticValidator()
        )
        self.integrity_validator = (
            integrity_validator or PairIntegrityValidator()
        )

    @staticmethod
    def _get(record: Any, key: str, default=None):
        if isinstance(record, Mapping):
            return record.get(key, default)
        return getattr(record, key, default)

    @staticmethod
    def _aggregate_reports(
        reports: Sequence[PairValidationReport],
        validator_version: str,
    ) -> PairValidationReport:
        issues_by_pair_id: dict[
            str, list[PairValidationIssue]
        ] = defaultdict(list)

        for report in reports:
            for result in report.pair_results:
                issues_by_pair_id[result.pair_id].extend(result.issues)

        results = [
            PairValidationResult(
                pair_id=pair_id,
                issues=tuple(issues),
            )
            for pair_id, issues in sorted(
                issues_by_pair_id.items()
            )
        ]

        return PairValidationReport.from_results(
            results,
            validator_version=validator_version,
        )

    def validate_pair(
        self,
        pair: Any,
        samples: Mapping[str, Any],
        variants: Mapping[str, Any],
        screening_records: Mapping | None = None,
        duplicate_groups: Mapping | None = None,
    ) -> PairValidationResult:
        """
        Validate a single pair using all three validators.
        """
        report = self.validate_batch(
            pairs=[pair],
            samples=samples,
            variants=variants,
            screening_records=screening_records,
            duplicate_groups=duplicate_groups,
        )

        if report.pair_results:
            return report.pair_results[0]

        pair_id = self._get(pair, "pair_id") or "__invalid_pair_id__"

        return PairValidationResult(
            pair_id=pair_id,
            issues=(),
        )

    def validate_batch(
        self,
        pairs: Sequence[Any],
        samples: Mapping[str, Any],
        variants: Mapping[str, Any],
        screening_records: Mapping | None = None,
        duplicate_groups: Mapping | None = None,
    ) -> PairValidationReport:
        """
        Run all validators and aggregate their issues.

        The input pairs are not modified and are not filtered.
        """
        screening_records = screening_records or {}
        duplicate_groups = duplicate_groups or {}

        # 1. Schema and sample-reference validation
        schema_report = self.schema_validator.validate_batch(
            pairs=pairs,
            samples=samples,
        )

        # 2. Positive/negative semantic validation
        semantic_report = self.semantic_validator.validate_batch(
            pairs=pairs,
            samples=samples,
            variants=variants,
            screening_records=screening_records,
            duplicate_groups=duplicate_groups,
        )

        # 3. Pair identity, duplicates, split/group integrity
        integrity_report = self.integrity_validator.validate_batch(
            pairs=pairs,
            samples=samples,
            duplicate_groups=duplicate_groups,
        )

        # 4. Aggregate all issues
        return self._aggregate_reports(
            reports=[
                schema_report,
                semantic_report,
                integrity_report,
            ],
            validator_version=self.config.validator_version,
        )