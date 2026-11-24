from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.safety.safe_persistence import (
    ArtifactValidator,
    CleanupState,
    CollisionMode,
    CommitState,
    DurabilityState,
    PersistenceResult,
    PersistenceStatus,
    SafePersistence,
    VerificationState,
)


def make_result(**overrides):
    values = {
        "status": PersistenceStatus.COMMITTED,
        "destination": Path("output/artifact.bin"),
        "temp_path": None,
        "commit_state": CommitState.COMMITTED,
        "verification_state": VerificationState.NOT_REQUIRED,
        "cleanup_state": CleanupState.NOT_NEEDED,
        "durability_state": DurabilityState.NOT_REQUESTED,
        "bytes_written": 10,
        "verified": False,
        "primary_error": None,
        "secondary_errors": (),
    }
    values.update(overrides)
    return PersistenceResult(**values)


def test_persistence_result_is_immutable():
    result = make_result()

    with pytest.raises(FrozenInstanceError):
        result.verified = True


def test_secondary_errors_are_tuple():
    result = make_result()

    assert isinstance(result.secondary_errors, tuple)


@pytest.mark.parametrize(
    ("enum_type", "expected_values"),
    [
        (
            CollisionMode,
            {"fail_if_exists", "replace"},
        ),
        (
            CommitState,
            {"not_committed", "committed", "outcome_unknown"},
        ),
        (
            VerificationState,
            {"not_required", "not_run", "passed", "failed"},
        ),
        (
            CleanupState,
            {
                "not_needed",
                "pending",
                "succeeded",
                "failed",
                "preserved",
            },
        ),
        (
            DurabilityState,
            {
                "not_requested",
                "data_synced",
                "directory_synced",
                "partial",
                "failed",
                "unknown",
            },
        ),
        (
            PersistenceStatus,
            {
                "committed",
                "committed_with_warnings",
                "rejected",
                "failed",
                "verify_failed",
                "commit_unknown",
            },
        ),
    ],
)
def test_enum_contract(enum_type, expected_values):
    assert {member.value for member in enum_type} == expected_values


def test_verified_requires_verification_passed():
    result = make_result(
        verification_state=VerificationState.PASSED,
        verified=True,
    )

    assert result.verified is True


def test_unverified_result_is_false_when_verification_not_required():
    result = make_result(
        verification_state=VerificationState.NOT_REQUIRED,
        verified=False,
    )

    assert result.verified is False


def test_validator_protocol_accepts_callable():
    def validator(path: Path) -> bool:
        return path.is_file()

    assert callable(validator)

    # Static typing contract only; Protocol does not enforce runtime validation.
    validator_type: ArtifactValidator = validator
    assert validator_type(Path("artifact.bin")) is False



def test_persist_bytes_commits_payload(tmp_path):
    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"test",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
    )

    assert (
        result.status
        is PersistenceStatus.COMMITTED_WITH_WARNINGS
    )
    assert result.durability_state is DurabilityState.PARTIAL
    assert any(
        "Directory fsync is unsupported" in error
        for error in result.secondary_errors
    )
    assert result.commit_state is CommitState.COMMITTED
    assert result.bytes_written == 4
    assert destination.read_bytes() == b"test"
    assert result.cleanup_state is CleanupState.SUCCEEDED

def test_persist_bytes_accepts_valid_artifact_validator(tmp_path):
    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"
    validator_calls = []

    def validator(artifact_path: Path) -> bool:
        validator_calls.append(artifact_path)
        return artifact_path.read_bytes() == b"test"

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"test",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        validator=validator,
    )

    assert (
        result.status
        is PersistenceStatus.COMMITTED_WITH_WARNINGS
    )

    assert result.durability_state is DurabilityState.PARTIAL
    assert any(
        "Directory fsync is unsupported" in error
        for error in result.secondary_errors
    )
    assert result.commit_state is CommitState.COMMITTED
    assert result.bytes_written == 4
    assert destination.read_bytes() == b"test"
    assert len(validator_calls) == 1
    assert validator_calls[0] != destination

def test_persist_bytes_rejects_invalid_artifact_validator(tmp_path):
    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"invalid",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        validator=lambda artifact_path: False,
    )

    assert result.status is PersistenceStatus.VERIFY_FAILED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert result.verification_state is VerificationState.FAILED
    assert result.bytes_written == 7
    assert not destination.exists()
    assert result.cleanup_state is CleanupState.SUCCEEDED

