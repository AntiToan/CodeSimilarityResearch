
from src.transformations.base import (
    Transformation,
    TransformationResult,
)
from src.transformations.variant_generator import (
    VariantGenerator,
    VariantValidationOutcome,
)


class FakeTransformation(Transformation):
    def __init__(self, name: str, suffix: str):
        self._name = name
        self.suffix = suffix

    @property
    def name(self) -> str:
        return self._name

    def transform(self, source: str, seed=None):
        transformed = source + self.suffix

        return TransformationResult(
            transformation_type=self.name,
            source_text=source,
            transformed_text=transformed,
            changed=transformed != source,
            config={"seed": seed},
        )


def make_transformations():
    return [
        FakeTransformation("whitespace", " \n"),
        FakeTransformation("formatting", "\n// formatted"),
        FakeTransformation("comments", "\n// removed"),
    ]


def make_probabilities():
    return {
        "whitespace": 1 / 3,
        "formatting": 1 / 3,
        "comments": 1 / 3,
    }


def passing_validator(original, transformed, transformation_type):
    return VariantValidationOutcome(passed=True)


def failing_validator(original, transformed, transformation_type):
    return VariantValidationOutcome(
        passed=False,
        reason="TEST_VALIDATION_FAILURE",
    )


def make_generator(
    validator=passing_validator,
    target_variants=2,
    max_attempts=5,
):
    return VariantGenerator(
        transformations=make_transformations(),
        probabilities=make_probabilities(),
        validator=validator,
        target_variants=target_variants,
        max_attempts_per_variant=max_attempts,
    )


def test_generates_target_variants():
    result = make_generator().generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 2
    assert result.target_variants == 2


def test_variant_ids_are_sequential():
    result = make_generator().generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert [
        variant.variant_id
        for variant in result.accepted_variants
    ] == [
        "sample_001_v001",
        "sample_001_v002",
    ]


def test_variants_keep_original_reference():
    original = "int main() {}\n"

    result = make_generator().generate(
        "sample_001",
        original,
        seed=42,
    )

    assert all(
        variant.source_text == original
        for variant in result.accepted_variants
    )


def test_variants_are_generated_from_original_not_chained():
    original = "ORIGINAL"

    result = make_generator().generate(
        "sample_001",
        original,
        seed=42,
    )

    assert all(
        variant.transformed_text.startswith(original)
        for variant in result.accepted_variants
    )


def test_validation_failure_rejects_attempts():
    result = make_generator(
        validator=failing_validator,
        target_variants=1,
        max_attempts=3,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 3
    assert result.status == "FAILED"


def test_quota_can_be_partial():
    result = make_generator(
        validator=failing_validator,
        target_variants=2,
        max_attempts=2,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 0
    assert len(result.attempts) == 4
    assert result.quota_reached is False


def test_attempt_limit_is_respected():
    result = make_generator(
        validator=failing_validator,
        target_variants=1,
        max_attempts=5,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert len(result.attempts) == 5


def test_deterministic_with_same_seed():
    first = make_generator().generate(
        "sample_001",
        "int main() {}\n",
        seed=123,
    )

    second = make_generator().generate(
        "sample_001",
        "int main() {}\n",
        seed=123,
    )

    assert [
        v.transformed_text for v in first.accepted_variants
    ] == [
        v.transformed_text for v in second.accepted_variants
    ]

    assert [
        a.transformation_type for a in first.attempts
    ] == [
        a.transformation_type for a in second.attempts
    ]


def test_result_status_completed():
    result = make_generator().generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.status == "COMPLETED"
    assert result.quota_reached is True


def test_result_status_failed():
    result = make_generator(
        validator=failing_validator,
        target_variants=2,
        max_attempts=1,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.status == "FAILED"
    assert result.quota_reached is False


def test_validator_exception_is_rejected():
    def crashing_validator(original, transformed, transformation_type):
        raise RuntimeError("validator crashed")

    result = make_generator(
        validator=crashing_validator,
        target_variants=1,
        max_attempts=2,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 0
    assert all(
        "VALIDATOR_ERROR" in attempt.rejection_reason
        for attempt in result.attempts
    )


def test_transformation_exception_is_rejected():
    class BrokenTransformation(Transformation):
        @property
        def name(self):
            return "broken"

        def transform(self, source, seed=None):
            raise RuntimeError("transform crashed")

    generator = VariantGenerator(
        transformations=[BrokenTransformation()],
        probabilities={"broken": 1.0},
        validator=passing_validator,
        target_variants=1,
        max_attempts_per_variant=2,
    )

    result = generator.generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 0
    assert len(result.attempts) == 2
    assert all(
        "TRANSFORMATION_ERROR" in attempt.rejection_reason
        for attempt in result.attempts
    )


def test_no_change_transformation_is_rejected():
    class NoChangeTransformation(Transformation):
        @property
        def name(self):
            return "no_change"

        def transform(self, source, seed=None):
            return TransformationResult(
                transformation_type=self.name,
                source_text=source,
                transformed_text=source,
                changed=False,
                config={},
            )

    generator = VariantGenerator(
        transformations=[NoChangeTransformation()],
        probabilities={"no_change": 1.0},
        validator=passing_validator,
        target_variants=1,
        max_attempts_per_variant=2,
    )

    result = generator.generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 0
    assert all(
        attempt.rejection_reason == "NO_CHANGE"
        for attempt in result.attempts
    )


def test_result_status_partial_when_only_one_variant_is_accepted():
    validation_calls = 0

    def validator(original, transformed, transformation_type):
        nonlocal validation_calls
        validation_calls += 1

        if validation_calls == 1:
            return VariantValidationOutcome(passed=True)

        return VariantValidationOutcome(
            passed=False,
            reason="TEST_VALIDATION_FAILURE",
        )

    result = make_generator(
        validator=validator,
        target_variants=2,
        max_attempts=1,
    ).generate(
        "sample_001",
        "int main() {}\n",
        seed=42,
    )

    assert result.accepted_count == 1
    assert result.status == "PARTIAL"
    assert result.quota_reached is False
