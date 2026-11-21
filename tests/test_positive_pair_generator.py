
from types import SimpleNamespace

from src.data.positive_pair_generator import PositivePairGenerator


def make_original(
    sample_id="original_001",
    problem_id="1",
    split="train",
):
    return SimpleNamespace(
        sample_id=sample_id,
        problem_id=problem_id,
        split=split,
        source_text="int main() {}",
        source_path="source/1/1001.txt",
    )


def make_variant(
    variant_id="variant_001",
    original_sample_id="original_001",
    problem_id="1",
    split="train",
    validation_status="PASS",
    transformation_type="formatting",
    generation_seed=42,
):
    return SimpleNamespace(
        variant_id=variant_id,
        original_sample_id=original_sample_id,
        problem_id=problem_id,
        split=split,
        validation_status=validation_status,
        transformation_type=transformation_type,
        generation_seed=generation_seed,
    )


def test_generates_positive_pair():
    generator = PositivePairGenerator()

    result = generator.generate(
        [make_original()],
        [make_variant()],
    )

    assert result.pairs_generated == 1

    pair = result.pairs[0]

    assert pair.label == 1
    assert pair.pair_type.value == "positive"
    assert pair.sample_a_id == "original_001"
    assert pair.sample_b_id == "variant_001"
    assert pair.source_a_id == pair.source_b_id == "original_001"
    assert pair.problem_a_id == pair.problem_b_id == "1"
    assert pair.split.value == "train"


def test_generation_method_contains_transformation_type():
    result = PositivePairGenerator().generate(
        [make_original()],
        [make_variant(transformation_type="comments")],
    )

    assert result.pairs[0].generation_method == "transformation:comments"


def test_pair_seed_is_inherited_from_variant():
    result = PositivePairGenerator().generate(
        [make_original()],
        [make_variant(generation_seed=1234)],
    )

    assert result.pairs[0].created_seed == 1234


def test_rejects_variant_that_did_not_pass_validation():
    result = PositivePairGenerator().generate(
        [make_original()],
        [make_variant(validation_status="FAIL")],
    )

    assert result.pairs_generated == 0
    assert result.variants_rejected == 1
    assert "not PASS" in result.rejections[0].reason


def test_rejects_variant_without_original():
    result = PositivePairGenerator().generate(
        [],
        [make_variant()],
    )

    assert result.pairs_generated == 0
    assert result.variants_rejected == 1
    assert "missing" in result.rejections[0].reason


def test_rejects_problem_id_mismatch():
    result = PositivePairGenerator().generate(
        [make_original(problem_id="1")],
        [make_variant(problem_id="2")],
    )

    assert result.pairs_generated == 0
    assert "problem ID" in result.rejections[0].reason


def test_rejects_split_mismatch():
    result = PositivePairGenerator().generate(
        [make_original(split="train")],
        [make_variant(split="test")],
    )

    assert result.pairs_generated == 0
    assert "split" in result.rejections[0].reason


def test_duplicate_variant_pair_is_rejected():
    variants = [
        make_variant(),
        make_variant(),
    ]

    result = PositivePairGenerator().generate(
        [make_original()],
        variants,
    )

    assert result.pairs_generated == 1
    assert result.variants_rejected == 1
    assert "Duplicate" in result.rejections[0].reason


def test_pair_id_is_deterministic():
    generator = PositivePairGenerator()

    first = generator.create_pair_id(
        "original_001",
        "variant_001",
    )

    second = generator.create_pair_id(
        "variant_001",
        "original_001",
    )

    assert first == second


def test_pair_id_differs_for_different_sample_pairs():
    generator = PositivePairGenerator()

    first = generator.create_pair_id(
        "original_001",
        "variant_001",
    )

    second = generator.create_pair_id(
        "original_001",
        "variant_002",
    )

    assert first != second


def test_empty_inputs_return_empty_result():
    result = PositivePairGenerator().generate([], [])

    assert result.pairs_generated == 0
    assert result.variants_seen == 0
    assert result.variants_eligible == 0
    assert result.variants_rejected == 0


def test_tracks_generation_counts():
    variants = [
        make_variant(variant_id="variant_001"),
        make_variant(
            variant_id="variant_002",
            validation_status="FAIL",
        ),
        make_variant(
            variant_id="variant_003",
            original_sample_id="missing_original",
        ),
    ]

    result = PositivePairGenerator().generate(
        [make_original()],
        variants,
    )

    assert result.variants_seen == 3
    assert result.variants_eligible == 1
    assert result.variants_rejected == 2
    assert result.pairs_generated == 1