def test_persist_bytes_rejects_non_bool_validator_result(tmp_path):
    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"test",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        validator=lambda artifact_path: 1,
    )

    assert result.status is PersistenceStatus.VERIFY_FAILED
    assert result.commit_state is CommitState.NOT_COMMITTED
    assert result.verification_state is VerificationState.FAILED
    assert not destination.exists()
    assert result.cleanup_state is CleanupState.SUCCEEDED
    assert "must return bool" in result.primary_error

def test_persist_bytes_verifies_committed_artifact(tmp_path):
    from src.safety.safe_persistence import (
        SafePersistence,
        CollisionMode,
        PersistenceStatus,
        CommitState,
        VerificationState,
        CleanupState,
    )

    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"
    payload = b"test"

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=payload,
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        verification_required=True,
    )

    assert (
        result.status
        is PersistenceStatus.COMMITTED_WITH_WARNINGS
    )
    assert result.durability_state is DurabilityState.PARTIAL
    assert any(
        "Directory fsync is unsupported" in error
        for error in result.secondary_errors
    )
    assert result.commit_state is CommitState.COMMITTED
    assert result.verification_state is VerificationState.PASSED
    assert result.verified is True
    assert result.cleanup_state is CleanupState.SUCCEEDED
    assert destination.read_bytes() == payload

def test_persist_bytes_reports_verification_failure_after_commit(
    tmp_path,
    monkeypatch,
):
    from src.safety.safe_persistence import (
        SafePersistence,
        CollisionMode,
        PersistenceStatus,
        CommitState,
        VerificationState,
        CleanupState,
    )

    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"
    payload = b"test"

    monkeypatch.setattr(
        SafePersistence,
        "_verify_committed_artifact",
        staticmethod(lambda destination, expected_payload: False),
    )

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=payload,
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
        verification_required=True,
    )

    assert result.status is PersistenceStatus.VERIFY_FAILED
    assert result.commit_state is CommitState.COMMITTED
    assert result.verification_state is VerificationState.FAILED
    assert result.verified is False
    assert result.cleanup_state is CleanupState.SUCCEEDED

    # Verification failure must not roll back a committed artifact.
    assert destination.exists()
    assert destination.read_bytes() == payload

    assert result.primary_error == (
        "Committed artifact verification failed."
    )

def test_persistence_result_rejects_verified_without_passed_state():
    import pytest

    from pathlib import Path
    from src.safety.safe_persistence import (
        PersistenceResult,
        PersistenceStatus,
        CommitState,
        VerificationState,
        CleanupState,
        DurabilityState,
    )

    with pytest.raises(ValueError, match="verified requires"):
        PersistenceResult(
            status=PersistenceStatus.COMMITTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.COMMITTED,
            verification_state=VerificationState.FAILED,
            cleanup_state=CleanupState.SUCCEEDED,
            durability_state=DurabilityState.DATA_SYNCED,
            bytes_written=4,
            verified=True,
            primary_error=None,
            secondary_errors=(),
        )

def test_cleanup_temp_maps_preserved_outcome_correctly(monkeypatch):
    from types import SimpleNamespace

    from src.safety.safe_persistence import (
        SafePersistence,
        CleanupState,
    )
    from src.safety.persistence_temp import TempCleanupOutcome

    monkeypatch.setattr(
        "src.safety.safe_persistence.cleanup_owned_temp_file",
        lambda ownership, preserve_temp=False: SimpleNamespace(
            outcome=TempCleanupOutcome.PRESERVED,
            error=None,
        ),
    )

    cleanup_state, secondary_errors = SafePersistence._cleanup_temp(
        ownership=object(),
        preserve_temp=True,
    )

    assert cleanup_state is CleanupState.PRESERVED
    assert secondary_errors == ()

def test_persist_bytes_preserves_temp_when_commit_outcome_unknown(
    tmp_path,
    monkeypatch,
):
    from src.safety.persistence_temp import (
        AtomicCommitOutcome,
        AtomicCommitResult,
    )

    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"

    def fake_commit(*, ownership, destination, mode, gate):
        return AtomicCommitResult(
            outcome=AtomicCommitOutcome.OUTCOME_UNKNOWN,
            mode=mode,
            destination=destination,
            error="Simulated uncertain commit outcome.",
        )

    monkeypatch.setattr(
        "src.safety.safe_persistence.commit_owned_temp_file",
        fake_commit,
    )

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"test",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
    )

    assert result.status is PersistenceStatus.COMMIT_UNKNOWN
    assert result.commit_state is CommitState.OUTCOME_UNKNOWN
    assert result.cleanup_state is CleanupState.PRESERVED
    assert result.temp_path is not None
    assert result.temp_path.exists()
    assert result.temp_path.read_bytes() == b"test"
    assert not destination.exists()

