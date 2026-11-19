
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.duplicate_detector import detect_exact_duplicates
from src.data.pair_generation_config import PairGenerationConfig
from src.data.source_splitter import assign_source_splits


def load_samples(metadata_path: Path) -> list[dict]:
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        samples = list(reader)

    if not samples:
        raise RuntimeError("Metadata contains no samples.")

    required_columns = {
        "sample_id",
        "problem_id",
        "source_path",
        "status",
    }

    actual_columns = set(samples[0].keys())
    missing = required_columns - actual_columns

    if missing:
        raise RuntimeError(
            f"Metadata missing required columns: {sorted(missing)}"
        )

    valid_samples = [
        sample
        for sample in samples
        if sample["status"].strip().lower() == "success"
    ]

    if len(valid_samples) != len(samples):
        print(
            f"WARNING: Excluded {len(samples) - len(valid_samples)} "
            "samples with non-success status."
        )

    return valid_samples


def validate_assignments(
    samples: list[dict],
    duplicate_groups: list[dict],
    assignments: dict[str, str],
) -> None:
    sample_ids = {str(sample["sample_id"]) for sample in samples}

    if sample_ids != set(assignments):
        raise RuntimeError(
            "Split coverage mismatch: assigned IDs differ from input IDs."
        )

    allowed_splits = {"train", "validation", "test"}

    if not set(assignments.values()).issubset(allowed_splits):
        raise RuntimeError("Invalid split label detected.")

    for group in duplicate_groups:
        assigned_splits = {
            assignments[sample_id]
            for sample_id in group["sample_ids"]
        }

        if len(assigned_splits) != 1:
            raise RuntimeError(
                f"Duplicate leakage detected in group "
                f"{group['duplicate_group_id']}"
            )


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = PairGenerationConfig(ROOT / "config" / "pair_generation_config.json")

    metadata_path = config.resolve_path(
        "dataset",
        "source_metadata_file",
    )

    source_root = config.resolve_path("dataset", "processed_dir")

    samples = load_samples(metadata_path)

    print(f"Loaded valid samples: {len(samples):,}")

    sample_hashes, duplicate_groups = detect_exact_duplicates(
        samples=samples,
        source_root=source_root,
    )

    print(f"Exact duplicate groups: {len(duplicate_groups):,}")

    assignments, report = assign_source_splits(
        samples=samples,
        duplicate_groups=duplicate_groups,
        ratios=config.get("split", "ratios"),
        seed=config.seed,
    )

    validate_assignments(
        samples=samples,
        duplicate_groups=duplicate_groups,
        assignments=assignments,
    )

    metadata_dir = metadata_path.parent
    duplicate_groups_path = metadata_dir / "duplicate_groups.csv"
    source_splits_path = metadata_dir / "source_splits.csv"

    duplicate_rows = [
        {
            "duplicate_group_id": group["duplicate_group_id"],
            "content_sha256": group["content_sha256"],
            "sample_count": group["sample_count"],
            "sample_ids": json.dumps(
                group["sample_ids"],
                ensure_ascii=False,
            ),
        }
        for group in duplicate_groups
    ]

    write_csv(
        duplicate_groups_path,
        duplicate_rows,
        [
            "duplicate_group_id",
            "content_sha256",
            "sample_count",
            "sample_ids",
        ],
    )

    sample_to_duplicate_group = {}

    for group in duplicate_groups:
        for sample_id in group["sample_ids"]:
            sample_to_duplicate_group[sample_id] = (
                group["duplicate_group_id"]
            )

    split_rows = []

    for sample in sorted(samples, key=lambda item: item["sample_id"]):
        sample_id = str(sample["sample_id"])

        matching_group = sample_to_duplicate_group.get(sample_id, "")

        split_rows.append(
            {
                "sample_id": sample_id,
                "problem_id": sample["problem_id"],
                "split": assignments[sample_id],
                "seed": config.seed,
                "method": "group_aware_stratified_greedy",
                "duplicate_group_id": matching_group,
                "split_version": config.get("config_version"),
                "content_sha256": sample_hashes[sample_id],
            }
        )

    write_csv(
        source_splits_path,
        split_rows,
        [
            "sample_id",
            "problem_id",
            "split",
            "seed",
            "method",
            "duplicate_group_id",
            "split_version",
            "content_sha256",
        ],
    )

    report["status"] = "completed"
    report["metadata_path"] = str(metadata_path)
    report["source_root"] = str(source_root)
    report["duplicate_groups_path"] = str(duplicate_groups_path)
    report["source_splits_path"] = str(source_splits_path)

    reports_dir = config.resolve_path("output", "reports_dir")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "split_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nSource split completed successfully.")
    print(f"Source splits: {source_splits_path}")
    print(f"Duplicate groups: {duplicate_groups_path}")
    print(f"Report: {report_path}")
    print("\nSplit counts:")

    for split, count in report["split_counts"].items():
        ratio = report["split_actual_ratios"][split]
        print(f"  {split:10s}: {count:6,} ({ratio:.2%})")


if __name__ == "__main__":
    main()
