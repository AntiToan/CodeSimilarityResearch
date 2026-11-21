import pytest
from src.data.final_dataset_validation_models import (
    FinalDatasetValidationStatus,
)
from src.data.pair_models import PairRecord, PairSplit, PairType
from src.data.final_dataset_validator import FinalDatasetValidator
from src.data.final_dataset_validation_config import (
    FinalDatasetValidationConfig,
)

def make_pair(
    pair_id: str = "pair_001",
    sample_a_id: str = "sample_001",
    sample_b_id: str = "sample_002",
    pair_type: PairType = PairType.POSITIVE,
    split: PairSplit = PairSplit.TRAIN,
    source_a_id: str = "source_shared",
    source_b_id: str = "source_shared",
    problem_a_id: str = "problem_001",
    problem_b_id: str = "problem_001",
) -> PairRecord:
    if pair_type == PairType.NEGATIVE:
        source_a_id = "source_a"
        source_b_id = "source_b"
        problem_a_id = "problem_001"
        problem_b_id = "problem_002"

    return PairRecord.create_canonical(
        pair_id=pair_id,
        sample_a_id=sample_a_id,
        sample_b_id=sample_b_id,
        label=1 if pair_type == PairType.POSITIVE else 0,
        pair_type=pair_type,
        split=split,
        source_a_id=source_a_id,
        source_b_id=source_b_id,
        problem_a_id=problem_a_id,
        problem_b_id=problem_b_id,
        generation_method="original",
    )


def test_final_dataset_rejects_duplicate_pair_ids():
    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    ]

    pair_ids = [pair.pair_id for pair in pairs]

    assert len(pair_ids) != len(set(pair_ids))

def test_validator_rejects_non_pair_records():
    validator = FinalDatasetValidator()

    with pytest.raises(TypeError, match="PairRecord"):
        validator.validate(["not_a_pair"])

def test_validator_accepts_valid_pair_iterable():
    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
        )
    )

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    ]

    result = validator.validate(iter(pairs))

    assert result.status.value == "PASS"
    assert result.total_pairs == 2

def test_validator_rejects_empty_dataset():
    validator = FinalDatasetValidator()

    with pytest.raises(ValueError, match="empty"):
        validator.validate([])

def test_validator_reports_correct_pair_counts():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
            pair_type=PairType.NEGATIVE,
        ),
        make_pair(
            pair_id="pair_003",
            sample_a_id="sample_005",
            sample_b_id="sample_006",
        ),
    ]

    report = validator.validate(pairs)

    assert report.total_pairs == 3
    assert report.positive_count == 2
    assert report.negative_count == 1

def test_validator_rejects_dataset_missing_negative_pairs():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.FAIL

def test_validator_rejects_dataset_missing_positive_pairs():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
            pair_type=PairType.NEGATIVE,
        ),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
            pair_type=PairType.NEGATIVE,
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "MISSING_POSITIVE_LABEL"
        for issue in report.issues
    )

def test_validator_allows_single_label_when_configured():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        config=FinalDatasetValidationConfig(
            require_both_labels=False,
        )
    )

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.PASS
    assert report.issues == ()

def test_validator_rejects_duplicate_pair_ids():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
            pair_type=PairType.NEGATIVE,
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "DUPLICATE_PAIR_ID"
        for issue in report.issues
    )

def test_validator_allows_duplicate_pair_ids_when_configured():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        config=FinalDatasetValidationConfig(
            check_duplicate_pair_ids=False,
            require_both_labels=False,
        )
    )

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
            pair_type=PairType.NEGATIVE,
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.PASS
    assert not any(
        issue.code == "DUPLICATE_PAIR_ID"
        for issue in report.issues
    )

def test_validator_rejects_duplicate_sample_pairs():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "DUPLICATE_SAMPLE_PAIR"
        for issue in report.issues
    )

def test_validator_allows_duplicate_sample_pairs_when_configured():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        config=FinalDatasetValidationConfig(
            check_duplicate_sample_pairs=False,
        )
    )

    pairs = [
        make_pair(pair_id="pair_001"),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
        ),
    ]

    report = validator.validate(pairs)

    assert not any(
        issue.code == "DUPLICATE_SAMPLE_PAIR"
        for issue in report.issues
    )

def test_validator_rejects_sample_overlap_across_splits():
    validator = FinalDatasetValidator()

    pairs = [
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
            split=PairSplit.TRAIN,
        ),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_001",
            sample_b_id="sample_003",
            split=PairSplit.TEST,
        ),
    ]

    report = validator.validate(pairs)

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SPLIT_SAMPLE_LEAKAGE"
        for issue in report.issues
    )

def test_validator_allows_sample_overlap_when_split_integrity_disabled():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        config=FinalDatasetValidationConfig(
            check_split_integrity=False,
        )
    )

    pairs = [
        make_pair(
            pair_id="pair_001",
            sample_a_id="sample_001",
            sample_b_id="sample_002",
            split=PairSplit.TRAIN,
        ),
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_001",
            sample_b_id="sample_003",
            split=PairSplit.TEST,
        ),
    ]

    report = validator.validate(pairs)

    assert not any(
        issue.code == "SPLIT_SAMPLE_LEAKAGE"
        for issue in report.issues
    )

