from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from pathlib import Path

from src.data.pair_models import PairRecord
from src.data.final_dataset_validation_models import (
    FinalDatasetValidationReport,
    FinalDatasetValidationStatus,
)
from src.safety.safe_persistence import (
    SafePersistence,
    CollisionMode,
    PersistenceResult,
)


PAIR_EXPORT_FIELDS = (
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
)


class FinalDatasetExporter:
    @staticmethod
    def serialize_pairs(
        pairs: Iterable[PairRecord],
    ) -> str:
        pair_list = tuple(pairs)

        if any(not isinstance(pair, PairRecord) for pair in pair_list):
            raise TypeError(
                "pairs must contain only PairRecord instances."
            )

        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(
            buffer,
            fieldnames=PAIR_EXPORT_FIELDS,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()

        for pair in pair_list:
            writer.writerow(
                {
                    "pair_id": pair.pair_id,
                    "sample_a_id": pair.sample_a_id,
                    "sample_b_id": pair.sample_b_id,
                    "label": pair.label,
                    "pair_type": pair.pair_type.value,
                    "split": pair.split.value,
                    "source_a_id": pair.source_a_id,
                    "source_b_id": pair.source_b_id,
                    "problem_a_id": pair.problem_a_id,
                    "problem_b_id": pair.problem_b_id,
                    "generation_method": pair.generation_method,
                    "created_seed": (
                        ""
                        if pair.created_seed is None
                        else pair.created_seed
                    ),
                }
            )

        return buffer.getvalue()

    @staticmethod
    def ensure_export_allowed(
        report: FinalDatasetValidationReport,
        *,
        allow_warnings: bool = False,
    ) -> None:
        if not isinstance(report, FinalDatasetValidationReport):
            raise TypeError(
                "report must be a FinalDatasetValidationReport."
            )

        if type(allow_warnings) is not bool:
            raise TypeError("allow_warnings must be a boolean.")

        if report.status == FinalDatasetValidationStatus.FAIL:
            raise ValueError(
                "Export blocked: final dataset validation failed."
            )

        if (
            report.status == FinalDatasetValidationStatus.WARNING
            and not allow_warnings
        ):
            raise ValueError(
                "Export blocked: final dataset validation has warnings."
            )

    @staticmethod
    def export_csv(
        pairs: Iterable[PairRecord],
        validation_report: FinalDatasetValidationReport,
        *,
        destination: str | Path,
        authorized_root: str | Path,
        collision_mode: CollisionMode,
        allow_warnings: bool = False,
    ) -> PersistenceResult:
        FinalDatasetExporter.ensure_export_allowed(
            validation_report,
            allow_warnings=allow_warnings,
        )

        pair_list = tuple(pairs)
        csv_payload = (
            FinalDatasetExporter.serialize_pairs(pair_list)
            .encode("utf-8")
        )

        expected_count = len(pair_list)

        def validate_csv_artifact(artifact_path: Path) -> bool:
            try:
                artifact_bytes = artifact_path.read_bytes()

                if artifact_bytes != csv_payload:
                    return False

                csv_text = artifact_bytes.decode("utf-8")
                reader = csv.DictReader(
                    io.StringIO(csv_text, newline="")
                )

                if tuple(reader.fieldnames or ()) != PAIR_EXPORT_FIELDS:
                    return False

                rows = list(reader)

                if len(rows) != expected_count:
                    return False

                return all(
                    set(row.keys()) == set(PAIR_EXPORT_FIELDS)
                    for row in rows
                )
            except (OSError, UnicodeDecodeError, csv.Error):
                return False

        return SafePersistence.persist_bytes(
            destination=Path(destination),
            payload=csv_payload,
            authorized_root=Path(authorized_root),
            collision_mode=collision_mode,
            validator=validate_csv_artifact,
            verification_required=True,
        )
