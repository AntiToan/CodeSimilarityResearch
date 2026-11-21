
from types import SimpleNamespace

import pytest

from src.data.pair_integrity_validator import (
    PairIntegrityValidationConfig,
    PairIntegrityValidator,
)
from src.data.pair_validation_models import PairValidationStatus


def make_sample(sample_id, split="train"):
    return SimpleNamespace(
        sample_id=sample_id,
        split=split,
    )


def make_pair(
    sample_a_id,
    sample_b_id,
    *,
    pair_id=None,
    split="train",
    pair_type="NEGATIVE",
):
    if pair_id is None:
        pair_id = PairIntegrityValidator.compute_pair_id(
            sample_a_id,
            sample_b_id,
        )

    return SimpleNamespace(
        pair_id=pair_id,
        sample_a_id=sample_a_id,
        sample_b_id=sample_b_id,
        split=split,
        pair_type=pair_type,
    )


@pytest.fixture
def validator():
    return PairIntegrityValidator()


@pytest.fixture
def samples():
    return {
        "s1": make_sample("s1", "train"),
        "s2": make_sample("s2", "train"),
        "s3": make_sample("s3", "test"),
        "s4": make_sample("s4", "test"),
    }


def issue_codes(result):
    return {issue.rule_id for issue in result.issues}


# ---------------------------------------------------------
# Pair ID Integrity
# ---------------------------------------------------------

def test_compute_pair_id_matches_generator_algorithm():
    from src.data.positive_pair_generator import PositivePairGenerator
    from src.data.negative_pair_generator import NegativePairGenerator

    expected = PositivePairGenerator.create_pair_id("s1", "s2")

    assert PairIntegrityValidator.compute_pair_id("s1", "s2") == expected
    assert NegativePairGenerator.create_pair_id("s1", "s2") == expected


def test_pair_id_is_order_independent():
    assert PairIntegrityValidator.compute_pair_id("s1", "s2") == (
        PairIntegrityValidator.compute_pair_id("s2", "s1")
    )


def test_valid_pair_has_no_issues(validator, samples):
    pair = make_pair("s1", "s2")

    result = validator.validate_pair(pair, samples)

    assert result.status == PairValidationStatus.PASS
    assert result.issues == ()


def test_pair_id_content_mismatch(validator, samples):
    pair = make_pair(
        "s1",
        "s2",
        pair_id="pair_invalid",
    )

    result = validator.validate_pair(pair, samples)

    assert result.status == PairValidationStatus.FAIL
    assert "PAIR_ID_CONTENT_MISMATCH" in issue_codes(result)


# ---------------------------------------------------------
# Duplicate Pair ID
# ---------------------------------------------------------

def test_duplicate_pair_id_detected(validator, samples):
    pair_a = make_pair("s1", "s2")
    pair_b = make_pair(
        "s1",
        "s3",
        pair_id=pair_a.pair_id,
    )

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    assert report.status == PairValidationStatus.FAIL
    assert report.total_pair_count == 1

    result = report.pair_results[0]

    assert "DUPLICATE_PAIR_ID" in issue_codes(result)
    assert "PAIR_ID_CONTENT_MISMATCH" in issue_codes(result)


def test_duplicate_pair_id_rule_can_be_disabled(samples):
    config = PairIntegrityValidationConfig(
        check_duplicate_pair_ids=False,
    )
    validator = PairIntegrityValidator(config)

    pair_a = make_pair("s1", "s2")
    pair_b = make_pair(
        "s1",
        "s3",
        pair_id=pair_a.pair_id,
    )

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    codes = issue_codes(report.pair_results[0])

    assert "DUPLICATE_PAIR_ID" not in codes


# ---------------------------------------------------------
# Duplicate Sample Pair
# ---------------------------------------------------------

def test_duplicate_sample_pair_detected(validator, samples):
    pair_a = make_pair("s1", "s2")
    pair_b = make_pair("s2", "s1")

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    assert report.status == PairValidationStatus.FAIL
    assert report.total_pair_count == 1

    result = report.pair_results[0]

    assert "DUPLICATE_SAMPLE_PAIR" in issue_codes(result)
    assert "DUPLICATE_PAIR_ID" in issue_codes(result)


