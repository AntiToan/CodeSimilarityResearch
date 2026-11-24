"""Hyperparameter grid for II.5. Trials are compared on the validation split only."""

from __future__ import annotations

import itertools
from typing import Any, Mapping, Sequence


def expand_grid(grid: Mapping[str, Sequence[Any]] | None) -> list[dict[str, Any]]:
    """Cartesian product in the key order given; an empty grid is one trial ``{}``."""
    if not grid:
        return [{}]
    for key, values in grid.items():
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
            raise ValueError(f"Grid entry {key!r} must be a non-empty list.")
    keys = list(grid)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(grid[k] for k in keys))]


def trial_run_id(run_id: str, index: int, total: int) -> str:
    return run_id if total == 1 else f"{run_id}-t{index:02d}"


def best_trial(trials: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Highest validation F1; ties -> lower validation loss -> earlier trial."""
    if not trials:
        raise ValueError("No trials to compare.")
    for trial in trials:
        if trial.get("best_val_f1") is None:
            raise ValueError(f"Trial {trial.get('run_id')} has no validation F1.")
    ranked = sorted(
        enumerate(trials),
        key=lambda item: (-item[1]["best_val_f1"], item[1]["best_val_loss"], item[0]),
    )
    return ranked[0][1]
