
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from src.transformations.validation.models import (
    ValidationResult,
    ValidationStatus,
)


class SyntaxValidator:
    def __init__(
        self,
        compiler: str = "clang++",
        standard: str = "c++17",
        timeout_seconds: int = 10,
    ) -> None:
        self.compiler = compiler
        self.standard = standard
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "V3_SYNTAX"

    def validate(self, candidate: str) -> ValidationResult:
        compiler_path = shutil.which(self.compiler)

        if compiler_path is None:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.ERROR,
                reason_codes=("COMPILER_UNAVAILABLE",),
                message="Configured C++ compiler was not found.",
                details={
                    "compiler": self.compiler,
                },
            )

        try:
            with tempfile.TemporaryDirectory(
                prefix="codesim_variant_"
            ) as temp_dir:
                source_path = Path(temp_dir) / "candidate.cpp"
                source_path.write_text(
                    candidate,
                    encoding="utf-8",
                    newline="",
                )

                command = [
                    compiler_path,
                    f"-std={self.standard}",
                    "-fsyntax-only",
                    "-x",
                    "c++",
                    str(source_path),
                ]

                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )

                if completed.returncode == 0:
                    return ValidationResult(
                        validator_name=self.name,
                        status=ValidationStatus.PASS,
                        message="C++ syntax validation passed.",
                    )

                return ValidationResult(
                    validator_name=self.name,
                    status=ValidationStatus.FAIL,
                    reason_codes=("SYNTAX_ERROR",),
                    message="Compiler rejected candidate syntax.",
                    details={
                        "return_code": completed.returncode,
                        "stderr": completed.stderr[-4000:],
                    },
                )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.ERROR,
                reason_codes=("VALIDATION_TIMEOUT",),
                message="Syntax validation timed out.",
                details={
                    "timeout_seconds": self.timeout_seconds,
                },
            )

        except OSError as exc:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.ERROR,
                reason_codes=("COMPILER_EXECUTION_ERROR",),
                message="Compiler could not be executed.",
                details={
                    "exception_type": type(exc).__name__,
                },
            )
