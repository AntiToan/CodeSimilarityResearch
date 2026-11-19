from pathlib import Path

from src.data.metadata_generator import generate_metadata


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "poj104"
    / "ProgramData"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "source"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "metadata"
    / "samples.csv"
)


if __name__ == "__main__":
    report = generate_metadata(
        raw_dir=RAW_DIR,
        processed_dir=PROCESSED_DIR,
        output_csv=OUTPUT_CSV,
    )

    print("\n========== METADATA SUMMARY ==========")
    print(f"Total samples: {report['total_samples']}")
    print(f"Successful: {report['successful_samples']}")
    print(f"Failed: {report['failed_samples']}")
    print(f"Output: {report['output_csv']}")
    print("===================================")