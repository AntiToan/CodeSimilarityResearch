from pathlib import Path
import stat

import pytest

from src.safety.path_safety import (
    WriteTargetValidationError,
    PathSafety,
)


def make_output_root(tmp_path):
    root = tmp_path / "output"
    root.mkdir()
    return root


def test_write_target_inside_output_root_is_allowed(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "sample.py"

    result = PathSafety.validate_write_target(target, root)

    assert result.path == target.resolve()
    assert result.root == root.resolve()
    assert result.relative_path == Path("sample.py")


def test_missing_leaf_is_allowed_without_creation(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "missing.py"

    result = PathSafety.validate_write_target(target, root)

    assert result.path == target.resolve()
    assert not target.exists()


def test_missing_nested_parent_is_allowed_without_creation(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "nested" / "deep" / "sample.py"

    result = PathSafety.validate_write_target(target, root)

    assert result.relative_path == Path("nested") / "deep" / "sample.py"
    assert not target.exists()
    assert not target.parent.exists()


def test_existing_regular_file_is_allowed(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "existing.py"
    target.write_text("existing content", encoding="utf-8")

    result = PathSafety.validate_write_target(target, root)

    assert result.path == target.resolve()
    assert target.read_text(encoding="utf-8") == "existing content"


def test_output_root_itself_is_rejected(tmp_path):
    root = make_output_root(tmp_path)

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(root, root)


def test_outside_target_is_rejected(tmp_path):
    root = make_output_root(tmp_path)
    outside = tmp_path / "outside.py"

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(outside, root)


def test_sibling_prefix_trap_is_rejected(tmp_path):
    root = make_output_root(tmp_path)
    sibling = tmp_path / "output_backup"
    sibling.mkdir()

    target = sibling / "sample.py"

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(target, root)


def test_existing_directory_as_target_is_rejected(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "subdirectory"
    target.mkdir()

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(target, root)


def test_relative_write_target_is_rejected(tmp_path):
    root = make_output_root(tmp_path)

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(
            Path("relative/sample.py"),
            root,
        )


def test_leaf_symlink_is_rejected(tmp_path):
    root = make_output_root(tmp_path)
    real_file = root / "real.py"
    link = root / "link.py"

    real_file.write_text("content", encoding="utf-8")

    try:
        link.symlink_to(real_file)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(link, root)


def test_internal_parent_symlink_is_allowed(tmp_path):
    root = make_output_root(tmp_path)
    real_dir = root / "real_dir"
    alias_dir = root / "alias_dir"

    real_dir.mkdir()

    try:
        alias_dir.symlink_to(real_dir, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    target = alias_dir / "sample.py"

    result = PathSafety.validate_write_target(target, root)

    assert result.path == (real_dir / "sample.py").resolve()
    assert result.relative_path == Path("real_dir") / "sample.py"


def test_external_parent_symlink_is_rejected(tmp_path):
    root = make_output_root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    alias_dir = root / "external_alias"

    try:
        alias_dir.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    target = alias_dir / "sample.py"

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(target, root)


def test_write_target_validation_does_not_mutate_filesystem(tmp_path):
    root = make_output_root(tmp_path)
    target = root / "nested" / "sample.py"

    PathSafety.validate_write_target(target, root)

    assert not target.exists()
    assert not target.parent.exists()


@pytest.mark.skipif(
    not hasattr(stat, "S_ISFIFO"),
    reason="FIFO inspection is unavailable on this platform",
)
def test_fifo_as_write_target_is_rejected(tmp_path):
    root = make_output_root(tmp_path)

    if not hasattr(__import__("os"), "mkfifo"):
        pytest.skip("FIFO creation unavailable on this platform")

    import os

    target = root / "pipe"
    os.mkfifo(target)

    with pytest.raises(WriteTargetValidationError):
        PathSafety.validate_write_target(target, root)