"""Tests for metrics, threshold selection, error analysis and the tuning grid (II.5–II.8)."""

import random

import numpy as np
import pytest

from src.evaluation.error_analysis import analyze_errors, error_rows
from src.evaluation.metrics import (
    MetricError,
    classification_metrics,
    confusion_counts,
    evaluate_scores,
    roc_auc,
    select_threshold,
)
from src.models.tuning import best_trial, expand_grid, trial_run_id

LABELS = [1, 1, 0, 0, 1]
SCORES = [0.9, 0.4, 0.6, 0.1, 0.8]


# ---------- metrics ----------

def test_confusion_and_metrics_by_hand():
    assert confusion_counts(LABELS, SCORES, 0.5) == {"tp": 2, "fp": 1, "tn": 1, "fn": 1}
    metrics = classification_metrics(LABELS, SCORES, 0.5)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(2 / 3)
    assert metrics["f1"] == pytest.approx(2 / 3)
    assert metrics["accuracy"] == pytest.approx(3 / 5)


def test_score_equal_to_threshold_counts_as_similar():
    assert confusion_counts([1, 0], [0.5, 0.5], 0.5) == {"tp": 1, "fp": 1, "tn": 0, "fn": 0}


def test_undefined_precision_is_zero():
    metrics = classification_metrics([1, 0], [0.1, 0.2], 0.9)
    assert metrics["precision"] == 0.0 and metrics["recall"] == 0.0 and metrics["f1"] == 0.0


def test_roc_auc_matches_sklearn():
    from sklearn.metrics import roc_auc_score

    assert roc_auc(LABELS, SCORES) == pytest.approx(roc_auc_score(LABELS, SCORES))


@pytest.mark.parametrize(
    "labels, scores",
    [
        ([], []),
        ([1, 0], [0.5]),
        ([1, 2], [0.5, 0.6]),
        ([1, 0], [0.5, float("nan")]),
    ],
)
def test_metrics_reject_invalid_inputs(labels, scores):
    with pytest.raises(MetricError):
        confusion_counts(labels, scores, 0.5)


def test_auc_needs_both_classes():
    with pytest.raises(MetricError):
        roc_auc([1, 1], [0.2, 0.3])


def test_evaluate_scores_has_required_metrics():
    report = evaluate_scores(LABELS, SCORES, 0.5)
    for key in ("pairs", "positives", "negatives", "roc_auc", "average_precision",
                "precision", "recall", "f1", "threshold"):
        assert key in report
    assert report["pairs"] == 5 and report["positives"] == 3


# ---------- threshold selection ----------

def brute_force(labels, scores):
    best = None
    for threshold in sorted(set(scores), reverse=True):
        f1 = classification_metrics(labels, scores, threshold)["f1"]
        if best is None or f1 > best[1]:
            best = (threshold, f1)
    return best


def test_select_threshold_matches_brute_force_with_ties():
    rng = random.Random(42)
    for _ in range(50):
        labels = [rng.randint(0, 1) for _ in range(40)]
        labels[0] = 1
        scores = [round(rng.random(), 1) for _ in range(40)]  # many ties
        choice = select_threshold(labels, scores)
        threshold, f1 = brute_force(labels, scores)
        assert choice.threshold == threshold
        assert choice.f1 == pytest.approx(f1)


def test_select_threshold_prefers_highest_threshold_on_ties():
    # threshold 0.9 and 0.6 both give F1 = 2/3; the stricter one wins.
    choice = select_threshold([1, 0, 0, 1], [0.9, 0.8, 0.7, 0.6])
    assert choice.threshold == 0.9
    assert choice.f1 == pytest.approx(2 / 3)


def test_select_threshold_perfect_separation():
    choice = select_threshold([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert choice.threshold == 0.8 and choice.f1 == 1.0


def test_select_threshold_needs_positives():
    with pytest.raises(MetricError):
        select_threshold([0, 0], [0.1, 0.2])


# ---------- error analysis ----------

ROWS = [
    {"pair_id": "p1", "label": "1", "score": "0.9", "pair_type": "positive"},
    {"pair_id": "p2", "label": "1", "score": "0.3", "pair_type": "positive"},
    {"pair_id": "p3", "label": "0", "score": "0.8", "pair_type": "negative"},
    {"pair_id": "p4", "label": "0", "score": "0.6", "pair_type": "negative"},
    {"pair_id": "p5", "label": "0", "score": "0.1", "pair_type": "negative"},
]


def test_error_rows_most_confident_first():
    errors = error_rows(ROWS, 0.5)
    assert [(e["pair_id"], e["outcome"]) for e in errors] == [
        ("p3", "fp"), ("p2", "fn"), ("p4", "fp"),
    ]
    assert errors[0]["margin"] == pytest.approx(0.3)


def test_analyze_errors_groups_and_counts():
    report = analyze_errors(ROWS, 0.5, group_fields=["pair_type"], top_k=1)
    assert report["counts"] == {"tp": 1, "fp": 2, "tn": 1, "fn": 1}
    negative = report["by_group"]["pair_type"]["negative"]
    assert negative["pairs"] == 3 and negative["fp"] == 2
    assert negative["error_rate"] == pytest.approx(2 / 3)
    assert [row["pair_id"] for row in report["top_false_positives"]] == ["p3"]
    assert report["score_quantiles"]["positive"]["max"] == pytest.approx(0.9)


def test_analyze_errors_rejects_bad_rows():
    with pytest.raises(MetricError):
        analyze_errors([{"pair_id": "x", "label": 1}], 0.5)
    with pytest.raises(MetricError):
        analyze_errors([], 0.5)


# ---------- tuning grid ----------

def test_expand_grid_order_and_empty_grid():
    assert expand_grid(None) == [{}]
    assert expand_grid({"lr": [1, 2], "margin": [0.3]}) == [
        {"lr": 1, "margin": 0.3}, {"lr": 2, "margin": 0.3},
    ]
    with pytest.raises(ValueError):
        expand_grid({"lr": []})
    with pytest.raises(ValueError):
        expand_grid({"lr": "2e-5"})


def test_trial_run_id():
    assert trial_run_id("r01", 1, 1) == "r01"
    assert trial_run_id("r01", 3, 4) == "r01-t03"


def test_best_trial_uses_f1_then_loss():
    trials = [
        {"run_id": "a", "best_val_f1": 0.8, "best_val_loss": 0.2},
        {"run_id": "b", "best_val_f1": 0.9, "best_val_loss": 0.4},
        {"run_id": "c", "best_val_f1": 0.9, "best_val_loss": 0.3},
    ]
    assert best_trial(trials)["run_id"] == "c"
    with pytest.raises(ValueError):
        best_trial([{"run_id": "x", "best_val_f1": None, "best_val_loss": 0.1}])


def test_metrics_are_deterministic():
    scores = np.linspace(0, 1, 11)
    labels = [0] * 5 + [1] * 6
    assert select_threshold(labels, scores) == select_threshold(labels, scores)


def test_utf8_console_prints_vietnamese_on_a_cp1252_stream(monkeypatch):
    import io
    import sys

    from src.models.experiment import utf8_console

    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252", newline="\n")
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "stderr", stream)
    utf8_console()
    print("Saved: D:/Sv Nghiên Cứu Khoa Học/run")
    stream.flush()
    assert buffer.getvalue().decode("utf-8") == "Saved: D:/Sv Nghiên Cứu Khoa Học/run\n"
