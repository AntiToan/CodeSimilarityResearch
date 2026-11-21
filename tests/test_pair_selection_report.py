from src.data.pair_selection_models import (
    PairSelectionReport,
    SplitSelectionStats,
    PairSelectionStatus,
    PairSelectionConfig,
)
import pytest

def test_report_aggregates_split_stats_and_serializes_correctly():
    stats = (
        SplitSelectionStats(
            split="train",
            candidate_positive_count=10,
            candidate_negative_count=8,
            target_positive_count=5,
            target_negative_count=5,
            selected_positive_count=5,
            selected_negative_count=5,
            unmet_positive_quota=0,
            unmet_negative_quota=0,
        ),
        SplitSelectionStats(
            split="validation",
            candidate_positive_count=4,
            candidate_negative_count=3,
            target_positive_count=2,
            target_negative_count=2,
            selected_positive_count=2,
            selected_negative_count=1,
            unmet_positive_quota=0,
            unmet_negative_quota=1,
        ),
        SplitSelectionStats(
            split="test",
            candidate_positive_count=3,
            candidate_negative_count=3,
            target_positive_count=2,
            target_negative_count=2,
            selected_positive_count=2,
            selected_negative_count=2,
            unmet_positive_quota=0,
            unmet_negative_quota=0,
        ),
    )

    report = PairSelectionReport.from_stats(
        stats,
        seed=42,
        selector_version="1.0.0",
    )

    assert report.total_candidate_count == 31
    assert report.total_selected_count == 17
    assert report.total_unmet_quota_count == 1
    assert report.status == PairSelectionStatus.WARNING

    data = report.to_dict()

    assert data["selector_version"] == "1.0.0"
    assert data["seed"] == 42
    assert data["status"] == "WARNING"
    assert data["total_candidate_count"] == 31
    assert data["total_selected_count"] == 17
    assert data["total_unmet_quota_count"] == 1

    assert len(data["split_stats"]) == 3
    assert [item["split"] for item in data["split_stats"]] == [
        "test",
        "train",
        "validation",
    ]

