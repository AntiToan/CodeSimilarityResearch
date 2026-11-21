
from __future__ import annotations

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_candidate_partitioner import PairCandidatePartition
from src.data.pair_selection_models import (
    PairSelectionResult,
    PairSelectionReport,
    PairSelectionStatus,
    SplitSelectionStats,
)
from src.data.pair_label_quota_planner import PairLabelQuota


class PairSelectionResultAssembler:
    def assemble(
    self,
    partition: PairCandidatePartition,
    quotas: tuple[PairLabelQuota, ...],
    selected_pairs: tuple[PairRecord, ...],
    selector_version: str = "1.0.0",
    seed: int = 42,
) -> tuple[PairSelectionResult, PairSelectionReport]:
        if not isinstance(partition, PairCandidatePartition):
            raise TypeError("partition must be PairCandidatePartition")

        if not isinstance(quotas, tuple):
            raise TypeError("quotas must be a tuple")

        if not isinstance(selected_pairs, tuple):
            raise TypeError("selected_pairs must be a tuple")

        if not isinstance(selector_version, str) or not selector_version.strip():
            raise ValueError("selector_version must be non-empty")

        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("seed must be an integer")

        for quota in quotas:
            if not isinstance(quota, PairLabelQuota):
                raise TypeError("quotas must contain PairLabelQuota")

        for pair in selected_pairs:
            if not isinstance(pair, PairRecord):
                raise TypeError("selected_pairs must contain PairRecord")

        split_data = {
            "train": (
                partition.train_pairs,
                partition.train_positive_count,
                partition.train_negative_count,
            ),
            "validation": (
                partition.validation_pairs,
                partition.validation_positive_count,
                partition.validation_negative_count,
            ),
            "test": (
                partition.test_pairs,
                partition.test_positive_count,
                partition.test_negative_count,
            ),
        }

        quota_by_split = {
            quota.split: quota
            for quota in quotas
        }

        if len(quota_by_split) != len(quotas):
            raise ValueError("duplicate quota splits")

        if set(quota_by_split) != set(split_data):
            raise ValueError("quotas must cover train, validation, and test")

        candidate_ids = {
            pair.pair_id
            for group, _, _ in split_data.values()
            for pair in group
        }

        selected_ids = [pair.pair_id for pair in selected_pairs]

        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("selected pairs contain duplicate pair_id values")

        if not set(selected_ids).issubset(candidate_ids):
            raise ValueError("selected pairs must come from candidate partition")

        candidate_by_id = {
            pair.pair_id: pair
            for group, _, _ in split_data.values()
            for pair in group
        }

        for pair in selected_pairs:
            if candidate_by_id[pair.pair_id] is not pair:
                raise ValueError("selected pair objects must be preserved")

        selected_by_split = {
            split: tuple(
                pair
                for pair in selected_pairs
                if pair.split == PairSplit(split)
            )
            for split in split_data
        }

        stats = []

        for split, (
            candidates,
            candidate_positive_count,
            candidate_negative_count,
        ) in split_data.items():
            quota = quota_by_split[split]
            split_selected = selected_by_split[split]

            selected_positive_count = sum(
                pair.pair_type == PairType.POSITIVE
                for pair in split_selected
            )

            selected_negative_count = sum(
                pair.pair_type == PairType.NEGATIVE
                for pair in split_selected
            )

            if (
                quota.candidate_positive_count != candidate_positive_count
                or quota.candidate_negative_count != candidate_negative_count
            ):
                raise ValueError(
                    "quota candidate counts do not match partition"
                )

            if (
                selected_positive_count > quota.target_positive_count
                or selected_negative_count > quota.target_negative_count
            ):
                raise ValueError("selected counts exceed quota targets")

            stats.append(
                SplitSelectionStats(
                    split=split,
                    candidate_positive_count=candidate_positive_count,
                    candidate_negative_count=candidate_negative_count,
                    target_positive_count=quota.target_positive_count,
                    target_negative_count=quota.target_negative_count,
                    selected_positive_count=selected_positive_count,
                    selected_negative_count=selected_negative_count,
                    unmet_positive_quota=(
                        quota.target_positive_count - selected_positive_count
                    ),
                    unmet_negative_quota=(
                        quota.target_negative_count - selected_negative_count
                    ),
                )
            )

        positive_count = sum(
            pair.pair_type == PairType.POSITIVE
            for pair in selected_pairs
        )

        negative_count = sum(
            pair.pair_type == PairType.NEGATIVE
            for pair in selected_pairs
        )

        has_unmet_quota = any(
            stat.unmet_positive_quota > 0
            or stat.unmet_negative_quota > 0
            for stat in stats
        )

        selection_result = PairSelectionResult(
            selected_pairs=selected_pairs,
            positive_count=positive_count,
            negative_count=negative_count,
            total_count=len(selected_pairs),
            selection_status=(
                PairSelectionStatus.WARNING
                if has_unmet_quota
                else PairSelectionStatus.PASS
            ),
        )

        report = PairSelectionReport(
            selector_version=selector_version,
            seed=seed,
            split_stats=tuple(stats),
        )

        return selection_result, report
