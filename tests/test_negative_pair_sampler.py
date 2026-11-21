
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.data.negative_pair_generator import NegativePairGenerator
from src.data.negative_pair_sampler import NegativePairSampler


def make_sample(
    sample_id,
    problem_id,
    split="train",
    source_id=None,
):
    return SimpleNamespace(
        sample_id=sample_id,
        problem_id=str(problem_id),
        split=split,
        source_id=source_id or sample_id,
        source_text=f"code for {sample_id}",
    )


def make_sampler(quota=3):
    generator = NegativePairGenerator(
        similarity_screener=Mock(return_value=True)
    )
    return NegativePairSampler(
        generator=generator,
        quota_per_anchor=quota,
    )


def make_candidates():
    return [
        make_sample("candidate_2a", "2"),
        make_sample("candidate_2b", "2"),
        make_sample("candidate_3a", "3"),
        make_sample("candidate_4a", "4"),
        make_sample("candidate_5a", "5"),
    ]


def test_samples_up_to_quota():
    result = make_sampler(quota=3).sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=42,
    )

    assert result.sampled_count == 3
    assert result.quota_reached is True


def test_prioritizes_distinct_problem_ids():
    result = make_sampler(quota=3).sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=42,
    )

    assert result.unique_problem_count == 3
    assert len(set(result.problem_ids_selected)) == 3


def test_one_pair_per_problem_when_diversity_is_available():
    result = make_sampler(quota=3).sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=42,
    )

    problems = [pair.problem_b_id for pair in result.pairs]

    assert len(problems) == 3
    assert len(set(problems)) == 3


def test_partial_quota_when_candidates_are_insufficient():
    candidates = [
        make_sample("candidate_2", "2"),
        make_sample("candidate_3", "3"),
    ]

    result = make_sampler(quota=3).sample(
        make_sample("anchor", "1"),
        candidates,
        seed=42,
    )

    assert result.sampled_count == 2
    assert result.quota_reached is False
    assert result.quota_remaining == 1


def test_empty_candidates():
    result = make_sampler().sample(
        make_sample("anchor", "1"),
        [],
    )

    assert result.sampled_count == 0
    assert result.quota_reached is False
    assert result.quota_remaining == 3


def test_deterministic_for_same_seed():
    sampler = make_sampler()

    first = sampler.sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=123,
    )

    second = sampler.sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=123,
    )

    assert [p.pair_id for p in first.pairs] == [
        p.pair_id for p in second.pairs
    ]


def test_same_seed_is_independent_of_candidate_input_order():
    sampler = make_sampler()
    candidates = make_candidates()

    first = sampler.sample(
        make_sample("anchor", "1"),
        candidates,
        seed=123,
    )

    second = sampler.sample(
        make_sample("anchor", "1"),
        list(reversed(candidates)),
        seed=123,
    )

    assert {p.pair_id for p in first.pairs} == {
        p.pair_id for p in second.pairs
    }


def test_different_seeds_can_change_sampling():
    candidates = [
        make_sample(f"candidate_{i}", str(i + 2))
        for i in range(10)
    ]

    sampler = make_sampler(quota=3)

    first = sampler.sample(
        make_sample("anchor", "1"),
        candidates,
        seed=10,
    )

    second = sampler.sample(
        make_sample("anchor", "1"),
        candidates,
        seed=99,
    )

    assert {p.pair_id for p in first.pairs} != {
        p.pair_id for p in second.pairs
    }


def test_fill_quota_when_distinct_problems_are_fewer():
    candidates = [
        make_sample("candidate_2a", "2"),
        make_sample("candidate_2b", "2"),
        make_sample("candidate_3a", "3"),
    ]

    result = make_sampler(quota=3).sample(
        make_sample("anchor", "1"),
        candidates,
        seed=42,
    )

    assert result.sampled_count == 3
    assert result.unique_problem_count == 2
    assert result.quota_reached is True


def test_sampling_statistics_preserved():
    result = make_sampler().sample(
        make_sample("anchor", "1"),
        make_candidates(),
        seed=42,
    )

    assert result.candidates_seen == 5
    assert result.candidates_eligible == 5
    assert result.candidates_rejected == 0


def test_rejections_preserved():
    candidates = [
        make_sample("same_problem", "1"),
        make_sample("valid", "2"),
    ]

    result = make_sampler(quota=1).sample(
        make_sample("anchor", "1"),
        candidates,
        seed=42,
    )

    assert result.candidates_rejected == 1
    assert len(result.rejections) == 1


def test_invalid_quota():
    generator = NegativePairGenerator(Mock(return_value=True))

    with pytest.raises(ValueError):
        NegativePairSampler(generator, quota_per_anchor=0)

    with pytest.raises(TypeError):
        NegativePairSampler(generator, quota_per_anchor=1.5)
