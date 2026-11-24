"""Tests for the II.3 bi-encoder/loss and the II.4 training loop.

A tiny randomly initialised RoBERTa and a whitespace tokenizer are built
locally, so no model is downloaded.
"""

import json
import math

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from src.models.contrastive_model import BiEncoder, contrastive_loss  # noqa: E402
from src.models.train import (  # noqa: E402
    PairExample,
    TrainConfig,
    checkpoint_name,
    train,
)

PAD_ID, BOS_ID, EOS_ID, VOCAB = 1, 0, 2, 64


def tiny_encoder():
    torch.manual_seed(0)
    config = transformers.RobertaConfig(
        vocab_size=VOCAB,
        hidden_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=32,
        max_position_embeddings=64,
        hidden_dropout_prob=0.0,
        attention_probs_dropout_prob=0.0,
        pad_token_id=PAD_ID,
        bos_token_id=BOS_ID,
        eos_token_id=EOS_ID,
    )
    return transformers.RobertaModel(config)


class WhitespaceTokenizer:
    """Deterministic stand-in for a Hugging Face tokenizer."""

    def _ids(self, code):
        return [3 + sum(ord(char) for char in token) % (VOCAB - 3) for token in code.split()]

    def __call__(self, codes, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        rows = [[BOS_ID] + self._ids(code)[: max_length - 2] + [EOS_ID] for code in codes]
        width = max(len(row) for row in rows)
        input_ids = [row + [PAD_ID] * (width - len(row)) for row in rows]
        mask = [[1] * len(row) + [0] * (width - len(row)) for row in rows]
        return {
            "input_ids": torch.tensor(input_ids),
            "attention_mask": torch.tensor(mask),
        }

    def save_pretrained(self, directory):
        (directory / "tokenizer.json").write_text("{}", encoding="utf-8")


TOY_CODES = [
    "int a , b ; cin >> a >> b ; cout << a + b ;",
    "int n ; long long f = 1 ; for ( int i = 2 ; i <= n ; i ++ ) f *= i ;",
    "string s ; reverse ( s . begin ( ) , s . end ( ) ) ; cout << s ;",
    "int x , y ; while ( y ) { int t = x % y ; x = y ; y = t ; }",
]


def toy_pairs():
    pairs = []
    for index, code in enumerate(TOY_CODES):
        pairs.append(PairExample(code, code + " ;", 1))
        pairs.append(PairExample(code, TOY_CODES[(index + 1) % len(TOY_CODES)], 0))
    return pairs


# ---------- contrastive loss ----------

def test_loss_is_zero_for_perfect_pairs():
    cosine = torch.tensor([1.0, 0.2])
    labels = torch.tensor([1.0, 0.0])
    assert contrastive_loss(cosine, labels, margin=0.5).item() == pytest.approx(0.0)


def test_loss_penalises_similar_negative_and_distant_positive():
    negative = contrastive_loss(torch.tensor([0.9]), torch.tensor([0.0]), margin=0.5)
    positive = contrastive_loss(torch.tensor([0.0]), torch.tensor([1.0]), margin=0.5)
    assert negative.item() == pytest.approx(0.16)
    assert positive.item() == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("cosine", "labels", "margin"),
    [
        (torch.tensor([0.5]), torch.tensor([1.0, 0.0]), 0.5),
        (torch.tensor([0.5]), torch.tensor([2.0]), 0.5),
        (torch.tensor([0.5]), torch.tensor([1.0]), 1.0),
    ],
)
def test_loss_rejects_invalid_inputs(cosine, labels, margin):
    with pytest.raises(ValueError):
        contrastive_loss(cosine, labels, margin=margin)


# ---------- bi-encoder ----------

def test_bi_encoder_rejects_unknown_pooling():
    with pytest.raises(ValueError):
        BiEncoder(tiny_encoder(), pooling="max")


@pytest.mark.parametrize("pooling", ["cls", "mean"])
def test_bi_encoder_outputs_unit_vectors_and_symmetric_cosine(pooling):
    model = BiEncoder(tiny_encoder(), pooling=pooling).eval()
    tokenizer = WhitespaceTokenizer()
    batch_a = tokenizer(TOY_CODES[:2])
    batch_b = tokenizer(TOY_CODES[2:])

    with torch.no_grad():
        vectors = model.encode(**batch_a)
        ab = model(batch_a, batch_b)
        ba = model(batch_b, batch_a)
        aa = model(batch_a, batch_a)

    assert vectors.shape == (2, 16)
    torch.testing.assert_close(vectors.norm(dim=-1), torch.ones(2))
    torch.testing.assert_close(ab, ba)
    torch.testing.assert_close(aa, torch.ones(2))


