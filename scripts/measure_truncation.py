"""II.2: measure how many POJ-104 programs exceed the encoder's token limit.

Only the tokenizer is needed (no PyTorch, no model weights).

Example:
    python scripts/measure_truncation.py --run-id II2-truncation-codebert
Result: experiments/results/<run-id>/truncation.json (never overwritten).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.algorithms.codebert import CodeEmbedder, EmbeddingConfig  # noqa: E402

DEFAULT_DATASET = "google/code_x_glue_cc_clone_detection_poj104"


def summarize(lengths: list[int], max_length: int) -> dict:
    array = np.asarray(lengths)
    truncated = int((array > max_length).sum())
    return {
        "programs": int(array.size),
        "truncated": truncated,
        "truncated_rate": truncated / array.size,
        "tokens_p50": float(np.percentile(array, 50)),
        "tokens_p90": float(np.percentile(array, 90)),
        "tokens_p95": float(np.percentile(array, 95)),
        "tokens_p99": float(np.percentile(array, 99)),
        "tokens_max": int(array.max()),
    }


def dataset_revision(dataset_id: str) -> str | None:
    try:
        from huggingface_hub import HfApi

        return HfApi().dataset_info(dataset_id).sha
    except Exception:  # network or API problems must not hide the measurement
        return None


def git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, check=False
        )
    except OSError:
        return None
    return completed.stdout.strip() or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test"])
    parser.add_argument("--output-root", default="experiments/results")
    args = parser.parse_args()

    output_path = Path(args.output_root) / args.run_id / "truncation.json"
    if output_path.exists():
        print(f"Refusing to overwrite {output_path}; use a new --run-id.", file=sys.stderr)
        return 1

    import datasets
    import transformers
    from transformers.utils import logging as hf_logging

    hf_logging.set_verbosity_error()  # silence "sequence longer than max" warnings

    embedder = CodeEmbedder(EmbeddingConfig(model_name=args.model, max_length=args.max_length))
    per_split: dict[str, dict] = {}
    split_counts: dict[str, Counter] = {}
    length_of: dict[tuple[str, str], int] = {}
    labels_by_split: dict[str, set[str]] = {}
    rows_loaded = 0
    empty_excluded = 0

    for split in args.splits:
        data = datasets.load_dataset(args.dataset, split=split)
        rows_loaded += len(data)
        kept = [
            (str(label), code)
            for label, code in zip(data["label"], data["code"])
            if isinstance(code, str) and code.strip()
        ]
        empty_excluded += len(data) - len(kept)
        lengths = embedder.token_lengths([code for _, code in kept])
        per_split[split] = summarize(lengths, args.max_length)

        counts: Counter = Counter()
        for (label, code), length in zip(kept, lengths):
            key = (label, hashlib.sha256(code.encode("utf-8")).hexdigest())
            counts[key] += 1
            length_of[key] = length
        split_counts[split] = counts
        labels_by_split[split] = {label for label, _ in kept}

    # The Hugging Face copy repeats whole problems at split boundaries
    # (e.g. problem 65 in train and validation). Count each program once:
    # for every (label, code) keep the largest multiplicity seen in any one
    # split, which preserves genuine duplicates inside a split.
    merged: Counter = Counter()
    for counts in split_counts.values():
        merged |= counts
    all_lengths = [length_of[key] for key, count in merged.items() for _ in range(count)]

    label_splits: dict[str, list[str]] = {}
    for split, labels in labels_by_split.items():
        for label in labels:
            label_splits.setdefault(label, []).append(split)
    shared_labels = sorted(
        (label for label, splits in label_splits.items() if len(splits) > 1),
        key=lambda value: (len(value), value),
    )

    result = {
        "checkpoint": "II.2",
        "measurement": "token length per program, special tokens included",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "model": args.model,
            "max_length": args.max_length,
            "dataset": args.dataset,
            "dataset_revision": dataset_revision(args.dataset),
            "splits": args.splits,
        },
        "overall": summarize(all_lengths, args.max_length),
        "overall_note": "each program counted once (cross-split repeats removed)",
        "per_split": per_split,
        "per_split_note": "splits exactly as published, repeats included",
        "rows_loaded": rows_loaded,
        "cross_split_duplicate_rows": rows_loaded - empty_excluded - len(all_lengths),
        "labels_in_multiple_splits": {label: label_splits[label] for label in shared_labels},
        "empty_programs_excluded": empty_excluded,
        "git_commit": git_commit(),
        "environment": {
            "python": platform.python_version(),
            "transformers": transformers.__version__,
            "datasets": datasets.__version__,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["overall"], indent=2))
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
