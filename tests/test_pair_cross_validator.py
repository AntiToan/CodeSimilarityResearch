from src.data.pair_cross_validator import PairCrossValidator
from src.data.pair_validation_models import (
    PairValidationIssue,
    PairValidationResult,
    PairValidationReport,
    ValidationSeverity,
)
from types import SimpleNamespace
from src.data.positive_pair_generator import PositivePairGenerator
from src.data.pair_validation_models import PairValidationStatus

class StubValidator:
    def __init__(self, report):
        self.report = report

    def validate_batch(self, **kwargs):
        return self.report


def make_issue(rule_id, pair_id):
    return PairValidationIssue(
        rule_id=rule_id,
        severity=ValidationSeverity.ERROR,
        message=f"Test issue: {rule_id}",
        pair_id=pair_id,
    )


def make_report(results, version="test"):
    return PairValidationReport.from_results(
        results,
        validator_version=version,
    )


def test_cross_validator_preserves_all_issues():
    pair_id = "pair_001"

    schema_report = make_report([
        PairValidationResult(
            pair_id=pair_id,
            issues=(make_issue("SCHEMA_ERROR", pair_id),),
        )
    ])

    semantic_report = make_report([
        PairValidationResult(
            pair_id=pair_id,
            issues=(make_issue("SEMANTIC_ERROR", pair_id),),
        )
    ])

    integrity_report = make_report([
        PairValidationResult(
            pair_id=pair_id,
            issues=(make_issue("INTEGRITY_ERROR", pair_id),),
        )
    ])

    validator = PairCrossValidator(
        schema_validator=StubValidator(schema_report),
        semantic_validator=StubValidator(semantic_report),
        integrity_validator=StubValidator(integrity_report),
    )

    report = validator.validate_batch(
        pairs=[{"pair_id": pair_id}],
        samples={},
        variants={},
    )

    assert len(report.pair_results) == 1

    result = report.pair_results[0]

    assert result.pair_id == pair_id
    assert len(result.issues) == 3

    rule_ids = {issue.rule_id for issue in result.issues}

    assert rule_ids == {
        "SCHEMA_ERROR",
        "SEMANTIC_ERROR",
        "INTEGRITY_ERROR",
    }


def test_cross_validator_aggregates_multiple_pair_ids():
    report_a = make_report([
        PairValidationResult(
            pair_id="pair_a",
            issues=(make_issue("ERROR_A", "pair_a"),),
        )
    ])

    report_b = make_report([
        PairValidationResult(
            pair_id="pair_b",
            issues=(make_issue("ERROR_B", "pair_b"),),
        )
    ])

    report_c = make_report([])

    validator = PairCrossValidator(
        schema_validator=StubValidator(report_a),
        semantic_validator=StubValidator(report_b),
        integrity_validator=StubValidator(report_c),
    )

    report = validator.validate_batch(
        pairs=[],
        samples={},
        variants={},
    )

    pair_ids = [result.pair_id for result in report.pair_results]

    assert pair_ids == ["pair_a", "pair_b"]


def test_cross_validator_empty_batch():
    empty_report = make_report([])

    validator = PairCrossValidator(
        schema_validator=StubValidator(empty_report),
        semantic_validator=StubValidator(empty_report),
        integrity_validator=StubValidator(empty_report),
    )

    report = validator.validate_batch(
        pairs=[],
        samples={},
        variants={},
    )

    assert report.pair_results == ()


def test_cross_validator_is_deterministic():
    report_a = make_report([
        PairValidationResult(
            pair_id="pair_b",
            issues=(make_issue("ERROR_B", "pair_b"),),
        ),
        PairValidationResult(
            pair_id="pair_a",
            issues=(make_issue("ERROR_A", "pair_a"),),
        ),
    ])

    empty_report = make_report([])

    validator = PairCrossValidator(
        schema_validator=StubValidator(report_a),
        semantic_validator=StubValidator(empty_report),
        integrity_validator=StubValidator(empty_report),
    )

    first = validator.validate_batch(
        pairs=[],
        samples={},
        variants={},
    )

    second = validator.validate_batch(
        pairs=[],
        samples={},
        variants={},
    )

    assert first.to_dict() == second.to_dict()
    assert [r.pair_id for r in first.pair_results] == [
        "pair_a",
        "pair_b",
    ]

def make_real_integration_fixtures():
    samples = {
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

    variants = {
        "variant_001": {
            "variant_id": "variant_001",
            "original_sample_id": "orig_001",
            "transformation_type": "whitespace",
            "validation_status": "PASS",
        }
    }

    pair = SimpleNamespace(
        pair_id=PositivePairGenerator.create_pair_id(
            "orig_001",
            "variant_001",
        ),
        sample_a_id="orig_001",
        sample_b_id="variant_001",
        label=1,
        pair_type="positive",
        split="train",
        source_a_id="orig_001",
        source_b_id="orig_001",
        problem_a_id="1",
        problem_b_id="1",
        generation_method="transformation:whitespace",
        created_seed=42,
    )

    return pair, samples, variants


def test_real_validators_integration_valid_positive_pair():
    pair, samples, variants = make_real_integration_fixtures()

    validator = PairCrossValidator()

    report = validator.validate_batch(
        pairs=[pair],
        samples=samples,
        variants=variants,
        screening_records={},
        duplicate_groups={},
    )

    assert len(report.pair_results) == 1

    result = report.pair_results[0]

    assert result.pair_id == pair.pair_id
    assert result.status == PairValidationStatus.PASS
    assert result.issues == ()


def test_real_validators_integration_preserves_schema_and_integrity_issues():
    pair, samples, variants = make_real_integration_fixtures()

    # Deliberately corrupt the pair ID and schema.
    pair.pair_id = "pair_invalid"
    pair.generation_method = ""

    validator = PairCrossValidator()

    report = validator.validate_batch(
        pairs=[pair],
        samples=samples,
        variants=variants,
        screening_records={},
        duplicate_groups={},
    )

    result = report.pair_results[0]
    rule_ids = {issue.rule_id for issue in result.issues}

    assert result.status.value == "FAIL"
    assert any("SCHEMA" in rule_id for rule_id in rule_ids)
    assert any("PAIR_ID" in rule_id for rule_id in rule_ids)