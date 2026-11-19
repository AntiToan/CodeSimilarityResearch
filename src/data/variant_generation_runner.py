
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class SampleRunError:
    sample_id: str
    error_type: str
    message: str


@dataclass
class VariantGenerationBatchResult:
    master_seed: int
    samples_processed: int = 0
    samples_succeeded: int = 0
    samples_failed: int = 0
    variants_written: int = 0
    variants_registered: int = 0
    sample_results: list[Any] = field(default_factory=list)
    errors: list[SampleRunError] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.samples_processed == 0:
            return 0.0

        return self.samples_succeeded / self.samples_processed

    @property
    def status(self) -> str:
        if self.samples_failed == 0:
            return "COMPLETED"

        if self.samples_succeeded == 0:
            return "FAILED"

        return "PARTIAL"


class VariantGenerationRunner:
    """Run variant generation over a collection of loaded samples."""

    def __init__(
        self,
        orchestrator: Any,
        master_seed: int = 42,
    ) -> None:
        if not isinstance(master_seed, int):
            raise ValueError("master_seed must be an integer.")

        self.orchestrator = orchestrator
        self.master_seed = master_seed

    def derive_sample_seed(self, sample_id: str) -> int:
        """Derive a stable deterministic seed for a sample."""

        payload = f"{self.master_seed}:{sample_id}".encode("utf-8")
        digest = hashlib.sha256(payload).digest()

        # Use the first 4 bytes as an unsigned 32-bit seed.
        return int.from_bytes(digest[:4], byteorder="big")

    def run(
        self,
        samples: Iterable[Any],
    ) -> VariantGenerationBatchResult:
        """Process samples sequentially and isolate per-sample errors."""

        batch_result = VariantGenerationBatchResult(
            master_seed=self.master_seed,
        )

        for sample in samples:
            batch_result.samples_processed += 1

            try:
                seed = self.derive_sample_seed(sample.sample_id)

                result = self.orchestrator.process_sample(
                    sample_id=sample.sample_id,
                    problem_id=sample.problem_id,
                    split=sample.split,
                    original_source=sample.source_text,
                    original_source_path=sample.source_path,
                    seed=seed,
                )

                batch_result.sample_results.append(result)
                batch_result.samples_succeeded += 1

                batch_result.variants_written += result.written_count
                batch_result.variants_registered += result.registered_count

            except Exception as exc:
                batch_result.samples_failed += 1
                batch_result.errors.append(
                    SampleRunError(
                        sample_id=sample.sample_id,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        return batch_result
