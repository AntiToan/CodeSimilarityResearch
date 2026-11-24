"""Pair-classification metrics and threshold selection (II.5, II.7; reused in Phase III).

Convention: a pair is predicted *similar* when ``score >= threshold``.
Thresholds are chosen on the validation split only, then frozen before any
test run (CLAUDE.md, rule 10).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


class MetricError(ValueError):
    """Raised when labels or scores cannot be evaluated safely."""


@dataclass(frozen=True)
class ThresholdChoice:
    threshold: float
    f1: float
    precision: float
    recall: float

    def to_dict(self) -> dict:
        return asdict(self)


def _validate(labels: Sequence[int], scores: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(labels)
    s = np.asarray(scores, dtype=np.float64)
    if y.ndim != 1 or s.ndim != 1:
        raise MetricError("labels and scores must be one-dimensional.")
    if y.size == 0:
        raise MetricError("labels must not be empty.")
    if y.size != s.size:
        raise MetricError(f"{y.size} labels but {s.size} scores.")
    if not np.isin(y, (0, 1)).all():
        raise MetricError("labels must be 0 or 1.")
    if not np.isfinite(s).all():
        raise MetricError("scores must be finite.")
    return y.astype(np.int64), s


def confusion_counts(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> dict[str, int]:
    y, s = _validate(labels, scores)
    predicted = s >= threshold
    positive = y == 1
    return {
        "tp": int(np.sum(predicted & positive)),
        "fp": int(np.sum(predicted & ~positive)),
        "tn": int(np.sum(~predicted & ~positive)),
        "fn": int(np.sum(~predicted & positive)),
    }


def _ratio(numerator: int, denominator: int) -> float:
    # Undefined ratios (no predicted / no actual positives) are reported as 0.0.
    return numerator / denominator if denominator else 0.0


def classification_metrics(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> dict[str, float | int]:
    counts = confusion_counts(labels, scores, threshold)
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return {
        "threshold": float(threshold),
        **counts,
        "precision": precision,
        "recall": recall,
        "f1": _ratio(2 * tp, 2 * tp + fp + fn),
        "accuracy": _ratio(tp + tn, tp + fp + tn + fn),
    }


def _require_both_classes(y: np.ndarray) -> None:
    if y.min() == y.max():
        raise MetricError("ROC-AUC and average precision need both labels present.")


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    from sklearn.metrics import roc_auc_score

    y, s = _validate(labels, scores)
    _require_both_classes(y)
    return float(roc_auc_score(y, s))


def average_precision(labels: Sequence[int], scores: Sequence[float]) -> float:
    from sklearn.metrics import average_precision_score

    y, s = _validate(labels, scores)
    _require_both_classes(y)
    return float(average_precision_score(y, s))


def select_threshold(labels: Sequence[int], scores: Sequence[float]) -> ThresholdChoice:
    """Threshold with the highest F1, searched over every distinct score.

    Ties go to the *highest* threshold: fewer pairs are flagged for the
    teacher, i.e. fewer false alarms at equal F1. Deterministic.
    """
    y, s = _validate(labels, scores)
    positives = int(y.sum())
    if positives == 0:
        raise MetricError("Cannot choose an F1 threshold without positive pairs.")

    order = np.argsort(-s, kind="stable")
    sorted_scores = s[order]
    cum_tp = np.cumsum(y[order])
    cum_fp = np.cumsum(1 - y[order])
    # Last index of each run of equal scores = predict positive for score >= value.
    last = np.flatnonzero(np.r_[sorted_scores[1:] != sorted_scores[:-1], True])
    tp = cum_tp[last]
    fp = cum_fp[last]
    f1 = 2 * tp / (tp + fp + positives)
    best = int(np.argmax(f1))  # first maximum = highest threshold among ties
    return ThresholdChoice(
        threshold=float(sorted_scores[last[best]]),
        f1=float(f1[best]),
        precision=float(tp[best] / (tp[best] + fp[best])),
        recall=float(tp[best] / positives),
    )


def evaluate_scores(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> dict[str, float | int]:
    """Threshold-free (ROC-AUC, AP) and thresholded metrics in one dict."""
    y, s = _validate(labels, scores)
    return {
        "pairs": int(y.size),
        "positives": int(y.sum()),
        "negatives": int(y.size - y.sum()),
        "roc_auc": roc_auc(y, s),
        "average_precision": average_precision(y, s),
        **classification_metrics(y, s, threshold),
    }
