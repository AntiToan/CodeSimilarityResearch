
import pytest

from src.transformations.validation import (
    StructuralValidator,
    ValidationStatus,
)


@pytest.fixture
def validator():
    return StructuralValidator()


def test_valid_candidate_passes(validator):
    result = validator.validate(
        original="int x = 1;\n",
        candidate="int x = 1; \n",
        variant_id="sample_v001",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.PASS


def test_empty_candidate_fails(validator):
    result = validator.validate(
        original="int x = 1;\n",
        candidate=" \n",
        variant_id="sample_v001",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.FAIL
    assert "CANDIDATE_EMPTY" in result.reason_codes


def test_unchanged_candidate_fails(validator):
    source = "int x = 1;\n"

    result = validator.validate(
        original=source,
        candidate=source,
        variant_id="sample_v001",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.FAIL
    assert "CANDIDATE_UNCHANGED" in result.reason_codes


def test_invalid_variant_id_fails(validator):
    result = validator.validate(
        original="int x = 1;\n",
        candidate="int x = 1; \n",
        variant_id=" ",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.FAIL
    assert "VARIANT_ID_INVALID" in result.reason_codes


def test_nul_character_fails(validator):
    result = validator.validate(
        original="int x = 1;\n",
        candidate="int x = 1;\x00\n",
        variant_id="sample_v001",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.FAIL
    assert "CANDIDATE_CONTAINS_NUL" in result.reason_codes


def test_final_newline_removal_fails(validator):
    result = validator.validate(
        original="int x = 1;\n",
        candidate="int x = 1;",
        variant_id="sample_v001",
        original_sample_id="sample",
        transformation_type="formatting",
    )

    assert result.status == ValidationStatus.FAIL
    assert "FINAL_NEWLINE_REMOVED" in result.reason_codes
