"""Error analysis for scored pairs (II.8; the same tables feed III.4–III.6).

Input rows are plain mappings with at least ``pair_id``, ``label`` (0/1) and
``score``; any other column (pair_type, generation_method,
transformation_type, problem ids...) can be used as a grouping key.
The analysis only reads scores: it never decides that a pair is plagiarism.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

import numpy as np

from src.evaluation.metrics import MetricError, confusion_counts

QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


def _rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise MetricError("No scored pairs to analyse.")
    clean = []
    for index, row in enumerate(rows):
        for key in ("pair_id", "label", "score"):
            if key not in row:
                raise MetricError(f"Row {index} has no {key!r}.")
        label = int(row["label"])
        score = float(row["score"])
        if label not in (0, 1) or not np.isfinite(score):
            raise MetricError(f"Row {index} has an invalid label or score.")
        clean.append({**row, "label": label, "score": score})
    return clean


def _outcome(label: int, score: float, threshold: float) -> str:
    predicted = score >= threshold
    if predicted:
        return "tp" if label == 1 else "fp"
    return "fn" if label == 1 else "tn"


def _quantiles(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    array = np.asarray(values)
    summary = {f"p{int(q * 100):02d}": float(np.quantile(array, q)) for q in QUANTILES}
    summary.update(min=float(array.min()), max=float(array.max()), mean=float(array.mean()))
    return summary


def error_rows(
    rows: Sequence[Mapping[str, Any]], threshold: float
) -> list[dict[str, Any]]:
    """Every misclassified pair with ``outcome`` (fp/fn) and ``margin`` (score - threshold)."""
    errors = []
    for row in _rows(rows):
        outcome = _outcome(row["label"], row["score"], threshold)
        if outcome in ("fp", "fn"):
            errors.append({**row, "outcome": outcome, "margin": row["score"] - threshold})
    # Most confident mistakes first: high-scoring FP, low-scoring FN.
    errors.sort(key=lambda r: (-abs(r["margin"]), str(r["pair_id"])))
    return errors


def analyze_errors(
    rows: Sequence[Mapping[str, Any]],
    threshold: float,
    group_fields: Sequence[str] = (),
    top_k: int = 50,
) -> dict[str, Any]:
    if top_k < 0:
        raise MetricError("top_k must be >= 0.")
    data = _rows(rows)
    labels = [row["label"] for row in data]
    scores = [row["score"] for row in data]
    errors = error_rows(data, threshold)

    by_group: dict[str, dict[str, dict[str, Any]]] = {}
    for field in group_fields:
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in data:
            buckets[str(row.get(field, "") or "")].append(row)
        table = {}
        for value in sorted(buckets):
            members = buckets[value]
            outcomes = [_outcome(r["label"], r["score"], threshold) for r in members]
            pos = [r["score"] for r in members if r["label"] == 1]
            neg = [r["score"] for r in members if r["label"] == 0]
            wrong = outcomes.count("fp") + outcomes.count("fn")
            table[value] = {
                "pairs": len(members),
                "positives": len(pos),
                "negatives": len(neg),
                "fp": outcomes.count("fp"),
                "fn": outcomes.count("fn"),
                "error_rate": wrong / len(members),
                "mean_score_positive": float(np.mean(pos)) if pos else None,
                "mean_score_negative": float(np.mean(neg)) if neg else None,
            }
        by_group[field] = table

    def top(outcome: str) -> list[dict[str, Any]]:
        return [row for row in errors if row["outcome"] == outcome][:top_k]

    return {
        "threshold": float(threshold),
        "counts": confusion_counts(labels, scores, threshold),
        "score_quantiles": {
            "positive": _quantiles([s for s, y in zip(scores, labels) if y == 1]),
            "negative": _quantiles([s for s, y in zip(scores, labels) if y == 0]),
        },
        "by_group": by_group,
        "top_false_positives": top("fp"),
        "top_false_negatives": top("fn"),
    }
