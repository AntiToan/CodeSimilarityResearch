import pytest

from src.transformations import (
    CommentsTransformation,
    FormattingTransformation,
    WhitespaceTransformation,
)
from src.transformations.selection import (
    TransformationSelectionError,
    TransformationSelector,
)


def build_transformations():
    return [
        WhitespaceTransformation(),
        FormattingTransformation(),
        CommentsTransformation(),
    ]


def build_probabilities():
    return {
        "whitespace": 1 / 3,
        "formatting": 1 / 3,
        "comments": 1 / 3,
    }


def test_select_one_transformation():
    result = TransformationSelector().select(
        transformations=build_transformations(),
        probabilities=build_probabilities(),
        count=1,
        seed=42,
    )

    assert len(result.selected) == 1
    assert result.selected[0] in build_probabilities()


def test_select_two_transformations():
    result = TransformationSelector().select(
        transformations=build_transformations(),
        probabilities=build_probabilities(),
        count=2,
        seed=42,
    )

    assert len(result.selected) == 2
    assert len(set(result.selected)) == 2


def test_sampling_without_replacement():
    result = TransformationSelector().select(
        transformations=build_transformations(),
        probabilities=build_probabilities(),
        count=3,
        seed=42,
    )

    assert len(result.selected) == 3
    assert len(set(result.selected)) == 3


def test_deterministic_selection_with_same_seed():
    selector = TransformationSelector()

    first = selector.select(
        build_transformations(),
        build_probabilities(),
        count=2,
        seed=12345,
    )

    second = selector.select(
        build_transformations(),
        build_probabilities(),
        count=2,
        seed=12345,
    )

    assert first.selected == second.selected


def test_different_seeds_are_supported():
    selector = TransformationSelector()

    results = {
        selector.select(
            build_transformations(),
            build_probabilities(),
            count=2,
            seed=seed,
        ).selected
        for seed in range(20)
    }

    # Different seeds should be capable of producing
    # different combinations. This is not a guarantee
    # for every small seed range.
    assert len(results) > 1


def test_zero_probability_transformation_is_not_selected():
    probabilities = {
        "whitespace": 1.0,
        "formatting": 0.0,
        "comments": 0.0,
    }

    result = TransformationSelector().select(
        build_transformations(),
        probabilities,
        count=1,
        seed=42,
    )

    assert result.selected == ("whitespace",)


def test_probability_keys_must_match_names():
    probabilities = {
        "whitespace": 0.5,
        "formatting": 0.5,
        "unknown": 0.0,
    }

    with pytest.raises(TransformationSelectionError):
        TransformationSelector().select(
            build_transformations(),
            probabilities,
            count=1,
            seed=42,
        )


def test_negative_probability_is_rejected():
    probabilities = {
        "whitespace": 1.0,
        "formatting": -0.1,
        "comments": 0.1,
    }

    with pytest.raises(TransformationSelectionError):
        TransformationSelector().select(
            build_transformations(),
            probabilities,
            count=1,
            seed=42,
        )


def test_count_must_be_one_or_two():
    with pytest.raises(TransformationSelectionError):
        TransformationSelector().select(
            build_transformations(),
            build_probabilities(),
            count=0,
            seed=42,
        )


def test_cannot_select_more_than_available():
    probabilities = {
        "whitespace": 1.0,
        "formatting": 0.0,
        "comments": 0.0,
    }

    with pytest.raises(TransformationSelectionError):
        TransformationSelector().select(
            build_transformations(),
            probabilities,
            count=2,
            seed=42,
        )


def test_duplicate_transformation_names_are_rejected():
    transformations = [
        WhitespaceTransformation(),
        WhitespaceTransformation(),
    ]

    probabilities = {
        "whitespace": 1.0,
    }

    with pytest.raises(TransformationSelectionError):
        TransformationSelector().select(
            transformations,
            probabilities,
            count=1,
            seed=42,
        )


def test_result_contains_selection_metadata():
    result = TransformationSelector().select(
        build_transformations(),
        build_probabilities(),
        count=2,
        seed=99,
    )

    assert result.seed == 99
    assert result.requested_count == 2
    assert result.available_count == 3
    assert len(result.probabilities) == 3