def test_mean_pooling_ignores_padding():
    model = BiEncoder(tiny_encoder(), pooling="mean").eval()
    tokenizer = WhitespaceTokenizer()
    alone = tokenizer([TOY_CODES[0]])
    padded = tokenizer([TOY_CODES[0], TOY_CODES[1]])  # TOY_CODES[0] gets padding

    with torch.no_grad():
        vector_alone = model.encode(**alone)[0]
        vector_padded = model.encode(**padded)[0]

    torch.testing.assert_close(vector_alone, vector_padded, atol=1e-5, rtol=1e-5)


# ---------- training loop ----------

def test_pair_example_and_config_validation():
    with pytest.raises(ValueError):
        PairExample("int a;", "int b;", 2)
    with pytest.raises(ValueError):
        PairExample("   ", "int b;", 1)
    with pytest.raises(ValueError):
        TrainConfig(run_id="../escape")
    with pytest.raises(ValueError):
        TrainConfig(learning_rate=0.0)


def test_checkpoint_name_follows_convention():
    config = TrainConfig(dataset_version="v1.0", run_id="r01")
    assert checkpoint_name(config, 2) == "codebert-base-v1.0-r01-ep2"


def test_training_reduces_loss_and_keeps_only_best_checkpoint(tmp_path):
    output_dir = tmp_path / "run"
    config = TrainConfig(
        batch_size=4,
        learning_rate=1e-2,
        epochs=8,
        max_length=32,
        run_id="toy",
        dataset_version="toy",
        output_dir=str(output_dir),
    )
    pairs = toy_pairs()
    model = BiEncoder(tiny_encoder(), pooling="cls")

    result = train(model, WhitespaceTokenizer(), pairs, pairs, config)

    assert len(result.history) == 8
    assert all(math.isfinite(record.train_loss) for record in result.history)
    assert result.history[-1].train_loss < result.history[0].train_loss

    saved = [path for path in output_dir.iterdir() if path.is_dir()]
    assert [path.name for path in saved] == [checkpoint_name(config, result.best_epoch)]
    assert (saved[0] / "bi_encoder.json").exists()

    report = json.loads((output_dir / "run_report.json").read_text(encoding="utf-8"))
    assert report["best_epoch"] == result.best_epoch
    assert len(report["history"]) == 8
    assert report["environment"]["torch"] == torch.__version__


def test_training_refuses_to_overwrite_previous_run(tmp_path):
    config = TrainConfig(
        batch_size=4,
        learning_rate=1e-3,
        epochs=1,
        max_length=32,
        run_id="toy",
        dataset_version="toy",
        output_dir=str(tmp_path),
    )
    pairs = toy_pairs()
    train(BiEncoder(tiny_encoder()), WhitespaceTokenizer(), pairs, pairs, config)

    with pytest.raises(FileExistsError):
        train(BiEncoder(tiny_encoder()), WhitespaceTokenizer(), pairs, pairs, config)


def test_training_rejects_empty_splits():
    model = BiEncoder(tiny_encoder())
    with pytest.raises(ValueError):
        train(model, WhitespaceTokenizer(), [], toy_pairs(), TrainConfig())


# ---------- II.5: selection on validation F1 ----------

def test_val_f1_selection_stores_validation_threshold(tmp_path):
    output_dir = tmp_path / "run"
    config = TrainConfig(
        batch_size=4,
        learning_rate=1e-2,
        epochs=3,
        max_length=32,
        run_id="toy",
        dataset_version="toy",
        output_dir=str(output_dir),
        selection_metric="val_f1",
    )
    pairs = toy_pairs()
    result = train(BiEncoder(tiny_encoder()), WhitespaceTokenizer(), pairs, pairs, config,
                   dataset_info={"version": "toy"})

    assert result.best_val_f1 is not None and 0.0 <= result.best_val_f1 <= 1.0
    assert all(record.val_f1 is not None and record.val_roc_auc is not None
               for record in result.history)
    best = max(result.history, key=lambda r: (r.val_f1, -r.val_loss))
    assert result.best_epoch == best.epoch

    meta = json.loads((output_dir / checkpoint_name(config, result.best_epoch)
                       / "bi_encoder.json").read_text(encoding="utf-8"))
    assert meta["threshold"] == result.best_threshold
    assert meta["threshold_selected_on"] == "validation"
    assert meta["selection_metric"] == "val_f1"

    report = json.loads((output_dir / "run_report.json").read_text(encoding="utf-8"))
    assert report["best_val_f1"] == result.best_val_f1
    assert report["dataset"] == {"version": "toy"}


def test_val_f1_selection_needs_both_labels_in_validation():
    config = TrainConfig(selection_metric="val_f1", max_length=32)
    positives = [pair for pair in toy_pairs() if pair.label == 1]
    with pytest.raises(ValueError, match="positive and negative"):
        train(BiEncoder(tiny_encoder()), WhitespaceTokenizer(), toy_pairs(), positives, config)


def test_config_rejects_unknown_selection_metric():
    with pytest.raises(ValueError):
        TrainConfig(selection_metric="accuracy")
