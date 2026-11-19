
from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.transformations.variant_generator import (
    VariantGenerationResult,
)


REPORT_VERSION = "1.0"


@dataclass
class SampleGenerationReport:
    original_sample_id: str
    split: str | None
    status: str
    target_variants: int
    accepted_variants: int
    attempts_total: int
    attempts_rejected: int
    accepted_transformations: dict[str, int] = field(
        default_factory=dict
    )
    rejection_reasons: dict[str, int] = field(
        default_factory=dict
    )


@dataclass
class VariantGenerationReport:
    dataset: str
    quota_target: int
    originals_processed: int = 0
    originals_completed: int = 0
    originals_partial: int = 0
    originals_failed: int = 0
    variants_accepted: int = 0
    attempts_total: int = 0
    attempts_rejected: int = 0
    transformations: Counter = field(default_factory=Counter)
    attempted_transformations: Counter = field(
        default_factory=Counter
    )
    rejection_reasons: Counter = field(default_factory=Counter)
    split_distribution: Counter = field(default_factory=Counter)
    samples: list[SampleGenerationReport] = field(
        default_factory=list
    )

    @property
    def quota_rate(self) -> float:
        if self.originals_processed == 0:
            return 0.0

        return self.originals_completed / self.originals_processed

    def add_result(
        self,
        result: VariantGenerationResult,
        split: str | None = None,
    ) -> None:
        self.originals_processed += 1

        if result.status == "COMPLETED":
            self.originals_completed += 1
        elif result.status == "PARTIAL":
            self.originals_partial += 1
        else:
            self.originals_failed += 1

        accepted = result.accepted_count
        rejected = result.rejected_count
        attempts = len(result.attempts)

        self.variants_accepted += accepted
        self.attempts_total += attempts
        self.attempts_rejected += rejected

        accepted_transformations: Counter = Counter()
        sample_rejection_reasons: Counter = Counter()
        sample_attempted_transformations: Counter = Counter()

        for variant in result.accepted_variants:
            self.transformations[
                variant.transformation_type
            ] += 1

            accepted_transformations[
                variant.transformation_type
            ] += 1

        for attempt in result.attempts:
            sample_attempted_transformations[
                attempt.transformation_type
            ] += 1

            self.attempted_transformations[
                attempt.transformation_type
            ] += 1

            if not attempt.accepted:
                reason = attempt.rejection_reason or "UNKNOWN"
                self.rejection_reasons[reason] += 1
                sample_rejection_reasons[reason] += 1

        if split is not None:
            self.split_distribution[split] += accepted

        self.samples.append(
            SampleGenerationReport(
                original_sample_id=result.original_sample_id,
                split=split,
                status=result.status,
                target_variants=result.target_variants,
                accepted_variants=accepted,
                attempts_total=attempts,
                attempts_rejected=rejected,
                accepted_transformations=dict(
                    accepted_transformations
                ),
                rejection_reasons=dict(
                    sample_rejection_reasons
                ),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": REPORT_VERSION,
            "dataset": self.dataset,
            "summary": {
                "originals_processed": self.originals_processed,
                "originals_completed": self.originals_completed,
                "originals_partial": self.originals_partial,
                "originals_failed": self.originals_failed,
                "variants_accepted": self.variants_accepted,
                "attempts_total": self.attempts_total,
                "attempts_rejected": self.attempts_rejected,
                "quota_target": self.quota_target,
                "quota_rate": self.quota_rate,
            },
            "transformations": dict(
                sorted(self.transformations.items())
            ),
            "attempted_transformations": dict(
                sorted(self.attempted_transformations.items())
            ),
            "rejection_reasons": dict(
                sorted(self.rejection_reasons.items())
            ),
            "split_distribution": dict(
                sorted(self.split_distribution.items())
            ),
            "samples": [
                {
                    "original_sample_id": sample.original_sample_id,
                    "split": sample.split,
                    "status": sample.status,
                    "target_variants": sample.target_variants,
                    "accepted_variants": sample.accepted_variants,
                    "attempts_total": sample.attempts_total,
                    "attempts_rejected": sample.attempts_rejected,
                    "accepted_transformations": (
                        sample.accepted_transformations
                    ),
                    "rejection_reasons": (
                        sample.rejection_reasons
                    ),
                }
                for sample in self.samples
            ],
        }


class VariantGenerationReportExporter:
    """Export variant generation reports as JSON."""

    @staticmethod
    def export_json(
        report: VariantGenerationReport,
        output_path: Path | str,
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_path.parent,
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                json.dump(
                    report.to_dict(),
                    temp_file,
                    indent=2,
                    ensure_ascii=False,
                )
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, output_path)
            temp_path = None

        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

        return output_path
