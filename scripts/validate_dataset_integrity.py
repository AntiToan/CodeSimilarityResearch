import csv
from pathlib import Path

# PATH CONFIGURATION
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "poj104" / "ProgramData"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed" / "poj104"
PROCESSED_DIR = PROCESSED_ROOT / "source"
METADATA_CSV = (
    PROCESSED_ROOT / "metadata" / "samples.csv"
)
EXPECTED_SAMPLES = 52_000

# HELPERS
def collect_txt_files(directory: Path) -> set[str]:
    """Collect relative paths of all .txt files."""
    return {
        file.relative_to(directory).as_posix()
        for file in directory.rglob("*.txt")
        if file.is_file()
    }

def load_metadata(csv_path: Path) -> list[dict]:
    """Load metadata CSV records."""
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

# VALIDATION
def validate_dataset_integrity() -> dict:
    errors = []

    # 1. Check directory existence
    for directory in (RAW_DIR, PROCESSED_DIR):
        if not directory.exists():
            errors.append(f"Missing directory: {directory}")
        elif not directory.is_dir():
            errors.append(f"Not a directory: {directory}")

    if not METADATA_CSV.is_file():
        errors.append(f"Missing metadata CSV: {METADATA_CSV}")

    if errors:
        return {
            "status": "FAIL",
            "errors": errors,
        }

    # 2. Collect dataset files
    raw_files = collect_txt_files(RAW_DIR)
    processed_files = collect_txt_files(PROCESSED_DIR)
    metadata_rows = load_metadata(METADATA_CSV)

    # 3. Extract paths from metadata
    metadata_raw_files = set()
    metadata_processed_files = set()
    sample_ids = []

    for row in metadata_rows:
        sample_ids.append(row["sample_id"])

        # original_path: ProgramData/<problem>/<file>
        raw_relative_path = Path(row["original_path"])

        if raw_relative_path.parts[0] == "ProgramData":
            raw_relative_path = Path(*raw_relative_path.parts[1:])

        metadata_raw_files.add(raw_relative_path.as_posix())

        # source_path: source/<problem>/<file>
        processed_relative_path = Path(row["source_path"])

        if processed_relative_path.parts[0] == "source":
            processed_relative_path = Path(
                *processed_relative_path.parts[1:]
            )

        metadata_processed_files.add(
            processed_relative_path.as_posix()
        )

    # 4. Compare Raw vs Processed
    missing_processed = raw_files - processed_files
    orphan_processed = processed_files - raw_files

    # 5. Compare Raw vs Metadata
    missing_metadata_raw = raw_files - metadata_raw_files
    orphan_metadata_raw = metadata_raw_files - raw_files

    # 6. Compare Processed vs Metadata
    missing_metadata_processed = (
        processed_files - metadata_processed_files
    )

    orphan_metadata_processed = (
        metadata_processed_files - processed_files
    )

    # 7. Check duplicate sample IDs
    duplicate_sample_ids = (
        len(sample_ids) - len(set(sample_ids))
    )

    # 8. Check sample counts
    count_checks = {
        "raw_count": len(raw_files),
        "processed_count": len(processed_files),
        "metadata_count": len(metadata_rows),
    }

    for name, count in count_checks.items():
        if count != EXPECTED_SAMPLES:
            errors.append(
                f"{name}: expected {EXPECTED_SAMPLES}, got {count}"
            )

    # 9. Check consistency
    integrity_checks = {
        "missing_processed": missing_processed,
        "orphan_processed": orphan_processed,
        "missing_metadata_raw": missing_metadata_raw,
        "orphan_metadata_raw": orphan_metadata_raw,
        "missing_metadata_processed": missing_metadata_processed,
        "orphan_metadata_processed": orphan_metadata_processed,
    }

    for name, files in integrity_checks.items():
        if files:
            errors.append(
                f"{name}: found {len(files)} inconsistent files"
            )

    if duplicate_sample_ids > 0:
        errors.append(
            f"Duplicate sample IDs: {duplicate_sample_ids}"
        )

    # 10. Report
    report = {
        "status": "PASS" if not errors else "FAIL",
        "counts": count_checks,
        "unique_sample_ids": len(set(sample_ids)),
        "duplicate_sample_ids": duplicate_sample_ids,
        "integrity": {
            name: len(files)
            for name, files in integrity_checks.items()
        },
        "errors": errors,
    }

    return report

# ENTRY POINT
def main():
    report = validate_dataset_integrity()

    print("=" * 60)
    print("DATASET INTEGRITY VALIDATION")
    print("=" * 60)

    if "counts" in report:
        print("\nDataset counts:")

        for name, count in report["counts"].items():
            print(f"  {name}: {count:,}")

        print(f"  unique_sample_ids: {report['unique_sample_ids']:,}")
        print(f"  duplicate_sample_ids: {report['duplicate_sample_ids']}")

        print("\nIntegrity checks:")

        for name, count in report["integrity"].items():
            print(f"  {name}: {count}")

    print("\nStatus:", report["status"])

    if report["errors"]:
        print("\nErrors:")

        for error in report["errors"]:
            print(f"  - {error}")

    print("=" * 60)

    if report["status"] == "PASS":
        print("DATASET INTEGRITY VALIDATION PASSED")
    else:
        print("DATASET INTEGRITY VALIDATION FAILED")


if __name__ == "__main__":
    main()