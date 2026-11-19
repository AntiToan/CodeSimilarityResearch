
from src.transformations import (
    CommentsTransformation,
    WhitespaceTransformation,
)
from src.transformations.validation import (
    TransformationValidator,
    ValidationStatus,
)


def test_replayed_transformation_passes():
    original = "\tint x = 1;\n"
    transformation = WhitespaceTransformation()
    candidate = transformation.transform(
        original,
        seed=42,
    ).transformed_text

    result = TransformationValidator().validate(
        original,
        candidate,
        transformation,
        seed=42,
    )

    assert result.status == ValidationStatus.PASS


def test_wrong_candidate_fails():
    original = "\tint x = 1;\n"
    transformation = WhitespaceTransformation()

    result = TransformationValidator().validate(
        original,
        "int y = 999;\n",
        transformation,
        seed=42,
    )

    assert result.status == ValidationStatus.FAIL
    assert "TRANSFORMATION_OUTPUT_MISMATCH" in result.reason_codes


def test_no_change_transformation_fails():
    original = "int x = 1;\n"
    transformation = WhitespaceTransformation()

    candidate = transformation.transform(original).transformed_text

    result = TransformationValidator().validate(
        original,
        candidate,
        transformation,
    )

    assert result.status == ValidationStatus.FAIL
    assert "TRANSFORMATION_NO_CHANGE" in result.reason_codes


def test_comments_replay_passes():
    original = "int x = 1; // comment\n"
    transformation = CommentsTransformation()
    candidate = transformation.transform(original).transformed_text

    result = TransformationValidator().validate(
        original,
        candidate,
        transformation,
    )

    assert result.status == ValidationStatus.PASS


def test_transformation_exception_returns_error():
    class BrokenTransformation:
        name = "broken"

        def transform(self, source, seed=None):
            raise RuntimeError("intentional test error")

    result = TransformationValidator().validate(
        original="int x = 1;\n",
        candidate="int y = 2;\n",
        transformation=BrokenTransformation(),
    )

    assert result.status == ValidationStatus.ERROR
    assert "TRANSFORMATION_REPLAY_ERROR" in result.reason_codes
