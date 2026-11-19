from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class PairGenerationConfigError(ValueError):
    """Raised when pair generation configuration is invalid."""

class PairGenerationConfig:
    """Load and validate pair generation configuration."""

    def __init__(
        self,
        config_path: str | Path = "config/pair_generation_config.json",
    ) -> None:
        self.config_path = Path(config_path).resolve()

        if not self.config_path.exists():
            raise PairGenerationConfigError(
                f"Config file not found: {self.config_path}"
            )

        if not self.config_path.is_file():
            raise PairGenerationConfigError(
                f"config path is not a file: {self.config_path}"
            )

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                self._config: dict[str, Any] = json.load(file)
        except json.JSONDecodeError as exc:
            raise PairGenerationConfigError(
                f"Invalid JSON config: {exc}"
            ) from exc 

        if not isinstance(self._config, dict):
            raise PairGenerationConfigError(
                "Config root must be a JSON object."
            )

        self.validate()

    @property
    def raw(self) -> dict[str, Any]:
        """Return the loaded configuration."""
        return self._config

    def get(self, *keys: str) -> Any:
        """Get a nested config value using successive keys."""
        current: Any = self._config

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                raise KeyError(
                    f"Configuration key not found: {'.'.join(keys)}"
                )
            current = current[key]

        return current

    def resolve_path(self, *keys: str) -> Path:
        """
        Resolve a configured path relative to the repository root.
        The repository root is inferred as the parent of the config directory.
        """
        configured_path = Path(self.get(*keys))

        if configured_path.is_absolute():
            return configured_path.resolve()

        project_root = self.config_path.parent.parent
        return (project_root / configured_path).resolve()

    @property
    def seed(self) -> int:
        return self.get("reproducibility", "seed")

    @property
    def dataset_name(self) -> str:
        return self.get("dataset", "name")

    def validate(self) -> None:
        """Validate configuration values and cross-field constraints."""
        self._validate_required_sections()
        self._validate_split_ratios()
        self._validate_transformations()
        self._validate_variants()
        self._validate_negative_pairs()
        self._validate_negative_screening()
        self._validate_pair_selection()
        self._validate_validation_settings()

    def _validate_required_sections(self) -> None:
        required_sections = (
            "dataset",
            "reproducibility",
            "split",
            "duplicate_detection",
            "variants",
            "transformations",
            "negative_pairs",
            "negative_screening",
            "pair_selection",
            "validation",
            "output",
        )

        for section in required_sections:
            if section not in self._config:
                raise PairGenerationConfigError(
                    f"Missing required config section: {section}"
                )

        dataset_name = self.get("dataset", "name")
        if not isinstance(dataset_name, str) or not dataset_name.strip():
            raise PairGenerationConfigError(
                "dataset.name must be a non-empty string."
            )

        seed = self.get("reproducibility", "seed")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise PairGenerationConfigError(
                "reproducibility.seed must be an integer."
            )

    def _validate_split_ratios(self) -> None:
        ratios = self.get("split", "ratios")

        expected = {"train", "validation", "test"}
        if not isinstance(ratios, dict) or set(ratios) != expected:
            raise PairGenerationConfigError(
                "split.ratios must contain train, validation, and test."
            )

        for name, ratio in ratios.items():
            if (
                not isinstance(ratio, (int, float))
                or isinstance(ratio, bool)
                or not 0 < ratio < 1
            ):
                raise PairGenerationConfigError(
                    f"Invalid split ratio for {name}: {ratio}"
                )

        total = sum(ratios.values())
        if abs(total - 1.0) > 1e-8:
            raise PairGenerationConfigError(
                f"Split ratios must sum to 1.0, got {total}."
            )

    def _validate_transformations(self) -> None:
        transformations = self.get("transformations")
        enabled = transformations.get("enabled")
        probabilities = transformations.get("probabilities")

        if not isinstance(enabled, list) or not enabled:
            raise PairGenerationConfigError(
                "transformations.enabled must be a non-empty list."
            )

        if len(enabled) != len(set(enabled)):
            raise PairGenerationConfigError(
                "Duplicate transformation types are not allowed."
            )

        if not isinstance(probabilities, dict):
            raise PairGenerationConfigError(
                "transformations.probabilities must be an object."
            )

        for name in enabled:
            if name not in probabilities:
                raise PairGenerationConfigError(
                    f"Missing probability for transformation: {name}"
                )

        enabled_probabilities = [probabilities[name] for name in enabled]

        for probability in enabled_probabilities:
            if (
                not isinstance(probability, (int, float))
                or isinstance(probability, bool)
                or not 0 <= probability <= 1
            ):
                raise PairGenerationConfigError(
                    "Transformation probabilities must be in [0, 1]."
                )

        if abs(sum(enabled_probabilities) - 1.0) > 1e-8:
            raise PairGenerationConfigError(
                "Enabled transformation probabilities must sum to 1.0."
            )

        if transformations.get("sampling") != "without_replacement":
            raise PairGenerationConfigError(
                "Only without_replacement transformation sampling is supported."
            )

    def _validate_variants(self) -> None:
        variants = self.get("variants")

        target = variants.get("target_per_original")
        maximum = variants.get("max_variants_per_original")
        attempts = variants.get("max_attempts_per_variant")

        for name, value in (
            ("target_per_original", target),
            ("max_variants_per_original", maximum),
            ("max_attempts_per_variant", attempts),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise PairGenerationConfigError(
                    f"variants.{name} must be a positive integer."
                )

        if target > maximum:
            raise PairGenerationConfigError(
                "Variant target cannot exceed maximum variants per original."
            )

        if variants.get("allow_variant_chaining") is not False:
            raise PairGenerationConfigError(
                "Variant chaining must be disabled."
            )

    def _validate_negative_pairs(self) -> None:
        negative_pairs = self.get("negative_pairs")

        quota = negative_pairs.get("target_per_anchor")
        attempts = negative_pairs.get("max_sampling_attempts")

        for name, value in (
            ("target_per_anchor", quota),
            ("max_sampling_attempts", attempts),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise PairGenerationConfigError(
                    f"negative_pairs.{name} must be a positive integer."
                )

        if negative_pairs.get("same_problem_allowed") is not False:
            raise PairGenerationConfigError(
                "Negative pairs must not contain same-problem samples."
            )

        if negative_pairs.get("same_lineage_allowed") is not False:
            raise PairGenerationConfigError(
                "Negative pairs must not contain same-lineage samples."
            )

        if negative_pairs.get("originals_only") is not True:
            raise PairGenerationConfigError(
                "Negative pair generation must use originals only."
            )

    def _validate_negative_screening(self) -> None:
        screening = self.get("negative_screening")

        threshold = screening.get("threshold")
        if (
            not isinstance(threshold, (int, float))
            or isinstance(threshold, bool)
            or not 0 <= threshold <= 1
        ):
            raise PairGenerationConfigError(
                "negative_screening.threshold must be in [0, 1]."
            )

        if screening.get("metric") != "token_jaccard":
            raise PairGenerationConfigError(
                "Unsupported negative screening metric."
            )

        if screening.get("fail_closed") is not True:
            raise PairGenerationConfigError(
                "Negative screening must fail closed."
            )

    def _validate_pair_selection(self) -> None:
        selection = self.get("pair_selection")

        if selection.get("oversampling") is not False:
            raise PairGenerationConfigError(
                "Pair selection must not oversample."
            )

        if selection.get("cross_split_transfer") is not False:
            raise PairGenerationConfigError(
                "Pairs must not be transferred across splits."
            )

        if selection.get("selection_count") != "min_class_count":
            raise PairGenerationConfigError(
                "Unsupported pair selection strategy."
            )

        ratio = selection.get("target_ratio")
        if (
            not isinstance(ratio, (int, float))
            or isinstance(ratio, bool)
            or ratio <= 0
        ):
            raise PairGenerationConfigError(
                "pair_selection.target_ratio must be positive."
            )

    def _validate_validation_settings(self) -> None:
        validation = self.get("validation")

        if validation.get("fail_closed") is not True:
            raise PairGenerationConfigError(
                "Validation must use fail-closed behavior."
            )

        parser_timeout = self.get(
            "validation", "parser", "timeout_seconds"
        )
        compiler_timeout = self.get(
            "validation", "compiler", "timeout_seconds"
        )

        for name, timeout in (
            ("parser", parser_timeout),
            ("compiler", compiler_timeout),
        ):
            if (
                not isinstance(timeout, (int, float))
                or isinstance(timeout, bool)
                or timeout <= 0
            ):
                raise PairGenerationConfigError(
                    f"Validation {name} timeout must be positive."
                )