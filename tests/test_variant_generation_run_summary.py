
from pathlib import Path
from types import SimpleNamespace

from src.data.variant_generation_run_summary import (
    VariantGenerationRunSummaryBuilder,
    VariantGenerationRunSummaryExporter,
)


def make_batch(
    *,
    status="COMPLETED",
    processed=10,
    succeeded=10,
    failed=0,
    written=20,
    registered=20,
    seed=42,
    errors=None,
):
    return SimpleNamespace(
        master_seed=seed,
        status=status,
        samples_processed=processed,
        samples_succeeded=succeeded,
        samples_failed=failed,
        variants_written=written,
        variants_registered=registered,
        success_rate=(succeeded / processed if processed else 0.0),
        errors=errors or [],
    )


def test_build_summary_from_completed_batch():
    batch = make_batch()

    summary = VariantGenerationRunSummaryBuilder.build(
        batch,
        dataset="poj104",
        split="train",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
    )

    assert summary.status == "COMPLETED"
    assert summary.samples_processed == 10
    assert summary.samples_succeeded == 10
    assert summary.samples_failed == 0
    assert summary.variants_written == 20
    assert summary.variants_registered == 20
    assert summary.success_rate == 1.0
    assert summary.error_count == 0


def test_build_summary_for_partial_batch():
    batch = make_batch(
        status="PARTIAL",
        processed=10,
        succeeded=8,
        failed=2,
        written=15,
        registered=15,
    )

    summary = VariantGenerationRunSummaryBuilder.build(batch)

    assert summary.status == "PARTIAL"
    assert summary.samples_failed == 2
    assert summary.success_rate == 0.8


def test_build_summary_for_failed_batch():
    batch = make_batch(
        status="FAILED",
        processed=5,
        succeeded=0,
        failed=5,
        written=0,
        registered=0,
    )

    summary = VariantGenerationRunSummaryBuilder.build(batch)

    assert summary.status == "FAILED"
    assert summary.samples_succeeded == 0
    assert summary.samples_failed == 5


def test_summary_includes_sample_errors():
    errors = [
        SimpleNamespace(
            sample_id="sample_1",
            error_type="ValueError",
            message="Invalid source",
        ),
        SimpleNamespace(
            sample_id="sample_2",
            error_type="OSError",
            message="File not found",
        ),
    ]

    batch = make_batch(
        status="PARTIAL",
        processed=2,
        succeeded=0,
        failed=2,
        errors=errors,
    )

    summary = VariantGenerationRunSummaryBuilder.build(batch)

    assert summary.error_count == 2
    assert summary.errors[0]["sample_id"] == "sample_1"
    assert summary.errors[0]["error_type"] == "ValueError"
    assert summary.errors[1]["sample_id"] == "sample_2"


def test_summary_to_dict_contains_error_count():
    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch()
    )

    payload = summary.to_dict()

    assert payload["dataset"] == "poj104"
    assert payload["split"] == "train"
    assert payload["master_seed"] == 42
    assert payload["error_count"] == 0


def test_summary_uses_default_timestamps():
    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch()
    )

    assert summary.started_at
    assert summary.finished_at


def test_export_json_creates_parent_directories(tmp_path):
    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch()
    )

    output_path = tmp_path / "reports" / "run_summary.json"

    result = VariantGenerationRunSummaryExporter.export_json(
        summary,
        output_path,
    )

    assert result == output_path
    assert output_path.exists()


def test_export_json_content(tmp_path):
    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch(),
        dataset="poj104",
        split="test",
    )

    output_path = tmp_path / "summary.json"

    VariantGenerationRunSummaryExporter.export_json(
        summary,
        output_path,
    )

    import json

    payload = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert payload["dataset"] == "poj104"
    assert payload["split"] == "test"
    assert payload["status"] == "COMPLETED"
    assert payload["variants_written"] == 20
    assert payload["error_count"] == 0


def test_export_json_is_valid_utf8(tmp_path):
    errors = [
        SimpleNamespace(
            sample_id="sample_vn",
            error_type="RuntimeError",
            message="Lỗi xử lý mã nguồn",
        )
    ]

    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch(
            status="PARTIAL",
            processed=1,
            succeeded=0,
            failed=1,
            errors=errors,
        )
    )

    output_path = tmp_path / "summary.json"

    VariantGenerationRunSummaryExporter.export_json(
        summary,
        output_path,
    )

    content = output_path.read_text(encoding="utf-8")

    assert "Lỗi xử lý mã nguồn" in content


def test_export_json_returns_path(tmp_path):
    summary = VariantGenerationRunSummaryBuilder.build(
        make_batch()
    )

    output_path = tmp_path / "summary.json"

    returned_path = VariantGenerationRunSummaryExporter.export_json(
        summary,
        output_path,
    )

    assert isinstance(returned_path, Path)
    assert returned_path == output_path
