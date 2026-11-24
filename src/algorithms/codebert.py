"""Embedding baseline for checkpoint II.2 (CodeBERT, later UniXcoder).

The numeric part (pooling, L2 normalisation, cosine, score mapping) uses
NumPy only, so it can be tested without PyTorch. ``torch`` and
``transformers`` are imported lazily, only when a model is actually loaded.

Score convention: ``score = (cosine + 1) / 2``, a monotonic map of cosine
into [0, 1] as required for every similarity algorithm in the project.
Decision thresholds must be chosen on the validation split, never fixed
in advance.

UniXcoder: set ``mode_token="<encoder-only>"`` and ``pooling="mean"``. The
input then becomes ``<s> <encoder-only> </s> code </s>``, as in the official
``UniXcoder/unixcoder.py`` (microsoft/CodeBERT repository), whose sentence
embedding is the mean over non-padding tokens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

SUPPORTED_POOLING = ("cls", "mean")
CHECKPOINT_META_FILE = "bi_encoder.json"


class EmbeddingError(ValueError):
    """Raised when inputs or intermediate tensors are invalid."""


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "microsoft/codebert-base"
    max_length: int = 512
    pooling: str = "cls"
    batch_size: int = 8
    device: str = "cpu"
    mode_token: str | None = None  # "<encoder-only>" for UniXcoder

    def __post_init__(self) -> None:
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise EmbeddingError("model_name must be a non-empty string.")
        if self.pooling not in SUPPORTED_POOLING:
            raise EmbeddingError(
                f"pooling must be one of {SUPPORTED_POOLING}, got {self.pooling!r}."
            )
        if not isinstance(self.max_length, int) or self.max_length <= 0:
            raise EmbeddingError("max_length must be a positive integer.")
        if not isinstance(self.batch_size, int) or self.batch_size <= 0:
            raise EmbeddingError("batch_size must be a positive integer.")
        if not isinstance(self.device, str) or not self.device.strip():
            raise EmbeddingError("device must be a non-empty string.")
        if self.mode_token is not None:
            if not isinstance(self.mode_token, str) or not self.mode_token.strip():
                raise EmbeddingError("mode_token must be None or a non-empty string.")
            if self.max_length <= 4:
                raise EmbeddingError("max_length must be > 4 when mode_token is used.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EmbeddingConfig":
        """Build a config from a dict; unknown keys are rejected (catches typos)."""
        allowed = {item.name for item in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise EmbeddingError(f"Unknown embedding config keys: {sorted(unknown)}")
        return cls(**dict(data))

    @classmethod
    def from_checkpoint(cls, checkpoint_dir: str | Path, **overrides: Any) -> "EmbeddingConfig":
        """Config for a fine-tuned checkpoint saved by ``src.models.train``.

        Pooling, mode token and max length come from ``bi_encoder.json`` so a
        checkpoint is always evaluated the way it was trained.
        """
        directory = Path(checkpoint_dir)
        meta_path = directory / CHECKPOINT_META_FILE
        if not meta_path.is_file():
            raise EmbeddingError(f"Not a bi-encoder checkpoint (missing {meta_path}).")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if "pooling" not in meta:
            raise EmbeddingError(f"{meta_path} has no 'pooling' entry.")
        values: dict[str, Any] = {
            "model_name": str(directory),
            "pooling": meta["pooling"],
            "max_length": meta.get("max_length", 512),
            "mode_token": meta.get("mode_token"),
        }
        values.update(overrides)
        return cls.from_dict(values)


@dataclass(frozen=True)
class TruncationStats:
    total: int
    truncated: int
    max_tokens: int

    @property
    def rate(self) -> float:
        return self.truncated / self.total if self.total else 0.0


def cls_pool(hidden_states: np.ndarray) -> np.ndarray:
    """Take the first token ([CLS] / <s>) of each sequence: (B, T, D) -> (B, D)."""
    hidden = np.asarray(hidden_states, dtype=np.float64)
    if hidden.ndim != 3 or hidden.shape[1] == 0:
        raise EmbeddingError("hidden_states must have shape (batch, tokens, dim).")
    return hidden[:, 0, :].copy()


def mean_pool(hidden_states: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    """Average token vectors where attention_mask == 1: (B, T, D) -> (B, D)."""
    hidden = np.asarray(hidden_states, dtype=np.float64)
    mask = np.asarray(attention_mask, dtype=np.float64)
    if hidden.ndim != 3:
        raise EmbeddingError("hidden_states must have shape (batch, tokens, dim).")
    if mask.shape != hidden.shape[:2]:
        raise EmbeddingError("attention_mask must have shape (batch, tokens).")
    counts = mask.sum(axis=1)
    if np.any(counts <= 0):
        raise EmbeddingError("Every sequence needs at least one attended token.")
    summed = (hidden * mask[:, :, None]).sum(axis=1)
    return summed / counts[:, None]


def pool(
    hidden_states: np.ndarray,
    attention_mask: np.ndarray,
    pooling: str,
) -> np.ndarray:
    if pooling == "cls":
        return cls_pool(hidden_states)
    if pooling == "mean":
        return mean_pool(hidden_states, attention_mask)
    raise EmbeddingError(f"Unsupported pooling: {pooling!r}")


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Scale each row to unit length; a zero vector is an error, not a silent pass."""
    array = np.asarray(vectors, dtype=np.float64)
    if array.ndim == 1:
        array = array[None, :]
    norms = np.linalg.norm(array, axis=1)
    if np.any(norms == 0.0) or not np.all(np.isfinite(norms)):
        raise EmbeddingError("Cannot normalise a zero or non-finite vector.")
    return array / norms[:, None]


def cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    a = l2_normalize(vector_a)[0]
    b = l2_normalize(vector_b)[0]
    if a.shape != b.shape:
        raise EmbeddingError("Vectors must have the same dimension.")
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def cosine_to_score(cosine: float | np.ndarray) -> float | np.ndarray:
    """Map cosine in [-1, 1] to a similarity score in [0, 1]."""
    score = (np.clip(cosine, -1.0, 1.0) + 1.0) / 2.0
    return float(score) if np.ndim(score) == 0 else score


def similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Pairwise scores in [0, 1] for a batch of embeddings: (N, D) -> (N, N)."""
    unit = l2_normalize(embeddings)
    cosine = np.clip(unit @ unit.T, -1.0, 1.0)
    scores = cosine_to_score(cosine)
    scores = (scores + scores.T) / 2.0
    np.fill_diagonal(scores, 1.0)
    return scores


def build_mode_inputs(
    tokenizer: Any,
    codes: Sequence[str],
    max_length: int,
    mode_token: str,
) -> dict[str, np.ndarray]:
    """UniXcoder-style batch: ``<s> MODE </s> code </s>``, padded to the longest row.

    Code tokens are cut to ``max_length - 4`` first, as in the official
    ``unixcoder.py``. A mode token missing from the vocabulary is an error
    (e.g. ``<encoder_only>`` with an underscore maps to ``<unk>``).
    """
    if max_length <= 4:
        raise EmbeddingError("max_length must be > 4 when mode_token is used.")
    mode_id = tokenizer.convert_tokens_to_ids(mode_token)
    if mode_id is None or mode_id == tokenizer.unk_token_id:
        raise EmbeddingError(f"Tokenizer vocabulary has no token {mode_token!r}.")

    rows = []
    for code in codes:
        tokens = tokenizer.tokenize(code)[: max_length - 4]
        rows.append(
            tokenizer.convert_tokens_to_ids(
                [tokenizer.cls_token, mode_token, tokenizer.sep_token, *tokens, tokenizer.sep_token]
            )
        )
    width = max(len(row) for row in rows)
    input_ids = np.full((len(rows), width), tokenizer.pad_token_id, dtype=np.int64)
    attention_mask = np.zeros((len(rows), width), dtype=np.int64)
    for index, row in enumerate(rows):
        input_ids[index, : len(row)] = row
        attention_mask[index, : len(row)] = 1
    return {"input_ids": input_ids, "attention_mask": attention_mask}


def _validate_codes(codes: Sequence[str]) -> list[str]:
    if isinstance(codes, str):
        raise EmbeddingError("Pass a sequence of code strings, not a single string.")
    items = list(codes)
    if not items:
        raise EmbeddingError("codes must not be empty.")
    for index, code in enumerate(items):
        if not isinstance(code, str) or not code.strip():
            raise EmbeddingError(f"Code at index {index} is empty or not a string.")
    return items


class CodeEmbedder:
    """Turn source code into L2-normalised vectors with a pre-trained encoder.

    ``tokenizer`` and ``model`` can be injected (e.g. in tests); otherwise
    they are loaded from Hugging Face on first use.
    """

    def __init__(
        self,
        config: EmbeddingConfig | None = None,
        *,
        tokenizer: Any = None,
        model: Any = None,
    ) -> None:
        self.config = config or EmbeddingConfig()
        self._tokenizer = tokenizer
        self._model = model

    def _ensure_tokenizer(self) -> Any:
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        return self._tokenizer

    def _ensure_model(self) -> Any:
        if self._model is None:
            from transformers import AutoModel

            model = AutoModel.from_pretrained(self.config.model_name)
            model.to(self.config.device)
            model.eval()
            self._model = model
        return self._model

    def token_lengths(self, codes: Sequence[str]) -> list[int]:
        """Token count per code, including special tokens, before truncation."""
        items = _validate_codes(codes)
        tokenizer = self._ensure_tokenizer()
        if self.config.mode_token:
            # <s> MODE </s> ... </s> adds four tokens around the code.
            return [len(tokenizer.tokenize(code)) + 4 for code in items]
        encoded = tokenizer(items, add_special_tokens=True, truncation=False)
        return [len(ids) for ids in encoded["input_ids"]]

    def truncation_stats(self, codes: Sequence[str]) -> TruncationStats:
        lengths = self.token_lengths(codes)
        limit = self.config.max_length
        return TruncationStats(
            total=len(lengths),
            truncated=sum(length > limit for length in lengths),
            max_tokens=max(lengths),
        )

    def embed(self, codes: Sequence[str]) -> np.ndarray:
        """Return an (N, D) array of unit-length embeddings."""
        import torch

        items = _validate_codes(codes)
        tokenizer = self._ensure_tokenizer()
        model = self._ensure_model()
        size = self.config.batch_size
        chunks: list[np.ndarray] = []

        for start in range(0, len(items), size):
            batch = items[start : start + size]
            if self.config.mode_token:
                arrays = build_mode_inputs(
                    tokenizer, batch, self.config.max_length, self.config.mode_token
                )
                inputs = {key: torch.as_tensor(value) for key, value in arrays.items()}
            else:
                inputs = tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=self.config.max_length,
                    return_tensors="pt",
                )
                inputs = {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs["attention_mask"],
                }
            inputs = {key: value.to(self.config.device) for key, value in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
            hidden = outputs.last_hidden_state.detach().cpu().numpy()
            mask = inputs["attention_mask"].detach().cpu().numpy()
            chunks.append(pool(hidden, mask, self.config.pooling))

        return l2_normalize(np.concatenate(chunks, axis=0))

    def similarity(self, code_a: str, code_b: str) -> float:
        """Score in [0, 1]. Each code is embedded alone, so the result is symmetric."""
        vector_a = self.embed([code_a])[0]
        vector_b = self.embed([code_b])[0]
        return float(cosine_to_score(float(np.clip(np.dot(vector_a, vector_b), -1.0, 1.0))))
