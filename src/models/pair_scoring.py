"""Score pairs with an encoder (zero-shot or fine-tuned), embedding each program once."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

import numpy as np

from src.algorithms.codebert import cosine_to_score


class Embedder(Protocol):
    def embed(self, codes: Sequence[str]) -> np.ndarray: ...


@dataclass(frozen=True)
class ScoringTiming:
    programs: int
    pairs: int
    embed_seconds: float
    score_seconds: float

    @property
    def total_seconds(self) -> float:
        return self.embed_seconds + self.score_seconds


def score_pairs(
    embedder: Embedder,
    pairs: Sequence[tuple[str, str]],
    codes: Mapping[str, str],
) -> tuple[np.ndarray, ScoringTiming]:
    """Score ``(id_a, id_b)`` pairs in [0, 1] as ``(cosine + 1) / 2``.

    Every distinct program is embedded once (sorted ID order, so the run is
    deterministic); a pair score is then a dot product of unit vectors.
    """
    if not pairs:
        raise ValueError("pairs must not be empty.")
    ids = sorted({sample_id for pair in pairs for sample_id in pair})
    missing = [sample_id for sample_id in ids if sample_id not in codes]
    if missing:
        raise KeyError(f"No source code for {len(missing)} samples, e.g. {missing[:3]}")

    start = time.perf_counter()
    vectors = embedder.embed([codes[sample_id] for sample_id in ids])
    embed_seconds = time.perf_counter() - start
    if vectors.shape[0] != len(ids):
        raise ValueError("Embedder returned a wrong number of vectors.")

    start = time.perf_counter()
    position = {sample_id: index for index, sample_id in enumerate(ids)}
    a = vectors[[position[pair[0]] for pair in pairs]]
    b = vectors[[position[pair[1]] for pair in pairs]]
    cosine = np.clip(np.einsum("ij,ij->i", a, b), -1.0, 1.0)
    scores = np.asarray(cosine_to_score(cosine), dtype=np.float64)
    score_seconds = time.perf_counter() - start

    return scores, ScoringTiming(len(ids), len(pairs), embed_seconds, score_seconds)