def test_duplicate_sample_pair_detected_with_different_pair_ids(
    validator,
    samples,
):
    pair_a = make_pair("s1", "s2")
    pair_b = make_pair(
        "s2",
        "s1",
        pair_id="pair_custom_2",
    )

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    assert report.status == PairValidationStatus.FAIL
    assert report.total_pair_count == 2

    for result in report.pair_results:
        assert "DUPLICATE_SAMPLE_PAIR" in issue_codes(result)


def test_non_duplicate_pairs_pass(validator, samples):
    pairs = [
        make_pair("s1", "s2", split="train"),
        make_pair("s3", "s4", split="test"),
    ]

    report = validator.validate_batch(
        pairs,
        samples,
    )

    assert report.status == PairValidationStatus.PASS
    assert report.total_pair_count == 2
    assert report.invalid_pair_count == 0


def test_duplicate_sample_pair_rule_can_be_disabled(samples):
    config = PairIntegrityValidationConfig(
        check_duplicate_sample_pairs=False,
    )
    validator = PairIntegrityValidator(config)

    pair_a = make_pair("s1", "s2")
    pair_b = make_pair("s2", "s1")

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    for result in report.pair_results:
        assert "DUPLICATE_SAMPLE_PAIR" not in issue_codes(result)


# ---------------------------------------------------------
# Split Leakage
# ---------------------------------------------------------

def test_cross_split_pair_detected(validator, samples):
    pair = make_pair(
        "s1",
        "s3",
        split="train",
    )

    result = validator.validate_pair(pair, samples)

    assert result.status == PairValidationStatus.FAIL
    assert "PAIR_SPLIT_LEAKAGE" in issue_codes(result)


def test_pair_split_mismatch_detected(validator, samples):
    pair = make_pair(
        "s1",
        "s2",
        split="test",
    )

    result = validator.validate_pair(pair, samples)

    assert "PAIR_SPLIT_LEAKAGE" in issue_codes(result)


def test_split_check_can_be_disabled(samples):
    config = PairIntegrityValidationConfig(
        check_split_leakage=False,
    )
    validator = PairIntegrityValidator(config)

    pair = make_pair("s1", "s3", split="train")

    result = validator.validate_pair(pair, samples)

    assert "PAIR_SPLIT_LEAKAGE" not in issue_codes(result)


# ---------------------------------------------------------
# Duplicate Group Leakage
# ---------------------------------------------------------

def test_negative_pair_same_duplicate_group_detected(
    validator,
    samples,
):
    pair = make_pair("s1", "s2", pair_type="NEGATIVE")

    duplicate_groups = {
        "s1": "dup_001",
        "s2": "dup_001",
    }

    result = validator.validate_pair(
        pair,
        samples,
        duplicate_groups,
    )

    assert result.status == PairValidationStatus.FAIL
    assert "DUPLICATE_GROUP_LEAKAGE" in issue_codes(result)


def test_negative_pair_different_duplicate_groups_pass(
    validator,
    samples,
):
    pair = make_pair("s1", "s2", pair_type="NEGATIVE")

    duplicate_groups = {
        "s1": "dup_001",
        "s2": "dup_002",
    }

    result = validator.validate_pair(
        pair,
        samples,
        duplicate_groups,
    )

    assert "DUPLICATE_GROUP_LEAKAGE" not in issue_codes(result)


def test_positive_pair_not_rejected_by_duplicate_group_check(
    validator,
    samples,
):
    pair = make_pair("s1", "s2", pair_type="POSITIVE")

    duplicate_groups = {
        "s1": "dup_001",
        "s2": "dup_001",
    }

    result = validator.validate_pair(
        pair,
        samples,
        duplicate_groups,
    )

    assert "DUPLICATE_GROUP_LEAKAGE" not in issue_codes(result)


def test_duplicate_group_check_can_be_disabled(samples):
    config = PairIntegrityValidationConfig(
        check_duplicate_group_leakage=False,
    )
    validator = PairIntegrityValidator(config)

    pair = make_pair("s1", "s2", pair_type="NEGATIVE")

    duplicate_groups = {
        "s1": "dup_001",
        "s2": "dup_001",
    }

    result = validator.validate_pair(
        pair,
        samples,
        duplicate_groups,
    )

    assert "DUPLICATE_GROUP_LEAKAGE" not in issue_codes(result)