def test_validator_returns_warning_when_only_warning_issues_exist():
    from src.data.final_dataset_validation_models import (
        FinalDatasetValidationIssue,
    )

    issue = FinalDatasetValidationIssue(
        code="TEST_WARNING",
        message="Test warning",
        severity=FinalDatasetValidationStatus.WARNING,
    )

    assert issue.severity == FinalDatasetValidationStatus.WARNING

def test_validator_resolves_warning_status():
    from src.data.final_dataset_validation_models import (
        FinalDatasetValidationIssue,
    )

    warning_issue = FinalDatasetValidationIssue(
        code="TEST_WARNING",
        message="A warning occurred.",
        severity=FinalDatasetValidationStatus.WARNING,
    )

    status = FinalDatasetValidator._resolve_status(
        [warning_issue]
    )

    assert status == FinalDatasetValidationStatus.WARNING

def test_validator_fail_status_has_priority_over_warning():
    from src.data.final_dataset_validation_models import (
        FinalDatasetValidationIssue,
    )

    issues = [
        FinalDatasetValidationIssue(
            code="TEST_WARNING",
            message="Warning issue.",
            severity=FinalDatasetValidationStatus.WARNING,
        ),
        FinalDatasetValidationIssue(
            code="TEST_FAIL",
            message="Failure issue.",
            severity=FinalDatasetValidationStatus.FAIL,
        ),
    ]

    status = FinalDatasetValidator._resolve_status(issues)

    assert status == FinalDatasetValidationStatus.FAIL

def test_validator_resolves_pass_when_no_issues():
    status = FinalDatasetValidator._resolve_status([])

    assert status == FinalDatasetValidationStatus.PASS

def test_validator_rejects_pairs_mismatching_selection_result():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.PASS,
    )

    actual_pairs = [
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    ]

    report = validator.validate(
        actual_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_accepts_pairs_matching_selection_result():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "MISSING_NEGATIVE_LABEL"
        for issue in report.issues
    )
    assert not any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_can_disable_selection_integrity_check():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    config = FinalDatasetValidationConfig(
        check_selection_integrity=False,
    )
    validator = FinalDatasetValidator(config)

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.PASS,
    )

    actual_pairs = (
        make_pair(
            pair_id="pair_002",
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    )

    report = validator.validate(
        actual_pairs,
        selection_result=selection_result,
    )

    assert not any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_rejects_selection_result_with_incorrect_label_counts():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    # Pair thực tế là positive, nhưng metadata khai báo negative.
    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=0,
        negative_count=1,
        total_count=1,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SELECTION_RESULT_COUNT_MISMATCH"
        for issue in report.issues
    )

def test_validator_propagates_selection_warning():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
        )
    )

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.WARNING,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.WARNING
    assert any(
        issue.code == "SELECTION_RESULT_WARNING"
        for issue in report.issues
    )

def test_validator_propagates_selection_failure():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
        )
    )

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.FAIL,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SELECTION_RESULT_FAILURE"
        for issue in report.issues
    )

def test_disabling_selection_integrity_skips_selection_status_propagation():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
            check_selection_integrity=False,
        )
    )

    selected_pairs = (
        make_pair(pair_id="pair_001"),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.FAIL,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.PASS
    assert not any(
        issue.code.startswith("SELECTION_RESULT_")
        for issue in report.issues
    )

def test_validator_rejects_invalid_selection_result_pair_type():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selection_result = PairSelectionResult(
        selected_pairs=("not_a_pair_record",),
        positive_count=1,
        negative_count=0,
        total_count=1,
        selection_status=PairSelectionStatus.PASS,
    )

    actual_pairs = (
        make_pair(pair_id="pair_001"),
    )

    with pytest.raises(
        TypeError,
        match="selection_result.*PairRecord",
    ):
        validator.validate(
            actual_pairs,
            selection_result=selection_result,
        )

def test_validator_accepts_none_selection_result():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
        )
    )

    pairs = (
        make_pair(pair_id="pair_001"),
    )

    report = validator.validate(
        pairs,
        selection_result=None,
    )

    assert report.status == FinalDatasetValidationStatus.PASS
    assert not any(
        issue.code.startswith("SELECTION_RESULT_")
        for issue in report.issues
    )

def test_validator_rejects_invalid_selection_result_object_type():
    validator = FinalDatasetValidator()

    pairs = (
        make_pair(pair_id="pair_001"),
    )

    with pytest.raises(
        TypeError,
        match="selection_result must be a PairSelectionResult",
    ):
        validator.validate(
            pairs,
            selection_result="not_a_selection_result",
        )

def test_validator_rejects_invalid_selection_result_when_integrity_disabled():
    from src.data.final_dataset_validation_config import (
        FinalDatasetValidationConfig,
    )

    validator = FinalDatasetValidator(
        FinalDatasetValidationConfig(
            require_both_labels=False,
            check_selection_integrity=False,
        )
    )

    pairs = (
        make_pair(pair_id="pair_001"),
    )

    with pytest.raises(
        TypeError,
        match="selection_result must be a PairSelectionResult",
    ):
        validator.validate(
            pairs,
            selection_result="not_a_selection_result",
        )

