"""Shared bookkeeping for Phase II scripts: configs, run folders, provenance, test log."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
TEST_LOG_NAME = "test_runs.log"


class ExperimentError(ValueError):
    """Raised when a run would break a project rule (frozen data, no overwrite, test log)."""


def utf8_console() -> None:
    """Write stdout/stderr as UTF-8 so Vietnamese paths print on Windows.

    A redirected Windows console defaults to cp1252, and printing a path such
    as "Sv Nghiên Cứu Khoa Học" would crash a script after its results were
    already written.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        raise ExperimentError(f"Config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def resolve_dataset_version(config: Mapping[str, Any], allow_unfrozen: bool) -> str:
    """Rule 16: Phase II only uses a frozen dataset, identified by its version tag."""
    version = config.get("dataset_version")
    if version:
        if not SAFE_NAME.match(str(version)):
            raise ExperimentError("dataset_version may only contain letters, digits, '.', '_', '-'.")
        return str(version)
    if allow_unfrozen:
        return "unfrozen"
    raise ExperimentError(
        "dataset_version is empty: fill it in after the pair dataset is frozen "
        "(rule 16), or pass --allow-unfrozen for a smoke test."
    )


def planned_run_dir(output_root: str | Path, run_id: str) -> Path:
    """Path of a new run folder; refuses to reuse an existing run."""
    if not SAFE_NAME.match(run_id):
        raise ExperimentError("run_id may only contain letters, digits, '.', '_' and '-'.")
    run_dir = Path(output_root) / run_id
    if run_dir.exists():
        raise ExperimentError(f"{run_dir} already exists; use a new --run-id.")
    return run_dir


def git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError:
        return None
    return completed.stdout.strip() or None


def environment() -> dict[str, Any]:
    info: dict[str, Any] = {"python": platform.python_version()}
    try:
        import torch

        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        info["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except ImportError:
        info["torch"] = None
    try:
        import transformers

        info["transformers"] = transformers.__version__
    except ImportError:
        info["transformers"] = None
    return info


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_validation_threshold(path: str | Path) -> tuple[float, str]:
    """Threshold from a validation result (metrics.json, tuning_report.json or bi_encoder.json).

    Refuses thresholds that were not selected on the validation split (rule 10).
    """
    source = Path(path)
    data = load_config(source)
    if "best_trial" in data:  # tuning_report.json
        data = {
            "threshold": (data["best_trial"] or {}).get("best_threshold"),
            "threshold_selected_on": "validation",
        }
    threshold = data.get("threshold")
    selected_on = data.get("threshold_selected_on")
    if threshold is None:
        raise ExperimentError(f"{source} has no threshold.")
    if selected_on != "validation":
        raise ExperimentError(f"{source}: threshold was not selected on validation.")
    return float(threshold), str(source)


def log_test_run(output_root: str | Path, entry: Mapping[str, Any]) -> Path:
    """Append one JSON line per test-split run (rule 10)."""
    log_path = Path(output_root) / TEST_LOG_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(entry), ensure_ascii=False) + "\n")
    return log_path
