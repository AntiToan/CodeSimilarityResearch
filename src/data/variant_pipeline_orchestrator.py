from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.data.variant_registry import VariantRegistryRecord
from src.transformations.variant_generator import (
    GeneratedVariant,
    VariantGenerationResult,
)


@dataclass(frozen=True)
class VariantPersistenceResult:
    variant_id: str
    written: bool
    registered: bool
    source_path: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.written and self.registered


@dataclass
class VariantPipelineSampleResult:
    generation_result: VariantGenerationResult
    persistence_results: list[VariantPersistenceResult] = field(
        default_factory=list
    )

    @property
    def written_count(self) -> int:
        return sum(item.written for item in self.persistence_results)

    @property
    def registered_count(self) -> int:
        return sum(item.registered for item in self.persistence_results)

    @property
    def failed_count(self) -> int:
        return sum(not item.success for item in self.persistence_results)


class VariantPipelineOrchestrator:
    """Orchestrate generation, writing, and registry persistence."""

    def __init__(
        self,
        generator: Any,
        writer: Any,
        registry: Any,
        report: Any,
        validator_version: str,
    ) -> None:
        if not validator_version:
            raise ValueError("validator_version must be non-empty.")

        self.generator = generator
        self.writer = writer
        self.registry = registry
        self.report = report
        self.validator_version = validator_version

    def process_sample(
        self,
        *,
        sample_id: str,
        problem_id: str,
        split: str,
        original_source: str,
        original_source_path: str | Path,
        seed: int,
    ) -> VariantPipelineSampleResult:
        """Process one original sample."""

        generation_result = self.generator.generate(
            original_sample_id=sample_id,
            original_source=original_source,
            seed=seed,
        )

        sample_result = VariantPipelineSampleResult(
            generation_result=generation_result,
        )

        self.report.add_result(
            generation_result,
            split=split,
        )

        for variant in generation_result.accepted_variants:
            persistence_result = self._persist_variant(
                variant=variant,
                problem_id=problem_id,
                split=split,
                original_source_path=original_source_path,
            )

            sample_result.persistence_results.append(
                persistence_result
            )

        return sample_result

    def _persist_variant(
        self,
        *,
        variant: GeneratedVariant,
        problem_id: str,
        split: str,
        original_source_path: str | Path,
    ) -> VariantPersistenceResult:
        """Write one variant and register it."""

        source_path: Path | None = None
        written = False

        try:
            source_path = self.writer.write_variant(
                variant=variant,
                problem_id=problem_id,
            )

            source_path = Path(source_path).resolve()

            if not source_path.is_file():
                raise FileNotFoundError(
                    f"Variant file was not created: {source_path}"
                )

            written = True

            source_hash = self.registry.compute_sha256(
                source_path
            )

            record = VariantRegistryRecord(
                variant_id=variant.variant_id,
                original_sample_id=variant.original_sample_id,
                problem_id=problem_id,
                split=split,
                variant_index=variant.variant_index,
                transformation_type=variant.transformation_type,
                generation_seed=variant.generation_seed,
                validator_version=self.validator_version,
                validation_status="PASS",
                source_path=str(source_path),
                original_source_path=str(
                    Path(original_source_path).resolve()
                ),
                source_hash=source_hash,
                created_at=self.registry.utc_now_iso(),
            )

            self.registry.register(record)

            return VariantPersistenceResult(
                variant_id=variant.variant_id,
                written=True,
                registered=True,
                source_path=str(source_path),
            )

        except Exception as exc:
            return VariantPersistenceResult(
                variant_id=variant.variant_id,
                written=written,
                registered=False,
                source_path=(
                    str(source_path) if source_path is not None else None
                ),
                error=f"{type(exc).__name__}: {exc}",
            )