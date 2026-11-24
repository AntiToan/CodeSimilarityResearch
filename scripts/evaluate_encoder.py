"""II.7: score pairs with an encoder (zero-shot or fine-tuned) and report metrics.

Validation: the threshold is selected on validation (best F1) unless
--threshold-from gives one. Test: needs --threshold-from (a threshold
selected on validation) and --confirm-test, and every run is appended to
<output-root>/test_runs.log (rule 10).

Examples:
    python scripts/evaluate_encoder.py --config experiments/configs/codebert_zero_shot.json \
        --run-id II7-codebert-zs-val-01
    python scripts/evaluate_encoder.py --config experiments/configs/codebert_finetune.json \
        --checkpoint <run>/<checkpoint-dir> --run-id II7-codebert-ft-val-01 --device cuda
Outputs: <output-root>/<run-id>/scores.csv and metrics.json (never overwritten).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.experiment import (  # noqa: E402
    ExperimentError,
    environment,
    git_commit,
    load_config,
    log_test_run,
    planned_run_dir,
    read_validation_threshold,
    resolve_dataset_version,
    utc_now,
)

FIRST_COLUMNS = [
    "pair_id", "split", "label", "score", "pair_type", "generation_method",
    "transformation_type", "problem_a_id", "problem_b_id", "sample_a_id", "sample_b_id",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an encoder on pairs (II.7)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--checkpoint", default=None, help="fine-tuned checkpoint folder")
    parser.add_argument("--threshold-from", default=None,
                        help="metrics.json / tuning_report.json / bi_encoder.json from validation")
    parser.add_argument("--confirm-test", action="store_true")
    parser.add_argument("--device", default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--output-root", default="experiments/results")
    parser.add_argument("--allow-unfrozen", action="store_true",
                        help="smoke tests only: accept an empty dataset_version")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        dataset_version = resolve_dataset_version(config, args.allow_unfrozen)
        run_dir = planned_run_dir(args.output_root, args.run_id)
        threshold = threshold_source = None
        if args.threshold_from:
            threshold, threshold_source = read_validation_threshold(args.threshold_from)
        if args.split == "test" and (threshold is None or not args.confirm_test):
            raise ExperimentError(
                "The test split needs --threshold-from (selected on validation) and "
                "--confirm-test; test runs are final evaluation only (rule 10)."
            )
    except ExperimentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    from src.algorithms.codebert import CodeEmbedder, EmbeddingConfig
    from src.evaluation.metrics import evaluate_scores, select_threshold
    from src.models.pair_dataset import DataPaths, fingerprint, load_split
    from src.models.pair_scoring import score_pairs

    overrides = {key: value for key, value in
                 {"device": args.device, "batch_size": args.batch_size}.items() if value is not None}
    if args.checkpoint:
        embedding = EmbeddingConfig.from_checkpoint(args.checkpoint, **overrides)
    else:
        embedding = EmbeddingConfig.from_dict({**config["embedding"], **overrides})

    paths = DataPaths.from_dict(config["data"], base_dir=ROOT)
    rows, codes = load_split(paths, args.split)
    scores, timing = score_pairs(
        CodeEmbedder(embedding), [(r.sample_a_id, r.sample_b_id) for r in rows], codes
    )
    labels = [row.label for row in rows]

    if threshold is None:
        choice = select_threshold(labels, scores)
        threshold, threshold_source = choice.threshold, "selected on this validation run (best F1)"
    metrics = evaluate_scores(labels, scores, threshold)

    run_dir.mkdir(parents=True, exist_ok=False)
    records = []
    for row, score in zip(rows, scores):
        record = row.to_record()
        record["score"] = float(score)
        records.append(record)
    extra_columns = sorted({key for record in records for key in record} - set(FIRST_COLUMNS))
    with (run_dir / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIRST_COLUMNS + extra_columns, restval="")
        writer.writeheader()
        writer.writerows(records)

    report = {
        "experiment_id": config.get("experiment_id"),
        "checkpoint": config.get("checkpoint"),
        "created_at": utc_now(),
        "split": args.split,
        "model": args.checkpoint or embedding.model_name,
        "embedding": asdict(embedding),
        "preprocessing_mode": "raw",
        "dataset": {"version": dataset_version, "fingerprint": fingerprint(paths, [args.split])},
        "threshold": threshold,
        "threshold_selected_on": "validation",
        "threshold_source": threshold_source,
        "metrics": metrics,
        "timing": {
            "programs": timing.programs,
            "pairs": timing.pairs,
            "embed_seconds": timing.embed_seconds,
            "score_seconds": timing.score_seconds,
            "total_seconds": timing.total_seconds,
            "pairs_per_second": timing.pairs / timing.total_seconds if timing.total_seconds else None,
        },
        "config_path": str(args.config),
        "git_commit": git_commit(),
        "environment": environment(),
    }
    (run_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.split == "test":
        log_path = log_test_run(args.output_root, {
            "created_at": report["created_at"],
            "run_id": args.run_id,
            "model": report["model"],
            "config_path": report["config_path"],
            "dataset": report["dataset"],
            "threshold": threshold,
            "threshold_source": threshold_source,
            "git_commit": report["git_commit"],
        })
        print(f"Test run logged in {log_path}")

    print(json.dumps({k: metrics[k] for k in ("pairs", "roc_auc", "precision", "recall", "f1")}, indent=2))
    print(f"Saved: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
