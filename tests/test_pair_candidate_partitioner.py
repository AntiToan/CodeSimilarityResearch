
import pytest

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_candidate_partitioner import (
    PairCandidatePartition,
    PairCandidatePartitioner,
)


def make_pair(
    pair_id,
    sample_a,
    sample_b,
    pair_type,
    split,
):
    is_positive = pair_type == PairType.POSITIVE

    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=sample_a,
        sample_b_id=sample_b,
        label=1 if is_positive else 0,
        pair_type=pair_type,
        split=split,
        source_a_id=f"src_{sample_a}",
        source_b_id=(
            f"src_{sample_a}" if is_positive else f"src_{sample_b}"
        ),
        problem_a_id="problem_1" if is_positive else "problem_1",
        problem_b_id="problem_1" if is_positive else "problem_2",
        generation_method="test",
        created_seed=42,
    )


def make_mixed_pairs():
    return (
        make_pair("p3", "s5", "s6", PairType.NEGATIVE, PairSplit.TEST),
        make_pair("p1", "s1", "s2", PairType.POSITIVE, PairSplit.TRAIN),
        make_pair("p4", "s7", "s8", PairType.POSITIVE, PairSplit.VALIDATION),
        make_pair("p2", "s3", "s4", PairType.NEGATIVE, PairSplit.TRAIN),
        make_pair("p5", "s9", "s10", PairType.NEGATIVE, PairSplit.VALIDATION),
    )


def test_partition_mixed_pairs():
    result = PairCandidatePartitioner().partition(make_mixed_pairs())

    assert len(result.train_pairs) == 2
    assert len(result.validation_pairs) == 2
    assert len(result.test_pairs) == 1
    assert result.total_count == 5


def test_partition_counts_positive_and_negative():
    result = PairCandidatePartitioner().partition(make_mixed_pairs())

    assert result.train_positive_count == 1
    assert result.train_negative_count == 1

    assert result.validation_positive_count == 1
    assert result.validation_negative_count == 1

    assert result.test_positive_count == 0
    assert result.test_negative_count == 1


def test_partition_orders_pairs_deterministically():
    result = PairCandidatePartitioner().partition(make_mixed_pairs())

    assert tuple(pair.pair_id for pair in result.train_pairs) == (
        "p1",
        "p2",
    )

    assert tuple(pair.pair_id for pair in result.validation_pairs) == (
        "p4",
        "p5",
    )

    assert tuple(pair.pair_id for pair in result.test_pairs) == ("p3",)


def test_partition_empty_input():
    result = PairCandidatePartitioner().partition([])

    assert result.train_pairs == ()
    assert result.validation_pairs == ()
    assert result.test_pairs == ()
    assert result.total_count == 0

    assert result.train_positive_count == 0
    assert result.train_negative_count == 0
    assert result.validation_positive_count == 0
    assert result.validation_negative_count == 0
    assert result.test_positive_count == 0
    assert result.test_negative_count == 0


def test_partition_preserves_all_pairs():
    pairs = make_mixed_pairs()
    result = PairCandidatePartitioner().partition(pairs)

    original_ids = {pair.pair_id for pair in pairs}
    partitioned_ids = {
        pair.pair_id
        for group in (
            result.train_pairs,
            result.validation_pairs,
            result.test_pairs,
        )
        for pair in group
    }

    assert partitioned_ids == original_ids
    assert result.total_count == len(pairs)


def test_partition_preserves_pair_objects():
    pairs = make_mixed_pairs()
    result = PairCandidatePartitioner().partition(pairs)

    original_by_id = {pair.pair_id: pair for pair in pairs}
    partitioned = (
        result.train_pairs
        + result.validation_pairs
        + result.test_pairs
    )

    for pair in partitioned:
        assert pair is original_by_id[pair.pair_id]


def test_partition_rejects_non_pair_record():
    with pytest.raises(TypeError):
        PairCandidatePartitioner().partition(["not_a_pair"])


def test_partition_result_rejects_total_count_mismatch():
    with pytest.raises(ValueError):
        PairCandidatePartition(
            train_pairs=(),
            validation_pairs=(),
            test_pairs=(),
            total_count=1,
            train_positive_count=0,
            train_negative_count=0,
            validation_positive_count=0,
            validation_negative_count=0,
            test_positive_count=0,
            test_negative_count=0,
        )


def test_partition_result_rejects_wrong_split_assignment():
    train_pair = make_pair(
        "p1", "s1", "s2", PairType.POSITIVE, PairSplit.TRAIN
    )

    with pytest.raises(ValueError):
        PairCandidatePartition(
            train_pairs=(),
            validation_pairs=(train_pair,),
            test_pairs=(),
            total_count=1,
            train_positive_count=0,
            train_negative_count=0,
            validation_positive_count=1,
            validation_negative_count=0,
            test_positive_count=0,
            test_negative_count=0,
        )


def test_partition_result_rejects_duplicate_pair_ids():
    pair_a = make_pair(
        "p1", "s1", "s2", PairType.POSITIVE, PairSplit.TRAIN
    )
    pair_b = make_pair(
        "p1", "s3", "s4", PairType.POSITIVE, PairSplit.TRAIN
    )

    with pytest.raises(ValueError, match="duplicate pair_id"):
        PairCandidatePartition(
            train_pairs=(pair_a, pair_b),
            validation_pairs=(),
            test_pairs=(),
            total_count=2,
            train_positive_count=2,
            train_negative_count=0,
            validation_positive_count=0,
            validation_negative_count=0,
            test_positive_count=0,
            test_negative_count=0,
        )


def test_partition_result_rejects_duplicate_sample_pairs():
    pair_a = make_pair(
        "p1", "s1", "s2", PairType.POSITIVE, PairSplit.TRAIN
    )
    pair_b = make_pair(
        "p2", "s1", "s2", PairType.POSITIVE, PairSplit.TRAIN
    )

    with pytest.raises(ValueError, match="duplicate sample pairs"):
        PairCandidatePartition(
            train_pairs=(pair_a, pair_b),
            validation_pairs=(),
            test_pairs=(),
            total_count=2,
            train_positive_count=2,
            train_negative_count=0,
            validation_positive_count=0,
            validation_negative_count=0,
            test_positive_count=0,
            test_negative_count=0,
        )
