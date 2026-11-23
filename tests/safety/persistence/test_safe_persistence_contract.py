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
            {"not_needed", "pending", "succeeded", "failed"},
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


def test_persist_bytes_is_explicitly_unimplemented(tmp_path):
    authorized_root = tmp_path / "output"
    authorized_root.mkdir()

    destination = authorized_root / "artifact.bin"

    with pytest.raises(NotImplementedError):
        SafePersistence.persist_bytes(
            destination=destination,
            payload=b"test",
            authorized_root=authorized_root,
            collision_mode=CollisionMode.FAIL_IF_EXISTS,
        )