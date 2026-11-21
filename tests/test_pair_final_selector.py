
import pytest

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.pair_label_quota_planner import PairLabelQuota
from src.data.pair_final_selector import PairFinalSelector


def make_pair(pair_id, pair_type, sample_a, sample_b, problem_a, problem_b):
    positive = pair_type == PairType.POSITIVE

    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=sample_a,
        sample_b_id=sample_b,
        label=1 if positive else 0,
        pair_type=pair_type,
        split=PairSplit.TRAIN,
        source_a_id=f"src_{sample_a}",
        source_b_id=f"src_{sample_a}" if positive else f"src_{sample_b}",
        problem_a_id=problem_a,
        problem_b_id=problem_a if positive else problem_b,
        generation_method="test",
        created_seed=42,
    )


def make_candidates():
    return (
        make_pair("p1", PairType.POSITIVE, "s1", "s2", "pr1", "pr1"),
        make_pair("p2", PairType.POSITIVE, "s1", "s3", "pr1", "pr1"),
        make_pair("p3", PairType.POSITIVE, "s4", "s5", "pr2", "pr2"),
        make_pair("p4", PairType.POSITIVE, "s6", "s7", "pr3", "pr3"),
        make_pair("n1", PairType.NEGATIVE, "s1", "s8", "pr1", "pr2"),
        make_pair("n2", PairType.NEGATIVE, "s9", "s10", "pr3", "pr4"),
        make_pair("n3", PairType.NEGATIVE, "s11", "s12", "pr5", "pr6"),
        make_pair("n4", PairType.NEGATIVE, "s13", "s14", "pr7", "pr8"),
    )


def make_quota():
    return PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=2,
        target_negative_count=2,
    )


def test_selects_exact_positive_and_negative_targets():
    result = PairFinalSelector().select(
        make_candidates(),
        make_quota(),
        seed=42,
    )

    assert len(result) == 4

    assert sum(
        pair.pair_type == PairType.POSITIVE
        for pair in result
    ) == 2

    assert sum(
        pair.pair_type == PairType.NEGATIVE
        for pair in result
    ) == 2


def test_selected_pairs_are_from_candidates():
    candidates = make_candidates()

    result = PairFinalSelector().select(
        candidates,
        make_quota(),
    )

    candidate_ids = {pair.pair_id for pair in candidates}
    selected_ids = {pair.pair_id for pair in result}

    assert selected_ids.issubset(candidate_ids)


def test_preserves_original_pair_objects():
    candidates = make_candidates()

    result = PairFinalSelector().select(
        candidates,
        make_quota(),
    )

    original_by_id = {
        pair.pair_id: pair
        for pair in candidates
    }

    for pair in result:
        assert pair is original_by_id[pair.pair_id]


def test_deterministic_for_same_seed():
    candidates = make_candidates()
    selector = PairFinalSelector()

    result_a = selector.select(candidates, make_quota(), seed=42)
    result_b = selector.select(candidates, make_quota(), seed=42)

    assert tuple(pair.pair_id for pair in result_a) == (
        tuple(pair.pair_id for pair in result_b)
    )


def test_input_order_does_not_affect_selection():
    candidates = make_candidates()
    selector = PairFinalSelector()

    result_a = selector.select(candidates, make_quota(), seed=42)
    result_b = selector.select(tuple(reversed(candidates)), make_quota(), seed=42)

    assert tuple(pair.pair_id for pair in result_a) == (
        tuple(pair.pair_id for pair in result_b)
    )


def test_zero_quota_returns_empty_tuple():
    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=0,
        target_negative_count=0,
    )

    result = PairFinalSelector().select(
        make_candidates(),
        quota,
    )

    assert result == ()


def test_positive_target_exceeding_candidates_raises():
    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=4,
        target_negative_count=0,
    )

    candidates = tuple(
        pair
        for pair in make_candidates()
        if pair.pair_type == PairType.NEGATIVE
    )

    with pytest.raises(ValueError, match="positive target exceeds"):
        PairFinalSelector().select(candidates, quota)


def test_negative_target_exceeding_candidates_raises():
    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=0,
        target_negative_count=4,
    )

    candidates = tuple(
        pair
        for pair in make_candidates()
        if pair.pair_type == PairType.POSITIVE
    )

    with pytest.raises(ValueError, match="negative target exceeds"):
        PairFinalSelector().select(candidates, quota)


def test_wrong_split_raises():
    candidates = make_candidates()

    quota = PairLabelQuota(
        split="test",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=1,
        target_negative_count=1,
    )

    with pytest.raises(ValueError, match="split"):
        PairFinalSelector().select(candidates, quota)


def test_invalid_quota_type_raises():
    with pytest.raises(TypeError, match="PairLabelQuota"):
        PairFinalSelector().select(make_candidates(), "invalid")


