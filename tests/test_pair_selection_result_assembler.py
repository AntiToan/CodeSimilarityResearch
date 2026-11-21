
import pytest

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_candidate_partitioner import PairCandidatePartitioner
from src.data.pair_label_quota_planner import (
    PairLabelQuota,
    PairLabelQuotaPlanner,
)
from src.data.pair_selection_models import PairSelectionStatus
from src.data.pair_final_selector import PairFinalSelector
from src.data.pair_selection_result_assembler import (
    PairSelectionResultAssembler,
)
from src.data.pair_selection_models import (
    PairSelectionConfig,
    PairSelectionStatus,
)
from dataclasses import replace

def make_pair(pair_id, pair_type, split):
    positive = pair_type == PairType.POSITIVE

    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=f"{pair_id}_a",
        sample_b_id=f"{pair_id}_b",
        label=1 if positive else 0,
        pair_type=pair_type,
        split=split,
        source_a_id=f"{pair_id}_src_a",
        source_b_id=f"{pair_id}_src_a" if positive else f"{pair_id}_src_b",
        problem_a_id="problem_1",
        problem_b_id="problem_1" if positive else "problem_2",
        generation_method="test",
        created_seed=42,
    )


def make_candidates():
    return (
        make_pair("tr_p1", PairType.POSITIVE, PairSplit.TRAIN),
        make_pair("tr_p2", PairType.POSITIVE, PairSplit.TRAIN),
        make_pair("tr_n1", PairType.NEGATIVE, PairSplit.TRAIN),
        make_pair("tr_n2", PairType.NEGATIVE, PairSplit.TRAIN),
        make_pair("va_p1", PairType.POSITIVE, PairSplit.VALIDATION),
        make_pair("va_n1", PairType.NEGATIVE, PairSplit.VALIDATION),
        make_pair("te_p1", PairType.POSITIVE, PairSplit.TEST),
        make_pair("te_n1", PairType.NEGATIVE, PairSplit.TEST),
    )


def prepare_selection():
    candidates = make_candidates()
    partition = PairCandidatePartitioner().partition(candidates)

    quotas = PairLabelQuotaPlanner().plan(
        partition,
        PairSelectionConfig(),
    )

    selected = []

    selector = PairFinalSelector()

    for split_pairs in (
        partition.train_pairs,
        partition.validation_pairs,
        partition.test_pairs,
    ):
        split_name = split_pairs[0].split.value if split_pairs else None

        if split_name is None:
            continue

        quota = next(q for q in quotas if q.split == split_name)

        selected.extend(
            selector.select(
                split_pairs,
                quota,
                seed=42,
            )
        )

    return partition, quotas, tuple(selected)


def test_assembly_counts_selected_pairs():
    partition, quotas, selected = prepare_selection()

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    assert result.total_count == 8
    assert result.positive_count == 4
    assert result.negative_count == 4


def test_assembly_preserves_selected_pair_objects():
    partition, quotas, selected = prepare_selection()

    result, _ = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    assert result.selected_pairs == selected

    for actual, expected in zip(result.selected_pairs, selected):
        assert actual is expected


def test_assembly_report_has_all_splits():
    partition, quotas, selected = prepare_selection()

    _, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    assert {stat.split for stat in report.split_stats} == {
        "train",
        "validation",
        "test",
    }


def test_assembly_reports_split_counts():
    partition, quotas, selected = prepare_selection()

    _, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    stats = {stat.split: stat for stat in report.split_stats}

    assert stats["train"].selected_positive_count == 2
    assert stats["train"].selected_negative_count == 2

    assert stats["validation"].selected_positive_count == 1
    assert stats["validation"].selected_negative_count == 1

    assert stats["test"].selected_positive_count == 1
    assert stats["test"].selected_negative_count == 1


def test_assembly_status_is_pass_when_quotas_met():
    partition, quotas, selected = prepare_selection()

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    assert result.selection_status == PairSelectionStatus.PASS
    assert report.status == PairSelectionStatus.PASS


def test_assembly_rejects_selected_pair_not_in_candidates():
    partition, quotas, selected = prepare_selection()

    outsider = make_pair(
        "outsider",
        PairType.POSITIVE,
        PairSplit.TRAIN,
    )

    with pytest.raises(ValueError, match="candidate partition"):
        PairSelectionResultAssembler().assemble(
            partition,
            quotas,
            selected + (outsider,),
        )


def test_assembly_rejects_duplicate_selected_pair_ids():
    partition, quotas, selected = prepare_selection()

    with pytest.raises(ValueError, match="duplicate pair_id"):
        PairSelectionResultAssembler().assemble(
            partition,
            quotas,
            selected + (selected[0],),
        )


def test_assembly_rejects_invalid_partition_type():
    with pytest.raises(TypeError, match="PairCandidatePartition"):
        PairSelectionResultAssembler().assemble(
            "invalid",
            (),
            (),
        )


def test_assembly_rejects_non_tuple_quotas():
    partition, _, selected = prepare_selection()

    with pytest.raises(TypeError, match="tuple"):
        PairSelectionResultAssembler().assemble(
            partition,
            [],
            selected,
        )


