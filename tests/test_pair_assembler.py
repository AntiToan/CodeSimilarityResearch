from types import SimpleNamespace

import pytest

from src.data.pair_assembler import PairAssembler
from src.data.positive_pair_generator import PositivePairGenerator
from enum import Enum
from src.data.pair_assembler import PairAssembler, PairAssemblyConfig

def make_pair(
    sample_a_id,
    sample_b_id,
    *,
    label,
    pair_type,
    pair_id=None,
    split="train",
    generation_method="test",
):
    if pair_id is None:
        pair_id = PositivePairGenerator.create_pair_id(
            sample_a_id,
            sample_b_id,
        )

    return SimpleNamespace(
        pair_id=pair_id,
        sample_a_id=sample_a_id,
        sample_b_id=sample_b_id,
        label=label,
        pair_type=pair_type,
        split=split,
        source_a_id=sample_a_id,
        source_b_id=sample_b_id,
        problem_a_id="1" if label == 1 else "1",
        problem_b_id="1" if label == 1 else "2",
        generation_method=generation_method,
        created_seed=42,
    )


def make_positive(a="s1", b="v1", **kwargs):
    return make_pair(
        a,
        b,
        label=1,
        pair_type="positive",
        **kwargs,
    )


def make_negative(a="s1", b="s2", **kwargs):
    return make_pair(
        a,
        b,
        label=0,
        pair_type="negative",
        **kwargs,
    )


def test_assemble_merges_positive_and_negative_pairs():
    positive = make_positive()
    negative = make_negative()

    result = PairAssembler().assemble(
        positive_pairs=[positive],
        negative_pairs=[negative],
    )

    assert result.total_count == 2
    assert result.positive_count == 1
    assert result.negative_count == 1
    assert result.assembly_status == "PASS"
    assert len(result.pairs) == 2


def test_assemble_empty_inputs():
    result = PairAssembler().assemble([], [])

    assert result.pairs == ()
    assert result.positive_count == 0
    assert result.negative_count == 0
    assert result.total_count == 0
    assert result.duplicate_pair_count == 0
    assert result.assembly_status == "PASS"


def test_assemble_positive_only():
    result = PairAssembler().assemble(
        positive_pairs=[make_positive()],
        negative_pairs=[],
    )

    assert result.total_count == 1
    assert result.positive_count == 1
    assert result.negative_count == 0


def test_assemble_negative_only():
    result = PairAssembler().assemble(
        positive_pairs=[],
        negative_pairs=[make_negative()],
    )

    assert result.total_count == 1
    assert result.positive_count == 0
    assert result.negative_count == 1

def test_assembly_is_deterministic_regardless_of_input_order():
    p1 = make_positive("s1", "v1")
    p2 = make_positive("s2", "v2")
    n1 = make_negative("s1", "s3")
    n2 = make_negative("s2", "s4")

    assembler = PairAssembler()

    result_a = assembler.assemble(
        positive_pairs=[p1, p2],
        negative_pairs=[n1, n2],
    )

    result_b = assembler.assemble(
        positive_pairs=[p2, p1],
        negative_pairs=[n2, n1],
    )

    ids_a = [pair.pair_id for pair in result_a.pairs]
    ids_b = [pair.pair_id for pair in result_b.pairs]

    assert ids_a == ids_b


def test_duplicate_pair_id_is_deduplicated():
    pair = make_positive()

    duplicate = make_positive(
        pair_id=pair.pair_id,
        generation_method="duplicate",
    )

    result = PairAssembler().assemble(
        positive_pairs=[pair, duplicate],
        negative_pairs=[],
    )

    assert result.total_count == 1
    assert result.duplicate_pair_count == 1


def test_duplicate_sample_pair_with_different_pair_ids_is_deduplicated():
    pair = make_positive("s1", "v1")

    duplicate = make_positive(
        "v1",
        "s1",
        pair_id="pair_duplicate_custom",
    )

    result = PairAssembler().assemble(
        positive_pairs=[pair, duplicate],
        negative_pairs=[],
    )

    assert result.total_count == 1
    assert result.duplicate_pair_count == 1


def test_conflicting_labels_for_same_sample_pair_raise_error():
    positive = make_positive("s1", "s2")

    negative = make_negative(
        "s2",
        "s1",
        pair_id="pair_negative_custom",
    )

    with pytest.raises(ValueError, match="Conflicting labels"):
        PairAssembler().assemble(
            positive_pairs=[positive],
            negative_pairs=[negative],
        )


def test_pair_id_collision_for_different_sample_pairs_raises_error():
    pair_a = make_positive(
        "s1",
        "v1",
        pair_id="pair_collision",
    )

    pair_b = make_positive(
        "s2",
        "v2",
        pair_id="pair_collision",
    )

    with pytest.raises(ValueError, match="Pair ID collision"):
        PairAssembler().assemble(
            positive_pairs=[pair_a, pair_b],
            negative_pairs=[],
        )

