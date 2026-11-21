
import pytest

from src.data.pair_selection_models import (
    PairSelectionConfig,
    PairSelectionReport,
    PairSelectionResult,
    PairSelectionStatus,
    SplitSelectionStats,
)


def make_stats(
    split="train",
    candidate_positive=10,
    candidate_negative=10,
    target_positive=8,
    target_negative=8,
    selected_positive=8,
    selected_negative=8,
    unmet_positive=0,
    unmet_negative=0,
):
    return SplitSelectionStats(
        split=split,
        candidate_positive_count=candidate_positive,
        candidate_negative_count=candidate_negative,
        target_positive_count=target_positive,
        target_negative_count=target_negative,
        selected_positive_count=selected_positive,
        selected_negative_count=selected_negative,
        unmet_positive_quota=unmet_positive,
        unmet_negative_quota=unmet_negative,
    )


# =========================
# Config tests
# =========================

def test_selection_config_defaults():
    config = PairSelectionConfig()

    assert config.seed == 42
    assert config.balance_labels is True
    assert config.prefer_endpoint_diversity is True
    assert config.prefer_problem_balance is True
    assert config.selector_version == "1.0.0"


def test_selection_config_custom_values():
    config = PairSelectionConfig(
        seed=123,
        balance_labels=False,
        prefer_endpoint_diversity=False,
        prefer_problem_balance=False,
        selector_version="2.0.0",
    )

    assert config.seed == 123
    assert config.balance_labels is False
    assert config.prefer_endpoint_diversity is False
    assert config.prefer_problem_balance is False
    assert config.selector_version == "2.0.0"


def test_selection_config_invalid_seed():
    with pytest.raises(TypeError):
        PairSelectionConfig(seed="42")


def test_selection_config_invalid_boolean():
    with pytest.raises(TypeError):
        PairSelectionConfig(balance_labels=1)


def test_selection_config_empty_version():
    with pytest.raises(ValueError):
        PairSelectionConfig(selector_version=" ")


# =========================
# Selection result tests
# =========================

def test_selection_result_valid():
    pairs = ("p1", "p2", "p3")

    result = PairSelectionResult(
        selected_pairs=pairs,
        positive_count=2,
        negative_count=1,
        total_count=3,
        selection_status=PairSelectionStatus.PASS,
    )

    assert result.selected_pairs == pairs
    assert result.positive_count == 2
    assert result.negative_count == 1
    assert result.total_count == 3
    assert result.selection_status == PairSelectionStatus.PASS


def test_selection_result_rejects_non_tuple():
    with pytest.raises(TypeError):
        PairSelectionResult(
            selected_pairs=["p1", "p2"],
            positive_count=1,
            negative_count=1,
            total_count=2,
            selection_status=PairSelectionStatus.PASS,
        )


def test_selection_result_rejects_negative_counts():
    with pytest.raises(ValueError):
        PairSelectionResult(
            selected_pairs=("p1",),
            positive_count=-1,
            negative_count=2,
            total_count=1,
            selection_status=PairSelectionStatus.PASS,
        )


def test_selection_result_rejects_total_mismatch():
    with pytest.raises(ValueError):
        PairSelectionResult(
            selected_pairs=("p1", "p2"),
            positive_count=1,
            negative_count=1,
            total_count=3,
            selection_status=PairSelectionStatus.PASS,
        )


def test_selection_result_rejects_label_count_mismatch():
    with pytest.raises(ValueError):
        PairSelectionResult(
            selected_pairs=("p1", "p2"),
            positive_count=2,
            negative_count=1,
            total_count=2,
            selection_status=PairSelectionStatus.PASS,
        )


def test_selection_result_rejects_invalid_status():
    with pytest.raises(TypeError):
        PairSelectionResult(
            selected_pairs=(),
            positive_count=0,
            negative_count=0,
            total_count=0,
            selection_status="PASS",
        )


# =========================
# Split stats tests
# =========================

def test_split_stats_valid():
    stats = make_stats()

    assert stats.candidate_count == 20
    assert stats.selected_count == 16
    assert stats.unmet_quota_count == 0


def test_split_stats_rejects_empty_split():
    with pytest.raises(ValueError):
        make_stats(split=" ")


def test_split_stats_rejects_negative_counts():
    with pytest.raises(ValueError):
        make_stats(candidate_positive=-1)


def test_split_stats_rejects_target_above_candidates():
    with pytest.raises(ValueError):
        make_stats(target_positive=11)


def test_split_stats_rejects_selected_above_target():
    with pytest.raises(ValueError):
        make_stats(selected_positive=9)


def test_split_stats_rejects_inconsistent_unmet_quota():
    with pytest.raises(ValueError):
        make_stats(
            selected_positive=6,
            unmet_positive=0,
        )


def test_split_stats_partial_selection_with_unmet_quota():
    stats = make_stats(
        target_positive=8,
        selected_positive=6,
        unmet_positive=2,
    )

    assert stats.unmet_positive_quota == 2
    assert stats.unmet_quota_count == 2
    assert stats.selected_count == 14


# =========================
# Selection report tests
# =========================

def test_report_from_stats_sorts_splits():
    report = PairSelectionReport.from_stats(
        stats=(
            make_stats(split="test"),
            make_stats(split="train"),
            make_stats(split="validation"),
        ),
        seed=42,
    )

    assert tuple(
        stats.split for stats in report.split_stats
    ) == ("test", "train", "validation")


def test_report_aggregates_counts():
    report = PairSelectionReport.from_stats(
        stats=(
            make_stats(split="train"),
            make_stats(
                split="test",
                candidate_positive=5,
                candidate_negative=7,
                target_positive=5,
                target_negative=5,
                selected_positive=5,
                selected_negative=5,
            ),
        ),
        seed=42,
    )

    assert report.total_candidate_count == 32
    assert report.total_selected_count == 26
    assert report.total_unmet_quota_count == 0
    assert report.status == PairSelectionStatus.PASS


def test_report_warns_when_quota_is_unmet():
    report = PairSelectionReport.from_stats(
        stats=(
            make_stats(
                selected_positive=6,
                unmet_positive=2,
            ),
        ),
        seed=42,
    )

    assert report.total_unmet_quota_count == 2
    assert report.status == PairSelectionStatus.WARNING


def test_report_rejects_duplicate_splits():
    with pytest.raises(ValueError):
        PairSelectionReport(
            selector_version="1.0.0",
            seed=42,
            split_stats=(
                make_stats(split="train"),
                make_stats(split="train"),
            ),
        )


def test_report_rejects_non_tuple_stats():
    with pytest.raises(TypeError):
        PairSelectionReport(
            selector_version="1.0.0",
            seed=42,
            split_stats=[make_stats()],
        )


def test_report_to_dict():
    report = PairSelectionReport.from_stats(
        stats=(make_stats(split="train"),),
        seed=123,
    )

    data = report.to_dict()

    assert data["selector_version"] == "1.0.0"
    assert data["seed"] == 123
    assert data["status"] == "PASS"
    assert data["total_candidate_count"] == 20
    assert data["total_selected_count"] == 16
    assert data["total_unmet_quota_count"] == 0
    assert len(data["split_stats"]) == 1
    assert data["split_stats"][0]["split"] == "train"
