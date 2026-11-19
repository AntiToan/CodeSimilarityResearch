
import hashlib
from pathlib import Path

import pytest

from src.data.variant_registry import (
    DuplicateVariantError,
    VariantRegistry,
    VariantRegistryRecord,
    VariantRegistrySchemaError,
    VARIANT_REGISTRY_COLUMNS,
)


def create_source(tmp_path, content="int main() {}\n"):
    source_path = tmp_path / "1001_v001.txt"
    source_path.write_text(content, encoding="utf-8")
    return source_path


def make_record(source_path, **overrides):
    defaults = {
        "variant_id": "sample_001_v001",
        "original_sample_id": "sample_001",
        "problem_id": "100",
        "split": "train",
        "variant_index": 1,
        "transformation_type": "whitespace",
        "generation_seed": 42,
        "validator_version": "1.0",
        "validation_status": "PASS",
        "source_path": str(source_path),
        "original_source_path": "data/processed/poj104/source/100/sample_001.txt",
        "source_hash": hashlib.sha256(
            source_path.read_bytes()
            if source_path.exists()
            else b""
        ).hexdigest(),
        "created_at": "2026-11-19T12:00:00Z",
    }
    defaults.update(overrides)
    return VariantRegistryRecord(**defaults)


def test_registry_creates_csv_with_schema(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(
        tmp_path / "metadata" / "variants.csv"
    )

    registry.register(make_record(source))

    assert registry.registry_path.exists()

    records = registry.read_all()
    assert len(records) == 1
    assert list(records[0].keys()) == VARIANT_REGISTRY_COLUMNS


def test_registry_records_accepted_variant(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(tmp_path / "variants.csv")

    registry.register(make_record(source))

    record = registry.read_all()[0]
    assert record["variant_id"] == "sample_001_v001"
    assert record["original_sample_id"] == "sample_001"
    assert record["problem_id"] == "100"
    assert record["split"] == "train"
    assert record["validation_status"] == "PASS"


def test_registry_rejects_non_pass_variant(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(tmp_path / "variants.csv")

    record = make_record(
        source,
        validation_status="FAIL",
    )

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(record)


def test_registry_rejects_invalid_split(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(tmp_path / "variants.csv")

    record = make_record(source, split="unknown")

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(record)


def test_registry_rejects_duplicate_variant_id(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(tmp_path / "variants.csv")
    record = make_record(source)

    registry.register(record)

    with pytest.raises(DuplicateVariantError):
        registry.register(record)

    assert registry.count() == 1


def test_registry_rejects_hash_mismatch(tmp_path):
    source = create_source(tmp_path, content="actual source\n")
    registry = VariantRegistry(tmp_path / "variants.csv")

    record = make_record(
        source,
        source_hash="0" * 64,
    )

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(record)


def test_registry_rejects_invalid_variant_id(tmp_path):
    source = create_source(tmp_path)
    registry = VariantRegistry(tmp_path / "variants.csv")

    record = make_record(
        source,
        variant_id="wrong_v001",
    )

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(record)


def test_registry_rejects_missing_source_file(tmp_path):
    missing_source = tmp_path / "missing.txt"
    registry = VariantRegistry(tmp_path / "variants.csv")

    record = make_record(missing_source)

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(record)


def test_registry_appends_records(tmp_path):
    source1 = create_source(tmp_path, "variant 1\n")
    registry = VariantRegistry(tmp_path / "variants.csv")

    registry.register(make_record(source1))

    source2 = tmp_path / "1001_v002.txt"
    source2.write_text("variant 2\n", encoding="utf-8")

    record2 = make_record(
        source2,
        variant_id="sample_001_v002",
        variant_index=2,
        transformation_type="comments",
    )

    registry.register(record2)

    assert registry.count() == 2
    assert [
        record["variant_id"] for record in registry.read_all()
    ] == [
        "sample_001_v001",
        "sample_001_v002",
    ]


def test_registry_rejects_corrupted_existing_schema(tmp_path):
    registry_path = tmp_path / "variants.csv"
    registry_path.write_text(
        "wrong_column\nvalue\n",
        encoding="utf-8",
    )

    registry = VariantRegistry(registry_path)
    source = create_source(tmp_path)

    with pytest.raises(VariantRegistrySchemaError):
        registry.register(make_record(source))


def test_registry_count_empty(tmp_path):
    registry = VariantRegistry(tmp_path / "variants.csv")

    assert registry.count() == 0
    assert registry.read_all() == []
