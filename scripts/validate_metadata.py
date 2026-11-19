import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "metadata"
    / "samples.csv"
)

PROCESSED_ROOT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
)

RAW_ROOT = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "poj104"
)


EXPECTED_TOTAL = 52_000
EXPECTED_PROBLEMS = 104
EXPECTED_PER_PROBLEM = 500

REQUIRED_FIELDS = [
    "sample_id",
    "problem_id",
    "filename",
    "language",
    "source_path",
    "original_path",
    "file_size_bytes",
    "status",
]


def validate_metadata():
    errors = []

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_FILE}"
        )

    with METADATA_FILE.open(
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        # Validate header
        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if field not in (reader.fieldnames or [])
        ]

        if missing_fields:
            raise ValueError(
                f"Missing metadata fields: {missing_fields}"
            )

        rows = list(reader)

    total_samples = len(rows)

    sample_ids = [
        row["sample_id"]
        for row in rows
    ]

    problem_ids = [
        row["problem_id"]
        for row in rows
    ]

    problem_counts = Counter(problem_ids)

    duplicate_sample_ids = [
        sample_id
        for sample_id, count in Counter(sample_ids).items()
        if count > 1
    ]

    empty_fields = []

    for index, row in enumerate(rows, start=2):
        for field in REQUIRED_FIELDS:
            if not row[field].strip():
                empty_fields.append(
                    f"Row {index}: empty field '{field}'"
                )

    failed_samples = [
        row
        for row in rows
        if row["status"] != "success"
    ]

    invalid_sizes = [
        row
        for row in rows
        if not row["file_size_bytes"].isdigit()
        or int(row["file_size_bytes"]) <= 0
    ]

    missing_processed_files = []
    missing_raw_files = []

    for row in rows:
        processed_file = (
            PROCESSED_ROOT / row["source_path"]
        )

        raw_file = (
            RAW_ROOT / row["original_path"]
        )

        if not processed_file.is_file():
            missing_processed_files.append(
                row["source_path"]
            )

        if not raw_file.is_file():
            missing_raw_files.append(
                row["original_path"]
            )

    # Summary
    print("\n========== METADATA VALIDATION ==========")
    print(f"Total samples: {total_samples}")
    print(f"Unique sample IDs: {len(set(sample_ids))}")
    print(f"Unique problems: {len(set(problem_ids))}")
    print(f"Failed samples: {len(failed_samples)}")
    print(f"Duplicate sample IDs: {len(duplicate_sample_ids)}")
    print(f"Empty required fields: {len(empty_fields)}")
    print(f"Invalid file sizes: {len(invalid_sizes)}")
    print(
        "Missing processed files: "
        f"{len(missing_processed_files)}"
    )
    print(
        "Missing raw files: "
        f"{len(missing_raw_files)}"
    )

    print("\nSamples per problem:")
    if problem_counts:
        print(
            f"Minimum: {min(problem_counts.values())}"
        )
        print(
            f"Maximum: {max(problem_counts.values())}"
        )

    # Assertions
    if total_samples != EXPECTED_TOTAL:
        errors.append(
            f"Expected {EXPECTED_TOTAL} samples, "
            f"got {total_samples}"
        )

    if len(set(sample_ids)) != total_samples:
        errors.append("Sample IDs are not unique")

    if len(set(problem_ids)) != EXPECTED_PROBLEMS:
        errors.append(
            f"Expected {EXPECTED_PROBLEMS} problems, "
            f"got {len(set(problem_ids))}"
        )

    wrong_problem_counts = {
        problem_id: count
        for problem_id, count in problem_counts.items()
        if count != EXPECTED_PER_PROBLEM
    }

    if wrong_problem_counts:
        errors.append(
            f"Problems with incorrect sample counts: "
            f"{wrong_problem_counts}"
        )

    if failed_samples:
        errors.append(
            f"Found {len(failed_samples)} non-success samples"
        )

    if empty_fields:
        errors.append(
            f"Found {len(empty_fields)} empty required fields"
        )

    if invalid_sizes:
        errors.append(
            f"Found {len(invalid_sizes)} invalid file sizes"
        )

    if missing_processed_files:
        errors.append(
            f"Found {len(missing_processed_files)} "
            "missing processed files"
        )

    if missing_raw_files:
        errors.append(
            f"Found {len(missing_raw_files)} missing raw files"
        )

    print("\n======================================")

    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return False

    print("\nVALIDATION PASSED")
    print("All metadata integrity checks passed.")
    return True


if __name__ == "__main__":
    passed = validate_metadata()

    if not passed:
        raise SystemExit(1)