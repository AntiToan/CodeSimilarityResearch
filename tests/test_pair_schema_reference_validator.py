import pytest

from src.data.pair_schema_reference_validator import (
    PairSchemaReferenceValidator,
)
from src.data.pair_validation_models import (
    PairValidationStatus,
)


SAMPLES = {
    "orig_001": {
        "sample_id": "orig_001",
        "source_id": "orig_001",
        "problem_id": "1",
        "split": "train",
    },
    "variant_001": {
        "sample_id": "variant_001",
        "original_sample_id": "orig_001",
        "problem_id": "1",
        "split": "train",
    },
    "orig_002": {
        "sample_id": "orig_002",
        "source_id": "orig_002",
        "problem_id": "2",
        "split": "train",
    },
}


def make_positive_pair(**overrides):
    pair = {
        "pair_id": "pair_001",
        "sample_a_id": "orig_001",
        "sample_b_id": "variant_001",
        "label": 1,
        "pair_type": "positive",
        "split": "train",
        "source_a_id": "orig_001",
        "source_b_id": "orig_001",
        "problem_a_id": "1",
        "problem_b_id": "1",
        "generation_method": "transformation:whitespace",
        "created_seed": 42,
    }
    pair.update(overrides)
    return pair


@pytest.fixture
def validator():
    return PairSchemaReferenceValidator()


# =========================
# Valid pair
# =========================

def test_valid_pair_passes(validator):
    result = validator.validate_pair(make_positive_pair(), SAMPLES)

    assert result.status == PairValidationStatus.PASS
    assert result.is_valid is True
    assert result.error_count == 0


# =========================
# Schema
# =========================

def test_missing_required_field_fails(validator):
    pair = make_positive_pair()
    del pair["generation_method"]

    result = validator.validate_pair(pair, SAMPLES)

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "SCHEMA_MISSING_FIELD"
        for issue in result.issues
    )


@pytest.mark.parametrize("label", [2, -1, "1", True])
def test_invalid_label_fails(validator, label):
    result = validator.validate_pair(
        make_positive_pair(label=label),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL


@pytest.mark.parametrize("pair_type", ["unknown", "", None])
def test_invalid_pair_type_fails(validator, pair_type):
    result = validator.validate_pair(
        make_positive_pair(pair_type=pair_type),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL


def test_label_pair_type_mismatch_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(label=0, pair_type="positive"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "SCHEMA_LABEL_TYPE_MISMATCH"
        for issue in result.issues
    )


@pytest.mark.parametrize("split", ["dev", "", None])
def test_invalid_split_fails(validator, split):
    result = validator.validate_pair(
        make_positive_pair(split=split),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL


@pytest.mark.parametrize("seed", ["42", 1.5, True])
def test_invalid_seed_fails(validator, seed):
    result = validator.validate_pair(
        make_positive_pair(created_seed=seed),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL


def test_none_seed_is_valid(validator):
    result = validator.validate_pair(
        make_positive_pair(created_seed=None),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.PASS


def test_empty_string_field_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(generation_method=""),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL


# =========================
# Sample reference
# =========================

def test_missing_sample_reference_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(sample_b_id="missing_sample"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "REFERENCE_SAMPLE_NOT_FOUND"
        for issue in result.issues
    )


def test_self_pair_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(sample_b_id="orig_001"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "REFERENCE_SELF_PAIR"
        for issue in result.issues
    )


def test_source_metadata_mismatch_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(source_b_id="wrong_source"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "REFERENCE_SOURCE_MISMATCH"
        for issue in result.issues
    )


def test_problem_metadata_mismatch_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(problem_b_id="99"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "REFERENCE_PROBLEM_MISMATCH"
        for issue in result.issues
    )


def test_pair_split_mismatch_fails(validator):
    result = validator.validate_pair(
        make_positive_pair(split="validation"),
        SAMPLES,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "REFERENCE_SPLIT_MISMATCH"
        for issue in result.issues
    )


# =========================
# Batch
# =========================

def test_batch_validates_multiple_pairs(validator):
    pair1 = make_positive_pair(pair_id="pair_001")
    pair2 = make_positive_pair(
        pair_id="pair_002",
        sample_a_id="orig_002",
        sample_b_id="orig_002",
        source_a_id="orig_002",
        source_b_id="orig_002",
        problem_a_id="2",
        problem_b_id="2",
    )

    report = validator.validate_batch(
        [pair1, pair2],
        SAMPLES,
    )

    assert report.total_pair_count == 2
    assert report.invalid_pair_count == 1
    assert report.status == PairValidationStatus.FAIL


def test_batch_duplicate_pair_id_is_reported(validator):
    pair1 = make_positive_pair()
    pair2 = make_positive_pair(
        sample_a_id="orig_002",
        sample_b_id="orig_002",
        source_a_id="orig_002",
        source_b_id="orig_002",
        problem_a_id="2",
        problem_b_id="2",
    )

    report = validator.validate_batch(
        [pair1, pair2],
        SAMPLES,
    )

    assert report.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "SCHEMA_DUPLICATE_PAIR_ID"
        for result in report.pair_results
        for issue in result.issues
    )


def test_batch_results_are_deterministically_sorted(validator):
    pairs = [
        make_positive_pair(pair_id="pair_003"),
        make_positive_pair(pair_id="pair_001"),
        make_positive_pair(pair_id="pair_002"),
    ]

    report = validator.validate_batch(pairs, SAMPLES)

    assert [
        result.pair_id
        for result in report.pair_results
    ] == [
        "pair_001",
        "pair_002",
        "pair_003",
    ]