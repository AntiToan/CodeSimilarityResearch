import json
import time

from collections import Counter
from pathlib import Path

from src.preprocessing.source_reader import (
    SourceReadError,
    read_source_file,
)

def process_dataset(
    input_dir: str | Path,
    output_dir: str | Path,
) -> dict:
    """
    Process all .txt source files recursively.

    Args:
        input_dir: Raw dataset directory.
        output_dir: Processed dataset directory.

    Returns:
        Dictionary containing processing statistics.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {input_path}"
        )

    if not input_path.is_dir():
        raise NotADirectoryError(
            f"Input path is not a directory: {input_path}"
        )

    output_path.mkdir(parents=True, exist_ok=True)

    source_files = sorted(input_path.rglob("*.txt"))

    start_time = time.perf_counter()

    successful_files = 0
    failed_files = 0

    encoding_counts = Counter()
    errors = []

    total_original_bytes = 0
    total_processed_bytes = 0

    for index, source_file in enumerate(source_files, start=1):
        relative_path = source_file.relative_to(input_path)
        destination_file = output_path / relative_path

        try:
            result = read_source_file(source_file)

            destination_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination_file.write_text(
                result["content"],
                encoding="utf-8",
                newline="\n",
            )

            successful_files += 1
            encoding_counts[result["encoding"]] += 1

            total_original_bytes += result["original_size"]
            total_processed_bytes += result["processed_size"]

        except (SourceReadError, OSError) as exc:
            failed_files += 1

            errors.append({
                "file": relative_path.as_posix(),
                "error": str(exc),
            })

        if index % 1000 == 0:
            print(
                f"Processed {index}/{len(source_files)} files..."
            )

    processing_time = time.perf_counter() - start_time

    report = {
        "total_files": len(source_files),
        "successful_files": successful_files,
        "failed_files": failed_files,
        "encoding_counts": dict(encoding_counts),
        "total_original_bytes": total_original_bytes,
        "total_processed_bytes": total_processed_bytes,
        "processing_time_seconds": round(processing_time, 2),
        "errors": errors,
    }

    report_path = output_path.parent / "preprocessing_report.json"

    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\nPreprocessing completed!")
    print(f"Total files: {len(source_files)}")
    print(f"Successful: {successful_files}")
    print(f"Failed: {failed_files}")
    print(f"Report: {report_path}")

    return report
