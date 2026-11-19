
from unittest.mock import Mock

import subprocess

from src.transformations.validation import (
    SyntaxValidator,
    ValidationStatus,
)


def test_compiler_unavailable(monkeypatch):
    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.shutil.which",
        lambda _: None,
    )

    result = SyntaxValidator().validate("int main() {}\n")

    assert result.status == ValidationStatus.ERROR
    assert "COMPILER_UNAVAILABLE" in result.reason_codes


def test_syntax_passes(monkeypatch):
    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.shutil.which",
        lambda _: "/usr/bin/clang++",
    )

    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=0,
            stderr="",
        ),
    )

    result = SyntaxValidator().validate("int main() {}\n")

    assert result.status == ValidationStatus.PASS


def test_syntax_error_fails(monkeypatch):
    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.shutil.which",
        lambda _: "/usr/bin/clang++",
    )

    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=1,
            stderr="error: expected ';'",
        ),
    )

    result = SyntaxValidator().validate("int main() { broken }\n")

    assert result.status == ValidationStatus.FAIL
    assert "SYNTAX_ERROR" in result.reason_codes


def test_timeout_returns_error(monkeypatch):
    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.shutil.which",
        lambda _: "/usr/bin/clang++",
    )

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="clang++",
            timeout=10,
        )

    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.subprocess.run",
        timeout,
    )

    result = SyntaxValidator().validate("int main() {}\n")

    assert result.status == ValidationStatus.ERROR
    assert "VALIDATION_TIMEOUT" in result.reason_codes


def test_compiler_execution_error_returns_error(monkeypatch):
    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.shutil.which",
        lambda _: "/usr/bin/clang++",
    )

    def raise_os_error(*args, **kwargs):
        raise OSError("cannot execute compiler")

    monkeypatch.setattr(
        "src.transformations.validation.v3_syntax.subprocess.run",
        raise_os_error,
    )

    result = SyntaxValidator().validate("int main() {}\n")

    assert result.status == ValidationStatus.ERROR
    assert "COMPILER_EXECUTION_ERROR" in result.reason_codes
