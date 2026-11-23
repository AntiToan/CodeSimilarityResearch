import os

import pytest
from types import SimpleNamespace
from src.safety.persistence_temp import (
    TempWriteError,
    create_owned_temp_file,
    write_owned_temp_bytes,
)
from dataclasses import replace
from src.safety.persistence_temp import (
    TEMP_WRITE_MAX_INTERRUPTED_RETRIES,
    TempWriteError,
    create_owned_temp_file,
    write_owned_temp_bytes,
)

def release_temp(temp):
    try:
        os.close(temp.fd)
    except OSError:
        pass

    try:
        temp.path.unlink(missing_ok=True)
    except OSError:
        pass


def test_write_owned_temp_bytes_writes_payload(tmp_path):
    destination = tmp_path / "output.bin"
    temp = create_owned_temp_file(destination)

    try:
        payload = b"hello safe persistence"

        written = write_owned_temp_bytes(temp, payload)

        assert written == len(payload)
        assert temp.path.read_bytes() == payload
    finally:
        release_temp(temp)


def test_write_owned_temp_bytes_empty_payload(tmp_path):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    try:
        written = write_owned_temp_bytes(temp, b"")

        assert written == 0
        assert temp.path.read_bytes() == b""
    finally:
        release_temp(temp)


def test_write_owned_temp_bytes_multiple_chunks(tmp_path, monkeypatch):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    real_write = os.write
    max_chunk = 3

    def partial_write(fd, data):
        return real_write(fd, data[:max_chunk])

    monkeypatch.setattr(os, "write", partial_write)

    try:
        payload = b"abcdefghij"

        written = write_owned_temp_bytes(temp, payload)

        assert written == len(payload)
        assert temp.path.read_bytes() == payload
    finally:
        monkeypatch.undo()
        release_temp(temp)


def test_write_owned_temp_bytes_retries_interrupted(
    tmp_path,
    monkeypatch,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    real_write = os.write
    state = {"interrupted": False}

    def interrupted_once(fd, data):
        if not state["interrupted"]:
            state["interrupted"] = True
            raise InterruptedError()

        return real_write(fd, data)

    monkeypatch.setattr(os, "write", interrupted_once)

    try:
        payload = b"retry me"

        written = write_owned_temp_bytes(temp, payload)

        assert state["interrupted"] is True
        assert written == len(payload)
        assert temp.path.read_bytes() == payload
    finally:
        monkeypatch.undo()
        release_temp(temp)


def test_write_owned_temp_bytes_zero_write_raises(
    tmp_path,
    monkeypatch,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    monkeypatch.setattr(os, "write", lambda fd, data: 0)

    try:
        with pytest.raises(TempWriteError) as exc_info:
            write_owned_temp_bytes(temp, b"payload")

        assert exc_info.value.bytes_written == 0
    finally:
        monkeypatch.undo()
        release_temp(temp)


def test_write_owned_temp_bytes_oserror_preserves_partial_count(
    tmp_path,
    monkeypatch,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    real_write = os.write
    state = {"calls": 0}

    def fail_after_partial_write(fd, data):
        state["calls"] += 1

        if state["calls"] == 1:
            return real_write(fd, data[:3])

        raise OSError("simulated disk write failure")

    monkeypatch.setattr(os, "write", fail_after_partial_write)

    try:
        with pytest.raises(TempWriteError) as exc_info:
            write_owned_temp_bytes(temp, b"abcdefgh")

        assert exc_info.value.bytes_written == 3
        assert temp.path.read_bytes() == b"abc"
        assert isinstance(exc_info.value.__cause__, OSError)
    finally:
        monkeypatch.undo()
        release_temp(temp)


@pytest.mark.parametrize(
    "ownership,payload",
    [
        (None, b"x"),
        ("invalid", b"x"),
    ],
)
def test_write_owned_temp_bytes_rejects_invalid_ownership(
    ownership,
    payload,
):
    with pytest.raises(TypeError):
        write_owned_temp_bytes(ownership, payload)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "text",
        bytearray(b"x"),
        memoryview(b"x"),
    ],
)
def test_write_owned_temp_bytes_rejects_non_bytes_payload(
    tmp_path,
    payload,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    try:
        with pytest.raises(TypeError):
            write_owned_temp_bytes(temp, payload)
    finally:
        release_temp(temp)

def test_write_owned_temp_bytes_closed_fd_fails(
    tmp_path,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    os.close(temp.fd)

    try:
        with pytest.raises(TempWriteError) as exc_info:
            write_owned_temp_bytes(temp, b"must not be written")

        assert exc_info.value.bytes_written == 0
        assert exc_info.value.__cause__ is None
        assert "unverifiable" in str(exc_info.value).lower()
        assert temp.path.read_bytes() == b""
    finally:
        temp.path.unlink(missing_ok=True)

def test_writer_rejects_foreign_descriptor(tmp_path):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    foreign_path = tmp_path / "foreign.bin"
    foreign_fd = os.open(
        foreign_path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )

    tampered = replace(temp, fd=foreign_fd)

    try:
        with pytest.raises(TempWriteError):
            write_owned_temp_bytes(tampered, b"must not reach foreign file")

        assert foreign_path.read_bytes() == b""
        assert temp.path.read_bytes() == b""
    finally:
        os.close(foreign_fd)
        release_temp(temp)

def test_writer_rejects_substituted_path_identity(
    tmp_path,
    monkeypatch,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    real_lstat = os.lstat

    def substituted_lstat(path):
        result = real_lstat(path)

        if path == temp.path:
            return SimpleNamespace(
                st_dev=result.st_dev + 1,
                st_ino=result.st_ino + 1,
            )

        return result

    monkeypatch.setattr(os, "lstat", substituted_lstat)

    try:
        with pytest.raises(TempWriteError) as exc_info:
            write_owned_temp_bytes(temp, b"must not be written")

        assert exc_info.value.bytes_written == 0
        assert exc_info.value.__cause__ is None
        assert "mismatch" in str(exc_info.value).lower()

        # Descriptor vẫn trỏ file gốc, file phải còn rỗng.
        assert temp.path.read_bytes() == b""
    finally:
        monkeypatch.undo()
        release_temp(temp)

def test_write_owned_temp_bytes_bounds_repeated_interruptions(
    tmp_path,
    monkeypatch,
):
    temp = create_owned_temp_file(tmp_path / "output.bin")

    calls = {"count": 0}

    def always_interrupt(fd, data):
        calls["count"] += 1
        raise InterruptedError("persistent interruption")

    monkeypatch.setattr(os, "write", always_interrupt)

    try:
        with pytest.raises(TempWriteError) as exc_info:
            write_owned_temp_bytes(temp, b"payload")

        assert exc_info.value.bytes_written == 0
        assert isinstance(exc_info.value.__cause__, InterruptedError)
        assert calls["count"] == (
            TEMP_WRITE_MAX_INTERRUPTED_RETRIES + 1
        )
        assert temp.path.read_bytes() == b""
    finally:
        monkeypatch.undo()
        release_temp(temp)