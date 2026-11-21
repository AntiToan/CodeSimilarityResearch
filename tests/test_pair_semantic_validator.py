import pytest

from src.data.pair_semantic_validator import PairSemanticValidator
from src.data.pair_validation_models import PairValidationStatus


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
    "orig_003": {
        "sample_id": "orig_003",
        "source_id": "orig_003",
        "problem_id": "3",
        "split": "train",
    },
}

VARIANTS = {
    "variant_001": {
        "variant_id": "variant_001",
        "original_sample_id": "orig_001",
        "transformation_type": "whitespace",
        "validation_status": "PASS",
    }
}

SCREENING = {
    ("orig_001", "orig_002"): {
        "status": "PASS",
        "method": "token_similarity",
    }
}

DUPLICATE_GROUPS = {
    "orig_001": "dup_001",
    "orig_003": "dup_001",
}


def make_positive(**overrides):
    pair = {
        "pair_id": "positive_001",
        "sample_a_id": "orig_001",
        "sample_b_id": "variant_001",
        "label": 1,
        "pair_type": "positive",
        "split": "train",
    }
    pair.update(overrides)
    return pair


def make_negative(**overrides):
    pair = {
        "pair_id": "negative_001",
        "sample_a_id": "orig_001",
        "sample_b_id": "orig_002",
        "label": 0,
        "pair_type": "negative",
        "split": "train",
    }
    pair.update(overrides)
    return pair


@pytest.fixture
def validator():
    return PairSemanticValidator()


# =========================
# Positive tests
# =========================

def test_valid_positive_passes(validator):
    result = validator.validate_pair(
        make_positive(),
        SAMPLES,
        VARIANTS,
    )

    assert result.status == PairValidationStatus.PASS


def test_positive_requires_one_original_and_one_variant(validator):
    pair = make_positive(
        sample_b_id="orig_002",
    )

    result = validator.validate_pair(
        pair,
        SAMPLES,
        VARIANTS,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "POSITIVE_ORIGINAL_VARIANT_ROLE"
        for issue in result.issues
    )


def test_positive_requires_variant_record(validator):
    result = validator.validate_pair(
        make_positive(),
        SAMPLES,
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "POSITIVE_VARIANT_RECORD_MISSING"
        for issue in result.issues
    )


def test_positive_original_lineage_mismatch(validator):
    altered_samples = {
        **SAMPLES,
        "variant_001": {
            **SAMPLES["variant_001"],
            "original_sample_id": "orig_002",
        },
    }

    result = validator.validate_pair(
        make_positive(),
        altered_samples,
        VARIANTS,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "POSITIVE_LINEAGE_MISMATCH"
        for issue in result.issues
    )


def test_positive_rejects_unapproved_transformation(validator):
    variants = {
        "variant_001": {
            **VARIANTS["variant_001"],
            "transformation_type": "unknown_transform",
        }
    }

    result = validator.validate_pair(
        make_positive(),
        SAMPLES,
        variants,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "POSITIVE_TRANSFORMATION_UNAPPROVED"
        for issue in result.issues
    )


def test_positive_requires_variant_validation_pass(validator):
    variants = {
        "variant_001": {
            **VARIANTS["variant_001"],
            "validation_status": "FAIL",
        }
    }

    result = validator.validate_pair(
        make_positive(),
        SAMPLES,
        variants,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "POSITIVE_VARIANT_VALIDATION_FAILED"
        for issue in result.issues
    )


# =========================
# Negative tests
# =========================

def test_valid_negative_passes(validator):
    result = validator.validate_pair(
        make_negative(),
        SAMPLES,
        VARIANTS,
        SCREENING,
        {},
    )

    assert result.status == PairValidationStatus.PASS


def test_negative_rejects_variant_endpoint(validator):
    pair = make_negative(
        sample_b_id="variant_001",
    )

    result = validator.validate_pair(
        pair,
        SAMPLES,
        VARIANTS,
        {},
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_VARIANT_ENDPOINT"
        for issue in result.issues
    )


def test_negative_rejects_same_problem(validator):
    samples = {
        **SAMPLES,
        "orig_002": {
            **SAMPLES["orig_002"],
            "problem_id": "1",
        },
    }

    result = validator.validate_pair(
        make_negative(),
        samples,
        VARIANTS,
        SCREENING,
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_SAME_PROBLEM"
        for issue in result.issues
    )


def test_negative_rejects_same_lineage(validator):
    samples = {
        **SAMPLES,
        "orig_002": {
            **SAMPLES["orig_002"],
            "source_id": "orig_001",
        },
    }

    result = validator.validate_pair(
        make_negative(),
        samples,
        VARIANTS,
        SCREENING,
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_SAME_LINEAGE"
        for issue in result.issues
    )


def test_negative_rejects_known_duplicate_group(validator):
    pair = make_negative(
        sample_a_id="orig_001",
        sample_b_id="orig_003",
    )

    result = validator.validate_pair(
        pair,
        SAMPLES,
        VARIANTS,
        {},
        DUPLICATE_GROUPS,
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_KNOWN_DUPLICATE"
        for issue in result.issues
    )


def test_negative_requires_screening_record(validator):
    result = validator.validate_pair(
        make_negative(),
        SAMPLES,
        VARIANTS,
        {},
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_SCREENING_RECORD_MISSING"
        for issue in result.issues
    )


def test_negative_rejects_failed_screening(validator):
    failed_screening = {
        ("orig_001", "orig_002"): {
            "status": "FAIL",
            "method": "token_similarity",
        }
    }

    result = validator.validate_pair(
        make_negative(),
        SAMPLES,
        VARIANTS,
        failed_screening,
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_SCREENING_NOT_PASSED"
        for issue in result.issues
    )


def test_negative_requires_screening_method(validator):
    screening_without_method = {
        ("orig_001", "orig_002"): {
            "status": "PASS",
        }
    }

    result = validator.validate_pair(
        make_negative(),
        SAMPLES,
        VARIANTS,
        screening_without_method,
        {},
    )

    assert result.status == PairValidationStatus.FAIL
    assert any(
        issue.rule_id == "NEGATIVE_SCREENING_METHOD_MISSING"
        for issue in result.issues
    )


# =========================
# Batch
# =========================

def test_batch_semantic_validation(validator):
    pairs = [
        make_positive(pair_id="pair_001"),
        make_negative(pair_id="pair_002"),
        make_negative(
            pair_id="pair_003",
            sample_b_id="orig_003",
        ),
    ]

    screening = {
        **SCREENING,
        ("orig_001", "orig_003"): {
            "status": "PASS",
            "method": "token_similarity",
        },
    }

    report = validator.validate_batch(
        pairs,
        SAMPLES,
        VARIANTS,
        screening,
        DUPLICATE_GROUPS,
    )

    assert report.total_pair_count == 3
    assert report.invalid_pair_count == 1
    assert report.status == PairValidationStatus.FAIL