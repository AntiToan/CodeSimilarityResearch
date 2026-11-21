import pytest

from src.data.pair_validation_models import (
    PairValidationIssue,
    PairValidationReport,
    PairValidationResult,
    PairValidationStatus,
    ValidationSeverity,
)


def make_error(pair_id="pair_001"):
    return PairValidationIssue(
        rule_id="SCHEMA_001",
        severity=ValidationSeverity.ERROR,
        message="Invalid schema",
        pair_id=pair_id,
    )


def make_warning(pair_id="pair_001"):
    return PairValidationIssue(
        rule_id="AUDIT_001",
        severity=ValidationSeverity.WARNING,
        message="Quota not reached",
        pair_id=pair_id,
    )


# =========================
# Issue tests
# =========================

def test_issue_error_properties():
    issue = make_error()

    assert issue.is_error is True
    assert issue.is_warning is False


def test_issue_warning_properties():
    issue = make_warning()

    assert issue.is_error is False
    assert issue.is_warning is True


def test_issue_rejects_empty_rule_id():
    with pytest.raises(ValueError):
        PairValidationIssue(
            rule_id="",
            severity=ValidationSeverity.ERROR,
            message="Invalid",
        )


def test_issue_rejects_empty_message():
    with pytest.raises(ValueError):
        PairValidationIssue(
            rule_id="RULE_001",
            severity=ValidationSeverity.ERROR,
            message="",
        )


def test_issue_rejects_invalid_severity():
    with pytest.raises(TypeError):
        PairValidationIssue(
            rule_id="RULE_001",
            severity="ERROR",
            message="Invalid severity",
        )


# =========================
# Pair result tests
# =========================

def test_pair_result_pass_without_issues():
    result = PairValidationResult(pair_id="pair_001")

    assert result.status == PairValidationStatus.PASS
    assert result.is_valid is True
    assert result.error_count == 0
    assert result.warning_count == 0


def test_pair_result_fail_with_error():
    result = PairValidationResult(
        pair_id="pair_001",
        issues=(make_error(),),
    )

    assert result.status == PairValidationStatus.FAIL
    assert result.is_valid is False
    assert result.error_count == 1


def test_pair_result_warning_without_error():
    result = PairValidationResult(
        pair_id="pair_001",
        issues=(make_warning(),),
    )

    assert result.status == PairValidationStatus.WARNING
    assert result.is_valid is True
    assert result.warning_count == 1


def test_error_takes_priority_over_warning():
    result = PairValidationResult(
        pair_id="pair_001",
        issues=(
            make_warning(),
            make_error(),
        ),
    )

    assert result.status == PairValidationStatus.FAIL
    assert result.error_count == 1
    assert result.warning_count == 1


def test_pair_result_rejects_mismatched_issue_pair_id():
    with pytest.raises(ValueError):
        PairValidationResult(
            pair_id="pair_001",
            issues=(make_error(pair_id="pair_999"),),
        )


def test_pair_result_rejects_empty_pair_id():
    with pytest.raises(ValueError):
        PairValidationResult(pair_id="")


# =========================
# Report tests
# =========================

def test_empty_report_is_pass():
    report = PairValidationReport.from_results([])

    assert report.total_pair_count == 0
    assert report.valid_pair_count == 0
    assert report.invalid_pair_count == 0
    assert report.status == PairValidationStatus.PASS


def test_report_counts_results_correctly():
    results = [
        PairValidationResult(pair_id="pair_001"),
        PairValidationResult(
            pair_id="pair_002",
            issues=(make_warning("pair_002"),),
        ),
        PairValidationResult(
            pair_id="pair_003",
            issues=(make_error("pair_003"),),
        ),
    ]

    report = PairValidationReport.from_results(results)

    assert report.total_pair_count == 3
    assert report.valid_pair_count == 2
    assert report.invalid_pair_count == 1
    assert report.pass_pair_count == 1
    assert report.warning_pair_count == 1
    assert report.error_count == 1
    assert report.warning_count == 1
    assert report.status == PairValidationStatus.FAIL


def test_report_warning_when_only_warnings_exist():
    results = [
        PairValidationResult(
            pair_id="pair_001",
            issues=(make_warning("pair_001"),),
        ),
        PairValidationResult(pair_id="pair_002"),
    ]

    report = PairValidationReport.from_results(results)

    assert report.status == PairValidationStatus.WARNING
    assert report.invalid_pair_count == 0
    assert report.valid_pair_count == 2


def test_report_sorts_results_deterministically():
    results = [
        PairValidationResult(pair_id="pair_003"),
        PairValidationResult(pair_id="pair_001"),
        PairValidationResult(pair_id="pair_002"),
    ]

    report = PairValidationReport.from_results(results)

    assert [
        result.pair_id
        for result in report.pair_results
    ] == [
        "pair_001",
        "pair_002",
        "pair_003",
    ]


def test_report_rejects_duplicate_pair_ids():
    with pytest.raises(ValueError):
        PairValidationReport(
            validator_version="1.0.0",
            pair_results=(
                PairValidationResult(pair_id="pair_001"),
                PairValidationResult(pair_id="pair_001"),
            ),
        )


def test_report_to_dict():
    report = PairValidationReport.from_results(
        [
            PairValidationResult(pair_id="pair_001"),
            PairValidationResult(
                pair_id="pair_002",
                issues=(make_warning("pair_002"),),
            ),
        ]
    )

    output = report.to_dict()

    assert output == {
        "validator_version": "1.0.0",
        "status": "WARNING",
        "total_pair_count": 2,
        "valid_pair_count": 2,
        "invalid_pair_count": 0,
        "pass_pair_count": 1,
        "warning_pair_count": 1,
        "error_count": 0,
        "warning_count": 1,
    }