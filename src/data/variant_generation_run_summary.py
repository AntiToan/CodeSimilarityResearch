
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class VariantGenerationRunSummary:
    dataset: str
    split: str
    master_seed: int
    status: str

    samples_processed: int
    samples_succeeded: int
    samples_failed: int

    variants_written: int
    variants_registered: int

    success_rate: float

    errors: list[dict[str, Any]]
    started_at: str
    finished_at: str

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["error_count"] = self.error_count
        return result


class VariantGenerationRunSummaryBuilder:
    @staticmethod
    def build(
        batch_result: Any,
        *,
        dataset: str = "poj104",
        split: str = "train",
        started_at: str | None = None,
        finished_at: str | None = None,
    ) -> VariantGenerationRunSummary:
        start_time = started_at or datetime.now(
            timezone.utc
        ).isoformat()

        end_time = finished_at or datetime.now(
            timezone.utc
        ).isoformat()

        errors = [
            {
                "sample_id": error.sample_id,
                "error_type": error.error_type,
                "message": error.message,
            }
            for error in batch_result.errors
        ]

        return VariantGenerationRunSummary(
            dataset=dataset,
            split=split,
            master_seed=batch_result.master_seed,
            status=batch_result.status,
            samples_processed=batch_result.samples_processed,
            samples_succeeded=batch_result.samples_succeeded,
            samples_failed=batch_result.samples_failed,
            variants_written=batch_result.variants_written,
            variants_registered=batch_result.variants_registered,
            success_rate=batch_result.success_rate,
            errors=errors,
            started_at=start_time,
            finished_at=end_time,
        )


class VariantGenerationRunSummaryExporter:
    @staticmethod
    def export_json(
        summary: VariantGenerationRunSummary,
        output_path: str | Path,
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = output_path.with_suffix(
            output_path.suffix + ".tmp"
        )

        try:
            with temporary_path.open(
                "w", encoding="utf-8"
            ) as file:
                json.dump(
                    summary.to_dict(),
                    file,
                    indent=2,
                    ensure_ascii=False,
                )
                file.write("\n")

            temporary_path.replace(output_path)

        finally:
            if temporary_path.exists():
                temporary_path.unlink()

        return output_path
