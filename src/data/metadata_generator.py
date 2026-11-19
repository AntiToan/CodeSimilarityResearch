import csv 
from pathlib import Path

METADATA_FIELDS = [
    "sample_id",
    "problem_id",
    "filename",
    "language",
    "source_path",
    "original_path",
    "file_size_bytes",
    "status",
]

def generate_metadata(
    raw_dir: str | Path,
    processed_dir: str | Path,
    output_csv: str | Path,
) -> dict:
    raw_path = Path(raw_dir)
    processed_path = Path(processed_dir)
    csv_path = Path(output_csv)

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw dataset directory not found: {raw_path}"
        )

    if not raw_path.is_dir():
        raise NotADirectoryError(
            f"Raw dataset path is not a directory: {raw_path}"
        )

    source_files = sorted(raw_path.rglob("*.txt"))

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    total_samples = 0
    successful_samples = 0
    failed_samples = 0

    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file, 
            fieldnames=METADATA_FIELDS,
        )

        writer.writeheader()

        for raw_file in source_files:
            relative_path = raw_file.relative_to(raw_path)
            problem_id = relative_path.parts[0]
            filename = raw_file.name 
            file_stem = raw_file.stem 

            # processed_file = processed_path / relative_path
            processed_file = processed_path / relative_path

            if total_samples == 0:
                print("DEBUG raw_path:", raw_path.resolve())
                print("DEBUG processed_path:", processed_path.resolve())
                print("DEBUG relative_path:", relative_path)
                print("DEBUG processed_file:", processed_file.resolve())
                print("DEBUG file_exists:", processed_file.is_file())

            sample_id = (
                f"poj104_{problem_id}_{file_stem}"
            )

            status = (
                "success"
                if processed_file.is_file()
                else "failed"
            )

            if status == "success":
                file_size = processed_file.stat().st_size
                successful_samples += 1
            else:
                file_size = 0
                failed_samples += 1

            record = {
                "sample_id": sample_id,
                "problem_id": problem_id,
                "filename": filename,
                "language": "cpp",
                "source_path": processed_file.relative_to(
                    processed_path.parent
                ).as_posix(),
                "original_path": raw_file.relative_to(
                    raw_path.parent
                ).as_posix(),
                "file_size_bytes": file_size,
                "status": status,
            }

            writer.writerow(record)
            total_samples += 1

    return {
        "total_samples": total_samples,
        "successful_samples": successful_samples,
        "failed_samples": failed_samples,
        "output_csv": str(csv_path),
    }