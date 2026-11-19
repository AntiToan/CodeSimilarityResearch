
from src.transformations import WhitespaceTransformation
from src.transformations.validation import (
    ValidationResult,
    ValidationStatus,
    VariantValidator,
)


class FakeSyntaxValidator:
    def validate(self, candidate):
        return ValidationResult(
            validator_name="V3_SYNTAX",
            status=ValidationStatus.PASS,
            message="Mock syntax pass",
        )


def test_all_validators_pass():
    original = "\tint main() {\n\t\treturn 0;\n\t}\n"

    transformation = WhitespaceTransformation()
    candidate = transformation.transform(
        original,
        seed=42,
    ).transformed_text

    validator = VariantValidator(
        v3=FakeSyntaxValidator(),
    )

    report = validator.validate(
        variant_id="sample_v001",
        original_sample_id="sample",
        original=original,
        candidate=candidate,
        transformation=transformation,
        seed=42,
    )

    assert report.overall_status == ValidationStatus.PASS
    assert report.accepted is True
    assert report.v1.status == ValidationStatus.PASS
    assert report.v2.status == ValidationStatus.PASS
    assert report.v3.status == ValidationStatus.PASS


def test_any_failed_validator_rejects_candidate():
    original = "int main() {\n    return 0;\n}\n"

    transformation = WhitespaceTransformation()
    candidate = original

    validator = VariantValidator(
        v3=FakeSyntaxValidator(),
    )

    report = validator.validate(
        variant_id="sample_v001",
        original_sample_id="sample",
        original=original,
        candidate=candidate,
        transformation=transformation,
        seed=42,
    )

    assert report.overall_status == ValidationStatus.FAIL
    assert report.accepted is False
    assert report.v1.status == ValidationStatus.FAIL
    assert report.v2.status == ValidationStatus.FAIL


def test_v3_error_rejects_candidate():
    original = "\tint x = 1;\n"
    transformation = WhitespaceTransformation()
    candidate = transformation.transform(original).transformed_text

    class ErrorSyntaxValidator:
        def validate(self, candidate):
            return ValidationResult(
                validator_name="V3_SYNTAX",
                status=ValidationStatus.ERROR,
                reason_codes=("COMPILER_UNAVAILABLE",),
            )

    report = VariantValidator(
        v3=ErrorSyntaxValidator(),
    ).validate(
        variant_id="sample_v001",
        original_sample_id="sample",
        original=original,
        candidate=candidate,
        transformation=transformation,
    )

    assert report.overall_status == ValidationStatus.FAIL
    assert report.accepted is False
    assert report.v3.status == ValidationStatus.ERROR
