from pathlib import Path

from src.preprocessing.batch_processor import process_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "poj104"
    / "ProgramData"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "source"
)


if __name__ == "__main__":
    print("Starting POJ-104 preprocessing...")
    print(f"Input: {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    report = process_dataset(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
    )

    print("\n========== FINAL SUMMARY ==========")
    print(f"Total files: {report['total_files']}")
    print(f"Successful: {report['successful_files']}")
    print(f"Failed: {report['failed_files']}")
    print(f"Encoding counts: {report['encoding_counts']}")
    print(
        f"Processing time: "
        f"{report['processing_time_seconds']} seconds"
    )
    print("================================")