def test_persist_bytes_preserves_temp_when_link_succeeds_then_raises(
    tmp_path,
    monkeypatch,
):
    import os

    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"
    original_link = os.link

    def link_then_raise(source, target, *args, **kwargs):
        original_link(source, target, *args, **kwargs)
        raise OSError("Simulated error after successful link.")

    monkeypatch.setattr(
        "src.safety.persistence_temp.os.link",
        link_then_raise,
    )

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"test",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.FAIL_IF_EXISTS,
    )

    assert result.status is PersistenceStatus.COMMIT_UNKNOWN
    assert result.commit_state is CommitState.OUTCOME_UNKNOWN
    assert result.cleanup_state is CleanupState.PRESERVED

    # The atomic link actually succeeded.
    assert destination.exists()
    assert destination.read_bytes() == b"test"

    # The original temporary file must also be preserved.
    assert result.temp_path is not None
    assert result.temp_path.exists()
    assert result.temp_path.read_bytes() == b"test"

    # Both paths refer to the same underlying file.
    assert os.path.samefile(destination, result.temp_path)

def test_persist_bytes_replace_succeeds_then_raises(
    tmp_path,
    monkeypatch,
):
    import os

    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"
    destination.write_bytes(b"old-content")

    original_replace = os.replace

    def replace_then_raise(source, target, *args, **kwargs):
        original_replace(source, target, *args, **kwargs)
        raise OSError("Simulated error after successful replace.")

    monkeypatch.setattr(
        "src.safety.persistence_temp.os.replace",
        replace_then_raise,
    )

    result = SafePersistence.persist_bytes(
        destination=destination,
        payload=b"new-content",
        authorized_root=authorized_root,
        collision_mode=CollisionMode.REPLACE,
    )

    assert result.status is PersistenceStatus.COMMIT_UNKNOWN
    assert result.commit_state is CommitState.OUTCOME_UNKNOWN

    # Replace actually happened.
    assert destination.exists()
    assert destination.read_bytes() == b"new-content"

    # The temp path was moved to destination.
    assert result.temp_path is not None
    assert not result.temp_path.exists()

    # Cleanup should recognize the missing temp path.
    assert result.cleanup_state is CleanupState.NOT_NEEDED

def test_committed_with_warnings_requires_actual_warning():
    with pytest.raises(
        ValueError,
        match="COMMITTED_WITH_WARNINGS requires a cleanup failure",
    ):
        PersistenceResult(
            status=PersistenceStatus.COMMITTED_WITH_WARNINGS,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.SUCCEEDED,
            durability_state=DurabilityState.DATA_SYNCED,
            bytes_written=4,
            verified=False,
            primary_error=None,
            secondary_errors=(),
        )

@pytest.mark.parametrize(
    "cleanup_state",
    [
        CleanupState.PENDING,
        CleanupState.FAILED,
        CleanupState.PRESERVED,
    ],
)
def test_committed_rejects_incomplete_cleanup(cleanup_state):
    with pytest.raises(
        ValueError,
        match="COMMITTED status requires completed cleanup",
    ):
        PersistenceResult(
            status=PersistenceStatus.COMMITTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=cleanup_state,
            durability_state=DurabilityState.DATA_SYNCED,
            bytes_written=4,
            verified=False,
            primary_error=None,
            secondary_errors=(),
        )

@pytest.mark.parametrize(
    "cleanup_state",
    [
        CleanupState.SUCCEEDED,
        CleanupState.PENDING,
    ],
)
def test_commit_unknown_rejects_inconsistent_cleanup(cleanup_state):
    with pytest.raises(
        ValueError,
        match="COMMIT_UNKNOWN requires preserved",
    ):
        PersistenceResult(
            status=PersistenceStatus.COMMIT_UNKNOWN,
            destination=Path("artifact.bin"),
            temp_path=Path("artifact.tmp"),
            commit_state=CommitState.OUTCOME_UNKNOWN,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=cleanup_state,
            durability_state=DurabilityState.DATA_SYNCED,
            bytes_written=4,
            verified=False,
            primary_error="Unknown commit outcome.",
            secondary_errors=(),
        )