def test_assembly_rejects_invalid_seed():
    partition, quotas, selected = prepare_selection()

    with pytest.raises(TypeError, match="seed"):
        PairSelectionResultAssembler().assemble(
            partition,
            quotas,
            selected,
            seed=True,
        )

def test_assembly_result_and_report_are_consistent():
    partition, quotas, selected = prepare_selection()

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    # Overall selected counts
    assert result.total_count == report.total_selected_count
    assert result.positive_count == sum(
        stat.selected_positive_count
        for stat in report.split_stats
    )
    assert result.negative_count == sum(
        stat.selected_negative_count
        for stat in report.split_stats
    )

    # Report totals
    assert report.total_candidate_count == 8
    assert report.total_selected_count == 8
    assert report.total_unmet_quota_count == 0

    # Status consistency
    assert result.selection_status == report.status
    assert result.selection_status == PairSelectionStatus.PASS

def test_assembly_result_and_report_are_consistent_when_quota_unmet():
    partition, quotas, selected = prepare_selection()

    incomplete_selected = selected[:-1]

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        incomplete_selected,
    )

    assert result.total_count == 7
    assert report.total_selected_count == 7
    assert report.total_unmet_quota_count == 1

    assert result.positive_count == sum(
        stat.selected_positive_count
        for stat in report.split_stats
    )
    assert result.negative_count == sum(
        stat.selected_negative_count
        for stat in report.split_stats
    )

    assert result.selection_status == PairSelectionStatus.WARNING
    assert report.status == PairSelectionStatus.WARNING
    assert result.selection_status == report.status

def test_assembly_preserves_split_integrity():
    partition, quotas, selected = prepare_selection()

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected,
    )

    expected_split_by_pair_id = {
        pair.pair_id: pair.split
        for group in (
            partition.train_pairs,
            partition.validation_pairs,
            partition.test_pairs,
        )
        for pair in group
    }

    # Every selected pair must remain in its original split.
    for pair in result.selected_pairs:
        assert pair.split == expected_split_by_pair_id[pair.pair_id]

    # Report must count selected pairs in the correct split.
    stats_by_split = {
        stat.split: stat
        for stat in report.split_stats
    }

    for split, pairs in (
        ("train", partition.train_pairs),
        ("validation", partition.validation_pairs),
        ("test", partition.test_pairs),
    ):
        selected_in_split = tuple(
            pair for pair in result.selected_pairs
            if pair.split.value == split
        )

        stat = stats_by_split[split]

        assert stat.selected_positive_count == sum(
            pair.pair_type == PairType.POSITIVE
            for pair in selected_in_split
        )
        assert stat.selected_negative_count == sum(
            pair.pair_type == PairType.NEGATIVE
            for pair in selected_in_split
        )

def test_assembly_handles_empty_selection():
    partition, quotas, _ = prepare_selection()

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected_pairs=(),
    )

    assert result.selected_pairs == ()
    assert result.total_count == 0
    assert result.positive_count == 0
    assert result.negative_count == 0

    assert report.total_selected_count == 0
    assert report.total_unmet_quota_count == sum(
        quota.target_positive_count + quota.target_negative_count
        for quota in quotas
    )

    assert result.selection_status == PairSelectionStatus.WARNING
    assert report.status == PairSelectionStatus.WARNING

    for stat in report.split_stats:
        assert stat.selected_positive_count == 0
        assert stat.selected_negative_count == 0
        assert stat.unmet_positive_quota == stat.target_positive_count
        assert stat.unmet_negative_quota == stat.target_negative_count

def test_assembly_handles_empty_candidate_partition():
    partition = PairCandidatePartitioner().partition(())

    quotas = PairLabelQuotaPlanner().plan(
        partition,
        PairSelectionConfig(),
    )

    result, report = PairSelectionResultAssembler().assemble(
        partition,
        quotas,
        selected_pairs=(),
    )

    assert result.selected_pairs == ()
    assert result.total_count == 0
    assert result.positive_count == 0
    assert result.negative_count == 0

    assert report.total_candidate_count == 0
    assert report.total_selected_count == 0
    assert report.total_unmet_quota_count == 0

    assert result.selection_status == PairSelectionStatus.PASS
    assert report.status == PairSelectionStatus.PASS

    assert len(report.split_stats) == 3

    for stat in report.split_stats:
        assert stat.candidate_positive_count == 0
        assert stat.candidate_negative_count == 0
        assert stat.target_positive_count == 0
        assert stat.target_negative_count == 0
        assert stat.selected_positive_count == 0
        assert stat.selected_negative_count == 0
        assert stat.unmet_positive_quota == 0
        assert stat.unmet_negative_quota == 0

def test_assembly_rejects_recreated_pair_object():
    partition, quotas, selected = prepare_selection()

    recreated_pair = replace(selected[0])

    assert recreated_pair == selected[0]
    assert recreated_pair is not selected[0]

    modified_selection = (recreated_pair,) + selected[1:]

    with pytest.raises(ValueError, match="objects must be preserved"):
        PairSelectionResultAssembler().assemble(
            partition,
            quotas,
            modified_selection,
        )