import hashlib
from src.data.duplicate_detector import (
    calculate_sha256,
    detect_exact_duplicates,
)

def test_calculate_sha256(tmp_path):
    file_path = tmp_path / "sample.cpp"
    content = b"int main() { return 0; }\n"
    file_path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert calculate_sha256(file_path) == expected

def test_detect_exact_duplicates(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()

    (source_root / "a.cpp").write_text(
        "int main() {}\n",
        encoding="utf-8",
    )
    (source_root / "b.cpp").write_text(
        "int main() {}\n",
        encoding="utf-8",
    )
    (source_root / "c.cpp").write_text(
        "int main() { return 1; }\n",
        encoding="utf-8",
    )

    samples = [
        {
            "sample_id": "a",
            "source_path": "a.cpp",
        },
        {
            "sample_id": "b",
            "source_path": "b.cpp",
        },
        {
            "sample_id": "c",
            "source_path": "c.cpp",
        },
    ]

    hashes, groups = detect_exact_duplicates(
        samples,
        source_root,
    )

    assert len(hashes) == 3
    assert len(groups) == 1
    assert groups[0]["sample_ids"] == ["a", "b"]
    assert groups[0]["sample_count"] == 2

def test_no_duplicates(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()

    (source_root / "a.cpp").write_text("int a;\n")
    (source_root / "b.cpp").write_text("int b;\n")

    samples = [
        {"sample_id": "a", "source_path": "a.cpp"},
        {"sample_id": "b", "source_path": "b.cpp"},
    ]

    _, groups = detect_exact_duplicates(samples, source_root)

    assert groups == []


def test_duplicate_group_id_is_deterministic(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()

    content = "int main() {}\n"
    (source_root / "a.cpp").write_text(content)
    (source_root / "b.cpp").write_text(content)

    samples = [
        {"sample_id": "b", "source_path": "b.cpp"},
        {"sample_id": "a", "source_path": "a.cpp"},
    ]

    _, first_groups = detect_exact_duplicates(samples, source_root)
    _, second_groups = detect_exact_duplicates(samples, source_root)

    assert first_groups == second_groups