@pytest.mark.parametrize(
    "status",
    [
        PersistenceStatus.COMMITTED,
        PersistenceStatus.COMMITTED_WITH_WARNINGS,
    ],
)
def test_successful_commit_status_rejects_failed_verification(status):
    with pytest.raises(
        ValueError,
        match="Successful commit statuses cannot have failed verification",
    ):
        PersistenceResult(
            status=status,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.COMMITTED,
            verification_state=VerificationState.FAILED,
            cleanup_state=(
                CleanupState.FAILED
                if status is PersistenceStatus.COMMITTED_WITH_WARNINGS
                else CleanupState.SUCCEEDED
            ),
            durability_state=DurabilityState.DATA_SYNCED,
            bytes_written=4,
            verified=False,
            primary_error=None,
            secondary_errors=(),
        )

def test_rejected_requires_no_commit_temp_or_cleanup():
    with pytest.raises(
        ValueError,
        match="REJECTED status cannot have a temp_path",
    ):
        PersistenceResult(
            status=PersistenceStatus.REJECTED,
            destination=Path("artifact.bin"),
            temp_path=Path("artifact.tmp"),
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=0,
            verified=False,
            primary_error="Path rejected.",
            secondary_errors=(),
        )

@pytest.mark.parametrize(
    "commit_state",
    [
        CommitState.COMMITTED,
        CommitState.OUTCOME_UNKNOWN,
    ],
)
def test_rejected_rejects_committed_or_unknown_state(commit_state):
    with pytest.raises(
        ValueError,
        match="REJECTED status requires NOT_COMMITTED",
    ):
        PersistenceResult(
            status=PersistenceStatus.REJECTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=commit_state,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=0,
            verified=False,
            primary_error="Path rejected.",
            secondary_errors=(),
        )


def test_rejected_requires_not_needed_cleanup():
    with pytest.raises(
        ValueError,
        match="REJECTED status requires NOT_NEEDED cleanup",
    ):
        PersistenceResult(
            status=PersistenceStatus.REJECTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.SUCCEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=0,
            verified=False,
            primary_error="Path rejected.",
            secondary_errors=(),
        )

@pytest.mark.parametrize(
    "bytes_written",
    [1, 10],
)
def test_rejected_requires_zero_bytes_written(bytes_written):
    with pytest.raises(
        ValueError,
        match="REJECTED status requires bytes_written to be 0",
    ):
        PersistenceResult(
            status=PersistenceStatus.REJECTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=bytes_written,
            verified=False,
            primary_error="Path rejected.",
            secondary_errors=(),
        )


@pytest.mark.parametrize(
    "durability_state",
    [
        DurabilityState.DATA_SYNCED,
        DurabilityState.DIRECTORY_SYNCED,
        DurabilityState.PARTIAL,
        DurabilityState.FAILED,
        DurabilityState.UNKNOWN,
    ],
)
def test_rejected_requires_not_requested_durability(durability_state):
    with pytest.raises(
        ValueError,
        match="REJECTED status requires NOT_REQUESTED durability",
    ):
        PersistenceResult(
            status=PersistenceStatus.REJECTED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=durability_state,
            bytes_written=0,
            verified=False,
            primary_error="Path rejected.",
            secondary_errors=(),
        )

def test_passed_verification_requires_committed_state():
    with pytest.raises(
        ValueError,
        match="Verification PASSED requires a committed artifact",
    ):
        PersistenceResult(
            status=PersistenceStatus.FAILED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.PASSED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=0,
            verified=False,
            primary_error="Persistence failed.",
            secondary_errors=(),
        )


def test_verified_true_requires_passed_verification():
    with pytest.raises(
        ValueError,
        match="verified requires verification_state PASSED",
    ):
        PersistenceResult(
            status=PersistenceStatus.FAILED,
            destination=Path("artifact.bin"),
            temp_path=None,
            commit_state=CommitState.NOT_COMMITTED,
            verification_state=VerificationState.NOT_REQUIRED,
            cleanup_state=CleanupState.NOT_NEEDED,
            durability_state=DurabilityState.NOT_REQUESTED,
            bytes_written=0,
            verified=True,
            primary_error="Persistence failed.",
            secondary_errors=(),
        )

# def test_failed_rejects_verified_true():
#     with pytest.raises(
#         ValueError,
#         match="FAILED status cannot be verified",
#     ):
#         PersistenceResult(
#             status=PersistenceStatus.FAILED,
#             destination=Path("artifact.bin"),
#             temp_path=None,
#             commit_state=CommitState.NOT_COMMITTED,
#             verification_state=VerificationState.NOT_REQUIRED,
#             cleanup_state=CleanupState.NOT_NEEDED,
#             durability_state=DurabilityState.NOT_REQUESTED,
#             bytes_written=0,
#             verified=True,
#             primary_error="Persistence failed.",
#             secondary_errors=(),
#         )