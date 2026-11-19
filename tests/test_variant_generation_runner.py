
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.data.variant_generation_runner import (
    VariantGenerationRunner,
)


def make_sample(
    sample_id="sample001",
    problem_id="1",
    split="train",
):
    return SimpleNamespace(
        sample_id=sample_id,
        problem_id=problem_id,
        split=split,
        source_text="int main() { return 0; }",
        source_path="source/1/1001.txt",
    )


def make_result(written=2, registered=2):
    return SimpleNamespace(
        written_count=written,
        registered_count=registered,
    )


def test_runner_initialization():
    orchestrator = Mock()

    runner = VariantGenerationRunner(
        orchestrator=orchestrator,
        master_seed=42,
    )

    assert runner.master_seed == 42
    assert runner.orchestrator is orchestrator


def test_runner_rejects_non_integer_seed():
    with pytest.raises(ValueError, match="integer"):
        VariantGenerationRunner(
            orchestrator=Mock(),
            master_seed="42",
        )


def test_derive_sample_seed_is_deterministic():
    runner = VariantGenerationRunner(
        orchestrator=Mock(),
        master_seed=42,
    )

    seed_a = runner.derive_sample_seed("sample001")
    seed_b = runner.derive_sample_seed("sample001")

    assert seed_a == seed_b
    assert 0 <= seed_a <= 0xFFFFFFFF


def test_different_samples_have_different_derived_seeds():
    runner = VariantGenerationRunner(
        orchestrator=Mock(),
        master_seed=42,
    )

    assert runner.derive_sample_seed("sample001") != (
        runner.derive_sample_seed("sample002")
    )


def test_different_master_seeds_produce_different_seeds():
    runner_a = VariantGenerationRunner(
        orchestrator=Mock(),
        master_seed=42,
    )
    runner_b = VariantGenerationRunner(
        orchestrator=Mock(),
        master_seed=43,
    )

    assert runner_a.derive_sample_seed("sample001") != (
        runner_b.derive_sample_seed("sample001")
    )


def test_run_empty_samples():
    runner = VariantGenerationRunner(
        orchestrator=Mock(),
        master_seed=42,
    )

    result = runner.run([])

    assert result.samples_processed == 0
    assert result.samples_succeeded == 0
    assert result.samples_failed == 0
    assert result.success_rate == 0.0
    assert result.status == "COMPLETED"


def test_run_single_sample_success():
    orchestrator = Mock()
    orchestrator.process_sample.return_value = make_result(
        written=2,
        registered=2,
    )

    runner = VariantGenerationRunner(
        orchestrator=orchestrator,
        master_seed=42,
    )

    sample = make_sample()
    result = runner.run([sample])

    assert result.samples_processed == 1
    assert result.samples_succeeded == 1
    assert result.samples_failed == 0
    assert result.variants_written == 2
    assert result.variants_registered == 2
    assert result.success_rate == 1.0
    assert result.status == "COMPLETED"

    orchestrator.process_sample.assert_called_once_with(
        sample_id=sample.sample_id,
        problem_id=sample.problem_id,
        split=sample.split,
        original_source=sample.source_text,
        original_source_path=sample.source_path,
        seed=runner.derive_sample_seed(sample.sample_id),
    )


def test_runner_isolates_sample_failure():
    orchestrator = Mock()
    orchestrator.process_sample.side_effect = [
        RuntimeError("sample failure"),
        make_result(written=1, registered=1),
    ]

    runner = VariantGenerationRunner(
        orchestrator=orchestrator,
        master_seed=42,
    )

    result = runner.run(
        [
            make_sample("sample001"),
            make_sample("sample002"),
        ]
    )

    assert result.samples_processed == 2
    assert result.samples_succeeded == 1
    assert result.samples_failed == 1
    assert result.variants_written == 1
    assert result.variants_registered == 1
    assert result.status == "PARTIAL"

    assert len(result.errors) == 1
    assert result.errors[0].sample_id == "sample001"
    assert result.errors[0].error_type == "RuntimeError"
    assert result.errors[0].message == "sample failure"


def test_runner_all_samples_failed():
    orchestrator = Mock()
    orchestrator.process_sample.side_effect = RuntimeError(
        "failure"
    )

    runner = VariantGenerationRunner(
        orchestrator=orchestrator,
        master_seed=42,
    )

    result = runner.run(
        [
            make_sample("sample001"),
            make_sample("sample002"),
        ]
    )

    assert result.samples_processed == 2
    assert result.samples_succeeded == 0
    assert result.samples_failed == 2
    assert result.status == "FAILED"
    assert len(result.errors) == 2


def test_runner_preserves_partial_variant_persistence():
    orchestrator = Mock()
    orchestrator.process_sample.return_value = make_result(
        written=2,
        registered=1,
    )

    runner = VariantGenerationRunner(
        orchestrator=orchestrator,
        master_seed=42,
    )

    result = runner.run([make_sample()])

    assert result.samples_succeeded == 1
    assert result.variants_written == 2
    assert result.variants_registered == 1