# ---------------------------------------------------------
# Deterministic Report
# ---------------------------------------------------------

def test_batch_report_is_deterministically_sorted(validator, samples):
    pairs = [
        make_pair("s3", "s4"),
        make_pair("s1", "s2"),
    ]

    report = validator.validate_batch(
        pairs,
        samples,
    )

    pair_ids = [result.pair_id for result in report.pair_results]

    assert pair_ids == sorted(pair_ids)


def test_empty_batch_returns_pass_report(validator, samples):
    report = validator.validate_batch([], samples)

    assert report.status == PairValidationStatus.PASS
    assert report.total_pair_count == 0
    assert report.error_count == 0


# ---------------------------------------------------------
# Batch Integrity & Edge Cases
# ---------------------------------------------------------

def test_missing_sample_metadata_detected(validator, samples):
    pair = make_pair("s1", "missing_sample")

    result = validator.validate_pair(pair, samples)

    assert result.status == PairValidationStatus.FAIL
    assert "PAIR_SAMPLE_METADATA_MISSING" in issue_codes(result)


def test_both_sample_metadata_missing_detected(validator):
    pair = make_pair("missing_a", "missing_b")

    result = validator.validate_pair(pair, {})

    assert result.status == PairValidationStatus.FAIL
    assert "PAIR_SAMPLE_METADATA_MISSING" in issue_codes(result)


def test_missing_metadata_and_duplicate_group_issues_aggregated(
    validator,
    samples,
):
    pair = make_pair("s1", "missing_sample", pair_type="NEGATIVE")

    duplicate_groups = {
        "s1": "dup_001",
        "missing_sample": "dup_001",
    }

    result = validator.validate_pair(
        pair,
        samples,
        duplicate_groups,
    )

    codes = issue_codes(result)

    assert "PAIR_SAMPLE_METADATA_MISSING" in codes
    assert "DUPLICATE_GROUP_LEAKAGE" in codes
    assert result.error_count == 2


def test_batch_aggregates_multiple_integrity_issues(
    validator,
    samples,
):
    pair_a = make_pair(
        "s1",
        "s3",
        split="train",
    )

    pair_b = make_pair(
        "s1",
        "missing_sample",
        pair_type="NEGATIVE",
    )

    duplicate_groups = {
        "s1": "dup_001",
        "missing_sample": "dup_001",
    }

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
        duplicate_groups,
    )

    assert report.status == PairValidationStatus.FAIL
    assert report.error_count >= 3

    all_codes = {
        issue.rule_id
        for result in report.pair_results
        for issue in result.issues
    }

    assert "PAIR_SPLIT_LEAKAGE" in all_codes
    assert "PAIR_SAMPLE_METADATA_MISSING" in all_codes
    assert "DUPLICATE_GROUP_LEAKAGE" in all_codes


def test_batch_repeated_same_pair_id_aggregates_all_issues(
    validator,
    samples,
):
    pair_a = make_pair("s1", "s2")
    pair_b = make_pair(
        "s1",
        "s3",
        pair_id=pair_a.pair_id,
    )

    report = validator.validate_batch(
        [pair_a, pair_b],
        samples,
    )

    assert report.total_pair_count == 1

    result = report.pair_results[0]
    codes = issue_codes(result)

    assert "DUPLICATE_PAIR_ID" in codes
    assert "PAIR_ID_CONTENT_MISMATCH" in codes
    assert result.status == PairValidationStatus.FAIL


def test_integrity_report_repeatable(validator, samples):
    pairs = [
        make_pair("s1", "s2"),
        make_pair("s3", "s4", split="test"),
        make_pair("s1", "s3", split="train"),
    ]

    report_a = validator.validate_batch(pairs, samples)
    report_b = validator.validate_batch(pairs, samples)

    assert report_a.to_dict() == report_b.to_dict()

    results_a = [
        (result.pair_id, result.issues)
        for result in report_a.pair_results
    ]
    results_b = [
        (result.pair_id, result.issues)
        for result in report_b.pair_results
    ]

    assert results_a == results_b
