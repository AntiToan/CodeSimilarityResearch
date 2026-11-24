from pathlib import Path

import pytest

from src.safety.safe_persistence import (
    CollisionMode,
    CommitState,
    CleanupState,
    DurabilityState,
    PersistenceStatus,
    SafePersistence,
    VerificationState,
)


def persist(destination, payload=b"data", root=None, **kwargs):
    return SafePersistence.persist_bytes(
        destination=destination,
        payload=payload,
        authorized_root=root,
        collision_mode=kwargs.get(
            "collision_mode",
            CollisionMode.FAIL_IF_EXISTS,
        ),
        validator=kwargs.get("validator"),
        verification_required=kwargs.get(
            "verification_required",
            False,
        ),
    )


def test_rejects_destination_outside_authorized_root(tmp_path):
    root = tmp_path / "authorized"
    outside = tmp_path / "outside"

    root.mkdir()
    outside.mkdir()

    destination = outside / "artifact.bin"

    result = persist(destination, root=root)

    assert result.status is PersistenceStatus.REJECTED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert result.bytes_written == 0
    assert not destination.exists()


def test_rejects_authorized_root_itself(tmp_path):
    root = tmp_path / "output"
    root.mkdir()

    result = persist(root, root=root)

    assert result.status is PersistenceStatus.REJECTED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert result.bytes_written == 0


def test_rejects_directory_as_destination(tmp_path):
    root = tmp_path / "output"
    destination = root / "folder"

    root.mkdir()
    destination.mkdir()

    result = persist(destination, root=root)

    assert result.status is PersistenceStatus.REJECTED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert destination.is_dir()


def test_rejects_leaf_symlink(tmp_path):
    root = tmp_path / "output"
    root.mkdir()

    target = root / "real.bin"
    target.write_bytes(b"original")

    link = root / "link.bin"

    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable on this platform.")

    result = persist(link, root=root)

    assert result.status is PersistenceStatus.REJECTED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert target.read_bytes() == b"original"


@pytest.mark.parametrize(
    "payload",
    [
        "text",
        bytearray(b"bytes"),
        None,
        123,
    ],
)
def test_rejects_non_bytes_payload(tmp_path, payload):
    root = tmp_path / "output"
    root.mkdir()

    destination = root / "artifact.bin"

    with pytest.raises(TypeError):
        persist(destination, payload=payload, root=root)

    assert not destination.exists()


@pytest.mark.parametrize(
    "destination",
    [
        "output/file.bin",
        None,
        123,
    ],
)
def test_rejects_invalid_destination_type(tmp_path, destination):
    root = tmp_path / "output"
    root.mkdir()

    with pytest.raises(TypeError):
        persist(destination, root=root)


@pytest.mark.parametrize(
    "root",
    [
        "output",
        None,
        123,
    ],
)
def test_rejects_invalid_root_type(tmp_path, root):
    destination = tmp_path / "output" / "file.bin"

    with pytest.raises(TypeError):
        persist(destination, root=root)


def test_rejects_invalid_collision_mode(tmp_path):
    root = tmp_path / "output"
    root.mkdir()

    with pytest.raises(TypeError):
        persist(
            root / "file.bin",
            root=root,
            collision_mode="replace",
        )


@pytest.mark.parametrize("verification_required", [0, 1, "yes", None])
def test_rejects_non_boolean_verification_flag(
    tmp_path,
    verification_required,
):
    root = tmp_path / "output"
    root.mkdir()

    with pytest.raises(TypeError):
        persist(
            root / "file.bin",
            root=root,
            verification_required=verification_required,
        )


def test_rejects_non_callable_validator(tmp_path):
    root = tmp_path / "output"
    root.mkdir()

    with pytest.raises(TypeError):
        persist(
            root / "file.bin",
            root=root,
            validator="not callable",
        )


def test_rejection_does_not_create_files(tmp_path):
    root = tmp_path / "output"
    root.mkdir()

    before = set(root.iterdir())

    result = persist(
        tmp_path / "outside.bin",
        root=root,
    )

    after = set(root.iterdir())

    assert result.status is PersistenceStatus.REJECTED
    assert after == before


# def test_valid_target_still_has_no_persistence_engine(tmp_path):
#     root = tmp_path / "output"
#     root.mkdir()

#     destination = root / "artifact.bin"

#     with pytest.raises(NotImplementedError):
#         persist(destination, root=root)

#     assert not destination.exists()
#     assert list(root.iterdir()) == []