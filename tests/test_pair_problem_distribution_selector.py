
import pytest

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_problem_distribution_selector import (
    PairProblemDistributionSelector,
)


def make_pair(pair_id, sample_a, sample_b, problem_a, problem_b):
    is_positive = problem_a == problem_b

    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=sample_a,
        sample_b_id=sample_b,
        label=1 if is_positive else 0,
        pair_type=PairType.POSITIVE if is_positive else PairType.NEGATIVE,
        split=PairSplit.TRAIN,
        source_a_id=f"src_{sample_a}",
        source_b_id=(
            f"src_{sample_a}"
            if is_positive
            else f"src_{sample_b}"
        ),
        problem_a_id=problem_a,
        problem_b_id=problem_b,
        generation_method="test",
        created_seed=42,
    )


def make_candidates():
    return (
        make_pair("p1", "s01", "s02", "problem_1", "problem_2"),
        make_pair("p2", "s03", "s04", "problem_1", "problem_3"),
        make_pair("p3", "s05", "s06", "problem_1", "problem_4"),
        make_pair("p4", "s07", "s08", "problem_5", "problem_6"),
        make_pair("p5", "s09", "s10", "problem_7", "problem_8"),
        make_pair("p6", "s11", "s12", "problem_9", "problem_10"),
        make_pair("p7", "s13", "s14", "problem_11", "problem_12"),
        make_pair("p8", "s15", "s16", "problem_13", "problem_14"),
    )


def test_selects_exact_target_count():
    result = PairProblemDistributionSelector().select(
        make_candidates(),
        target_count=4,
        seed=42,
    )

    assert len(result) == 4


def test_selected_pairs_are_from_candidates():
    candidates = make_candidates()

    result = PairProblemDistributionSelector().select(
        candidates,
        target_count=4,
        seed=42,
    )

    candidate_ids = {pair.pair_id for pair in candidates}
    selected_ids = {pair.pair_id for pair in result}

    assert selected_ids.issubset(candidate_ids)


def test_preserves_original_pair_objects():
    candidates = make_candidates()

    result = PairProblemDistributionSelector().select(
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
    selector = PairProblemDistributionSelector()

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


def test_input_order_does_not_affect_result():
    candidates = make_candidates()
    selector = PairProblemDistributionSelector()

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


def test_zero_target_returns_empty():
    result = PairProblemDistributionSelector().select(
        make_candidates(),
        target_count=0,
    )

    assert result == ()


def test_target_exceeding_candidates_raises():
    with pytest.raises(ValueError):
        PairProblemDistributionSelector().select(
            make_candidates(),
            target_count=100,
        )


def test_negative_target_raises():
    with pytest.raises(ValueError):
        PairProblemDistributionSelector().select(
            make_candidates(),
            target_count=-1,
        )


def test_invalid_target_type_raises():
    with pytest.raises(TypeError):
        PairProblemDistributionSelector().select(
            make_candidates(),
            target_count=1.5,
        )


def test_invalid_seed_type_raises():
    with pytest.raises(TypeError):
        PairProblemDistributionSelector().select(
            make_candidates(),
            target_count=2,
            seed="42",
        )


def test_non_pair_candidates_raise():
    with pytest.raises(TypeError):
        PairProblemDistributionSelector().select(
            ["invalid"],
            target_count=1,
        )
