import csv
import io

from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.final_dataset_exporter import FinalDatasetExporter


def make_pairs():
    return (
        PairRecord(
            pair_id="pair_001",
            sample_a_id="original_001",
            sample_b_id="variant_001",
            label=1,
            pair_type=PairType.POSITIVE,
            split=PairSplit.TRAIN,
            source_a_id="original_001",
            source_b_id="original_001",
            problem_a_id="1",
            problem_b_id="1",
            generation_method="transformation",
            created_seed=42,
        ),
        PairRecord(
            pair_id="pair_002",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
            label=0,
            pair_type=PairType.NEGATIVE,
            split=PairSplit.VALIDATION,
            source_a_id="source_001",
            source_b_id="source_002",
            problem_a_id="1",
            problem_b_id="2",
            generation_method="cross_problem_sampling",
            created_seed=42,
        ),
    )


def test_serialize_pairs_has_complete_schema_and_preserves_order():
    pairs = make_pairs()

    csv_text = FinalDatasetExporter.serialize_pairs(pairs)

    rows = list(csv.DictReader(io.StringIO(csv_text)))

    assert len(rows) == 2
    assert list(rows[0]) == [
        "pair_id",
        "sample_a_id",
        "sample_b_id",
        "label",
        "pair_type",
        "split",
        "source_a_id",
        "source_b_id",
        "problem_a_id",
        "problem_b_id",
        "generation_method",
        "created_seed",
    ]

    assert rows[0]["pair_id"] == "pair_001"
    assert rows[0]["pair_type"] == PairType.POSITIVE.value
    assert rows[0]["split"] == PairSplit.TRAIN.value
    assert rows[0]["created_seed"] == "42"

    assert rows[1]["pair_id"] == "pair_002"
    assert rows[1]["pair_type"] == PairType.NEGATIVE.value
    assert rows[1]["split"] == PairSplit.VALIDATION.value


def test_serialize_pairs_is_deterministic():
    pairs = make_pairs()

    first = FinalDatasetExporter.serialize_pairs(pairs)
    second = FinalDatasetExporter.serialize_pairs(pairs)

    assert first == second

import pytest
from src.data.final_dataset_validation_models import (
    FinalDatasetValidationReport,
    FinalDatasetValidationStatus,
)


def make_validation_report(status):
    return FinalDatasetValidationReport(
        status=status,
        total_pairs=2,
        positive_count=1,
        negative_count=1,
        issues=(),
    )


def test_export_gate_accepts_pass():
    report = make_validation_report(
        FinalDatasetValidationStatus.PASS
    )

    FinalDatasetExporter.ensure_export_allowed(report)


def test_export_gate_rejects_warning_by_default():
    report = make_validation_report(
        FinalDatasetValidationStatus.WARNING
    )

    with pytest.raises(ValueError):
        FinalDatasetExporter.ensure_export_allowed(report)


def test_export_gate_accepts_warning_when_explicitly_allowed():
    report = make_validation_report(
        FinalDatasetValidationStatus.WARNING
    )

    FinalDatasetExporter.ensure_export_allowed(
        report,
        allow_warnings=True,
    )


def test_export_gate_never_allows_fail():
    report = make_validation_report(
        FinalDatasetValidationStatus.FAIL
    )

    with pytest.raises(ValueError):
        FinalDatasetExporter.ensure_export_allowed(
            report,
            allow_warnings=True,
        )

from src.safety.safe_persistence import (
    CollisionMode,
    CommitState,
    VerificationState,
)


def test_export_csv_persists_and_verifies_artifact(tmp_path):
    pairs = make_pairs()
    report = make_validation_report(
        FinalDatasetValidationStatus.PASS
    )
    destination = tmp_path / "final_dataset.csv"

    result = FinalDatasetExporter.export_csv(
        pairs,
        report,
        destination=destination,
        authorized_root=tmp_path,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
    )

    assert result.commit_state is CommitState.COMMITTED
    assert result.verification_state is VerificationState.PASSED
    assert result.verified is True
    assert destination.is_file()
    assert destination.read_bytes() == (
        FinalDatasetExporter.serialize_pairs(pairs).encode("utf-8")
    )

def test_export_fail_report_never_creates_artifact(tmp_path):
    pairs = make_pairs()
    report = make_validation_report(
        FinalDatasetValidationStatus.FAIL
    )
    destination = tmp_path / "blocked_fail.csv"

    with pytest.raises(ValueError, match="validation failed"):
        FinalDatasetExporter.export_csv(
            pairs,
            report,
            destination=destination,
            authorized_root=tmp_path,
            collision_mode=CollisionMode.FAIL_IF_EXISTS,
            allow_warnings=True,
        )

    assert not destination.exists()


def test_export_warning_default_does_not_create_artifact(tmp_path):
    pairs = make_pairs()
    report = make_validation_report(
        FinalDatasetValidationStatus.WARNING
    )
    destination = tmp_path / "blocked_warning.csv"

    with pytest.raises(ValueError, match="has warnings"):
        FinalDatasetExporter.export_csv(
            pairs,
            report,
            destination=destination,
            authorized_root=tmp_path,
            collision_mode=CollisionMode.FAIL_IF_EXISTS,
        )

    assert not destination.exists()

def test_export_warning_when_explicitly_allowed_persists_artifact(tmp_path):
    pairs = make_pairs()
    report = make_validation_report(
        FinalDatasetValidationStatus.WARNING
    )
    destination = tmp_path / "warning_allowed.csv"

    result = FinalDatasetExporter.export_csv(
        pairs,
        report,
        destination=destination,
        authorized_root=tmp_path,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        allow_warnings=True,
    )

    assert result.commit_state is CommitState.COMMITTED
    assert result.verification_state is VerificationState.PASSED
    assert result.verified is True
    assert destination.is_file()

def test_export_collision_fail_if_exists_preserves_existing_artifact(tmp_path):
    pairs = make_pairs()
    report = make_validation_report(
        FinalDatasetValidationStatus.PASS
    )
    destination = tmp_path / "existing_dataset.csv"
    original_content = b"existing-artifact-must-not-be-overwritten"

    destination.write_bytes(original_content)

    result = FinalDatasetExporter.export_csv(
        pairs,
        report,
        destination=destination,
        authorized_root=tmp_path,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
    )

    assert result.commit_state is CommitState.NOT_COMMITTED
    assert destination.read_bytes() == original_content

def test_export_invalid_pair_input_does_not_create_artifact(tmp_path):
    report = make_validation_report(
        FinalDatasetValidationStatus.PASS
    )
    destination = tmp_path / "invalid_input.csv"

    with pytest.raises(TypeError, match="PairRecord"):
        FinalDatasetExporter.export_csv(
            [object()],
            report,
            destination=destination,
            authorized_root=tmp_path,
            collision_mode=CollisionMode.FAIL_IF_EXISTS,
        )

    assert not destination.exists()