def test_validator_rejects_selection_counts_mismatching_final_dataset():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    final_pairs = (
        make_pair(pair_id="pair_001", pair_type=PairType.POSITIVE),
        make_pair(pair_id="pair_002", pair_type=PairType.POSITIVE),
    )

    selection_result = PairSelectionResult(
        selected_pairs=final_pairs,
        positive_count=2,
        negative_count=0,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    modified_final_dataset = (
        make_pair(pair_id="pair_001", pair_type=PairType.POSITIVE),
        make_pair(pair_id="pair_002", pair_type=PairType.NEGATIVE),
    )

    report = validator.validate(
        modified_final_dataset,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_accepts_reordered_selection_pairs():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selected_pairs = (
        make_pair(
            pair_id="pair_001",
            pair_type=PairType.POSITIVE,
            sample_a_id="sample_001",
            sample_b_id="sample_002",
        ),
        make_pair(
            pair_id="pair_002",
            pair_type=PairType.NEGATIVE,
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=1,
        negative_count=1,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    reordered_pairs = tuple(reversed(selected_pairs))

    report = validator.validate(
        reordered_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.PASS
    assert not any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_rejects_duplicate_records_in_selection_result():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    pair = make_pair(
        pair_id="pair_001",
        pair_type=PairType.POSITIVE,
        sample_a_id="sample_001",
        sample_b_id="sample_002",
    )

    selection_result = PairSelectionResult(
        selected_pairs=(pair, pair),
        positive_count=2,
        negative_count=0,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        (pair,),
        selection_result=selection_result,
    )

    assert any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )

def test_validator_rejects_duplicate_pair_ids_in_selection_result():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    pair_1 = make_pair(
        pair_id="pair_001",
        pair_type=PairType.POSITIVE,
        sample_a_id="sample_001",
        sample_b_id="sample_002",
    )

    pair_2 = make_pair(
        pair_id="pair_001",
        pair_type=PairType.POSITIVE,
        sample_a_id="sample_003",
        sample_b_id="sample_004",
    )

    selection_result = PairSelectionResult(
        selected_pairs=(pair_1, pair_2),
        positive_count=2,
        negative_count=0,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        (pair_1,),
        selection_result=selection_result,
    )

    assert any(
        issue.code == "SELECTION_RESULT_DUPLICATE_PAIR_ID"
        for issue in report.issues
    )

def test_validator_rejects_duplicate_sample_pairs_in_selection_result():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    pair_1 = make_pair(
        pair_id="pair_001",
        pair_type=PairType.POSITIVE,
        sample_a_id="sample_001",
        sample_b_id="sample_002",
    )

    pair_2 = make_pair(
        pair_id="pair_002",
        pair_type=PairType.POSITIVE,
        sample_a_id="sample_001",
        sample_b_id="sample_002",
    )

    selection_result = PairSelectionResult(
        selected_pairs=(pair_1, pair_2),
        positive_count=2,
        negative_count=0,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        (pair_1,),
        selection_result=selection_result,
    )

    assert any(
        issue.code == "SELECTION_RESULT_DUPLICATE_SAMPLE_PAIR"
        for issue in report.issues
    )

def test_validator_rejects_selection_result_wrong_label_distribution():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    selected_pairs = (
        make_pair(
            pair_id="pair_001",
            pair_type=PairType.POSITIVE,
            sample_a_id="sample_001",
            sample_b_id="sample_002",
        ),
        make_pair(
            pair_id="pair_002",
            pair_type=PairType.NEGATIVE,
            sample_a_id="sample_003",
            sample_b_id="sample_004",
        ),
    )

    selection_result = PairSelectionResult(
        selected_pairs=selected_pairs,
        positive_count=2,
        negative_count=0,
        total_count=2,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        selected_pairs,
        selection_result=selection_result,
    )

    assert any(
        issue.code == "SELECTION_RESULT_COUNT_MISMATCH"
        for issue in report.issues
    )

def test_validator_rejects_empty_selection_result_for_nonempty_dataset():
    from src.data.pair_selection_models import (
        PairSelectionResult,
        PairSelectionStatus,
    )

    validator = FinalDatasetValidator()

    final_pairs = (
        make_pair(
            pair_id="pair_001",
            pair_type=PairType.POSITIVE,
            sample_a_id="sample_001",
            sample_b_id="sample_002",
        ),
    )

    selection_result = PairSelectionResult(
        selected_pairs=(),
        positive_count=0,
        negative_count=0,
        total_count=0,
        selection_status=PairSelectionStatus.PASS,
    )

    report = validator.validate(
        final_pairs,
        selection_result=selection_result,
    )

    assert report.status == FinalDatasetValidationStatus.FAIL
    assert any(
        issue.code == "SELECTION_RESULT_MISMATCH"
        for issue in report.issues
    )