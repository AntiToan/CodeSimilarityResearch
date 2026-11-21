
import pytest

from src.data.pair_models import (
    PairRecord,
    PairSplit,
    PairType,
)


def make_positive(**overrides):
    values = {
        "pair_id": "pair_001",
        "sample_a_id": "original_001",
        "sample_b_id": "variant_001",
        "label": 1,
        "pair_type": PairType.POSITIVE,
        "split": PairSplit.TRAIN,
        "source_a_id": "original_001",
        "source_b_id": "original_001",
        "problem_a_id": "1",
        "problem_b_id": "1",
        "generation_method": "transformation",
        "created_seed": 42,
    }
    values.update(overrides)
    return PairRecord(**values)


def make_negative(**overrides):
    values = {
        "pair_id": "pair_002",
        "sample_a_id": "sample_001",
        "sample_b_id": "sample_002",
        "label": 0,
        "pair_type": PairType.NEGATIVE,
        "split": PairSplit.TRAIN,
        "source_a_id": "source_001",
        "source_b_id": "source_002",
        "problem_a_id": "1",
        "problem_b_id": "2",
        "generation_method": "cross_problem_sampling",
        "created_seed": 42,
    }
    values.update(overrides)
    return PairRecord(**values)


def test_valid_positive_pair():
    pair = make_positive()

    assert pair.label == 1
    assert pair.pair_type == PairType.POSITIVE
    assert pair.split == PairSplit.TRAIN


def test_valid_negative_pair():
    pair = make_negative()

    assert pair.label == 0
    assert pair.pair_type == PairType.NEGATIVE


def test_rejects_self_pair():
    with pytest.raises(ValueError, match="Self-pairs"):
        make_positive(
            sample_b_id="original_001"
        )


def test_positive_pair_requires_label_one():
    with pytest.raises(ValueError, match="label=1"):
        make_positive(label=0)


def test_positive_pair_requires_same_lineage():
    with pytest.raises(ValueError, match="same source lineage"):
        make_positive(source_b_id="another_source")


def test_negative_pair_requires_label_zero():
    with pytest.raises(ValueError, match="label=0"):
        make_negative(label=1)


def test_negative_pair_requires_different_problems():
    with pytest.raises(ValueError, match="different problem IDs"):
        make_negative(problem_b_id="1")


def test_negative_pair_requires_different_lineages():
    with pytest.raises(ValueError, match="different source lineages"):
        make_negative(source_b_id="source_001")


def test_rejects_invalid_label():
    with pytest.raises(ValueError, match="0 or 1"):
        make_positive(label=2)


def test_rejects_boolean_label():
    with pytest.raises(TypeError, match="integer"):
        make_positive(label=True)


def test_rejects_empty_pair_id():
    with pytest.raises(ValueError, match="pair_id"):
        make_positive(pair_id="  ")


def test_rejects_invalid_split():
    with pytest.raises(TypeError, match="PairSplit"):
        make_positive(split="train")


def test_rejects_invalid_pair_type():
    with pytest.raises(TypeError, match="PairType"):
        make_positive(pair_type="positive")


def test_rejects_invalid_seed_type():
    with pytest.raises(TypeError, match="created_seed"):
        make_positive(created_seed=3.14)


def test_accepts_null_seed():
    pair = make_positive(created_seed=None)

    assert pair.created_seed is None


def test_rejects_noncanonical_order():
    with pytest.raises(ValueError, match="lexicographically"):
        make_positive(
            sample_a_id="z_sample",
            sample_b_id="a_sample",
        )


def test_canonical_key():
    pair = make_positive()

    assert pair.canonical_key == (
        "original_001",
        "variant_001",
    )


def test_create_canonical_swaps_sample_metadata():
    pair = PairRecord.create_canonical(
        pair_id="pair_003",
        sample_a_id="z_variant",
        sample_b_id="a_original",
        label=1,
        pair_type=PairType.POSITIVE,
        split=PairSplit.TRAIN,
        source_a_id="lineage_1",
        source_b_id="lineage_1",
        problem_a_id="10",
        problem_b_id="2",
        generation_method="transformation",
        created_seed=42,
    )

    assert pair.sample_a_id == "a_original"
    assert pair.sample_b_id == "z_variant"
    assert pair.problem_a_id == "2"
    assert pair.problem_b_id == "10"
    assert pair.source_a_id == pair.source_b_id == "lineage_1"
