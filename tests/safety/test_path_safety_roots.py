from pathlib import Path

import pytest

from src.safety.path_safety import (
    RootConfigurationError,
    PathSafety,
)


def test_distinct_sibling_roots_are_allowed(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "output"

    source.mkdir()
    output.mkdir()

    canonical_source, canonical_output = (
        PathSafety.validate_distinct_roots(source, output)
    )

    assert canonical_source == source.resolve()
    assert canonical_output == output.resolve()


def test_prefix_similar_sibling_roots_are_allowed(tmp_path):
    source = tmp_path / "data"
    output = tmp_path / "data_backup"

    source.mkdir()
    output.mkdir()

    result = PathSafety.validate_distinct_roots(source, output)

    assert result == (source.resolve(), output.resolve())


def test_identical_roots_are_rejected(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(root, root)


def test_output_nested_inside_source_is_rejected(tmp_path):
    source = tmp_path / "source"
    output = source / "generated"

    source.mkdir()
    output.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_source_nested_inside_output_is_rejected(tmp_path):
    output = tmp_path / "output"
    source = output / "input"

    output.mkdir()
    source.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_missing_source_root_is_rejected(tmp_path):
    source = tmp_path / "missing_source"
    output = tmp_path / "output"

    output.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_missing_output_root_is_rejected(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "missing_output"

    source.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_file_used_as_source_root_is_rejected(tmp_path):
    source = tmp_path / "source.txt"
    output = tmp_path / "output"

    source.write_text("data", encoding="utf-8")
    output.mkdir()

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_file_used_as_output_root_is_rejected(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "output.txt"

    source.mkdir()
    output.write_text("data", encoding="utf-8")

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output)


def test_symlinked_roots_that_resolve_to_same_directory_are_rejected(
    tmp_path,
):
    real_root = tmp_path / "real_root"
    alias_root = tmp_path / "alias_root"
    output = tmp_path / "output"

    real_root.mkdir()
    output.mkdir()

    try:
        alias_root.symlink_to(real_root, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(real_root, alias_root)


def test_symlinked_output_nested_inside_source_is_rejected(tmp_path):
    source = tmp_path / "source"
    real_output = source / "actual_output"
    output_link = tmp_path / "output_link"

    source.mkdir()
    real_output.mkdir()

    try:
        output_link.symlink_to(real_output, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    with pytest.raises(RootConfigurationError):
        PathSafety.validate_distinct_roots(source, output_link)


def test_symlinked_roots_to_independent_directories_are_allowed(tmp_path):
    source = tmp_path / "real_source"
    output = tmp_path / "real_output"
    source_alias = tmp_path / "source_alias"

    source.mkdir()
    output.mkdir()

    try:
        source_alias.symlink_to(source, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    canonical_source, canonical_output = (
        PathSafety.validate_distinct_roots(source_alias, output)
    )

    assert canonical_source == source.resolve()
    assert canonical_output == output.resolve()


def test_distinct_roots_does_not_mutate_filesystem(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "output"

    source.mkdir()
    output.mkdir()

    PathSafety.validate_distinct_roots(source, output)

    assert source.is_dir()
    assert output.is_dir()