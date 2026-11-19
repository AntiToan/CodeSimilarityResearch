
import hashlib

from src.data.variant_registry import (
    VariantRegistry,
    VariantRegistryRecord,
)
from src.data.variant_registry_integrity import (
    VariantRegistryIntegrityValidator,
)


def make_source(tmp_path, name, content):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_record(
    variant_path,
    original_path,
    variant_id="sample_001_v001",
    original_id="sample_001",
    problem_id="100",
    split="train",
    index=1,
):
    return VariantRegistryRecord(
        variant_id=variant_id,
        original_sample_id=original_id,
        problem_id=problem_id,
        split=split,
        variant_index=index,
        transformation_type="whitespace",
        generation_seed=42,
        validator_version="1.0",
        validation_status="PASS",
        source_path=str(variant_path),
        original_source_path=str(original_path),
        source_hash=hashlib.sha256(
            variant_path.read_bytes()
        ).hexdigest(),
        created_at="2026-11-19T12:00:00Z",
    )


def test_integrity_passes_valid_registry(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "int main() {}\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "int main() { }\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert report.passed
    assert report.status == "PASS"
    assert report.total_records == 1
    assert report.valid_records == 1
    assert report.issues == []


def test_integrity_detects_variant_hash_mismatch(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    variant.write_text("tampered\n", encoding="utf-8")

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert not report.passed
    assert any(
        issue.code == "VARIANT_HASH_MISMATCH"
        for issue in report.issues
    )


def test_integrity_detects_original_missing(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    original.unlink()

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "ORIGINAL_SOURCE_MISSING"
        for issue in report.issues
    )


def test_integrity_detects_variant_missing(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    variant.unlink()

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "VARIANT_SOURCE_MISSING"
        for issue in report.issues
    )


def test_integrity_detects_variant_identical_to_original(tmp_path):
    content = "same source\n"

    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        content,
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        content,
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "VARIANT_EQUALS_ORIGINAL"
        for issue in report.issues
    )


def test_integrity_detects_problem_folder_mismatch(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "200",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "PROBLEM_PATH_MISMATCH"
        for issue in report.issues
    )


def test_integrity_detects_duplicate_variant_content(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant1 = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "duplicate content\n",
    )
    variant2 = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v002.txt",
        "duplicate content\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(
        make_record(variant1, original)
    )
    registry.register(
        make_record(
            variant2,
            original,
            variant_id="sample_001_v002",
            index=2,
        )
    )

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "DUPLICATE_VARIANT_CONTENT"
        for issue in report.issues
    )


def test_integrity_detects_inconsistent_original_content(tmp_path):
    original1 = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original one\n",
    )
    original2 = make_source(
        tmp_path / "source_copy" / "100",
        "sample_001_copy.txt",
        "original two\n",
    )
    variant1 = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant one\n",
    )
    variant2 = make_source(
        tmp_path / "variants_copy" / "100",
        "sample_001_v002.txt",
        "variant two\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(
        make_record(variant1, original1)
    )
    registry.register(
        make_record(
            variant2,
            original2,
            variant_id="sample_001_v002",
            index=2,
        )
    )

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "ORIGINAL_CONTENT_INCONSISTENT"
        for issue in report.issues
    )


def test_integrity_detects_invalid_split_in_existing_registry(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    # Simulate external/manual corruption of the registry.
    rows = registry.read_all()
    rows[0]["split"] = "invalid_split"
    registry._atomic_write(rows)

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert any(
        issue.code == "INVALID_SPLIT"
        for issue in report.issues
    )


def test_integrity_empty_registry_passes(tmp_path):
    registry = VariantRegistry(tmp_path / "variants.csv")

    report = VariantRegistryIntegrityValidator(
        registry
    ).validate()

    assert report.passed
    assert report.total_records == 0
    assert report.valid_records == 0


def test_integrity_does_not_modify_registry(tmp_path):
    original = make_source(
        tmp_path / "source" / "100",
        "sample_001.txt",
        "original\n",
    )
    variant = make_source(
        tmp_path / "variants" / "100",
        "sample_001_v001.txt",
        "variant\n",
    )

    registry = VariantRegistry(tmp_path / "variants.csv")
    registry.register(make_record(variant, original))

    before = registry.registry_path.read_bytes()

    VariantRegistryIntegrityValidator(
        registry
    ).validate()

    after = registry.registry_path.read_bytes()

    assert before == after
