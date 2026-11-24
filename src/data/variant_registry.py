from __future__ import annotations
import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from src.safety.safe_persistence import (
    SafePersistence,
    CollisionMode,
    PersistenceStatus,
)

VARIANT_REGISTRY_COLUMNS = [
    "variant_id",
    "original_sample_id",
    "problem_id",
    "split",
    "variant_index",
    "transformation_type",
    "generation_seed",
    "validator_version",
    "validation_status",
    "source_path",
    "original_source_path",
    "source_hash",
    "created_at",
]

VALID_SPLITS = {"train", "validation", "test"}


class VariantRegistryError(Exception):
    """Base exception for variant registry errors."""

class VariantRegistrySchemaError(VariantRegistryError):
    """Invalid registry schema or record."""

class DuplicateVariantError(VariantRegistryError):
    """Variant ID already exists in registry."""

@dataclass(frozen=True)
class VariantRegistryRecord:
    variant_id: str
    original_sample_id: str
    problem_id: str
    split: str
    variant_index: int
    transformation_type: str
    generation_seed: int
    validator_version: str
    validation_status: str
    source_path: str
    original_source_path: str
    source_hash: str
    created_at: str


class VariantRegistry:
    """CSV registry for accepted variants."""

    def __init__(self, registry_path: Path | str) -> None:
        self.registry_path = Path(registry_path)

    @staticmethod
    def compute_sha256(source_path: Path | str) -> str:
        path = Path(source_path)

        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def utc_now_iso() -> str:
        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _validate_record(record: VariantRegistryRecord) -> None:
        if record.validation_status != "PASS":
            raise VariantRegistrySchemaError(
                "Only PASS variants may be registered."
            )

        if record.split not in VALID_SPLITS:
            raise VariantRegistrySchemaError(
                f"Invalid split: {record.split!r}"
            )

        if record.variant_index <= 0:
            raise VariantRegistrySchemaError(
                "variant_index must be positive."
            )

        if record.generation_seed < 0:
            raise VariantRegistrySchemaError(
                "generation_seed must be non-negative."
            )

        required_strings = [
            record.variant_id,
            record.original_sample_id,
            record.problem_id,
            record.transformation_type,
            record.validator_version,
            record.source_path,
            record.original_source_path,
            record.source_hash,
            record.created_at,
        ]

        if any(
            not isinstance(value, str) or not value.strip()
            for value in required_strings
        ):
            raise VariantRegistrySchemaError(
                "Required string fields must be non-empty."
            )

        if len(record.source_hash) != 64:
            raise VariantRegistrySchemaError(
                "source_hash must be a SHA-256 hex digest."
            )

        try:
            int(record.source_hash, 16)
        except ValueError as exc:
            raise VariantRegistrySchemaError(
                "source_hash must be hexadecimal."
            ) from exc

        expected_variant_id = (
            f"{record.original_sample_id}"
            f"_v{record.variant_index:03d}"
        )

        if record.variant_id != expected_variant_id:
            raise VariantRegistrySchemaError(
                "variant_id does not match original_sample_id "
                "and variant_index."
            )

        try:
            datetime.fromisoformat(
                record.created_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise VariantRegistrySchemaError(
                "created_at must be a valid ISO-8601 timestamp."
            ) from exc

    def _read_records(self) -> list[dict[str, str]]:
        if not self.registry_path.exists():
            return []

        with self.registry_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != VARIANT_REGISTRY_COLUMNS:
                raise VariantRegistrySchemaError(
                    "Existing registry schema does not match expected "
                    "columns."
                )

            records = list(reader)

        for row in records:
            if set(row) != set(VARIANT_REGISTRY_COLUMNS):
                raise VariantRegistrySchemaError(
                    "Registry contains invalid row schema."
                )

        return records

    def _atomic_write(
        self,
        records: list[dict[str, str]],
    ) -> None:
        self.registry_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        csv_buffer = io.StringIO(newline="")

        writer = csv.DictWriter(
            csv_buffer,
            fieldnames=VARIANT_REGISTRY_COLUMNS,
        )
        writer.writeheader()
        writer.writerows(records)

        payload = csv_buffer.getvalue().encode("utf-8")
        csv_buffer.close()

        persistence_result = SafePersistence.persist_bytes(
            destination=self.registry_path.absolute(),
            payload=payload,
            authorized_root=self.registry_path.parent.resolve(),
            collision_mode=CollisionMode.REPLACE,
        )

        if persistence_result.status not in (
            PersistenceStatus.COMMITTED,
            PersistenceStatus.COMMITTED_WITH_WARNINGS,
        ):
            raise OSError(
                persistence_result.primary_error
                or (
                    "Variant registry persistence failed: "
                    f"{persistence_result.status.value}"
                )
            )

    def register(
        self,
        record: VariantRegistryRecord,
    ) -> None:
        self._validate_record(record)

        source_file = Path(record.source_path)

        if not source_file.is_file():
            raise VariantRegistrySchemaError(
                f"Variant source file does not exist: {source_file}"
            )

        actual_hash = self.compute_sha256(source_file)

        if actual_hash != record.source_hash:
            raise VariantRegistrySchemaError(
                "source_hash does not match variant source file."
            )

        records = self._read_records()

        if any(
            row["variant_id"] == record.variant_id
            for row in records
        ):
            raise DuplicateVariantError(
                f"Variant already registered: {record.variant_id}"
            )

        new_record = {
            column: str(getattr(record, column))
            for column in VARIANT_REGISTRY_COLUMNS
        }

        records.append(new_record)
        self._atomic_write(records)

    def read_all(self) -> list[dict[str, str]]:
        return self._read_records()

    def count(self) -> int:
        return len(self._read_records())
