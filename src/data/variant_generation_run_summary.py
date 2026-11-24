from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from src.safety.safe_persistence import (
    SafePersistence,
    CollisionMode,
    PersistenceStatus,
)

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

        payload = (
            json.dumps(
                summary.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")

        persistence_result = SafePersistence.persist_bytes(
            destination=output_path.absolute(),
            payload=payload,
            authorized_root=output_path.parent.resolve(),
            collision_mode=CollisionMode.REPLACE,
        )

        if persistence_result.status not in (
            PersistenceStatus.COMMITTED,
            PersistenceStatus.COMMITTED_WITH_WARNINGS,
        ):
            raise OSError(
                persistence_result.primary_error
                or (
                    "Run summary persistence failed: "
                    f"{persistence_result.status.value}"
                )
            )

        return output_path