def test_report_preserves_each_split_statistics():
    train = SplitSelectionStats(
        split="train",
        candidate_positive_count=10,
        candidate_negative_count=8,
        target_positive_count=5,
        target_negative_count=5,
        selected_positive_count=5,
        selected_negative_count=5,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    validation = SplitSelectionStats(
        split="validation",
        candidate_positive_count=4,
        candidate_negative_count=3,
        target_positive_count=2,
        target_negative_count=2,
        selected_positive_count=2,
        selected_negative_count=1,
        unmet_positive_quota=0,
        unmet_negative_quota=1,
    )

    test = SplitSelectionStats(
        split="test",
        candidate_positive_count=3,
        candidate_negative_count=3,
        target_positive_count=2,
        target_negative_count=2,
        selected_positive_count=2,
        selected_negative_count=2,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    report = PairSelectionReport.from_stats(
        (train, validation, test),
        seed=42,
    )

    split_data = {
        item["split"]: item
        for item in report.to_dict()["split_stats"]
    }

    assert split_data["train"]["candidate_count"] == 18
    assert split_data["train"]["selected_count"] == 10
    assert split_data["train"]["unmet_quota_count"] == 0

    assert split_data["validation"]["candidate_count"] == 7
    assert split_data["validation"]["selected_count"] == 3
    assert split_data["validation"]["unmet_quota_count"] == 1

    assert split_data["test"]["candidate_count"] == 6
    assert split_data["test"]["selected_count"] == 4
    assert split_data["test"]["unmet_quota_count"] == 0

def test_report_status_matches_quota_completion():
    complete_stats = (
        SplitSelectionStats(
            split="train",
            candidate_positive_count=4,
            candidate_negative_count=4,
            target_positive_count=2,
            target_negative_count=2,
            selected_positive_count=2,
            selected_negative_count=2,
            unmet_positive_quota=0,
            unmet_negative_quota=0,
        ),
    )

    incomplete_stats = (
        SplitSelectionStats(
            split="train",
            candidate_positive_count=4,
            candidate_negative_count=4,
            target_positive_count=2,
            target_negative_count=2,
            selected_positive_count=2,
            selected_negative_count=1,
            unmet_positive_quota=0,
            unmet_negative_quota=1,
        ),
    )

    complete_report = PairSelectionReport.from_stats(
        complete_stats,
        seed=42,
    )

    incomplete_report = PairSelectionReport.from_stats(
        incomplete_stats,
        seed=42,
    )

    assert complete_report.status == PairSelectionStatus.PASS
    assert complete_report.total_unmet_quota_count == 0

    assert incomplete_report.status == PairSelectionStatus.WARNING
    assert incomplete_report.total_unmet_quota_count == 1

def test_empty_report_has_zero_counts_and_pass_status():
    report = PairSelectionReport.from_stats(
        stats=(),
        seed=42,
        selector_version="1.0.0",
    )

    assert report.split_stats == ()
    assert report.total_candidate_count == 0
    assert report.total_selected_count == 0
    assert report.total_unmet_quota_count == 0
    assert report.status == PairSelectionStatus.PASS

    data = report.to_dict()

    assert data["split_stats"] == []
    assert data["total_candidate_count"] == 0
    assert data["total_selected_count"] == 0
    assert data["total_unmet_quota_count"] == 0
    assert data["status"] == "PASS"

def test_report_split_order_is_deterministic():
    train_stats = SplitSelectionStats(
        split="train",
        candidate_positive_count=10,
        candidate_negative_count=10,
        target_positive_count=5,
        target_negative_count=5,
        selected_positive_count=5,
        selected_negative_count=5,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    validation_stats = SplitSelectionStats(
        split="validation",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=2,
        target_negative_count=2,
        selected_positive_count=2,
        selected_negative_count=2,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    test_stats = SplitSelectionStats(
        split="test",
        candidate_positive_count=6,
        candidate_negative_count=6,
        target_positive_count=3,
        target_negative_count=3,
        selected_positive_count=3,
        selected_negative_count=3,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    report_a = PairSelectionReport.from_stats(
        stats=(train_stats, validation_stats, test_stats),
        seed=42,
        selector_version="1.0.0",
    )

    report_b = PairSelectionReport.from_stats(
        stats=(test_stats, train_stats, validation_stats),
        seed=42,
        selector_version="1.0.0",
    )

    assert report_a.split_stats == report_b.split_stats

    assert [
        stat.split for stat in report_a.split_stats
    ] == ["test", "train", "validation"]

    assert report_a.to_dict() == report_b.to_dict()

def test_report_rejects_duplicate_split_stats():
    stats = SplitSelectionStats(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=2,
        target_negative_count=2,
        selected_positive_count=2,
        selected_negative_count=2,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    with pytest.raises(ValueError, match="duplicate"):
        PairSelectionReport(
            selector_version="1.0.0",
            seed=42,
            split_stats=(stats, stats),
        )

def test_report_rejects_invalid_metadata():
    stats = SplitSelectionStats(
        split="train",
        candidate_positive_count=4,
        candidate_negative_count=4,
        target_positive_count=2,
        target_negative_count=2,
        selected_positive_count=2,
        selected_negative_count=2,
        unmet_positive_quota=0,
        unmet_negative_quota=0,
    )

    with pytest.raises(ValueError):
        PairSelectionReport(
            selector_version="",
            seed=42,
            split_stats=(stats,),
        )

    with pytest.raises(TypeError, match="seed must be an integer"):
        PairSelectionReport(
            selector_version="1.0.0",
            seed="42",
            split_stats=(stats,),
        )

def test_split_stats_reject_inconsistent_unmet_quota():
    with pytest.raises(ValueError, match="unmet"):
        SplitSelectionStats(
            split="train",
            candidate_positive_count=10,
            candidate_negative_count=10,
            target_positive_count=5,
            target_negative_count=5,
            selected_positive_count=4,
            selected_negative_count=5,
            unmet_positive_quota=0,
            unmet_negative_quota=0,
        )

def test_report_rejects_boolean_seed():
    with pytest.raises(TypeError, match="seed must be an integer"):
        PairSelectionReport(
            selector_version="1.0.0",
            seed=True,
            split_stats=(),
        )

def test_selection_config_rejects_boolean_seed():
    with pytest.raises(TypeError, match="seed must be an integer"):
        PairSelectionConfig(seed=True)

@pytest.mark.parametrize(
    "field_name",
    [
        "balance_labels",
        "prefer_endpoint_diversity",
        "prefer_problem_balance",
    ],
)
def test_selection_config_rejects_non_boolean_flags(field_name):
    with pytest.raises(TypeError):
        PairSelectionConfig(**{field_name: 1})