def test_invalid_positive_label_raises_error():
    invalid = make_pair(
        "s1",
        "v1",
        label=0,
        pair_type="positive",
    )

    with pytest.raises(ValueError, match="Expected label 1"):
        PairAssembler().assemble(
            positive_pairs=[invalid],
            negative_pairs=[],
        )


def test_invalid_negative_pair_type_raises_error():
    invalid = make_pair(
        "s1",
        "s2",
        label=0,
        pair_type="positive",
    )

    with pytest.raises(ValueError, match="Expected pair_type"):
        PairAssembler().assemble(
            positive_pairs=[],
            negative_pairs=[invalid],
        )


def test_self_pair_is_rejected():
    invalid = make_positive("s1", "s1")

    with pytest.raises(ValueError, match="Self-pairs"):
        PairAssembler().assemble(
            positive_pairs=[invalid],
            negative_pairs=[],
        )


def test_empty_pair_id_is_rejected():
    invalid = make_positive(pair_id="")

    with pytest.raises(ValueError, match="Pair ID must not be empty"):
        PairAssembler().assemble(
            positive_pairs=[invalid],
            negative_pairs=[],
        )


def test_split_is_preserved():
    positive = make_positive(split="validation")
    negative = make_negative(split="test")

    result = PairAssembler().assemble(
        positive_pairs=[positive],
        negative_pairs=[negative],
    )

    splits = {
        pair.pair_id: pair.split
        for pair in result.pairs
    }

    assert splits[positive.pair_id] == "validation"
    assert splits[negative.pair_id] == "test"


def test_input_records_are_not_mutated():
    positive = make_positive()
    negative = make_negative()

    original_positive = vars(positive).copy()
    original_negative = vars(negative).copy()

    PairAssembler().assemble(
        positive_pairs=[positive],
        negative_pairs=[negative],
    )

    assert vars(positive) == original_positive
    assert vars(negative) == original_negative

def test_assembler_accepts_dict_records():
    positive = {
        "pair_id": "pair_pos",
        "sample_a_id": "s1",
        "sample_b_id": "v1",
        "label": 1,
        "pair_type": "positive",
        "split": "train",
        "source_a_id": "s1",
        "source_b_id": "s1",
        "problem_a_id": "1",
        "problem_b_id": "1",
        "generation_method": "test",
        "created_seed": 42,
    }

    negative = {
        "pair_id": "pair_neg",
        "sample_a_id": "s2",
        "sample_b_id": "s3",
        "label": 0,
        "pair_type": "negative",
        "split": "test",
        "source_a_id": "s2",
        "source_b_id": "s3",
        "problem_a_id": "2",
        "problem_b_id": "3",
        "generation_method": "test",
        "created_seed": 42,
    }

    result = PairAssembler().assemble([positive], [negative])

    assert result.total_count == 2
    assert result.positive_count == 1
    assert result.negative_count == 1


def test_duplicate_sample_pair_check_can_be_disabled():
    pair_a = make_positive("s1", "v1")
    pair_b = make_positive(
        "v1",
        "s1",
        pair_id="custom_duplicate_id",
    )

    assembler = PairAssembler(
        config=PairAssemblyConfig(
            check_duplicate_pair_ids=True,
            check_duplicate_sample_pairs=False,
        )
    )

    result = assembler.assemble([pair_a, pair_b], [])

    assert result.total_count == 2
    assert result.duplicate_pair_count == 0


def test_duplicate_pair_id_check_can_be_disabled():
    pair_a = make_positive("s1", "v1", pair_id="custom_id")
    pair_b = make_positive("s2", "v2", pair_id="custom_id")

    assembler = PairAssembler(
        config=PairAssemblyConfig(
            check_duplicate_pair_ids=False,
            check_duplicate_sample_pairs=True,
        )
    )

    result = assembler.assemble([pair_a, pair_b], [])

    assert result.total_count == 2
    assert result.duplicate_pair_count == 0


def test_pair_type_label_consistency_check_can_be_disabled():
    unusual_pair = make_pair(
        "s1",
        "s2",
        label=1,
        pair_type="unusual_positive",
    )

    assembler = PairAssembler(
        config=PairAssemblyConfig(
            validate_pair_type_label_consistency=False,
        )
    )

    result = assembler.assemble([unusual_pair], [])

    assert result.total_count == 1
    assert result.positive_count == 1


def test_pair_type_enum_is_supported():
    class PairType(Enum):
        POSITIVE = "positive"
        NEGATIVE = "negative"

    positive = make_positive()
    positive.pair_type = PairType.POSITIVE

    result = PairAssembler().assemble([positive], [])

    assert result.total_count == 1
    assert result.positive_count == 1