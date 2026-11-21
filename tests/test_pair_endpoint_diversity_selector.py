
import pytest

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_endpoint_diversity_selector import (
    PairEndpointDiversitySelector,
)


def make_pair(pair_id, sample_a, sample_b):
    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=sample_a,
        sample_b_id=sample_b,
        label=0,
        pair_type=PairType.NEGATIVE,
        split=PairSplit.TRAIN,
        source_a_id=f"src_{sample_a}",
        source_b_id=f"src_{sample_b}",
        problem_a_id="problem_1",
        problem_b_id="problem_2",
        generation_method="test",
        created_seed=42,
    )


def make_candidates():
    return (
        make_pair("p1", "s1", "s2"),
        make_pair("p2", "s1", "s3"),
        make_pair("p3", "s1", "s4"),
        make_pair("p4", "s1", "s5"),
        make_pair("p5", "s6", "s7"),
        make_pair("p6", "s8", "s9"),
        make_pair("p7", "s10", "s11"),
        make_pair("p8", "s12", "s13"),
    )


def test_selects_exact_target_count():
    result = PairEndpointDiversitySelector().select(
        make_candidates(),
        target_count=4,
        seed=42,
    )

    assert len(result) == 4


def test_selected_pairs_are_from_original_candidates():
    candidates = make_candidates()

    result = PairEndpointDiversitySelector().select(
        candidates,
        target_count=4,
        seed=42,
    )

    original_ids = {pair.pair_id for pair in candidates}
    selected_ids = {pair.pair_id for pair in result}

    assert selected_ids.issubset(original_ids)


def test_preserves_original_pair_objects():
    candidates = make_candidates()

    result = PairEndpointDiversitySelector().select(
        candidates,
        target_count=4,
        seed=42,
    )

    original_by_id = {
        pair.pair_id: pair
        for pair in candidates
    }

    for pair in result:
        assert pair is original_by_id[pair.pair_id]


def test_deterministic_for_same_seed():
    candidates = make_candidates()
    selector = PairEndpointDiversitySelector()

    result_a = selector.select(
        candidates,
        target_count=5,
        seed=42,
    )

    result_b = selector.select(
        candidates,
        target_count=5,
        seed=42,
    )

    assert tuple(pair.pair_id for pair in result_a) == (
        tuple(pair.pair_id for pair in result_b)
    )


def test_input_order_does_not_affect_selection():
    candidates = make_candidates()
    selector = PairEndpointDiversitySelector()

    result_a = selector.select(
        candidates,
        target_count=5,
        seed=42,
    )

    result_b = selector.select(
        tuple(reversed(candidates)),
        target_count=5,
        seed=42,
    )

    assert tuple(pair.pair_id for pair in result_a) == (
        tuple(pair.pair_id for pair in result_b)
    )


def test_zero_target_returns_empty_tuple():
    result = PairEndpointDiversitySelector().select(
        make_candidates(),
        target_count=0,
    )

    assert result == ()


def test_target_exceeding_candidates_raises():
    with pytest.raises(ValueError):
        PairEndpointDiversitySelector().select(
            make_candidates(),
            target_count=100,
        )


def test_negative_target_raises():
    with pytest.raises(ValueError):
        PairEndpointDiversitySelector().select(
            make_candidates(),
            target_count=-1,
        )


def test_invalid_target_type_raises():
    with pytest.raises(TypeError):
        PairEndpointDiversitySelector().select(
            make_candidates(),
            target_count=1.5,
        )


def test_invalid_seed_type_raises():
    with pytest.raises(TypeError):
        PairEndpointDiversitySelector().select(
            make_candidates(),
            target_count=2,
            seed="42",
        )


def test_non_pair_candidates_raise():
    with pytest.raises(TypeError):
        PairEndpointDiversitySelector().select(
            ["invalid"],
            target_count=1,
        )
