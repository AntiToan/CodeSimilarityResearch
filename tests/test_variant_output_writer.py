
from pathlib import Path

import pytest

from src.data.variant_output_writer import (
    InvalidVariantPathError,
    VariantFileExistsError,
    VariantOutputWriter,
)
from src.transformations.variant_generator import GeneratedVariant


def make_variant(
    variant_id="sample_001_v001",
    original_sample_id="sample_001",
    text="int main() {}\n",
):
    return GeneratedVariant(
        variant_id=variant_id,
        original_sample_id=original_sample_id,
        variant_index=1,
        transformation_type="whitespace",
        generation_seed=42,
        source_text="int main() {}\n",
        transformed_text=text,
    )


def test_build_path_uses_problem_id_and_variant_id(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")

    path = writer.build_path(
        problem_id="100",
        variant_id="sample_001_v001",
        original_sample_id="sample_001",
    )

    assert path == (
        tmp_path / "variants" / "100" / "sample_001_v001.txt"
    ).resolve()


def test_write_variant_creates_file(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")
    variant = make_variant()

    path = writer.write_variant(
        variant,
        problem_id="100",
    )

    assert path.exists()
    assert path.read_text(encoding="utf-8") == "int main() {}\n"


def test_write_variant_creates_problem_directory(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")

    writer.write_variant(
        make_variant(),
        problem_id="100",
    )

    assert (tmp_path / "variants" / "100").is_dir()


def test_write_variant_normalizes_newlines(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")

    variant = make_variant(
        text="line1\r\nline2\rline3\n"
    )

    path = writer.write_variant(
        variant,
        problem_id="100",
    )

    assert path.read_bytes() == b"line1\nline2\nline3\n"


def test_existing_variant_is_never_overwritten(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")
    variant = make_variant(text="first version\n")

    first_path = writer.write_variant(
        variant,
        problem_id="100",
    )

    with pytest.raises(VariantFileExistsError):
        writer.write_variant(
            make_variant(text="second version\n"),
            problem_id="100",
        )

    assert first_path.read_text(encoding="utf-8") == "first version\n"


@pytest.mark.parametrize(
    "problem_id",
    [
        "../outside",
        "..",
        "100/../../outside",
        "100\\..\\outside",
    ],
)
def test_rejects_unsafe_problem_id(tmp_path, problem_id):
    writer = VariantOutputWriter(tmp_path / "variants")

    with pytest.raises(InvalidVariantPathError):
        writer.build_path(
            problem_id=problem_id,
            variant_id="sample_001_v001",
            original_sample_id="sample_001",
        )


@pytest.mark.parametrize(
    "variant_id",
    [
        "../outside_v001",
        "sample_001/../../outside",
        "sample_001_v1",
        "sample_001_v0001",
        "bad id_v001",
    ],
)
def test_rejects_unsafe_variant_id(tmp_path, variant_id):
    writer = VariantOutputWriter(tmp_path / "variants")

    with pytest.raises(InvalidVariantPathError):
        writer.build_path(
            problem_id="100",
            variant_id=variant_id,
            original_sample_id="sample_001",
        )


def test_rejects_variant_belonging_to_another_original(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")

    with pytest.raises(InvalidVariantPathError):
        writer.build_path(
            problem_id="100",
            variant_id="sample_002_v001",
            original_sample_id="sample_001",
        )


def test_original_file_is_not_touched(tmp_path):
    original_root = tmp_path / "source" / "100"
    original_root.mkdir(parents=True)

    original_path = original_root / "sample_001.txt"
    original_content = "original source\n"
    original_path.write_text(
        original_content,
        encoding="utf-8",
    )

    writer = VariantOutputWriter(tmp_path / "variants")
    writer.write_variant(
        make_variant(text="modified source\n"),
        problem_id="100",
    )

    assert original_path.read_text(encoding="utf-8") == original_content


def test_output_is_utf8(tmp_path):
    writer = VariantOutputWriter(tmp_path / "variants")

    path = writer.write_variant(
        make_variant(text="// tiếng Việt\n"),
        problem_id="100",
    )

    assert path.read_text(encoding="utf-8") == "// tiếng Việt\n"
