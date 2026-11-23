from pathlib import Path
import pytest
from src.safety.persistence_temp import (
    TEMP_CREATE_MAX_ATTEMPTS,
    TempCreationError,
    create_owned_temp_file,
)
from src.safety.persistence_temp import (
    OwnershipVerificationState,
    verify_temp_ownership,
)
import os
from dataclasses import replace

from src.safety.persistence_temp import (
    OwnershipVerificationState,
    create_owned_temp_file,
    verify_temp_ownership,
)

def release_temp(temp):
    try:
        import os
        os.close(temp.fd)
    finally:
        temp.path.unlink(missing_ok=True)


def test_temp_created_in_destination_directory(tmp_path):
    destination = tmp_path / "output.bin"

    temp = create_owned_temp_file(destination)

    try:
        assert temp.path.parent == destination.parent
        assert temp.path.exists()
        assert temp.path.name.endswith(".tmp")
    finally:
        release_temp(temp)


def test_temp_creation_is_exclusive(tmp_path):
    destination = tmp_path / "output.bin"

    temp = create_owned_temp_file(destination)

    try:
        assert temp.fd >= 0
        assert temp.path.is_file()
    finally:
        release_temp(temp)


def test_temp_ownership_identity_matches_descriptor(tmp_path):
    import os

    temp = create_owned_temp_file(tmp_path / "output.bin")

    try:
        descriptor_stat = os.fstat(temp.fd)
        path_stat = os.stat(temp.path, follow_symlinks=False)

        assert temp.identity == (
            descriptor_stat.st_dev,
            descriptor_stat.st_ino,
        )

        assert temp.identity == (
            path_stat.st_dev,
            path_stat.st_ino,
        )
    finally:
        release_temp(temp)


def test_temp_attempt_starts_at_zero(tmp_path):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    try:
        assert temp.attempt == 0
    finally:
        release_temp(temp)


def test_missing_parent_is_not_created(tmp_path):
    missing_parent = tmp_path / "missing"
    destination = missing_parent / "output.bin"

    with pytest.raises(FileNotFoundError):
        create_owned_temp_file(destination)

    assert not missing_parent.exists()


def test_collision_retries_with_next_attempt(tmp_path, monkeypatch):
    import uuid

    class FixedUUID:
        hex = "a" * 32

    monkeypatch.setattr(
        uuid,
        "uuid4",
        lambda: FixedUUID(),
    )

    destination = tmp_path / "output.bin"

    first_candidate = (
        tmp_path / f".safepersist-{'a' * 32}-0.tmp"
    )

    first_candidate.touch()

    temp = create_owned_temp_file(destination)

    try:
        assert temp.attempt == 1
        assert temp.path.name == (
            f".safepersist-{'a' * 32}-1.tmp"
        )
        assert first_candidate.exists()
    finally:
        release_temp(temp)


def test_collision_retries_are_bounded(tmp_path, monkeypatch):
    import uuid

    class FixedUUID:
        hex = "b" * 32

    monkeypatch.setattr(
        uuid,
        "uuid4",
        lambda: FixedUUID(),
    )

    destination = tmp_path / "output.bin"

    for attempt in range(TEMP_CREATE_MAX_ATTEMPTS):
        (
            tmp_path
            / f".safepersist-{'b' * 32}-{attempt}.tmp"
        ).touch()

    with pytest.raises(TempCreationError):
        create_owned_temp_file(destination)

    assert len(list(tmp_path.glob(".safepersist-*.tmp"))) == (
        TEMP_CREATE_MAX_ATTEMPTS
    )

def test_identity_capture_failure_closes_fd_without_unverified_cleanup(
    tmp_path,
    monkeypatch,
):
    import os
    import src.safety.persistence_temp as temp_module

    real_open = os.open
    real_windows_create_fd = getattr(
        temp_module,
        "_windows_create_temp_fd",
        None,
    )

    real_fstat = os.fstat

    captured_fds = []
    captured_paths = []

    def tracked_open(path, flags, mode=0o777):
        fd = real_open(path, flags, mode)
        captured_fds.append(fd)
        captured_paths.append(Path(path))
        return fd

    def tracked_windows_create_fd(path):
        fd = real_windows_create_fd(path)
        captured_fds.append(fd)
        captured_paths.append(Path(path))
        return fd

    if os.name == "nt":
        monkeypatch.setattr(
            temp_module,
            "_windows_create_temp_fd",
            tracked_windows_create_fd,
        )
    else:
        monkeypatch.setattr(temp_module.os, "open", tracked_open)

    def failing_fstat(fd):
        raise OSError("simulated fstat failure")

    monkeypatch.setattr(temp_module.os, "fstat", failing_fstat)


    with pytest.raises(TempCreationError):
        temp_module.create_owned_temp_file(
            tmp_path / "output.bin"
        )

    # Restore the monkeypatches before verifying descriptor state.
    monkeypatch.undo()

    assert len(captured_fds) == 1

    with pytest.raises(OSError):
        real_fstat(captured_fds[0])

    # Identity was not verified, so the primitive must not
    # unlink the file blindly by pathname.
    assert captured_paths[0].exists()

