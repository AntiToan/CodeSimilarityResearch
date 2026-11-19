from pathlib import Path
from unittest.mock import Mock

from src.data.variant_pipeline_orchestrator import (
    VariantPipelineOrchestrator,
    VariantPersistenceResult,
)


def test_persistence_result_success():
    result = VariantPersistenceResult(
        variant_id="sample_v001",
        written=True,
        registered=True,
    )

    assert result.success is True


def test_persistence_result_written_but_not_registered():
    result = VariantPersistenceResult(
        variant_id="sample_v001",
        written=True,
        registered=False,
        error="Registry error",
    )

    assert result.success is False
    assert result.written is True
    assert result.registered is False


def test_persistence_result_failed_write():
    result = VariantPersistenceResult(
        variant_id="sample_v001",
        written=False,
        registered=False,
        error="Write error",
    )

    assert result.success is False
    assert result.written is False


def test_orchestrator_calls_generator_and_report():
    generator = Mock()
    generation_result = Mock()
    generation_result.accepted_variants = []
    generator.generate.return_value = generation_result

    writer = Mock()
    registry = Mock()
    report = Mock()

    orchestrator = VariantPipelineOrchestrator(
        generator=generator,
        writer=writer,
        registry=registry,
        report=report,
        validator_version="v1",
    )

    result = orchestrator.process_sample(
        sample_id="sample001",
        problem_id="100",
        split="train",
        original_source="print(1);",
        original_source_path=Path("originals/sample001.cpp"),
        seed=42,
    )

    generator.generate.assert_called_once_with(
        original_sample_id="sample001",
        original_source="print(1);",
        seed=42,
    )

    report.add_result.assert_called_once_with(
        generation_result,
        split="train",
    )

    assert result.generation_result is generation_result
    assert result.persistence_results == []
    writer.write_variant.assert_not_called()
    registry.register.assert_not_called()


def test_orchestrator_rejects_empty_validator_version():
    try:
        VariantPipelineOrchestrator(
            generator=Mock(),
            writer=Mock(),
            registry=Mock(),
            report=Mock(),
            validator_version="",
        )
    except ValueError as exc:
        assert "validator_version" in str(exc)
    else:
        raise AssertionError("Expected ValueError")