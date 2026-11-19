
from src.data.source_splitter import (
    SourceSplitError,
    assign_source_splits,
)


RATIOS = {
    "train": 0.8,
    "validation": 0.1,
    "test": 0.1,
}


def make_samples(count_per_problem=100, problems=3):
    samples = []

    for problem in range(1, problems + 1):
        for index in range(count_per_problem):
            samples.append(
                {
                    "sample_id": f"p{problem}_s{index}",
                    "problem_id": problem,
                }
            )

    return samples


def test_all_samples_are_assigned():
    samples = make_samples()

    assignments, report = assign_source_splits(
        samples,
        [],
        RATIOS,
        seed=42,
    )

    assert len(assignments) == len(samples)
    assert set(assignments.values()) == {
        "train",
        "validation",
        "test",
    }
    assert report["total_samples"] == len(samples)


def test_duplicate_group_stays_in_one_split():
    samples = make_samples(count_per_problem=30, problems=2)

    duplicate_groups = [
        {
            "duplicate_group_id": "dup_001",
            "sample_ids": ["p1_s0", "p2_s0"],
        }
    ]

    assignments, _ = assign_source_splits(
        samples,
        duplicate_groups,
        RATIOS,
        seed=42,
    )

    assert assignments["p1_s0"] == assignments["p2_s0"]


def test_split_is_reproducible():
    samples = make_samples()

    first, _ = assign_source_splits(
        samples,
        [],
        RATIOS,
        seed=123,
    )

    second, _ = assign_source_splits(
        samples,
        [],
        RATIOS,
        seed=123,
    )

    assert first == second


def test_different_seed_can_change_assignment():
    samples = make_samples(count_per_problem=100, problems=4)

    first, _ = assign_source_splits(
        samples,
        [],
        RATIOS,
        seed=42,
    )

    second, _ = assign_source_splits(
        samples,
        [],
        RATIOS,
        seed=99,
    )

    assert first != second


def test_invalid_ratio_sum():
    samples = make_samples()

    invalid_ratios = {
        "train": 0.7,
        "validation": 0.1,
        "test": 0.1,
    }

    try:
        assign_source_splits(
            samples,
            [],
            invalid_ratios,
            seed=42,
        )
    except SourceSplitError:
        pass
    else:
        raise AssertionError("Expected SourceSplitError")


def test_duplicate_group_unknown_sample_rejected():
    samples = make_samples(count_per_problem=5, problems=1)

    duplicate_groups = [
        {
            "duplicate_group_id": "dup_001",
            "sample_ids": ["p1_s0", "not_found"],
        }
    ]

    try:
        assign_source_splits(
            samples,
            duplicate_groups,
            RATIOS,
            seed=42,
        )
    except SourceSplitError:
        pass
    else:
        raise AssertionError("Expected SourceSplitError")


def test_duplicate_groups_cannot_overlap():
    samples = make_samples(count_per_problem=5, problems=1)

    duplicate_groups = [
        {
            "duplicate_group_id": "dup_001",
            "sample_ids": ["p1_s0", "p1_s1"],
        },
        {
            "duplicate_group_id": "dup_002",
            "sample_ids": ["p1_s0", "p1_s2"],
        },
    ]

    try:
        assign_source_splits(
            samples,
            duplicate_groups,
            RATIOS,
            seed=42,
        )
    except SourceSplitError:
        pass
    else:
        raise AssertionError("Expected SourceSplitError")
