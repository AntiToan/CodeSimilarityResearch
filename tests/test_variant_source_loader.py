
import csv

import pytest

from src.data.variant_source_loader import (
    LoadedSample,
    SourceFileLoadError,
    SourceMetadataError,
    VariantSourceLoader,
)


METADATA_COLUMNS = [
    "sample_id",
    "problem_id",
    "filename",
    "language",
    "source_path",
    "original_path",
    "file_size_bytes",
    "status",
]

SPLIT_COLUMNS = [
    "sample_id",
    "problem_id",
    "split",
    "seed",
    "method",
    "duplicate_group_id",
    "split_version",
    "content_sha256",
]


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def make_metadata(sample_id, source_path, status="success"):
    return {
        "sample_id": sample_id,
        "problem_id": "1",
        "filename": "1001.txt",
        "language": "cpp",
        "source_path": source_path,
        "original_path": "ProgramData/1/1001.txt",
        "file_size_bytes": "10",
        "status": status,
    }


def make_split(sample_id, split="train"):
    return {
        "sample_id": sample_id,
        "problem_id": "1",
        "split": split,
        "seed": "42",
        "method": "group_aware_stratified_greedy",
        "duplicate_group_id": "",
        "split_version": "1.0.0",
        "content_sha256": "dummy_hash",
    }


@pytest.fixture
def dataset(tmp_path):
    processed_root = tmp_path / "processed" / "poj104"
    metadata_dir = processed_root / "metadata"
    source_root = processed_root / "source"

    metadata_path = metadata_dir / "samples.csv"
    splits_path = metadata_dir / "source_splits.csv"

    source_file = source_root / "1" / "1001.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("int main() { return 0; }", encoding="utf-8")

    write_csv(
        metadata_path,
        METADATA_COLUMNS,
        [make_metadata("sample001", "source/1/1001.txt")],
    )
    write_csv(
        splits_path,
        SPLIT_COLUMNS,
        [make_split("sample001", "train")],
    )

    loader = VariantSourceLoader(
        metadata_path=metadata_path,
        splits_path=splits_path,
        source_root=processed_root,
    )

    return {
        "loader": loader,
        "metadata_path": metadata_path,
        "splits_path": splits_path,
        "source_root": source_root,
        "source_file": source_file,
    }


def test_load_successful_sample(dataset):
    samples = dataset["loader"].load()

    assert len(samples) == 1

    sample = samples[0]
    assert isinstance(sample, LoadedSample)
    assert sample.sample_id == "sample001"
    assert sample.problem_id == "1"
    assert sample.split == "train"
    assert sample.language == "cpp"
    assert sample.source_text == "int main() { return 0; }"
    assert sample.source_path == dataset["source_file"].resolve()


def test_metadata_duplicate_sample_id(dataset):
    write_csv(
        dataset["metadata_path"],
        METADATA_COLUMNS,
        [
            make_metadata("sample001", "source/1/1001.txt"),
            make_metadata("sample001", "source/1/1001.txt"),
        ],
    )

    with pytest.raises(SourceMetadataError, match="Duplicate"):
        dataset["loader"].load()


def test_duplicate_split_sample_id(dataset):
    write_csv(
        dataset["splits_path"],
        SPLIT_COLUMNS,
        [
            make_split("sample001", "train"),
            make_split("sample001", "test"),
        ],
    )

    with pytest.raises(SourceMetadataError, match="Duplicate"):
        dataset["loader"].load()


def test_missing_split_assignment(dataset):
    write_csv(
        dataset["splits_path"],
        SPLIT_COLUMNS,
        [],
    )

    with pytest.raises(SourceMetadataError):
        dataset["loader"].load()


def test_invalid_split_name(dataset):
    write_csv(
        dataset["splits_path"],
        SPLIT_COLUMNS,
        [make_split("sample001", "invalid")],
    )

    with pytest.raises(SourceMetadataError, match="Invalid split"):
        dataset["loader"].load()


def test_missing_source_file(dataset):
    dataset["source_file"].unlink()

    with pytest.raises(SourceFileLoadError, match="not found"):
        dataset["loader"].load()


def test_missing_metadata_column(dataset):
    columns = METADATA_COLUMNS.copy()
    columns.remove("language")

    row = make_metadata("sample001", "source/1/1001.txt")
    row.pop("language")

    write_csv(
        dataset["metadata_path"],
        columns,
        [row],
    )

    with pytest.raises(SourceMetadataError, match="Missing columns"):
        dataset["loader"].load()


def test_metadata_file_missing(dataset):
    dataset["metadata_path"].unlink()

    with pytest.raises(SourceMetadataError, match="not found"):
        dataset["loader"].load()


def test_non_success_metadata_is_not_loaded(dataset):
    write_csv(
        dataset["metadata_path"],
        METADATA_COLUMNS,
        [make_metadata("sample001", "source/1/1001.txt", "failed")],
    )
    write_csv(
        dataset["splits_path"],
        SPLIT_COLUMNS,
        [],
    )

    with pytest.raises(SourceMetadataError):
        dataset["loader"].load()


def test_source_path_traversal_rejected(dataset):
    write_csv(
        dataset["metadata_path"],
        METADATA_COLUMNS,
        [make_metadata("sample001", "../outside.txt")],
    )

    with pytest.raises(SourceFileLoadError, match="escapes"):
        dataset["loader"].load()
