"""Training loop for the contrastive bi-encoder (II.4) and checkpoint convention (II.6).

The best checkpoint is chosen on the *validation* split. For now the
criterion is validation loss; once labelled validation pairs exist (after
the pair dataset is frozen), II.5 switches selection to validation F1.

Outputs (only when ``output_dir`` is set):
    <output_dir>/<model>-<dataset_version>-<run_id>-ep<k>/   best checkpoint
    <output_dir>/run_report.json                           config, history, versions
Existing outputs are never overwritten: a rerun needs a new run_id/output_dir.
"""

from __future__ import annotations

import json
import math
import platform
import random
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from src.models.contrastive_model import BiEncoder, contrastive_loss

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


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


@dataclass
class EpochRecord:
    epoch: int
    train_loss: float
    val_loss: float
    is_best: bool


@dataclass
class TrainResult:
    history: list[EpochRecord] = field(default_factory=list)
    best_epoch: int | None = None
    best_val_loss: float = math.inf
    best_checkpoint: str | None = None


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def checkpoint_name(config: TrainConfig, epoch: int) -> str:
    """II.6 convention: <model>-<dataset_version>-<run_id>-ep<k>."""
    model_short = config.model_name.rstrip("/").split("/")[-1]
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


def _batch_loss(
    model: BiEncoder,
    tokenizer: Any,
    batch: list[PairExample],
    config: TrainConfig,
) -> torch.Tensor:
    inputs_a = _tokenize(tokenizer, [pair.code_a for pair in batch], config)
    inputs_b = _tokenize(tokenizer, [pair.code_b for pair in batch], config)
    labels = torch.tensor(
        [pair.label for pair in batch],
        dtype=torch.float32,
        device=config.device,
    )
    cosine = model(inputs_a, inputs_b)
    return contrastive_loss(cosine, labels, margin=config.margin)


def evaluate_loss(
    model: BiEncoder,
    tokenizer: Any,
    pairs: Sequence[PairExample],
    config: TrainConfig,
) -> float:
    model.eval()
    total = 0.0
    with torch.no_grad():
        for batch in _batches(pairs, config.batch_size):
            total += _batch_loss(model, tokenizer, batch, config).item() * len(batch)
    return total / len(pairs)


def save_checkpoint(model: BiEncoder, tokenizer: Any, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    model.encoder.save_pretrained(directory)
    tokenizer.save_pretrained(directory)
    (directory / "bi_encoder.json").write_text(
        json.dumps({"pooling": model.pooling}, indent=2),
        encoding="utf-8",
    )


def _git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError:
        return None
    return completed.stdout.strip() or None


def _environment() -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    try:
        import transformers

        info["transformers"] = transformers.__version__
    except ImportError:
        info["transformers"] = None
    return info


def train(
    model: BiEncoder,
    tokenizer: Any,
    train_pairs: Sequence[PairExample],
    val_pairs: Sequence[PairExample],
    config: TrainConfig,
) -> TrainResult:
    if not train_pairs:
        raise ValueError("train_pairs must not be empty.")
    if not val_pairs:
        raise ValueError("val_pairs must not be empty.")

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
        val_loss = evaluate_loss(model, tokenizer, val_pairs, config)
        if not (math.isfinite(train_loss) and math.isfinite(val_loss)):
            raise FloatingPointError(f"Non-finite loss at epoch {epoch}.")

        is_best = val_loss < result.best_val_loss
        if is_best:
            result.best_epoch = epoch
            result.best_val_loss = val_loss
            if output_dir is not None:
                new_dir = output_dir / checkpoint_name(config, epoch)
                save_checkpoint(model, tokenizer, new_dir)
                previous = result.best_checkpoint
                result.best_checkpoint = str(new_dir)
                if previous is not None:
                    # Keep only the best checkpoint of *this* run.
                    shutil.rmtree(previous)

        result.history.append(EpochRecord(epoch, train_loss, val_loss, is_best))

    if report_path is not None:
        report = {
            "created_at": created_at,
            "config": asdict(config),
            "train_pairs": len(train_pairs),
            "val_pairs": len(val_pairs),
            "history": [asdict(record) for record in result.history],
            "best_epoch": result.best_epoch,
            "best_val_loss": result.best_val_loss,
            "best_checkpoint": result.best_checkpoint,
            "selection_metric": "val_loss",
            "git_commit": _git_commit(),
            "environment": _environment(),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return result
