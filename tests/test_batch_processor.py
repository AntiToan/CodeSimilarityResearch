import json
from src.preprocessing.batch_processor import process_dataset

def test_batch_processor_success(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed" / "source"

    # Tạo dataset giả gồm nhiều thư mục
    (input_dir / "1").mkdir(parents=True)
    (input_dir / "2").mkdir(parents=True)

    (input_dir / "1" / "101.txt").write_text(
        "int main() {\r\n    return 0;\r\n}\r\n",
        encoding="utf-8",
    )

    (input_dir / "2" / "202.txt").write_text(
        "int main() {\n    return 1;\n}\n",
        encoding="utf-8",
    )

    report = process_dataset(input_dir, output_dir)

    # Kiểm tra thống kê
    assert report["total_files"] == 2
    assert report["successful_files"] == 2
    assert report["failed_files"] == 0

    # Kiểm tra giữ nguyên cấu trúc thư mục
    assert (output_dir / "1" / "101.txt").exists()
    assert (output_dir / "2" / "202.txt").exists()

    # Kiểm tra chuẩn hóa newline
    content = (output_dir / "1" / "101.txt").read_text(
        encoding="utf-8"
    )
    assert "\r" not in content

    # Kiểm tra report
    report_path = output_dir.parent / "preprocessing_report.json"
    assert report_path.exists()

    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["successful_files"] == 2


def test_batch_processor_handles_invalid_file(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed" / "source"

    (input_dir / "1").mkdir(parents=True)

    # File hợp lệ
    (input_dir / "1" / "valid.txt").write_text(
        "int main() { return 0; }\n",
        encoding="utf-8",
    )

    # File có byte không giải mã được bằng các encoding hỗ trợ
    (input_dir / "1" / "invalid.txt").write_bytes(b"\x81")

    report = process_dataset(input_dir, output_dir)

    assert report["total_files"] == 2
    assert report["successful_files"] == 1
    assert report["failed_files"] == 1

    # File lỗi không được tạo ra ở đầu ra
    assert not (output_dir / "1" / "invalid.txt").exists()

    # File hợp lệ vẫn phải được xử lý
    assert (output_dir / "1" / "valid.txt").exists()

    assert len(report["errors"]) == 1
    assert report["errors"][0]["file"] == "1/invalid.txt"

# pytest tests/test_batch_processor.py -v