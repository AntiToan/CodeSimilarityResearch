import os
import pytest

from src.safety.persistence_temp import (
    DirectorySyncState,
    sync_committed_directory,
)


@pytest.mark.skipif(
    os.name == "nt",
    reason="Directory fsync is not supported by this implementation on Windows.",
)
def test_sync_committed_directory_succeeds(tmp_path):
    destination = tmp_path / "artifact.bin"
    destination.write_bytes(b"payload")

    result = sync_committed_directory(destination)

    assert result.state is DirectorySyncState.SYNCED
    assert result.error is None

@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows-specific directory sync behavior.",
)
def test_sync_committed_directory_reports_unsupported_on_windows(
    tmp_path,
):
    destination = tmp_path / "artifact.bin"
    destination.write_bytes(b"payload")

    result = sync_committed_directory(destination)

    assert result.state is DirectorySyncState.UNSUPPORTED
    assert result.error is not None