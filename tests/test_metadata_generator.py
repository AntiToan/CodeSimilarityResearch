import csv
from src.data.metadata_generator import generate_metadata

def test_generate_metadata(tmp_path):
    raw_dir = tmp_path / "raw" / "ProgramData"
    processed_dir = tmp_path / "processed" / "source"
    output_csv = tmp_path / "processed" / "metadata" / "samples.csv"

    # Tạo raw dataset
    (raw_dir / "1").mkdir(parents=True)
    (raw_dir / "2").mkdir(parents=True)

    (raw_dir / "1" / "1.txt").write_text(
        "int main() { return 0; }\n",
        encoding="utf-8",
    )

    (raw_dir / "2" / "2.txt").write_text(
        "int main() { return 1; }\n",
        encoding="utf-8",
    )

    # Tạo processed dataset (một file thành công)
    (processed_dir / "1").mkdir(parents=True)

    (processed_dir / "1" / "1.txt").write_text(
        "int main() { return 0; }\n",
        encoding="utf-8",
    )

    report = generate_metadata(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        output_csv=output_csv,
    )

    assert report["total_samples"] == 2
    assert report["successful_samples"] == 1
    assert report["failed_samples"] == 1

    assert output_csv.exists()

    with output_csv.open(
        encoding="utf-8",
        newline="",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2

    # Kiểm tra sample thành công
    first_sample = rows[0]

    assert first_sample["sample_id"] == "poj104_1_1"
    assert first_sample["problem_id"] == "1"
    assert first_sample["filename"] == "1.txt"
    assert first_sample["language"] == "cpp"
    assert first_sample["status"] == "success"
    assert int(first_sample["file_size_bytes"]) > 0

    # Đảm bảo path không phải absolute path
    assert not first_sample["source_path"].startswith("/")
    assert not first_sample["original_path"].startswith("/")

    # Kiểm tra sample bị thiếu processed file
    second_sample = rows[1]

    assert second_sample["sample_id"] == "poj104_2_2"
    assert second_sample["status"] == "failed"
    assert int(second_sample["file_size_bytes"]) == 0