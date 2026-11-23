from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol
from src.safety.path_safety import (
    PathSafety,
    WriteTargetValidationError,
)

class CollisionMode(Enum):
    FAIL_IF_EXISTS = "fail_if_exists"
    REPLACE = "replace"


class CommitState(Enum):
    NOT_COMMITTED = "not_committed"
    COMMITTED = "committed"
    OUTCOME_UNKNOWN = "outcome_unknown"


class VerificationState(Enum):
    NOT_REQUIRED = "not_required"
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


class CleanupState(Enum):
    NOT_NEEDED = "not_needed"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DurabilityState(Enum):
    NOT_REQUESTED = "not_requested"
    DATA_SYNCED = "data_synced"
    DIRECTORY_SYNCED = "directory_synced"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


class PersistenceStatus(Enum):
    COMMITTED = "committed"
    COMMITTED_WITH_WARNINGS = "committed_with_warnings"
    REJECTED = "rejected"
    FAILED = "failed"
    VERIFY_FAILED = "verify_failed"
    COMMIT_UNKNOWN = "commit_unknown"


@dataclass(frozen=True)
class PersistenceResult:
    status: PersistenceStatus
    destination: Path

    temp_path: Path | None

    commit_state: CommitState
    verification_state: VerificationState
    cleanup_state: CleanupState
    durability_state: DurabilityState

    bytes_written: int
    verified: bool

    primary_error: str | None
    secondary_errors: tuple[str, ...]


class ArtifactValidator(Protocol):
    def __call__(self, artifact_path: Path) -> bool:
        ...


class SafePersistence:
    """
    Security-oriented persistence boundary.

    This module currently defines the contract and result model only.
    Filesystem persistence behavior is intentionally unimplemented.
    """

    @staticmethod
    def _validate_inputs(
        *,
        destination: Path,
        payload: bytes,
        authorized_root: Path,
        collision_mode: CollisionMode,
        validator: ArtifactValidator | None,
        verification_required: bool,
    ) -> None:
        if not isinstance(destination, Path):
            raise TypeError("destination must be a Path.")

        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes.")

        if not isinstance(authorized_root, Path):
            raise TypeError("authorized_root must be a Path.")

        if not isinstance(collision_mode, CollisionMode):
            raise TypeError("collision_mode must be a CollisionMode.")

        if validator is not None and not callable(validator):
            raise TypeError("validator must be callable or None.")

        if type(verification_required) is not bool:
            raise TypeError("verification_required must be bool.")

    @staticmethod
    def persist_bytes(
        *,
        destination: Path,
        payload: bytes,
        authorized_root: Path,
        collision_mode: CollisionMode,
        validator: ArtifactValidator | None = None,
        verification_required: bool = False,
    ) -> PersistenceResult:
        SafePersistence._validate_inputs(
            destination=destination,
            payload=payload,
            authorized_root=authorized_root,
            collision_mode=collision_mode,
            validator=validator,
            verification_required=verification_required,
        )

        try:
            validated_target = PathSafety.validate_write_target(
                destination,
                authorized_root,
            )
        except WriteTargetValidationError as exc:
            return PersistenceResult(
                status=PersistenceStatus.REJECTED,
                destination=destination,
                temp_path=None,
                commit_state=CommitState.NOT_COMMITTED,
                verification_state=(
                    VerificationState.NOT_RUN
                    if verification_required
                    else VerificationState.NOT_REQUIRED
                ),
                cleanup_state=CleanupState.NOT_NEEDED,
                durability_state=DurabilityState.NOT_REQUESTED,
                bytes_written=0,
                verified=False,
                primary_error=str(exc),
                secondary_errors=(),
            )
        # No filesystem write operation is implemented here.
        raise NotImplementedError(
            "Persistence engine is not implemented yet."
        )