def test_invalid_seed_type_raises():
    with pytest.raises(TypeError, match="seed"):
        PairFinalSelector().select(make_candidates(), make_quota(), seed="42")


def test_non_pair_candidates_raise():
    with pytest.raises(TypeError, match="PairRecord"):
        PairFinalSelector().select(["invalid"], make_quota())


def test_duplicate_pair_ids_raise():
    pair = make_candidates()[0]
    duplicate = make_pair(
        pair.pair_id,
        PairType.POSITIVE,
        "s100",
        "s101",
        "pr100",
        "pr100",
    )

    with pytest.raises(ValueError, match="duplicate pair_id"):
        PairFinalSelector().select((pair, duplicate), make_quota())


def test_duplicate_sample_pairs_raise():
    pair = make_candidates()[0]
    duplicate = make_pair(
        "another_id",
        PairType.POSITIVE,
        pair.sample_a_id,
        pair.sample_b_id,
        "pr1",
        "pr1",
    )

    with pytest.raises(ValueError, match="duplicate sample pairs"):
        PairFinalSelector().select((pair, duplicate), make_quota())

def test_invalid_endpoint_diversity_config_raises():
    with pytest.raises(TypeError, match="prefer_endpoint_diversity"):
        PairFinalSelector().select(
            make_candidates(),
            make_quota(),
            prefer_endpoint_diversity=1,
        )


def test_invalid_problem_balance_config_raises():
    with pytest.raises(TypeError, match="prefer_problem_balance"):
        PairFinalSelector().select(
            make_candidates(),
            make_quota(),
            prefer_problem_balance=1,
        )


def test_endpoint_diversity_preference_changes_selection():
    candidates = make_candidates()

    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=2,
        target_negative_count=0,
    )

    selector = PairFinalSelector()

    contrasting_seed = None
    diversity_enabled = None
    diversity_disabled = None

    for seed in range(100):
        enabled = selector.select(
            candidates,
            quota,
            seed=seed,
            prefer_endpoint_diversity=True,
            prefer_problem_balance=False,
        )

        disabled = selector.select(
            candidates,
            quota,
            seed=seed,
            prefer_endpoint_diversity=False,
            prefer_problem_balance=False,
        )

        disabled_endpoints = [
            endpoint
            for pair in disabled
            for endpoint in (pair.sample_a_id, pair.sample_b_id)
        ]

        enabled_endpoints = [
            endpoint
            for pair in enabled
            for endpoint in (pair.sample_a_id, pair.sample_b_id)
        ]

        has_overlap_without_diversity = (
            len(disabled_endpoints) != len(set(disabled_endpoints))
        )

        has_no_overlap_with_diversity = (
            len(enabled_endpoints) == len(set(enabled_endpoints))
        )

        if (
            has_overlap_without_diversity
            and has_no_overlap_with_diversity
        ):
            contrasting_seed = seed
            diversity_enabled = enabled
            diversity_disabled = disabled
            break

    assert contrasting_seed is not None, (
        "Could not find a seed demonstrating endpoint diversity behavior"
    )

    assert tuple(
        pair.pair_id for pair in diversity_enabled
    ) != tuple(
        pair.pair_id for pair in diversity_disabled
    )

def test_problem_balance_preference_changes_selection():
    candidates = [
        make_pair("p1", PairType.POSITIVE, "s1", "s2", "pr1", "pr1"),
        make_pair("p2", PairType.POSITIVE, "s3", "s4", "pr1", "pr1"),
        make_pair("p3", PairType.POSITIVE, "s5", "s6", "pr2", "pr2"),
        make_pair("p4", PairType.POSITIVE, "s7", "s8", "pr3", "pr3"),
    ]

    quota = PairLabelQuota(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=0,
        target_positive_count=2,
        target_negative_count=0,
    )

    selector = PairFinalSelector()

    contrasting_seed = None

    for seed in range(100):
        balanced = selector.select(
            candidates,
            quota,
            seed=seed,
            prefer_endpoint_diversity=False,
            prefer_problem_balance=True,
        )

        unbalanced = selector.select(
            candidates,
            quota,
            seed=seed,
            prefer_endpoint_diversity=False,
            prefer_problem_balance=False,
        )

        def max_problem_usage(selected):
            usage = {}

            for pair in selected:
                for problem_id in {
                    pair.problem_a_id,
                    pair.problem_b_id,
                }:
                    usage[problem_id] = usage.get(problem_id, 0) + 1

            return max(usage.values(), default=0)

        if (
            max_problem_usage(balanced)
            < max_problem_usage(unbalanced)
        ):
            contrasting_seed = seed
            break

    assert contrasting_seed is not None, (
        "Problem balance preference did not affect problem distribution"
    )