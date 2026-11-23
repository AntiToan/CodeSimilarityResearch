
import os
from pathlib import Path
import pytest
from src.safety.persistence_temp import (
    AtomicCommitMode,
    AtomicCommitOutcome,
    PreCommitGateState,
    commit_owned_temp_file,
    create_owned_temp_file,
    evaluate_pre_commit_gate,
    sync_owned_temp_file,
    write_owned_temp_bytes,
)
from src.safety.persistence_temp import (
    verify_temp_ownership,
    OwnershipVerificationState
)


def test_fail_if_exists_commit_succeeds(tmp_path):
    destination = tmp_path / "artifact.bin"
    payload = b"atomic-commit-test"

    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(ownership, payload)
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.exists()
        assert destination.read_bytes() == payload

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_replace_commit_succeeds_and_replaces_existing_content(tmp_path):
    destination = tmp_path / "artifact.bin"
    destination.write_bytes(b"old-content")

    payload = b"new-atomic-content"
    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(ownership, payload)
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.REPLACE,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.read_bytes() == b"new-atomic-content"
        assert not ownership.path.exists()

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)



def test_fail_if_exists_commit_does_not_overwrite_existing_destination(
    tmp_path,
):
    destination = tmp_path / "artifact.bin"
    old_payload = b"old-content"
    new_payload = b"new-atomic-content"

    # Pre-existing destination.
    destination.write_bytes(old_payload)

    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            new_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(new_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Existing destination must not be overwritten.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED
        assert destination.exists()
        assert destination.read_bytes() == old_payload

        # Temp file must remain available after rejection.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == new_payload

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_commit_is_blocked_when_pre_commit_gate_is_denied(
    tmp_path,
    monkeypatch,
):
    from src.safety.persistence_temp import (
        PreCommitGateResult,
        PreCommitGateState,
        PreCommitDenialReason,
    )

    destination = tmp_path / "artifact.bin"
    payload = b"gate-denied-payload"

    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def forbidden_link(*args, **kwargs):
        mutation_calls.append("link")
        raise AssertionError("os.link must not be called when gate is denied")

    def forbidden_replace(*args, **kwargs):
        mutation_calls.append("replace")
        raise AssertionError("os.replace must not be called when gate is denied")

    monkeypatch.setattr(os, "link", forbidden_link)
    monkeypatch.setattr(os, "replace", forbidden_replace)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = PreCommitGateResult(
            state=PreCommitGateState.DENIED,
            reason=PreCommitDenialReason.SYNC_NOT_COMPLETED,
        )

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Denied gate must reject the commit.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED

        # No destination mutation.
        assert not destination.exists()

        # Temp file must remain intact.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == payload

        # Neither atomic mutation operation may be invoked.
        assert mutation_calls == []

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_commit_is_blocked_when_temp_ownership_mismatches(
    tmp_path,
):
    import os

    destination = tmp_path / "artifact.bin"
    payload = b"original-owned-payload"
    replacement_payload = b"replacement-unowned-payload"

    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        # Replace the temp pathname with an unowned file.
        ownership.path.unlink()
        ownership.path.write_bytes(replacement_payload)

        verification = verify_temp_ownership(ownership)

        assert verification.state is OwnershipVerificationState.MISMATCH

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Ownership mismatch must block commit.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED

        # Destination must not be created.
        assert not destination.exists()

        # The replacement file must remain untouched.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == replacement_payload

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_commit_is_blocked_when_temp_path_is_missing(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    payload = b"temp-missing-payload"

    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def forbidden_link(*args, **kwargs):
        mutation_calls.append("link")
        raise AssertionError("os.link must not be called")

    def forbidden_replace(*args, **kwargs):
        mutation_calls.append("replace")
        raise AssertionError("os.replace must not be called")

    monkeypatch.setattr(os, "link", forbidden_link)
    monkeypatch.setattr(os, "replace", forbidden_replace)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        # Simulate the temp pathname disappearing after the gate.
        ownership.path.unlink()

        verification = verify_temp_ownership(ownership)

        assert verification.state is OwnershipVerificationState.MISSING

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED
        assert not destination.exists()
        assert not ownership.path.exists()
        assert mutation_calls == []

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_commit_is_blocked_when_ownership_is_unverifiable(
    tmp_path,
    monkeypatch,
):
    import src.safety.persistence_temp as temp_module

    destination = tmp_path / "artifact.bin"
    payload = b"unverifiable-ownership-payload"

    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def forbidden_link(*args, **kwargs):
        mutation_calls.append("link")
        raise AssertionError("os.link must not be called")

    def forbidden_replace(*args, **kwargs):
        mutation_calls.append("replace")
        raise AssertionError("os.replace must not be called")

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        # Inject fstat failure only during commit-time verification.
        monkeypatch.setattr(
            temp_module.os,
            "fstat",
            lambda fd: (_ for _ in ()).throw(
                OSError("simulated descriptor verification failure")
            ),
        )
        monkeypatch.setattr(os, "link", forbidden_link)
        monkeypatch.setattr(os, "replace", forbidden_replace)

        verification = verify_temp_ownership(ownership)

        assert verification.state is OwnershipVerificationState.UNVERIFIABLE

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED
        assert not destination.exists()

        assert ownership.path.exists()
        assert ownership.path.read_bytes() == payload

        assert mutation_calls == []

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_atomic_mutation_oserror_returns_outcome_unknown(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    payload = b"atomic-mutation-error-payload"

    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def failing_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))
        raise PermissionError("simulated atomic link failure")

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", failing_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # An OSError during atomic mutation must not be
        # reported as definite success or definite rejection.
        assert result.outcome is AtomicCommitOutcome.OUTCOME_UNKNOWN

        # The original error must be preserved in the result.
        assert isinstance(result.error, PermissionError)

        # No retry: exactly one mutation attempt.
        assert len(mutation_calls) == 1

        # In this simulated failure, destination was not created.
        assert not destination.exists()

        # Temp remains available; no automatic cleanup.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == payload

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_atomic_mutation_filenotfound_returns_not_committed(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    payload = b"atomic-filenotfound-payload"

    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def failing_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))
        raise FileNotFoundError("simulated atomic link source missing")

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", failing_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # FileNotFoundError is classified as a definite rejection.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED

        # No retry.
        assert len(mutation_calls) == 1

        # Destination remains absent.
        assert not destination.exists()

        # Temp is preserved for explicit recovery/cleanup.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == payload

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_atomic_mutation_fileexists_returns_not_committed(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    old_payload = b"existing-destination-content"
    new_payload = b"atomic-fileexists-payload"

    destination.write_bytes(old_payload)
    ownership = create_owned_temp_file(destination)

    mutation_calls = []

    def failing_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))
        raise FileExistsError("simulated destination collision")

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            new_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(new_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", failing_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # FileExistsError must be classified specifically.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED

        # No retry.
        assert len(mutation_calls) == 1

        # Existing destination must remain untouched.
        assert destination.exists()
        assert destination.read_bytes() == old_payload

        # Temp remains intact.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == new_payload

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_fail_if_exists_handles_destination_race_at_atomic_boundary(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    temp_payload = b"owned-temp-payload"
    racing_payload = b"racing-writer-payload"

    ownership = create_owned_temp_file(destination)

    real_link = os.link
    mutation_calls = []

    def racing_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        # Simulate another actor winning the race
        # immediately before the real atomic link.
        Path(dst).write_bytes(racing_payload)

        # The real link must now fail with FileExistsError.
        return real_link(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            temp_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(temp_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED
        assert not destination.exists()

        monkeypatch.setattr(os, "link", racing_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Late collision must be classified as NOT_COMMITTED.
        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED

        # The racing actor's content must not be overwritten.
        assert destination.exists()
        assert destination.read_bytes() == racing_payload

        # Only one atomic mutation attempt; no retry.
        assert len(mutation_calls) == 1

        # Our owned temp file remains intact.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == temp_payload

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_replace_handles_destination_race_at_atomic_boundary(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    temp_payload = b"owned-temp-payload"
    racing_payload = b"racing-writer-payload"

    ownership = create_owned_temp_file(destination)

    real_replace = os.replace
    mutation_calls = []

    def racing_replace(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        # Simulate another actor creating the destination
        # immediately before our atomic replace.
        Path(dst).write_bytes(racing_payload)

        # REPLACE semantics intentionally replace the racing file.
        return real_replace(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            temp_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(temp_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED
        assert not destination.exists()

        monkeypatch.setattr(os, "replace", racing_replace)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.REPLACE,
            gate=gate,
        )

        # REPLACE mode should commit despite the late destination.
        assert result.outcome is AtomicCommitOutcome.COMMITTED

        # Our temp content replaces the racing writer's content.
        assert destination.exists()
        assert destination.read_bytes() == temp_payload
        assert destination.read_bytes() != racing_payload

        # The temp pathname should be consumed by replace.
        assert not ownership.path.exists()

        # Exactly one atomic mutation attempt.
        assert len(mutation_calls) == 1

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_path_substitution_after_verification_exposes_toctou(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    owned_payload = b"original-owned-payload"
    substituted_payload = b"substituted-unowned-payload"

    ownership = create_owned_temp_file(destination)
    real_link = os.link
    mutation_calls = []

    def substitute_then_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        # Ownership has already been verified by commit.
        # Substitute the pathname immediately before the
        # actual atomic link operation.
        Path(src).unlink()
        Path(src).write_bytes(substituted_payload)

        return real_link(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", substitute_then_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Characterize the currently known TOCTOU limitation:
        # verification succeeded before pathname substitution.
        assert result.outcome is AtomicCommitOutcome.COMMITTED

        assert destination.exists()
        assert destination.read_bytes() == substituted_payload
        assert destination.read_bytes() != owned_payload

        assert len(mutation_calls) == 1

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)

def test_atomic_mutation_succeeds_then_raises_outcome_unknown(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    payload = b"mutation-completed-before-error"

    ownership = create_owned_temp_file(destination)

    real_link = os.link
    mutation_calls = []

    def link_then_raise(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        # Perform the real atomic mutation first.
        real_link(src, dst, *args, **kwargs)

        # Simulate an error reported after mutation occurred.
        raise PermissionError("simulated post-mutation error")

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", link_then_raise)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # The API cannot claim certainty after the injected error.
        assert result.outcome is AtomicCommitOutcome.OUTCOME_UNKNOWN
        assert isinstance(result.error, PermissionError)

        # Mutation actually happened before the error.
        assert destination.exists()
        assert destination.read_bytes() == payload

        # No retry.
        assert len(mutation_calls) == 1

        # Hard-link commit leaves the owned temp path present.
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == payload

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_path_symlink_substitution_at_mutation_boundary(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    attacker_target = tmp_path / "attacker.bin"

    owned_payload = b"original-owned-payload"
    attacker_payload = b"attacker-controlled-payload"

    attacker_target.write_bytes(attacker_payload)
    ownership = create_owned_temp_file(destination)

    real_link = os.link
    mutation_calls = []

    def substitute_with_symlink_then_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        Path(src).unlink()
        try:
            Path(src).symlink_to(attacker_target)
        except OSError as exc:
            pytest.skip(f"Symlink creation unavailable on this platform: {exc}")

        return real_link(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", substitute_with_symlink_then_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Characterize behavior when temp pathname becomes a symlink.
        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.exists()
        assert destination.read_bytes() == attacker_payload
        assert destination.read_bytes() != owned_payload
        assert len(mutation_calls) == 1

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_path_hardlink_substitution_at_mutation_boundary(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"
    attacker_target = tmp_path / "attacker.bin"

    owned_payload = b"original-owned-payload"
    attacker_payload = b"attacker-controlled-payload"

    attacker_target.write_bytes(attacker_payload)
    ownership = create_owned_temp_file(destination)

    real_link = os.link
    mutation_calls = []

    def substitute_with_hardlink_then_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        Path(src).unlink()
        real_link(attacker_target, src)

        return real_link(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(
            os,
            "link",
            substitute_with_hardlink_then_link,
        )

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Characterize the hard-link pathname substitution exposure.
        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.exists()
        assert destination.read_bytes() == attacker_payload
        assert destination.read_bytes() != owned_payload
        assert len(mutation_calls) == 1

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_path_hardlink_substitution_before_verification_is_blocked(
    tmp_path,
):
    destination = tmp_path / "artifact.bin"
    attacker_target = tmp_path / "attacker.bin"

    owned_payload = b"original-owned-payload"
    attacker_payload = b"attacker-controlled-payload"

    attacker_target.write_bytes(attacker_payload)
    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        # Substitute the temp pathname BEFORE ownership verification.
        ownership.path.unlink()
        os.link(attacker_target, ownership.path)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        # Ownership verification should detect the substitution.
        assert gate.state is not PreCommitGateState.PASSED

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.NOT_COMMITTED
        assert not destination.exists()
        assert ownership.path.exists()
        assert ownership.path.read_bytes() == attacker_payload

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_content_mutation_after_gate_before_commit(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "artifact.bin"

    owned_payload = b"original-owned-payload"
    mutated_payload = b"X" * len(owned_payload)

    ownership = create_owned_temp_file(destination)
    real_link = os.link
    mutation_calls = []

    def mutate_content_then_link(src, dst, *args, **kwargs):
        mutation_calls.append((src, dst))

        # Preserve pathname and file identity, but mutate content.
        Path(src).write_bytes(mutated_payload)

        return real_link(src, dst, *args, **kwargs)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        assert gate.state is PreCommitGateState.PASSED

        monkeypatch.setattr(os, "link", mutate_content_then_link)

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        # Characterize content-integrity exposure at mutation boundary.
        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.exists()
        assert destination.read_bytes() == mutated_payload
        assert destination.read_bytes() != owned_payload
        assert len(mutation_calls) == 1

    finally:
        monkeypatch.undo()
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)


def test_temp_content_mutation_after_sync_before_gate(
    tmp_path,
):
    destination = tmp_path / "artifact.bin"

    owned_payload = b"original-owned-payload"
    mutated_payload = b"modified-owned-payload"

    assert len(owned_payload) == len(mutated_payload)

    ownership = create_owned_temp_file(destination)

    try:
        bytes_written = write_owned_temp_bytes(
            ownership,
            owned_payload,
        )
        sync_owned_temp_file(ownership)

        # Mutate content after sync, before gate evaluation.
        ownership.path.write_bytes(mutated_payload)

        gate = evaluate_pre_commit_gate(
            ownership=ownership,
            expected_bytes=len(owned_payload),
            bytes_written=bytes_written,
            sync_completed=True,
        )

        # Characterize whether the gate accepts same-length mutation.
        assert gate.state is PreCommitGateState.PASSED

        result = commit_owned_temp_file(
            ownership=ownership,
            destination=destination,
            mode=AtomicCommitMode.FAIL_IF_EXISTS,
            gate=gate,
        )

        assert result.outcome is AtomicCommitOutcome.COMMITTED
        assert destination.read_bytes() == mutated_payload
        assert destination.read_bytes() != owned_payload

    finally:
        os.close(ownership.fd)
        ownership.path.unlink(missing_ok=True)
