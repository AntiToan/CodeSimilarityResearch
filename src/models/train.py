"""Training loop for the contrastive bi-encoder (II.4), validation-based
selection (II.5) and checkpoint convention (II.6).

The best epoch is chosen on the *validation* split, by ``selection_metric``:
- ``val_f1``: F1 at the best threshold on validation (ties -> lower val loss);
  the threshold is stored with the checkpoint and reused, unchanged, on test.
- ``val_loss``: lowest validation loss (for toy/smoke runs).

Outputs (only when ``output_dir`` is set):
    <output_dir>/<model>-<dataset_version>-<run_id>-ep<k>/   best checkpoint
    <output_dir>/run_report.json                           config, history, versions
Existing outputs are never overwritten: a rerun needs a new run_id/output_dir.
"""

from __future__ import annotations

import json
import math
import random
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from src.algorithms.codebert import CHECKPOINT_META_FILE, build_mode_inputs
from src.evaluation.metrics import roc_auc, select_threshold
from src.models.contrastive_model import BiEncoder, contrastive_loss
from src.models.experiment import environment, git_commit

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
SELECTION_METRICS = ("val_f1", "val_loss")


@dataclass(frozen=True)
class PairExample:
    code_a: str
    code_b: str
    label: int  # 1 = similar (positive), 0 = not similar (negative)

    def __post_init__(self) -> None:
        if self.label not in (0, 1):
            raise ValueError("label must be 0 or 1.")
        for name in ("code_a", "code_b"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")


@dataclass(frozen=True)
class TrainConfig:
    model_name: str = "microsoft/codebert-base"
    pooling: str = "cls"
    max_length: int = 512
    batch_size: int = 8
    learning_rate: float = 2e-5
    epochs: int = 3
    margin: float = 0.5
    seed: int = 42
    device: str = "cpu"
    run_id: str = "run"
    dataset_version: str = "unfrozen"
    output_dir: str | None = None
    mode_token: str | None = None  # "<encoder-only>" for UniXcoder
    selection_metric: str = "val_loss"

    def __post_init__(self) -> None:
        for name in ("max_length", "batch_size", "epochs"):
            value = getattr(self, name)
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if not self.learning_rate > 0:
            raise ValueError("learning_rate must be positive.")
        if not -1.0 < self.margin < 1.0:
            raise ValueError("margin must be in (-1, 1).")
        for name in ("run_id", "dataset_version"):
            if not _SAFE_NAME.match(getattr(self, name)):
                raise ValueError(f"{name} may only contain letters, digits, '.', '_' and '-'.")
        if self.selection_metric not in SELECTION_METRICS:
            raise ValueError(f"selection_metric must be one of {SELECTION_METRICS}.")
        if self.mode_token is not None and (
            not isinstance(self.mode_token, str) or not self.mode_token.strip()
        ):
            raise ValueError("mode_token must be None or a non-empty string.")


@dataclass
class EpochRecord:
    epoch: int
    train_loss: float
    val_loss: float
    is_best: bool
    val_f1: float | None = None
    val_threshold: float | None = None
    val_roc_auc: float | None = None


@dataclass
class TrainResult:
    history: list[EpochRecord] = field(default_factory=list)
    best_epoch: int | None = None
    best_val_loss: float = math.inf  # validation loss of the selected epoch
    best_val_f1: float | None = None
    best_threshold: float | None = None
    best_checkpoint: str | None = None


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def checkpoint_name(config: TrainConfig, epoch: int) -> str:
    """II.6 convention: <model>-<dataset_version>-<run_id>-ep<k>."""
    model_short = config.model_name.rstrip("/\\").replace("\\", "/").split("/")[-1]
    return f"{model_short}-{config.dataset_version}-{config.run_id}-ep{epoch}"


def _batches(
    pairs: Sequence[PairExample],
    batch_size: int,
    rng: random.Random | None = None,
) -> list[list[PairExample]]:
    order = list(range(len(pairs)))
    if rng is not None:
        rng.shuffle(order)
    return [
        [pairs[index] for index in order[start : start + batch_size]]
        for start in range(0, len(order), batch_size)
    ]


def _tokenize(tokenizer: Any, codes: list[str], config: TrainConfig) -> dict[str, torch.Tensor]:
    if config.mode_token:
        arrays = build_mode_inputs(tokenizer, codes, config.max_length, config.mode_token)
        encoded = {key: torch.as_tensor(value) for key, value in arrays.items()}
    else:
        encoded = tokenizer(
            codes,
            padding=True,
            truncation=True,
            max_length=config.max_length,
            return_tensors="pt",
        )
    return {
        "input_ids": encoded["input_ids"].to(config.device),
        "attention_mask": encoded["attention_mask"].to(config.device),
    }


def _batch_cosine(
    model: BiEncoder,
    tokenizer: Any,
    batch: list[PairExample],
    config: TrainConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    inputs_a = _tokenize(tokenizer, [pair.code_a for pair in batch], config)
    inputs_b = _tokenize(tokenizer, [pair.code_b for pair in batch], config)
    labels = torch.tensor(
        [pair.label for pair in batch],
        dtype=torch.float32,
        device=config.device,
    )
    return model(inputs_a, inputs_b), labels


def _batch_loss(
    model: BiEncoder,
    tokenizer: Any,
    batch: list[PairExample],
    config: TrainConfig,
) -> torch.Tensor:
    cosine, labels = _batch_cosine(model, tokenizer, batch, config)
    return contrastive_loss(cosine, labels, margin=config.margin)


def evaluate(
    model: BiEncoder,
    tokenizer: Any,
    pairs: Sequence[PairExample],
    config: TrainConfig,
) -> tuple[float, np.ndarray]:
    """Mean contrastive loss and per-pair scores ``(cosine + 1) / 2``."""
    model.eval()
    total = 0.0
    scores: list[np.ndarray] = []
    with torch.no_grad():
        for batch in _batches(pairs, config.batch_size):
            cosine, labels = _batch_cosine(model, tokenizer, batch, config)
            total += contrastive_loss(cosine, labels, margin=config.margin).item() * len(batch)
            scores.append(((cosine.clamp(-1.0, 1.0) + 1.0) / 2.0).cpu().numpy())
    return total / len(pairs), np.concatenate(scores).astype(np.float64)


def evaluate_loss(
    model: BiEncoder,
    tokenizer: Any,
    pairs: Sequence[PairExample],
    config: TrainConfig,
) -> float:
    return evaluate(model, tokenizer, pairs, config)[0]


def save_checkpoint(
    model: BiEncoder,
    tokenizer: Any,
    directory: Path,
    meta: Mapping[str, Any] | None = None,
) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    model.encoder.save_pretrained(directory)
    tokenizer.save_pretrained(directory)
    payload = {"pooling": model.pooling, **(meta or {})}
    (directory / CHECKPOINT_META_FILE).write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def _is_better(
    config: TrainConfig, result: TrainResult, val_loss: float, val_f1: float | None
) -> bool:
    if result.best_epoch is None:
        return True
    if config.selection_metric == "val_loss":
        return val_loss < result.best_val_loss
    assert val_f1 is not None and result.best_val_f1 is not None
    return (val_f1, -val_loss) > (result.best_val_f1, -result.best_val_loss)


def train(
    model: BiEncoder,
    tokenizer: Any,
    train_pairs: Sequence[PairExample],
    val_pairs: Sequence[PairExample],
    config: TrainConfig,
    dataset_info: Mapping[str, Any] | None = None,
) -> TrainResult:
    if not train_pairs:
        raise ValueError("train_pairs must not be empty.")
    if not val_pairs:
        raise ValueError("val_pairs must not be empty.")
    val_labels = np.asarray([pair.label for pair in val_pairs])
    has_both_labels = val_labels.min() != val_labels.max()
    if config.selection_metric == "val_f1" and not has_both_labels:
        raise ValueError("selection_metric='val_f1' needs positive and negative validation pairs.")

    output_dir = Path(config.output_dir) if config.output_dir else None
    report_path = output_dir / "run_report.json" if output_dir else None
    if report_path is not None and report_path.exists():
        raise FileExistsError(f"Run output already exists: {report_path}")

    set_seed(config.seed)
    rng = random.Random(config.seed)
    model.to(config.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    result = TrainResult()
    created_at = datetime.now(timezone.utc).isoformat()

    for epoch in range(1, config.epochs + 1):
        model.train()
        total = 0.0
        for batch in _batches(train_pairs, config.batch_size, rng):
            optimizer.zero_grad()
            loss = _batch_loss(model, tokenizer, batch, config)
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)

        train_loss = total / len(train_pairs)
        val_loss, val_scores = evaluate(model, tokenizer, val_pairs, config)
        if not (math.isfinite(train_loss) and math.isfinite(val_loss)):
            raise FloatingPointError(f"Non-finite loss at epoch {epoch}.")

        val_f1 = val_threshold = val_auc = None
        if has_both_labels:
            choice = select_threshold(val_labels, val_scores)
            val_f1, val_threshold = choice.f1, choice.threshold
            val_auc = roc_auc(val_labels, val_scores)

        is_best = _is_better(config, result, val_loss, val_f1)
        if is_best:
            result.best_epoch = epoch
            result.best_val_loss = val_loss
            result.best_val_f1 = val_f1
            result.best_threshold = val_threshold
            if output_dir is not None:
                new_dir = output_dir / checkpoint_name(config, epoch)
                save_checkpoint(
                    model,
                    tokenizer,
                    new_dir,
                    meta={
                        "base_model": config.model_name,
                        "max_length": config.max_length,
                        "mode_token": config.mode_token,
                        "epoch": epoch,
                        "run_id": config.run_id,
                        "dataset_version": config.dataset_version,
                        "selection_metric": config.selection_metric,
                        "threshold": val_threshold,
                        "threshold_selected_on": "validation" if val_threshold is not None else None,
                    },
                )
                previous = result.best_checkpoint
                result.best_checkpoint = str(new_dir)
                if previous is not None:
                    # Keep only the best checkpoint of *this* run.
                    shutil.rmtree(previous)

        result.history.append(
            EpochRecord(epoch, train_loss, val_loss, is_best, val_f1, val_threshold, val_auc)
        )

    if report_path is not None:
        report = {
            "created_at": created_at,
            "config": asdict(config),
            "dataset": dict(dataset_info or {}),
            "train_pairs": len(train_pairs),
            "val_pairs": len(val_pairs),
            "history": [asdict(record) for record in result.history],
            "selection_metric": config.selection_metric,
            "best_epoch": result.best_epoch,
            "best_val_loss": result.best_val_loss,
            "best_val_f1": result.best_val_f1,
            "best_threshold": result.best_threshold,
            "best_checkpoint": result.best_checkpoint,
            "git_commit": git_commit(),
            "environment": environment(),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return result
