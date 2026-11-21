from __future__ import annotations

from typing import Iterable
from collections import Counter
from src.data.final_dataset_validation_config import (
    FinalDatasetValidationConfig,
)
from src.data.pair_models import PairRecord
from src.data.final_dataset_validation_models import (
    FinalDatasetValidationIssue,
    FinalDatasetValidationReport,
    FinalDatasetValidationStatus,
)
from collections import Counter
from src.data.pair_models import PairRecord, PairSplit
from src.data.pair_selection_models import PairSelectionResult

class FinalDatasetValidator:
    def __init__(
        self,
        config: FinalDatasetValidationConfig | None = None,
    ) -> None:
        self.config = config or FinalDatasetValidationConfig()

    @staticmethod
    def _resolve_status(
        issues: list[FinalDatasetValidationIssue],
    ) -> FinalDatasetValidationStatus:
        if any(
            issue.severity == FinalDatasetValidationStatus.FAIL
            for issue in issues
        ):
            return FinalDatasetValidationStatus.FAIL

        if any(
            issue.severity == FinalDatasetValidationStatus.WARNING
            for issue in issues
        ):
            return FinalDatasetValidationStatus.WARNING

        return FinalDatasetValidationStatus.PASS

    def validate(
        self,
        pairs: Iterable[PairRecord],
        selection_result: PairSelectionResult | None = None,
    ) -> FinalDatasetValidationReport:
        pair_list = tuple(pairs)

        for pair in pair_list:
            if not isinstance(pair, PairRecord):
                raise TypeError(
                    "All items must be PairRecord instances."
                )

        if selection_result is not None and not isinstance(
            selection_result,
            PairSelectionResult,
        ):
            raise TypeError(
                "selection_result must be a PairSelectionResult."
            )

        if self.config.require_non_empty and not pair_list:
            raise ValueError(
                "Final dataset must not be empty."
            )

        positive_count = sum(
            pair.label == 1 for pair in pair_list
        )
        negative_count = sum(
            pair.label == 0 for pair in pair_list
        )

        issues: list[FinalDatasetValidationIssue] = []

        if self.config.check_duplicate_pair_ids:
            pair_id_counts = Counter(
                pair.pair_id for pair in pair_list
            )

            duplicate_ids = [
                pair_id
                for pair_id, count in pair_id_counts.items()
                if count > 1
            ]

            if duplicate_ids:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="DUPLICATE_PAIR_ID",
                        message=(
                            "Duplicate pair IDs found: "
                            f"{duplicate_ids}"
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

        if self.config.check_duplicate_sample_pairs:
            sample_pair_counts = Counter(
                (pair.sample_a_id, pair.sample_b_id)
                for pair in pair_list
            )

            duplicate_sample_pairs = [
                sample_pair
                for sample_pair, count in sample_pair_counts.items()
                if count > 1
            ]

            if duplicate_sample_pairs:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="DUPLICATE_SAMPLE_PAIR",
                        message=(
                            "Duplicate sample pairs found: "
                            f"{duplicate_sample_pairs}"
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

        if self.config.require_both_labels:
            if positive_count == 0:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="MISSING_POSITIVE_LABEL",
                        message="Dataset contains no positive pairs.",
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

            if negative_count == 0:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="MISSING_NEGATIVE_LABEL",
                        message="Dataset contains no negative pairs.",
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

        if self.config.check_split_integrity:
            sample_splits: dict[str, set[PairSplit]] = {}

            for pair in pair_list:
                sample_splits.setdefault(
                    pair.sample_a_id, set()
                ).add(pair.split)

                sample_splits.setdefault(
                    pair.sample_b_id, set()
                ).add(pair.split)

            leaked_samples = {
                sample_id: splits
                for sample_id, splits in sample_splits.items()
                if len(splits) > 1
            }

            if leaked_samples:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SPLIT_SAMPLE_LEAKAGE",
                        message=(
                            "Samples appear across multiple splits: "
                            f"{leaked_samples}"
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )
        
        # if not isinstance(
        #     selection_result,
        #     PairSelectionResult,
        # ):
        #     raise TypeError(
        #         "selection_result must be a PairSelectionResult."
        #     )

        if (self.config.check_selection_integrity and selection_result is not None):
            for pair in selection_result.selected_pairs:
                if not isinstance(pair, PairRecord):
                    raise TypeError(
                        "All selection_result items must be PairRecord instances."
                    )
                
            actual_pair_ids = {
                pair.pair_id for pair in pair_list
            }

            selected_pair_ids = {
                pair.pair_id
                for pair in selection_result.selected_pairs
            }

            selection_pair_ids = [
                pair.pair_id
                for pair in selection_result.selected_pairs
            ]

            duplicate_selection_pair_ids = sorted(
                pair_id
                for pair_id, count in Counter(
                    selection_pair_ids
                ).items()
                if count > 1
            )

            if duplicate_selection_pair_ids:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_DUPLICATE_PAIR_ID",
                        message=(
                            "Duplicate pair IDs found in selection_result: "
                            f"{duplicate_selection_pair_ids}"
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

            selection_sample_pairs = [
                tuple(sorted((pair.sample_a_id, pair.sample_b_id)))
                for pair in selection_result.selected_pairs
            ]

            duplicate_selection_sample_pairs = sorted(
                sample_pair
                for sample_pair, count in Counter(
                    selection_sample_pairs
                ).items()
                if count > 1
            )

            if duplicate_selection_sample_pairs:
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_DUPLICATE_SAMPLE_PAIR",
                        message=(
                            "Duplicate sample pairs found in selection_result: "
                            f"{duplicate_selection_sample_pairs}"
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

            if Counter(pair_list) != Counter(selection_result.selected_pairs):
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_MISMATCH",
                        message=(
                            "Final dataset does not match "
                            "selection_result selected_pairs."
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

            actual_positive_count = sum(
                pair.label == 1
                for pair in selection_result.selected_pairs
            )

            actual_negative_count = sum(
                pair.label == 0
                for pair in selection_result.selected_pairs
            )

            actual_total_count = len(
                selection_result.selected_pairs
            )

            if (
                actual_positive_count != selection_result.positive_count
                or actual_negative_count != selection_result.negative_count
                or actual_total_count != selection_result.total_count
            ):
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_COUNT_MISMATCH",
                        message=(
                            "Selection result counts do not match "
                            "its selected pairs."
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

            if (
                selection_result.selection_status.value == "WARNING"
            ):
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_WARNING",
                        message=(
                            "Pair selection completed with warnings."
                        ),
                        severity=FinalDatasetValidationStatus.WARNING,
                    )
                )

            if selection_result.selection_status.value == "FAIL":
                issues.append(
                    FinalDatasetValidationIssue(
                        code="SELECTION_RESULT_FAILURE",
                        message=(
                            "Pair selection completed with failure."
                        ),
                        severity=FinalDatasetValidationStatus.FAIL,
                    )
                )

        status = self._resolve_status(issues)

        return FinalDatasetValidationReport(
            status=status,
            total_pairs=len(pair_list),
            positive_count=positive_count,
            negative_count=negative_count,
            issues=tuple(issues),
        )