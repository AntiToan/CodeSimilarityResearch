import os

import numpy as np
import pytest

from src.algorithms.codebert import (
    CodeEmbedder,
    EmbeddingConfig,
    EmbeddingError,
    cls_pool,
    cosine_similarity,
    cosine_to_score,
    l2_normalize,
    mean_pool,
    pool,
    similarity_matrix,
)


class FakeTokenizer:
    """Whitespace tokenizer that mimics the Hugging Face call used for lengths."""

    def __call__(self, codes, add_special_tokens=True, truncation=False):
        extra = 2 if add_special_tokens else 0
        return {"input_ids": [list(range(len(code.split()) + extra)) for code in codes]}


# ---------- config ----------

def test_config_defaults_are_valid():
    config = EmbeddingConfig()
    assert config.model_name == "microsoft/codebert-base"
    assert config.max_length == 512
    assert config.pooling == "cls"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pooling": "max"},
        {"max_length": 0},
        {"batch_size": -1},
        {"model_name": " "},
        {"device": ""},
    ],
)
def test_config_rejects_invalid_values(kwargs):
    with pytest.raises(EmbeddingError):
        EmbeddingConfig(**kwargs)


def test_config_from_dict_rejects_unknown_keys():
    with pytest.raises(EmbeddingError):
        EmbeddingConfig.from_dict({"pooling": "mean", "poolling": "cls"})


def test_config_from_dict_builds_config():
    config = EmbeddingConfig.from_dict({"pooling": "mean", "max_length": 256})
    assert config.pooling == "mean"
    assert config.max_length == 256


# ---------- pooling ----------

def test_cls_pool_takes_first_token():
    hidden = np.arange(2 * 3 * 4, dtype=float).reshape(2, 3, 4)
    np.testing.assert_array_equal(cls_pool(hidden), hidden[:, 0, :])


def test_mean_pool_ignores_padding():
    hidden = np.array([[[1.0, 1.0], [3.0, 3.0], [100.0, 100.0]]])
    mask = np.array([[1, 1, 0]])
    np.testing.assert_allclose(mean_pool(hidden, mask), [[2.0, 2.0]])


def test_mean_pool_rejects_sequence_without_tokens():
    hidden = np.ones((1, 2, 3))
    with pytest.raises(EmbeddingError):
        mean_pool(hidden, np.zeros((1, 2)))


def test_mean_pool_rejects_mask_shape_mismatch():
    with pytest.raises(EmbeddingError):
        mean_pool(np.ones((1, 2, 3)), np.ones((1, 3)))


def test_pool_rejects_unknown_strategy():
    with pytest.raises(EmbeddingError):
        pool(np.ones((1, 2, 3)), np.ones((1, 2)), "max")


# ---------- normalisation, cosine, score ----------

def test_l2_normalize_gives_unit_rows():
    unit = l2_normalize(np.array([[3.0, 4.0], [0.0, 2.0]]))
    np.testing.assert_allclose(np.linalg.norm(unit, axis=1), [1.0, 1.0])


def test_l2_normalize_rejects_zero_vector():
    with pytest.raises(EmbeddingError):
        l2_normalize(np.array([[0.0, 0.0]]))


def test_cosine_similarity_identical_and_symmetric():
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([-2.0, 0.5, 1.0])
    assert cosine_similarity(a, a) == pytest.approx(1.0)
    assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))


@pytest.mark.parametrize(
    ("cosine", "expected"),
    [(1.0, 1.0), (-1.0, 0.0), (0.0, 0.5), (1.5, 1.0), (-3.0, 0.0)],
)
def test_cosine_to_score_maps_into_unit_interval(cosine, expected):
    assert cosine_to_score(cosine) == pytest.approx(expected)


def test_similarity_matrix_properties():
    rng = np.random.default_rng(42)
    scores = similarity_matrix(rng.normal(size=(5, 8)))
    assert scores.shape == (5, 5)
    np.testing.assert_allclose(scores, scores.T)
    np.testing.assert_allclose(np.diag(scores), 1.0)
    assert scores.min() >= 0.0 and scores.max() <= 1.0


# ---------- embedder without a real model ----------

