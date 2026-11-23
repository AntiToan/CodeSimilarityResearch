
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.safety.path_safety import (
    PathSafety,
    PathSafetyError,
    PathResolutionError,
    PathContainmentError,
    RootConfigurationError,
    SymlinkPolicyError,
    WriteTargetValidationError,
    PathSafetyResult,
)


def test_exception_hierarchy():
    exceptions = [
        PathResolutionError,
        PathContainmentError,
        RootConfigurationError,
        SymlinkPolicyError,
        WriteTargetValidationError,
    ]

    for exception_type in exceptions:
        assert issubclass(exception_type, PathSafetyError)

def test_path_safety_result_is_immutable():
    result = PathSafetyResult(
        path=Path("C:/output/file.py"),
        root=Path("C:/output"),
        relative_path=Path("file.py"),
    )

    with pytest.raises(FrozenInstanceError):
        result.path = Path("C:/changed.py")

def test_public_api_exists():
    assert callable(PathSafety.canonicalize)
    assert callable(PathSafety.validate_containment)
    assert callable(PathSafety.validate_distinct_roots)
    assert callable(PathSafety.validate_write_target)
