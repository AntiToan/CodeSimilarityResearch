from types import SimpleNamespace
from unittest.mock import Mock
from src.data.negative_pair_generator import NegativePairGenerator

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

def test_generates_valid_negative_pair():
    screener = Mock(return_value=True)
    generator = NegativePairGenerator(screener)

    anchor = make_sample("sample_001", "1")
    candidate = make_sample("sample_002", "2")

    result = generator.generate(anchor, [candidate], seed=42)

    assert result.pairs_generated == 1

    pair = result.pairs[0]

    assert pair.label == 0
    assert pair.pair_type.value == "negative"
    assert pair.problem_a_id != pair.problem_b_id
    assert pair.source_a_id != pair.source_b_id
    assert pair.split.value == "train"
    assert pair.created_seed == 42


def test_rejects_same_problem_candidate():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1"),
        [make_sample("b", "1")],
    )

    assert result.pairs_generated == 0
    assert "Same-problem" in result.rejections[0].reason


def test_rejects_shared_lineage():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("original", "1", source_id="lineage"),
        [make_sample("variant", "2", source_id="lineage")],
    )

    assert result.pairs_generated == 0
    assert "Shared source lineage" in result.rejections[0].reason


def test_rejects_cross_split_candidate():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1", split="train"),
        [make_sample("b", "2", split="test")],
    )

    assert result.pairs_generated == 0
    assert "Cross-split" in result.rejections[0].reason


def test_rejects_known_duplicate_group():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1"),
        [make_sample("b", "2")],
        duplicate_groups={
            "a": "dup_001",
            "b": "dup_001",
        },
    )

    assert result.pairs_generated == 0
    assert "duplicate group" in result.rejections[0].reason.lower()


def test_rejects_similarity_screening_failure():
    generator = NegativePairGenerator(Mock(return_value=False))

    result = generator.generate(
        make_sample("a", "1"),
        [make_sample("b", "2")],
    )

    assert result.pairs_generated == 0
    assert "similarity screening" in result.rejections[0].reason.lower()


def test_screener_exception_is_isolated():
    screener = Mock(side_effect=RuntimeError("screening crashed"))
    generator = NegativePairGenerator(screener)

    result = generator.generate(
        make_sample("a", "1"),
        [
            make_sample("b", "2"),
            make_sample("c", "3"),
        ],
    )

    assert result.pairs_generated == 0
    assert result.candidates_seen == 2
    assert result.candidates_rejected == 2
    assert all("screening error" in r.reason.lower() for r in result.rejections)


def test_accepts_multiple_candidates_from_different_problems():
    generator = NegativePairGenerator(Mock(return_value=True))

    anchor = make_sample("a", "1")
    candidates = [
        make_sample("b", "2"),
        make_sample("c", "3"),
        make_sample("d", "4"),
    ]

    result = generator.generate(anchor, candidates, seed=7)

    assert result.pairs_generated == 3
    assert result.candidates_eligible == 3
    assert len({pair.pair_id for pair in result.pairs}) == 3


def test_pair_ids_are_order_independent():
    generator = NegativePairGenerator(Mock(return_value=True))

    assert generator.create_pair_id("a", "b") == generator.create_pair_id("b", "a")


def test_duplicate_candidate_rejected():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1"),
        [
            make_sample("b", "2"),
            make_sample("b", "2"),
        ],
    )

    assert result.pairs_generated == 1
    assert result.candidates_rejected == 1
    assert "Duplicate pair" in result.rejections[-1].reason


def test_rejects_self_pair():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1"),
        [make_sample("a", "1")],
    )

    assert result.pairs_generated == 0
    assert "Self-pair" in result.rejections[0].reason


def test_empty_candidates():
    generator = NegativePairGenerator(Mock(return_value=True))

    result = generator.generate(
        make_sample("a", "1"),
        [],
    )

    assert result.pairs_generated == 0
    assert result.candidates_seen == 0
    assert result.candidates_rejected == 0
