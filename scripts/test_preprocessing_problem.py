from pathlib import Path
from src.preprocessing.batch_processor import process_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    PROJECT_ROOT / "data" / "raw" / "poj104" / "ProgramData" / "1"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "poj104" / "test_problem_1" / "source"
)

if __name__ == "__main__":
    report = process_dataset(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
    )

    print("\n--- Problem 1 Test Summary ---")
    print(f"Total files: {report['total_files']}")
    print(f"Successful: {report['successful_files']}")
    print(f"Failed: {report['failed_files']}")
    print(f"Encoding counts: {report['encoding_counts']}")
    print(
        f"Processing time: "
        f"{report['processing_time_seconds']} seconds"
    )

# python -m scripts.test_preprocessing_problem
