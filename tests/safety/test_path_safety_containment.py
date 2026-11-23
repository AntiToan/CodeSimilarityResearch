from pathlib import Path

import pytest

from src.safety.path_safety import (
    PathContainmentError,
    PathSafety,
)


def test_root_itself_is_allowed(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    result = PathSafety.validate_containment(root, root)

    assert result.path == root.resolve()
    assert result.root == root.resolve()
    assert result.relative_path == Path(".")


def test_child_path_is_allowed(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    candidate = root / "nested" / "sample.py"

    result = PathSafety.validate_containment(candidate, root)

    assert result.path == candidate.resolve()
    assert result.root == root.resolve()
    assert result.relative_path == Path("nested") / "sample.py"


def test_missing_child_is_allowed_without_creation(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    candidate = root / "missing" / "sample.py"

    result = PathSafety.validate_containment(candidate, root)

    assert result.path == candidate.resolve()
    assert result.relative_path == Path("missing") / "sample.py"
    assert not candidate.exists()
    assert not candidate.parent.exists()


def test_sibling_prefix_trap_is_rejected(tmp_path):
    root = tmp_path / "dataset"
    sibling = tmp_path / "dataset_backup"

    root.mkdir()
    sibling.mkdir()

    candidate = sibling / "sample.py"

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(candidate, root)


def test_outside_path_is_rejected(tmp_path):
    root = tmp_path / "dataset"
    outside = tmp_path / "outside.py"

    root.mkdir()

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(outside, root)


def test_traversal_escape_is_rejected(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    candidate = root / ".." / "outside.py"

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(candidate, root)


def test_missing_root_is_rejected(tmp_path):
    root = tmp_path / "missing_root"
    candidate = root / "sample.py"

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(candidate, root)


def test_file_as_root_is_rejected(tmp_path):
    root_file = tmp_path / "root.txt"
    root_file.write_text("test", encoding="utf-8")

    candidate = root_file / "sample.py"

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(candidate, root_file)


def test_containment_does_not_mutate_filesystem(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()

    candidate = root / "nested" / "sample.py"

    PathSafety.validate_containment(candidate, root)

    assert not candidate.exists()
    assert not candidate.parent.exists()


def test_internal_symlink_is_allowed(tmp_path):
    root = tmp_path / "dataset"
    internal = root / "internal"

    root.mkdir()
    internal.mkdir()

    link = root / "alias"

    try:
        link.symlink_to(internal, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    candidate = link / "sample.py"

    result = PathSafety.validate_containment(candidate, root)

    assert result.path == (internal / "sample.py").resolve()
    assert result.root == root.resolve()


def test_external_symlink_is_rejected(tmp_path):
    root = tmp_path / "dataset"
    outside = tmp_path / "outside"

    root.mkdir()
    outside.mkdir()

    link = root / "external"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")

    candidate = link / "secret.py"

    with pytest.raises(PathContainmentError):
        PathSafety.validate_containment(candidate, root)