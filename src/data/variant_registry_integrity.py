
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.data.variant_registry import (
    VariantRegistry,
    VariantRegistrySchemaError,
)


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str
    variant_id: str | None = None


@dataclass
class VariantRegistryIntegrityReport:
    registry_path: str
    total_records: int = 0
    valid_records: int = 0
    issues: list[IntegrityIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"

    def add_issue(
        self,
        code: str,
        message: str,
        variant_id: str | None = None,
    ) -> None:
        self.issues.append(
            IntegrityIssue(
                code=code,
                message=message,
                variant_id=variant_id,
            )
        )


class VariantRegistryIntegrityValidator:
    """Read-only audit of variant registry and source files."""

    def __init__(self, registry: VariantRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _hash_file(path: Path) -> str | None:
        try:
            return VariantRegistry.compute_sha256(path)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _safe_path(path_value: str) -> Path | None:
        try:
            return Path(path_value).resolve()
        except (OSError, RuntimeError, ValueError):
            return None

    def validate(self) -> VariantRegistryIntegrityReport:
        report = VariantRegistryIntegrityReport(
            registry_path=str(self.registry.registry_path)
        )

        try:
            records = self.registry.read_all()
        except (OSError, VariantRegistrySchemaError) as exc:
            report.add_issue(
                "REGISTRY_READ_ERROR",
                str(exc),
            )
            return report

        report.total_records = len(records)

        variant_ids: set[str] = set()
        original_variant_indexes: set[tuple[str, int]] = set()
        variant_hashes: dict[str, str] = {}
        original_hashes: dict[str, str] = {}

        for row in records:
            variant_id = row.get("variant_id")
            original_id = row.get("original_sample_id")

            # R2: Unique variant IDs.
            if variant_id in variant_ids:
                report.add_issue(
                    "DUPLICATE_VARIANT_ID",
                    f"Duplicate variant_id: {variant_id}",
                    variant_id,
                )
            else:
                variant_ids.add(variant_id)

            # R3: ID and index consistency.
            try:
                variant_index = int(row.get("variant_index", ""))
            except (TypeError, ValueError):
                variant_index = -1

            expected_id = (
                f"{original_id}_v{variant_index:03d}"
                if variant_index > 0
                else None
            )

            if variant_id != expected_id:
                report.add_issue(
                    "VARIANT_ID_MISMATCH",
                    "variant_id does not match original ID/index.",
                    variant_id,
                )

            # R4: Unique index for each original.
            index_key = (original_id, variant_index)
            if index_key in original_variant_indexes:
                report.add_issue(
                    "DUPLICATE_VARIANT_INDEX",
                    f"Duplicate variant index {variant_index} "
                    f"for original {original_id}.",
                    variant_id,
                )
            else:
                original_variant_indexes.add(index_key)

            # R11, R12: Metadata constraints.
            if row.get("split") not in {"train", "validation", "test"}:
                report.add_issue(
                    "INVALID_SPLIT",
                    f"Invalid split: {row.get('split')}",
                    variant_id,
                )

            if row.get("validation_status") != "PASS":
                report.add_issue(
                    "INVALID_VALIDATION_STATUS",
                    "Registry record is not marked PASS.",
                    variant_id,
                )

            # R5, R6: Variant source exists and hash matches.
            variant_path = self._safe_path(row.get("source_path", ""))

            if variant_path is None or not variant_path.is_file():
                report.add_issue(
                    "VARIANT_SOURCE_MISSING",
                    "Variant source file is missing or invalid.",
                    variant_id,
                )
                actual_variant_hash = None
            else:
                actual_variant_hash = self._hash_file(variant_path)

                if actual_variant_hash is None:
                    report.add_issue(
                        "VARIANT_HASH_ERROR",
                        "Could not compute variant source hash.",
                        variant_id,
                    )
                elif actual_variant_hash != row.get("source_hash"):
                    report.add_issue(
                        "VARIANT_HASH_MISMATCH",
                        "Variant source hash does not match registry.",
                        variant_id,
                    )

            # R7: Original source exists.
            original_path = self._safe_path(
                row.get("original_source_path", "")
            )

            if original_path is None or not original_path.is_file():
                report.add_issue(
                    "ORIGINAL_SOURCE_MISSING",
                    "Original source file is missing or invalid.",
                    variant_id,
                )
                actual_original_hash = None
            else:
                actual_original_hash = self._hash_file(original_path)

                if actual_original_hash is None:
                    report.add_issue(
                        "ORIGINAL_HASH_ERROR",
                        "Could not compute original source hash.",
                        variant_id,
                    )

            # R8: Check problem folder consistency.
            if variant_path is not None and original_path is not None:
                variant_problem = variant_path.parent.name
                original_problem = original_path.parent.name
                registered_problem = row.get("problem_id")

                if (
                    variant_problem != original_problem
                    or variant_problem != registered_problem
                ):
                    report.add_issue(
                        "PROBLEM_PATH_MISMATCH",
                        (
                            f"Problem mismatch: variant={variant_problem}, "
                            f"original={original_problem}, "
                            f"registry={registered_problem}"
                        ),
                        variant_id,
                    )

            # R9: Variant must differ from original content.
            if (
                actual_variant_hash is not None
                and actual_original_hash is not None
                and actual_variant_hash == actual_original_hash
            ):
                report.add_issue(
                    "VARIANT_EQUALS_ORIGINAL",
                    "Variant source is byte-identical to original.",
                    variant_id,
                )

            # R10: Detect identical variant source hashes.
            if actual_variant_hash is not None:
                if actual_variant_hash in variant_hashes:
                    report.add_issue(
                        "DUPLICATE_VARIANT_CONTENT",
                        f"Same content as variant "
                        f"{variant_hashes[actual_variant_hash]}.",
                        variant_id,
                    )
                else:
                    variant_hashes[actual_variant_hash] = variant_id

            # Detect inconsistent original paths for the same original ID.
            if actual_original_hash is not None:
                previous_hash = original_hashes.get(original_id)

                if (
                    previous_hash is not None
                    and previous_hash != actual_original_hash
                ):
                    report.add_issue(
                        "ORIGINAL_CONTENT_INCONSISTENT",
                        "Same original_sample_id points to "
                        "different original contents.",
                        variant_id,
                    )
                else:
                    original_hashes[original_id] = actual_original_hash

        report.valid_records = (
            report.total_records
            if report.passed
            else max(
                0,
                report.total_records
                - len(
                    {
                        issue.variant_id
                        for issue in report.issues
                        if issue.variant_id is not None
                    }
                ),
            )
        )

        return report
