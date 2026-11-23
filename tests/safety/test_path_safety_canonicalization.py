from pathlib import Path

import pytest

from src.safety.path_safety import (
    PathResolutionError,
    PathSafety,
)


def test_absolute_path_canonicalizes(tmp_path):
    result = PathSafety.canonicalize(tmp_path / "a" / ".." / "b.py")

    assert result.is_absolute()
    assert result == (tmp_path / "b.py").resolve()


def test_relative_path_requires_explicit_base():
    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize("file.py")


def test_relative_path_with_absolute_base(tmp_path):
    result = PathSafety.canonicalize(
        "nested/file.py",
        base_dir=tmp_path,
    )

    assert result == (tmp_path / "nested" / "file.py").resolve()
    assert result.is_absolute()


def test_relative_base_is_rejected():
    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize(
            "file.py",
            base_dir="relative/base",
        )


def test_missing_leaf_is_allowed(tmp_path):
    target = tmp_path / "not_created.py"

    result = PathSafety.canonicalize(target)

    assert result == target.resolve()
    assert not target.exists()


def test_dot_and_dotdot_are_normalized(tmp_path):
    result = PathSafety.canonicalize(
        tmp_path / "folder" / ".." / "file.py"
    )

    assert result == (tmp_path / "file.py").resolve()


def test_null_byte_rejected(tmp_path):
    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize(str(tmp_path) + "\x00invalid")


def test_empty_path_rejected():
    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize("")


def test_base_dir_must_exist(tmp_path):
    missing_base = tmp_path / "missing_base"

    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize(
            "file.py",
            base_dir=missing_base,
        )


def test_base_dir_must_be_directory(tmp_path):
    base_file = tmp_path / "base.txt"
    base_file.write_text("x", encoding="utf-8")

    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize(
            "file.py",
            base_dir=base_file,
        )


def test_canonicalization_does_not_create_target(tmp_path):
    target = tmp_path / "nested" / "target.py"

    PathSafety.canonicalize(target)

    assert not target.exists()
    assert not target.parent.exists()

def test_drive_relative_path_rejected():
    with pytest.raises(PathResolutionError):
        PathSafety.canonicalize("C:folder\\file.py")