
import json

from src.data.variant_generation_report import (
    VariantGenerationReport,
    VariantGenerationReportExporter,
)
from src.transformations.variant_generator import (
    GeneratedVariant,
    VariantAttempt,
    VariantGenerationResult,
)


def make_variant(sample_id, index, transformation):
    return GeneratedVariant(
        variant_id=f"{sample_id}_v{index:03d}",
        original_sample_id=sample_id,
        variant_index=index,
        transformation_type=transformation,
        generation_seed=100 + index,
        source_text="original",
        transformed_text=f"transformed_{index}",
    )


def make_result(
    sample_id,
    accepted=0,
    rejected=0,
    target=2,
    transformations=None,
    rejection_reason="VALIDATION_FAILED",
):
    result = VariantGenerationResult(
        original_sample_id=sample_id,
        seed=42,
        target_variants=target,
    )

    transformations = transformations or ["whitespace", "comments"]

    for index in range(1, accepted + 1):
        transformation = transformations[
            (index - 1) % len(transformations)
        ]
        result.accepted_variants.append(
            make_variant(sample_id, index, transformation)
        )
        result.attempts.append(
            VariantAttempt(
                variant_index=index,
                attempt_index=1,
                transformation_type=transformation,
                seed=100 + index,
                accepted=True,
            )
        )

    for index in range(1, rejected + 1):
        result.attempts.append(
            VariantAttempt(
                variant_index=min(index, target),
                attempt_index=index,
                transformation_type="formatting",
                seed=200 + index,
                accepted=False,
                rejection_reason=rejection_reason,
            )
        )

    return result


def test_report_aggregates_completed_result():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result("sample_001", accepted=2),
        split="train",
    )

    assert report.originals_processed == 1
    assert report.originals_completed == 1
    assert report.variants_accepted == 2
    assert report.attempts_total == 2
    assert report.attempts_rejected == 0
    assert report.quota_rate == 1.0


def test_report_aggregates_partial_result():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result(
            "sample_001",
            accepted=1,
            rejected=2,
        ),
        split="validation",
    )

    assert report.originals_partial == 1
    assert report.variants_accepted == 1
    assert report.attempts_total == 3
    assert report.attempts_rejected == 2
    assert report.quota_rate == 0.0


def test_report_aggregates_failed_result():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result(
            "sample_001",
            accepted=0,
            rejected=5,
        ),
        split="test",
    )

    assert report.originals_failed == 1
    assert report.variants_accepted == 0
    assert report.attempts_rejected == 5


def test_report_counts_rejection_reasons():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result(
            "sample_001",
            accepted=1,
            rejected=2,
            rejection_reason="VALIDATION_FAILED",
        )
    )

    assert report.rejection_reasons == {
        "VALIDATION_FAILED": 2
    }


def test_report_counts_accepted_transformations():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result(
            "sample_001",
            accepted=2,
            transformations=["whitespace", "comments"],
        )
    )

    assert report.transformations == {
        "whitespace": 1,
        "comments": 1,
    }


def test_report_counts_attempted_transformations():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result(
            "sample_001",
            accepted=1,
            rejected=2,
        )
    )

    assert report.attempted_transformations["formatting"] == 2
    assert report.attempted_transformations["whitespace"] == 1


def test_report_tracks_split_distribution():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    report.add_result(
        make_result("sample_001", accepted=2),
        split="train",
    )
    report.add_result(
        make_result("sample_002", accepted=1, rejected=1),
        split="validation",
    )

    assert report.split_distribution == {
        "train": 2,
        "validation": 1,
    }


def test_report_empty_quota_rate_is_zero():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    assert report.quota_rate == 0.0


def test_report_to_dict_contains_expected_schema():
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )
    report.add_result(
        make_result("sample_001", accepted=2),
        split="train",
    )

    payload = report.to_dict()

    assert payload["report_version"] == "1.0"
    assert payload["dataset"] == "poj104"
    assert payload["summary"]["originals_processed"] == 1
    assert payload["summary"]["variants_accepted"] == 2
    assert payload["samples"][0]["original_sample_id"] == "sample_001"


def test_report_exporter_creates_json(tmp_path):
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )
    report.add_result(
        make_result("sample_001", accepted=2),
        split="train",
    )

    output = tmp_path / "reports" / "run.json"

    exported_path = VariantGenerationReportExporter.export_json(
        report,
        output,
    )

    assert exported_path.exists()

    payload = json.loads(
        exported_path.read_text(encoding="utf-8")
    )

    assert payload["summary"]["variants_accepted"] == 2


def test_report_exporter_overwrites_previous_report_atomically(
    tmp_path,
):
    report = VariantGenerationReport(
        dataset="poj104",
        quota_target=2,
    )

    output = tmp_path / "report.json"

    VariantGenerationReportExporter.export_json(
        report,
        output,
    )

    report.add_result(
        make_result("sample_001", accepted=2),
        split="train",
    )

    VariantGenerationReportExporter.export_json(
        report,
        output,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["variants_accepted"] == 2