def test_ownership_verification_succeeds_for_untouched_temp(tmp_path):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    try:
        result = verify_temp_ownership(temp)

        assert result.state is OwnershipVerificationState.VERIFIED
        assert result.expected_identity == temp.identity
        assert result.descriptor_identity == temp.identity
        assert result.path_identity == temp.identity
        assert result.error is None
    finally:
        release_temp(temp)


def test_ownership_verification_detects_missing_path(tmp_path):
    import os

    temp = create_owned_temp_file(tmp_path / "output.bin")
    os.close(temp.fd)
    temp.path.unlink()
    result = verify_temp_ownership(temp)

    assert result.state is OwnershipVerificationState.MISSING
    assert result.descriptor_identity is None
    assert result.path_identity is None


def test_ownership_verification_detects_replaced_file(tmp_path):
    import os

    temp = create_owned_temp_file(tmp_path / "output.bin")

    os.close(temp.fd)

    temp.path.unlink()
    temp.path.write_bytes(b"foreign file")

    try:
        result = verify_temp_ownership(temp)

        assert result.state is OwnershipVerificationState.MISMATCH
        assert result.path_identity != temp.identity
    finally:
        temp.path.unlink(missing_ok=True)


def test_ownership_verification_detects_replaced_symlink(tmp_path):
    import os

    temp = create_owned_temp_file(tmp_path / "output.bin")

    target = tmp_path / "foreign-target.txt"
    target.write_text("foreign target", encoding="utf-8")

    os.close(temp.fd)

    temp.path.unlink()

    try:
        temp.path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not supported here.")

    try:
        result = verify_temp_ownership(temp)

        assert result.state is OwnershipVerificationState.MISMATCH
        assert result.path_identity != temp.identity
    finally:
        temp.path.unlink(missing_ok=True)

def test_ownership_verification_detects_closed_descriptor(tmp_path):
    import os

    temp = create_owned_temp_file(tmp_path / "output.bin")

    os.close(temp.fd)

    result = verify_temp_ownership(temp)

    assert result.state is OwnershipVerificationState.UNVERIFIABLE
    assert result.descriptor_identity is None

    # Test owns this fixture; remove the created temp explicitly.
    temp.path.unlink(missing_ok=True)


def test_ownership_verification_rejects_invalid_argument(tmp_path):
    with pytest.raises(TypeError):
        verify_temp_ownership(tmp_path / "not-an-ownership-object")

def test_ownership_verification_detects_foreign_descriptor(
    tmp_path,
):
    destination = tmp_path / "output.bin"
    temp = create_owned_temp_file(destination)

    foreign_path = tmp_path / "foreign.bin"
    foreign_path.write_bytes(b"foreign")

    foreign_fd = os.open(foreign_path, os.O_RDONLY)

    tampered = replace(temp, fd=foreign_fd)

    try:
        result = verify_temp_ownership(tampered)

        assert result.state == OwnershipVerificationState.MISMATCH
        assert result.path_identity == temp.identity
        assert result.descriptor_identity != temp.identity
    finally:
        os.close(foreign_fd)
        release_temp(temp)

def test_ownership_verification_detects_forged_identity(
    tmp_path,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    forged_identity = (
        temp.identity[0] + 1,
        temp.identity[1] + 1,
    )

    tampered = replace(
        temp,
        identity=forged_identity,
    )

    try:
        result = verify_temp_ownership(tampered)

        assert result.state == OwnershipVerificationState.MISMATCH
        assert result.path_identity == temp.identity
        assert result.expected_identity == forged_identity
    finally:
        release_temp(temp)