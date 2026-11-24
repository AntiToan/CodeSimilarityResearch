"""II.4/II.5: fine-tune a bi-encoder on the frozen pair dataset, optionally over a grid.

Every trial trains on `train` and is judged on `validation` only (rule 10);
the test split is never loaded here.

Example (Colab GPU):
    python scripts/train_encoder.py --config experiments/configs/codebert_finetune.json \
        --run-id II5-codebert-01 --device cuda --output-root /content/drive/MyDrive/codesim
Outputs: <output-root>/<run-id>/ (tuning_report.json, run_report.json per trial, best checkpoint per trial).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.experiment import (  # noqa: E402
    ExperimentError,
    git_commit,
    load_config,
    planned_run_dir,
    resolve_dataset_version,
    utc_now,
    utf8_console,
)
from src.models.pair_dataset import (  # noqa: E402
    CodeStore,
    DataPaths,
    assert_disjoint_samples,
    fingerprint,
    load_split,
)
from src.models.tuning import best_trial, expand_grid, trial_run_id  # noqa: E402

RESERVED_TRAIN_KEYS = {"run_id", "dataset_version", "output_dir", "device"}


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description="Fine-tune a bi-encoder (II.4/II.5)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output-root", default="experiments/results")
    parser.add_argument("--max-train-pairs", type=int, default=None,
                        help="pilot run on a seeded random subset of train pairs")
    parser.add_argument("--allow-unfrozen", action="store_true",
                        help="smoke tests only: accept an empty dataset_version")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        dataset_version = resolve_dataset_version(config, args.allow_unfrozen)
        run_dir = planned_run_dir(args.output_root, args.run_id)
        base = dict(config.get("train", {}))
        reserved = RESERVED_TRAIN_KEYS & set(base)
        if reserved:
            raise ExperimentError(f"'train' must not set {sorted(reserved)}; they come from the CLI.")
    except ExperimentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    import torch
    from transformers import AutoTokenizer

    from src.models.contrastive_model import BiEncoder
    from src.models.train import PairExample, TrainConfig, train

    paths = DataPaths.from_dict(config["data"], base_dir=ROOT)
    store = CodeStore(paths)
    train_rows, train_codes = load_split(paths, "train", store)
    val_rows, val_codes = load_split(paths, "validation", store)
    assert_disjoint_samples({"train": train_rows, "validation": val_rows})

    seed = int(base.get("seed", 42))
    used_rows = sorted(train_rows, key=lambda row: row.pair_id)
    if args.max_train_pairs is not None and args.max_train_pairs < len(used_rows):
        used_rows = random.Random(seed).sample(used_rows, args.max_train_pairs)

    def examples(rows, codes):
        return [PairExample(codes[r.sample_a_id], codes[r.sample_b_id], r.label) for r in rows]

    train_examples = examples(used_rows, train_codes)
    val_examples = examples(val_rows, val_codes)
    dataset_info = {
        "version": dataset_version,
        "fingerprint": fingerprint(paths, ["train", "validation"]),
        "split_source": paths.split_source,
        "train_pairs_total": len(train_rows),
        "train_pairs_used": len(train_examples),
        "train_subset_seed": seed if len(train_examples) < len(train_rows) else None,
        "validation_pairs": len(val_examples),
    }

    trials = expand_grid(config.get("grid"))
    summaries = []
    for index, overrides in enumerate(trials, start=1):
        trial_id = trial_run_id(args.run_id, index, len(trials))
        train_config = TrainConfig(
            **{**base, **overrides},
            device=args.device,
            run_id=trial_id,
            dataset_version=dataset_version,
            output_dir=str(run_dir if len(trials) == 1 else run_dir / trial_id),
        )
        print(f"[{index}/{len(trials)}] {trial_id} {overrides}", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(train_config.model_name)
        model = BiEncoder.from_pretrained(train_config.model_name, pooling=train_config.pooling)
        result = train(model, tokenizer, train_examples, val_examples, train_config, dataset_info)
        summaries.append(
            {
                "run_id": trial_id,
                "overrides": overrides,
                "best_epoch": result.best_epoch,
                "best_val_loss": result.best_val_loss,
                "best_val_f1": result.best_val_f1,
                "best_threshold": result.best_threshold,
                "best_checkpoint": result.best_checkpoint,
            }
        )
        print(f"    best epoch {result.best_epoch}: val_f1={result.best_val_f1} "
              f"val_loss={result.best_val_loss:.4f}", flush=True)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    report = {
        "experiment_id": config.get("experiment_id"),
        "checkpoint": config.get("checkpoint"),
        "created_at": utc_now(),
        "config_path": str(args.config),
        "config": config,
        "device": args.device,
        "dataset": dataset_info,
        "selection": "best validation F1 (ties: lower validation loss); test split not used",
        "trials": summaries,
        "best_trial": best_trial(summaries) if all(s["best_val_f1"] is not None for s in summaries) else None,
        "git_commit": git_commit(),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "tuning_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved: {run_dir / 'tuning_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
