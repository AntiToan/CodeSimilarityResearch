from __future__ import annotations
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Iterable

class DuplicateDetectionError(RuntimeError):
    """Raised when duplicate detection cannot be completed safely."""

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file using streaming reads."""
    sha256 = hashlib.sha256()

    try:
        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)
    except OSError as exc:
        raise DuplicateDetectionError(
            f"Cannot read source file: {file_path}"
        ) from exc 

    return sha256.hexdigest()

def detect_exact_duplicates(samples: Iterable[dict], source_root: Path) -> tuple[dict[str, str], list[dict]]:
    """Detect exact duplicates using SHA-256.

    Returns:
        sample_hashes:
            Mapping sample_id -> SHA-256.

        duplicate_groups:
            List of groups containing at least two samples.
            Each group contains a deterministic group ID, hash,
            and sorted sample IDs.
    """
    sample_hashes: dict[str, str] = {}
    hash_to_samples: dict[str, list[str]] = defaultdict(list)

    for sample in samples:
        sample_id = str(sample["sample_id"])
        relative_path = Path(str(sample["source_path"]))
        file_path = (source_root / relative_path).resolve()

        if not file_path.is_relative_to(source_root.resolve()):
            raise DuplicateDetectionError(
                f"Source path escapes source root: {sample_id}"
            )

        if not file_path.is_file():
            raise DuplicateDetectionError(
                f"Source file does not exist: {sample_id} ({file_path})"
            )

        content_hash = calculate_sha256(file_path)
        sample_hashes[sample_id] = content_hash
        hash_to_samples[content_hash].append(sample_id)

    duplicate_group: list[dict] = []

    for content_hash, sample_ids in sorted(hash_to_samples.items()):
        if len(sample_ids) < 2:
            continue

        sorted_ids = sorted(sample_ids)
        group_id = f"dup_{content_hash[:16]}"

        duplicate_group.append(
            {
                "duplicate_group_id": group_id,
                "content_sha256": content_hash,
                "sample_count": len(sorted_ids),
                "sample_ids": sorted_ids,
            }
        )

    return sample_hashes, duplicate_group