"""Bi-encoder and contrastive loss for checkpoint II.3.

Both code fragments are encoded by the *same* encoder (shared weights),
pooled into one vector each, L2-normalised, and compared with cosine.
Pooling matches ``src.algorithms.codebert`` so zero-shot and fine-tuned
scores are computed the same way.
"""

from __future__ import annotations

from typing import Mapping

import torch
import torch.nn.functional as F

SUPPORTED_POOLING = ("cls", "mean")


class BiEncoder(torch.nn.Module):
    def __init__(self, encoder: torch.nn.Module, pooling: str = "cls") -> None:
        if pooling not in SUPPORTED_POOLING:
            raise ValueError(f"pooling must be one of {SUPPORTED_POOLING}, got {pooling!r}.")
        super().__init__()
        self.encoder = encoder
        self.pooling = pooling

    @classmethod
    def from_pretrained(cls, model_name: str, pooling: str = "cls") -> "BiEncoder":
        from transformers import AutoModel

        return cls(AutoModel.from_pretrained(model_name), pooling=pooling)

    def encode(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """(B, T) token ids -> (B, D) unit-length vectors."""
        hidden = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        ).last_hidden_state

        if self.pooling == "cls":
            vectors = hidden[:, 0]
        else:
            mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
            vectors = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)

        return F.normalize(vectors, p=2, dim=-1)

    def forward(
        self,
        batch_a: Mapping[str, torch.Tensor],
        batch_b: Mapping[str, torch.Tensor],
    ) -> torch.Tensor:
        """Cosine similarity per pair, shape (B,)."""
        vectors_a = self.encode(batch_a["input_ids"], batch_a["attention_mask"])
        vectors_b = self.encode(batch_b["input_ids"], batch_b["attention_mask"])
        return (vectors_a * vectors_b).sum(dim=-1)


def contrastive_loss(
    cosine: torch.Tensor,
    labels: torch.Tensor,
    margin: float = 0.5,
) -> torch.Tensor:
    """Cosine form of the contrastive loss (Hadsell, Chopra, LeCun, 2006).

    label 1 (similar):     (1 - cos)^2
    label 0 (not similar): max(0, cos - margin)^2
    """
    if not -1.0 < margin < 1.0:
        raise ValueError("margin must be in (-1, 1).")
    if cosine.shape != labels.shape:
        raise ValueError("cosine and labels must have the same shape.")

    labels = labels.to(cosine.dtype)
    if torch.any((labels != 0) & (labels != 1)):
        raise ValueError("labels must be 0 or 1.")

    positive = labels * (1.0 - cosine).pow(2)
    negative = (1.0 - labels) * torch.clamp(cosine - margin, min=0.0).pow(2)
    return (positive + negative).mean()
