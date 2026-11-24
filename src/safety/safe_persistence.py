from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from src.safety.persistence_temp import (
    create_owned_temp_file,
    write_owned_temp_bytes,
    sync_owned_temp_file,
    evaluate_pre_commit_gate,
    commit_owned_temp_file,
    cleanup_owned_temp_file,
    TempCleanupOutcome,
    TempWriteError,
    OwnershipVerificationState,
    AtomicCommitMode,
    AtomicCommitOutcome,
    PreCommitDenialReason,
    PreCommitGateResult,
    TempSyncError,
    DirectorySyncState,
    sync_committed_directory,
)
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
    PRESERVED = "preserved"


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

    def __post_init__(self) -> None:
        if type(self.bytes_written) is not int or self.bytes_written < 0:
            raise ValueError("bytes_written must be a non-negative integer.")

        if type(self.verified) is not bool:
            raise TypeError("verified must be bool.")

        if self.verified and (
            self.verification_state is not VerificationState.PASSED
        ):
            raise ValueError(
                "verified requires verification_state PASSED."
            )

        if self.verification_state is VerificationState.PASSED:
            if self.commit_state is not CommitState.COMMITTED:
                raise ValueError(
                    "Verification PASSED requires a committed artifact."
                )

            if not self.verified:
                raise ValueError(
                    "Verification PASSED requires verified=True."
                )

        if (
            self.verification_state is VerificationState.FAILED
            and self.verified
        ):
            raise ValueError(
                "Verification FAILED cannot have verified=True."
            )

        if self.status is PersistenceStatus.COMMITTED:
            if self.commit_state is not CommitState.COMMITTED:
                raise ValueError(
                    "COMMITTED status requires COMMITTED commit_state."
                )

            if self.cleanup_state not in (
                CleanupState.SUCCEEDED,
                CleanupState.NOT_NEEDED,
            ):
                raise ValueError(
                    "COMMITTED status requires completed cleanup."
                )

        if self.status is PersistenceStatus.COMMITTED_WITH_WARNINGS:
            if self.commit_state is not CommitState.COMMITTED:
                raise ValueError(
                    "COMMITTED_WITH_WARNINGS requires COMMITTED commit_state."
                )

            if (
                self.cleanup_state is not CleanupState.FAILED
                and not self.secondary_errors
            ):
                raise ValueError(
                    "COMMITTED_WITH_WARNINGS requires a cleanup failure "
                    "or at least one secondary error."
                )

        if self.status is PersistenceStatus.VERIFY_FAILED:
            if self.verification_state is not VerificationState.FAILED:
                raise ValueError(
                    "VERIFY_FAILED requires failed verification."
                )

        # if self.status is PersistenceStatus.FAILED:
        #     if self.verification_state is VerificationState.PASSED:
        #         raise ValueError(
        #             "FAILED status cannot have PASSED verification."
        #         )

        #     if self.verified:
        #         raise ValueError(
        #             "FAILED status cannot be verified."
        #         )

        if self.status in (
            PersistenceStatus.COMMITTED,
            PersistenceStatus.COMMITTED_WITH_WARNINGS,
        ):
            if self.verification_state is VerificationState.FAILED:
                raise ValueError(
                    "Successful commit statuses cannot have failed verification."
                )

        if self.status is PersistenceStatus.REJECTED:
            if self.commit_state is not CommitState.NOT_COMMITTED:
                raise ValueError(
                    "REJECTED status requires NOT_COMMITTED commit_state."
                )

            if self.temp_path is not None:
                raise ValueError(
                    "REJECTED status cannot have a temp_path."
                )

            if self.cleanup_state is not CleanupState.NOT_NEEDED:
                raise ValueError(
                    "REJECTED status requires NOT_NEEDED cleanup."
                )

        if self.status is PersistenceStatus.REJECTED:
            if self.bytes_written != 0:
                raise ValueError(
                    "REJECTED status requires bytes_written to be 0."
                )

            if self.durability_state is not DurabilityState.NOT_REQUESTED:
                raise ValueError(
                    "REJECTED status requires NOT_REQUESTED durability."
                )

        if self.status is PersistenceStatus.COMMIT_UNKNOWN:
            if self.commit_state is not CommitState.OUTCOME_UNKNOWN:
                raise ValueError(
                    "COMMIT_UNKNOWN requires OUTCOME_UNKNOWN commit_state."
                )

            if self.cleanup_state not in (
                CleanupState.PRESERVED,
                CleanupState.NOT_NEEDED,
                CleanupState.FAILED,
            ):
                raise ValueError(
                    "COMMIT_UNKNOWN requires preserved, unnecessary, "
                    "or failed cleanup."
                )

        if self.status is PersistenceStatus.FAILED:
            if self.commit_state is not CommitState.NOT_COMMITTED:
                raise ValueError(
                    "FAILED status requires NOT_COMMITTED commit_state."
                )


