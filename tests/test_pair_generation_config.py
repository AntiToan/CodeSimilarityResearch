
import copy
import json
from pathlib import Path

import pytest

from src.data.pair_generation_config import (
    PairGenerationConfig,
    PairGenerationConfigError,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "pair_generation_config.json"


@pytest.fixture
def config_data():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def temp_config(tmp_path, config_data):
    def write_config(data):
        path = tmp_path / "pair_generation_config.json"
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        return path

    return write_config


def test_load_default_config():
    config = PairGenerationConfig(CONFIG_PATH)

    assert config.dataset_name == "poj104"
    assert config.seed == 42


def test_get_nested_value():
    config = PairGenerationConfig(CONFIG_PATH)

    assert config.get("split", "ratios", "train") == 0.8
    assert config.get("negative_pairs", "target_per_anchor") == 3


def test_resolve_relative_path():
    config = PairGenerationConfig(CONFIG_PATH)

    resolved = config.resolve_path("dataset", "processed_dir")

    assert resolved == (ROOT / "data" / "processed" / "poj104").resolve()


def test_missing_config_file(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(PairGenerationConfigError):
        PairGenerationConfig(missing_path)


def test_invalid_split_ratios(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["split"]["ratios"]["train"] = 0.7

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="must sum to 1.0",
    ):
        PairGenerationConfig(path)


def test_invalid_transformation_probabilities(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["transformations"]["probabilities"]["whitespace"] = 0.8

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="must sum to 1.0",
    ):
        PairGenerationConfig(path)


def test_variant_target_cannot_exceed_maximum(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["variants"]["target_per_original"] = 3
    data["variants"]["max_variants_per_original"] = 2

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="cannot exceed maximum",
    ):
        PairGenerationConfig(path)


def test_negative_pairs_must_be_cross_problem(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["negative_pairs"]["same_problem_allowed"] = True

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="same-problem",
    ):
        PairGenerationConfig(path)


def test_negative_screening_threshold_range(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["negative_screening"]["threshold"] = 1.5

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="must be in",
    ):
        PairGenerationConfig(path)


def test_oversampling_must_be_disabled(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["pair_selection"]["oversampling"] = True

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="must not oversample",
    ):
        PairGenerationConfig(path)


def test_variant_chaining_must_be_disabled(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["variants"]["allow_variant_chaining"] = True

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="must be disabled",
    ):
        PairGenerationConfig(path)


def test_validation_timeout_must_be_positive(temp_config, config_data):
    data = copy.deepcopy(config_data)
    data["validation"]["parser"]["timeout_seconds"] = 0

    path = temp_config(data)

    with pytest.raises(
        PairGenerationConfigError,
        match="timeout must be positive",
    ):
        PairGenerationConfig(path)


def test_config_raw_access():
    config = PairGenerationConfig(CONFIG_PATH)

    assert isinstance(config.raw, dict)
    assert config.raw["pipeline_version"] == "1.0.0"