def test_truncation_stats_with_fake_tokenizer():
    embedder = CodeEmbedder(EmbeddingConfig(max_length=5), tokenizer=FakeTokenizer())
    stats = embedder.truncation_stats(["a b", "a b c d", "int x ;"])
    # lengths with 2 special tokens: 4, 6, 5 -> one is over the limit of 5
    assert stats.total == 3
    assert stats.truncated == 1
    assert stats.max_tokens == 6
    assert stats.rate == pytest.approx(1 / 3)


@pytest.mark.parametrize("codes", [[], ["int a;", "   "], "int a;"])
def test_embedder_rejects_invalid_inputs(codes):
    embedder = CodeEmbedder(tokenizer=FakeTokenizer())
    with pytest.raises(EmbeddingError):
        embedder.token_lengths(codes)


# ---------- real model (opt-in: downloads ~500 MB) ----------

@pytest.mark.skipif(
    os.environ.get("RUN_MODEL_TESTS") != "1",
    reason="Set RUN_MODEL_TESTS=1 to download CodeBERT and run this test.",
)
def test_codebert_end_to_end():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")

    embedder = CodeEmbedder(EmbeddingConfig())
    code_a = "int add(int a, int b) { return a + b; }\n"
    code_b = "int add(int x, int y) { return x + y; }\n"

    embeddings = embedder.embed([code_a, code_b])
    assert embeddings.shape == (2, 768)
    np.testing.assert_allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-6)

    score_ab = embedder.similarity(code_a, code_b)
    assert 0.0 <= score_ab <= 1.0
    assert score_ab == pytest.approx(embedder.similarity(code_b, code_a))
    assert embedder.similarity(code_a, code_a) == pytest.approx(1.0, abs=1e-6)


# ---------- UniXcoder-style inputs (mode token) ----------

class FakeModeTokenizer:
    """Tiny vocabulary with the special tokens used by UniXcoder."""

    cls_token, sep_token = "<s>", "</s>"
    pad_token_id, unk_token_id = 1, 3
    vocab = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3, "<encoder-only>": 6}

    def tokenize(self, code):
        return code.split()

    def convert_tokens_to_ids(self, tokens):
        if isinstance(tokens, str):
            return self.vocab.get(tokens, self.unk_token_id)
        return [self.vocab.get(token, 10 + len(token)) for token in tokens]


def test_build_mode_inputs_layout_truncation_and_padding():
    from src.algorithms.codebert import build_mode_inputs

    batch = build_mode_inputs(FakeModeTokenizer(), ["a bb ccc dddd", "a"], 7, "<encoder-only>")
    # <s> <encoder-only> </s> + at most 7 - 4 = 3 code tokens + </s>
    assert batch["input_ids"].tolist() == [
        [0, 6, 2, 11, 12, 13, 2],
        [0, 6, 2, 11, 2, 1, 1],
    ]
    assert batch["attention_mask"].tolist() == [[1] * 7, [1, 1, 1, 1, 1, 0, 0]]


def test_build_mode_inputs_rejects_unknown_mode_token():
    from src.algorithms.codebert import build_mode_inputs

    with pytest.raises(EmbeddingError, match="no token"):
        build_mode_inputs(FakeModeTokenizer(), ["a"], 16, "<encoder_only>")


def test_token_lengths_with_mode_token_counts_four_special_tokens():
    embedder = CodeEmbedder(
        EmbeddingConfig(mode_token="<encoder-only>", pooling="mean"),
        tokenizer=FakeModeTokenizer(),
    )
    assert embedder.token_lengths(["a b c"]) == [7]


@pytest.mark.parametrize("kwargs", [{"mode_token": ""}, {"mode_token": "<m>", "max_length": 4}])
def test_config_rejects_invalid_mode_token(kwargs):
    with pytest.raises(EmbeddingError):
        EmbeddingConfig(**kwargs)


def test_config_from_checkpoint_reads_training_settings(tmp_path):
    import json

    (tmp_path / "bi_encoder.json").write_text(
        json.dumps({"pooling": "mean", "max_length": 256, "mode_token": "<encoder-only>",
                    "threshold": 0.7}),
        encoding="utf-8",
    )
    config = EmbeddingConfig.from_checkpoint(tmp_path, device="cuda")
    assert config.model_name == str(tmp_path)
    assert (config.pooling, config.max_length, config.mode_token, config.device) == (
        "mean", 256, "<encoder-only>", "cuda",
    )
    with pytest.raises(EmbeddingError, match="Not a bi-encoder"):
        EmbeddingConfig.from_checkpoint(tmp_path / "missing")