class ArtifactValidator(Protocol):
    def __call__(self, artifact_path: Path) -> bool:
        ...


class SafePersistence:
    """
    Security-oriented persistence boundary.

    Coordinates validated filesystem paths, owned temporary-file
    creation, payload writing, synchronization, pre-commit checks,
    atomic commit, and temporary-file cleanup.

    Artifact validation, post-commit content verification, and
    directory durability handling are implemented. Full pipeline
    integration remains pending.
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
    def _cleanup_temp(
        ownership,
        *,
        preserve_temp: bool = False,
    ) -> tuple[CleanupState, tuple[str, ...]]:
        try:
            result = cleanup_owned_temp_file(
                ownership,
                preserve_temp=preserve_temp,
            )
        except Exception as exc:
            return CleanupState.FAILED, (
                f"Cleanup raised an exception: {exc}",
            )

        if result.outcome is TempCleanupOutcome.CLEANED:
            return CleanupState.SUCCEEDED, ()

        if result.outcome is TempCleanupOutcome.NOT_NEEDED:
            return CleanupState.NOT_NEEDED, ()

        if result.outcome is TempCleanupOutcome.PRESERVED:
            return CleanupState.PRESERVED, ()

        return CleanupState.FAILED, (
            result.error or "Temp cleanup failed.",
        )

    @staticmethod
    def _verify_committed_artifact(
        destination: Path,
        expected_payload: bytes,
    ) -> bool:
        try:
            if not isinstance(destination, Path):
                return False

            if not destination.is_file():
                return False

            actual_payload = destination.read_bytes()

            return actual_payload == expected_payload

        except (OSError, RuntimeError, ValueError):
            return False

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
        ownership = None
        bytes_written = 0

        try:
            ownership = create_owned_temp_file(validated_target.path)

            bytes_written = write_owned_temp_bytes(
                ownership,
                payload,
            )

        except Exception as exc:
            cleanup_state = CleanupState.NOT_NEEDED
            secondary_errors = ()

            if ownership is not None:
                cleanup_state, secondary_errors = (
                    SafePersistence._cleanup_temp(
                        ownership,
                    )
                )

            return PersistenceResult(
                status=PersistenceStatus.FAILED,
                destination=validated_target.path,
                temp_path=(
                    ownership.path
                    if ownership is not None
                    else None
                ),
                commit_state=CommitState.NOT_COMMITTED,
                verification_state=(
                    VerificationState.NOT_RUN
                    if verification_required
                    else VerificationState.NOT_REQUIRED
                ),
                cleanup_state=cleanup_state,
                durability_state=DurabilityState.NOT_REQUESTED,
                bytes_written=(
                    exc.bytes_written
                    if isinstance(exc, TempWriteError)
                    else bytes_written
                ),
                verified=False,
                primary_error=str(exc),
                secondary_errors=secondary_errors,
            )

        if validator is not None:
            try:
                validation_passed = validator(ownership.path)

                if type(validation_passed) is not bool:
                    raise TypeError(
                        "Artifact validator must return bool."
                    )

                if not validation_passed:
                    raise ValueError(
                        "Artifact validation failed."
                    )

            except Exception as exc:
                cleanup_state, secondary_errors = (
                    SafePersistence._cleanup_temp(ownership)
                )

                return PersistenceResult(
                    status=PersistenceStatus.VERIFY_FAILED,
                    destination=validated_target.path,
                    temp_path=ownership.path,
                    commit_state=CommitState.NOT_COMMITTED,
                    verification_state=VerificationState.FAILED,
                    cleanup_state=cleanup_state,
                    durability_state=DurabilityState.NOT_REQUESTED,
                    bytes_written=bytes_written,
                    verified=False,
                    primary_error=str(exc),
                    secondary_errors=secondary_errors,
                )
        sync_completed = False
        durability_state = DurabilityState.NOT_REQUESTED

        try:
            sync_owned_temp_file(ownership)
            sync_completed = True
            durability_state = DurabilityState.DATA_SYNCED

        except TempSyncError as exc:
            cleanup_state, secondary_errors = (
                SafePersistence._cleanup_temp(ownership)
            )

            return PersistenceResult(
                status=PersistenceStatus.FAILED,
                destination=validated_target.path,
                temp_path=ownership.path,
                commit_state=CommitState.NOT_COMMITTED,
                verification_state=(
                    VerificationState.NOT_RUN
                    if verification_required
                    else VerificationState.NOT_REQUIRED
                ),
                cleanup_state=cleanup_state,
                durability_state=DurabilityState.FAILED,
                bytes_written=bytes_written,
                verified=False,
                primary_error=str(exc),
                secondary_errors=secondary_errors,
            )

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=sync_completed,
        )

        if not gate.allowed:
            cleanup_state, secondary_errors = (
                SafePersistence._cleanup_temp(ownership)
            )

            return PersistenceResult(
                status=PersistenceStatus.FAILED,
                destination=validated_target.path,
                temp_path=ownership.path,
                commit_state=CommitState.NOT_COMMITTED,
                verification_state=(
                    VerificationState.NOT_RUN
                    if verification_required
                    else VerificationState.NOT_REQUIRED
                ),
                cleanup_state=cleanup_state,
                durability_state=durability_state,
                bytes_written=bytes_written,
                verified=False,
                primary_error=f"Pre-commit gate denied: {gate.reason}",
                secondary_errors=secondary_errors,
            )

        commit_mode = (
            AtomicCommitMode.FAIL_IF_EXISTS
            if collision_mode is CollisionMode.FAIL_IF_EXISTS
            else AtomicCommitMode.REPLACE
        )

        commit_result = commit_owned_temp_file(
            ownership=ownership,
            destination=validated_target.path,
            mode=commit_mode,
            gate=gate,
        )

        verification_state = (
            VerificationState.NOT_RUN
            if verification_required
            else VerificationState.NOT_REQUIRED
        )
        verified = False
        verification_error = None

        if commit_result.outcome is AtomicCommitOutcome.COMMITTED:
            commit_state = CommitState.COMMITTED

            directory_sync_errors = ()

            directory_sync_result = sync_committed_directory(
                validated_target.path,
            )

            if directory_sync_result.state is DirectorySyncState.SYNCED:
                durability_state = DurabilityState.DIRECTORY_SYNCED

            else:
                durability_state = DurabilityState.PARTIAL

                directory_sync_errors = (
                    directory_sync_result.error
                    or "Directory sync is unsupported.",
                )

            if verification_required:
                verified = SafePersistence._verify_committed_artifact(
                    validated_target.path,
                    payload,
                )

                verification_state = (
                    VerificationState.PASSED
                    if verified
                    else VerificationState.FAILED
                )

                if not verified:
                    verification_error = (
                        "Committed artifact verification failed."
                    )

            cleanup_state, cleanup_errors = (
                SafePersistence._cleanup_temp(ownership)
            )

            secondary_errors = (
                *directory_sync_errors,
                *cleanup_errors,
            )

        elif commit_result.outcome is AtomicCommitOutcome.NOT_COMMITTED:
            commit_state = CommitState.NOT_COMMITTED

            cleanup_state, secondary_errors = (
                SafePersistence._cleanup_temp(ownership)
            )

        else:
            commit_state = CommitState.OUTCOME_UNKNOWN

            cleanup_state, secondary_errors = (
                SafePersistence._cleanup_temp(
                    ownership,
                    preserve_temp=True,
                )
            )

        if verification_state is VerificationState.FAILED:
            status = PersistenceStatus.VERIFY_FAILED

        elif commit_state is CommitState.COMMITTED:
            status = (
                PersistenceStatus.COMMITTED
                if (
                    cleanup_state is not CleanupState.FAILED
                    and not secondary_errors
                )
                else PersistenceStatus.COMMITTED_WITH_WARNINGS
            )

        elif commit_state is CommitState.OUTCOME_UNKNOWN:
            status = PersistenceStatus.COMMIT_UNKNOWN

        else:
            status = PersistenceStatus.FAILED

        return PersistenceResult(
            status=status,
            destination=validated_target.path,
            temp_path=ownership.path,
            commit_state=commit_state,
            verification_state=verification_state,
            verified=verified,
            cleanup_state=cleanup_state,
            durability_state=durability_state,
            bytes_written=bytes_written,
            primary_error=(
                verification_error
                if verification_error is not None
                else commit_result.error
            ),
            secondary_errors=secondary_errors,
        )
