
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


VALID_SPLITS = {"train", "validation", "test"}


class VariantSourceLoaderError(Exception):
    """Base error for source loader."""


class SourceMetadataError(VariantSourceLoaderError):
    """Metadata or split data is invalid."""


class SourceFileLoadError(VariantSourceLoaderError):
    """Source file cannot be loaded."""


@dataclass(frozen=True)
class LoadedSample:
    sample_id: str
    problem_id: str
    filename: str
    language: str
    split: str
    source_path: Path
    source_text: str
    file_size_bytes: int


class VariantSourceLoader:
    """Load valid source samples and join them with split assignments."""

    REQUIRED_METADATA_COLUMNS = {
        "sample_id",
        "problem_id",
        "filename",
        "language",
        "source_path",
        "file_size_bytes",
        "status",
    }

    REQUIRED_SPLIT_COLUMNS = {
        "sample_id",
        "split",
    }

    def __init__(
        self,
        metadata_path: Path | str,
        splits_path: Path | str,
        source_root: Path | str,
    ) -> None:
        self.metadata_path = Path(metadata_path)
        self.splits_path = Path(splits_path)
        self.source_root = Path(source_root).resolve()

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        if not path.is_file():
            raise SourceMetadataError(
                f"CSV file not found: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                return list(csv.DictReader(file))
        except (OSError, UnicodeError, csv.Error) as exc:
            raise SourceMetadataError(
                f"Cannot read CSV file: {path}"
            ) from exc

    @staticmethod
    def _require_columns(
        rows: list[dict[str, str]],
        required: set[str],
        path: Path,
    ) -> None:
        if not rows:
            raise SourceMetadataError(
                f"CSV contains no records: {path}"
            )

        actual = set(rows[0].keys())
        missing = required - actual

        if missing:
            raise SourceMetadataError(
                f"Missing columns in {path}: {sorted(missing)}"
            )

    @staticmethod
    def _validate_unique_ids(
        rows: list[dict[str, str]],
        field: str,
        source_name: str,
    ) -> None:
        ids = [row[field] for row in rows]

        if len(ids) != len(set(ids)):
            raise SourceMetadataError(
                f"Duplicate {field} in {source_name}."
            )

    def _resolve_source_path(self, relative_path: str) -> Path:
        candidate = (self.source_root / relative_path).resolve()

        # Prevent paths from escaping the source root.
        if not candidate.is_relative_to(self.source_root):
            raise SourceFileLoadError(
                f"Source path escapes source root: {relative_path}"
            )

        return candidate

    def load(self) -> list[LoadedSample]:
        metadata_rows = self._read_csv(self.metadata_path)
        split_rows = self._read_csv(self.splits_path)

        self._require_columns(
            metadata_rows,
            self.REQUIRED_METADATA_COLUMNS,
            self.metadata_path,
        )
        self._require_columns(
            split_rows,
            self.REQUIRED_SPLIT_COLUMNS,
            self.splits_path,
        )

        self._validate_unique_ids(
            metadata_rows,
            "sample_id",
            "metadata",
        )
        self._validate_unique_ids(
            split_rows,
            "sample_id",
            "source splits",
        )

        # Only samples marked "success" are eligible for generation.
        valid_metadata = [
            row
            for row in metadata_rows
            if row["status"].strip().lower() == "success"
        ]

        metadata_by_id = {
            row["sample_id"]: row
            for row in valid_metadata
        }

        splits_by_id = {
            row["sample_id"]: row["split"].strip()
            for row in split_rows
        }

        missing_splits = (
            set(metadata_by_id) - set(splits_by_id)
        )
        if missing_splits:
            raise SourceMetadataError(
                f"{len(missing_splits)} valid samples "
                "have no split assignment."
            )

        extra_splits = (
            set(splits_by_id) - set(metadata_by_id)
        )
        if extra_splits:
            raise SourceMetadataError(
                f"{len(extra_splits)} split IDs have no "
                "successful metadata record."
            )

        loaded_samples: list[LoadedSample] = []

        for sample_id, row in metadata_by_id.items():
            split = splits_by_id[sample_id]

            if split not in VALID_SPLITS:
                raise SourceMetadataError(
                    f"Invalid split for {sample_id}: {split!r}"
                )

            source_path = self._resolve_source_path(
                row["source_path"]
            )

            if not source_path.is_file():
                raise SourceFileLoadError(
                    f"Source file not found: {source_path}"
                )

            try:
                source_text = source_path.read_text(
                    encoding="utf-8"
                )
            except (OSError, UnicodeError) as exc:
                raise SourceFileLoadError(
                    f"Cannot read source file: {source_path}"
                ) from exc

            try:
                file_size_bytes = int(row["file_size_bytes"])
            except (ValueError, TypeError) as exc:
                raise SourceMetadataError(
                    f"Invalid file size for {sample_id}"
                ) from exc

            if file_size_bytes < 0:
                raise SourceMetadataError(
                    f"Negative file size for {sample_id}"
                )

            loaded_samples.append(
                LoadedSample(
                    sample_id=sample_id,
                    problem_id=row["problem_id"],
                    filename=row["filename"],
                    language=row["language"],
                    split=split,
                    source_path=source_path,
                    source_text=source_text,
                    file_size_bytes=file_size_bytes,
                )
            )

        loaded_samples.sort(
            key=lambda sample: (
                sample.problem_id,
                sample.sample_id,
            )
        )

        return loaded_samples
