
import pytest

from src.data.pair_candidate_partitioner import PairCandidatePartitioner
from src.data.pair_selection_models import PairSelectionConfig
from src.data.pair_label_quota_planner import (
    PairLabelQuota,
    PairLabelQuotaPlanner,
)
from src.data.pair_models import PairRecord, PairSplit, PairType

def make_partition():
    partition = PairCandidatePartitioner().partition([])
    return partition


def test_balanced_quota_for_empty_candidates():
    planner = PairLabelQuotaPlanner()
    result = planner.plan(
        make_partition(),
        PairSelectionConfig(),
    )

    assert len(result) == 3

    for quota in result:
        assert quota.target_positive_count == 0
        assert quota.target_negative_count == 0


def test_balanced_quota_uses_minimum_label_count():
    partition = PairCandidatePartitioner().partition([])

    planner = PairLabelQuotaPlanner()
    result = planner.plan(partition, PairSelectionConfig())

    assert all(quota.is_balanced for quota in result)

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
        make_pair("tr_p3", PairType.POSITIVE, PairSplit.TRAIN),
        make_pair("tr_n1", PairType.NEGATIVE, PairSplit.TRAIN),
        make_pair("tr_n2", PairType.NEGATIVE, PairSplit.TRAIN),
        make_pair("va_p1", PairType.POSITIVE, PairSplit.VALIDATION),
        make_pair("va_p2", PairType.POSITIVE, PairSplit.VALIDATION),
        make_pair("va_n1", PairType.NEGATIVE, PairSplit.VALIDATION),
        make_pair("te_p1", PairType.POSITIVE, PairSplit.TEST),
        make_pair("te_n1", PairType.NEGATIVE, PairSplit.TEST),
        make_pair("te_n2", PairType.NEGATIVE, PairSplit.TEST),
    )


def test_quota_calculation_per_split():
    partition = PairCandidatePartitioner().partition(make_candidates())

    result = PairLabelQuotaPlanner().plan(
        partition,
        PairSelectionConfig(),
    )

    quotas = {quota.split: quota for quota in result}

    assert quotas["train"].candidate_positive_count == 3
    assert quotas["train"].candidate_negative_count == 2
    assert quotas["train"].target_positive_count == 2
    assert quotas["train"].target_negative_count == 2

    assert quotas["validation"].target_positive_count == 1
    assert quotas["validation"].target_negative_count == 1

    assert quotas["test"].target_positive_count == 1
    assert quotas["test"].target_negative_count == 1


def test_unbalanced_config_preserves_all_candidate_counts():
    partition = PairCandidatePartitioner().partition(make_candidates())

    config = PairSelectionConfig(balance_labels=False)

    result = PairLabelQuotaPlanner().plan(partition, config)

    quotas = {quota.split: quota for quota in result}

    assert quotas["train"].target_positive_count == 3
    assert quotas["train"].target_negative_count == 2

    assert quotas["validation"].target_positive_count == 2
    assert quotas["validation"].target_negative_count == 1

    assert quotas["test"].target_positive_count == 1
    assert quotas["test"].target_negative_count == 2


def test_quota_properties():
    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=10,
        candidate_negative_count=7,
        target_positive_count=7,
        target_negative_count=7,
    )

    assert quota.target_count == 14
    assert quota.candidate_count == 17
    assert quota.unmet_positive_quota == 3
    assert quota.unmet_negative_quota == 0
    assert quota.is_balanced


def test_quota_rejects_target_exceeding_candidates():
    with pytest.raises(ValueError):
        PairLabelQuota(
            split="train",
            candidate_positive_count=5,
            candidate_negative_count=5,
            target_positive_count=6,
            target_negative_count=5,
        )


def test_quota_rejects_negative_counts():
    with pytest.raises(ValueError):
        PairLabelQuota(
            split="train",
            candidate_positive_count=-1,
            candidate_negative_count=5,
            target_positive_count=0,
            target_negative_count=0,
        )


def test_quota_rejects_invalid_count_types():
    with pytest.raises(TypeError):
        PairLabelQuota(
            split="train",
            candidate_positive_count=1.5,
            candidate_negative_count=5,
            target_positive_count=0,
            target_negative_count=0,
        )


def test_quota_to_dict():
    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=5,
        candidate_negative_count=3,
        target_positive_count=3,
        target_negative_count=3,
    )

    data = quota.to_dict()

    assert data["split"] == "train"
    assert data["target_count"] == 6
    assert data["is_balanced"] is True
