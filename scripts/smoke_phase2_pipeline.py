"""End-to-end smoke test of Phase II on a synthetic dataset (NOT research results).

Builds a toy export in the Phase I layout, then runs the real scripts:
  1. evaluate_encoder.py  zero-shot on validation        (II.7)
  2. train_encoder.py     fine-tune, select on val F1    (II.4/II.5/II.6)
  3. evaluate_encoder.py  the fine-tuned checkpoint      (II.7)
  4. analyze_errors.py    FP/FN tables                   (II.8)
  5. evaluate_encoder.py  on test without a validation threshold -> must be refused

Example (CPU, a few minutes, downloads the model once):
    python scripts/smoke_phase2_pipeline.py --run-id II-smoke-01
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.experiment import ExperimentError, planned_run_dir, utf8_console  # noqa: E402
from src.models.toy_export import write_toy_export  # noqa: E402


def run(script: str, *args: str, expect_ok: bool = True) -> None:
    command = [sys.executable, str(ROOT / "scripts" / script), *args]
    print("$ " + " ".join(command[1:]), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if (completed.returncode == 0) != expect_ok:
        raise SystemExit(f"Unexpected exit code {completed.returncode} from {script}.")


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description="Phase II smoke test on toy data")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--pooling", default="cls", choices=("cls", "mean"))
    parser.add_argument("--mode-token", default=None, help='"<encoder-only>" for UniXcoder')
    parser.add_argument("--output-root", default="experiments/results")
    parser.add_argument("--keep-checkpoint", action="store_true")
    args = parser.parse_args()

    try:
        base = planned_run_dir(args.output_root, args.run_id).resolve()
    except ExperimentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    data = write_toy_export(base / "toy_export")
    results = base / "runs"

    config = {
        "experiment_id": "II-smoke-toy",
        "checkpoint": "II.4-II.8 smoke",
        "dataset_version": None,
        "data": data,
        "embedding": {"model_name": args.model, "max_length": 128, "pooling": args.pooling,
                      "batch_size": 4, "device": "cpu", "mode_token": args.mode_token},
        "train": {"model_name": args.model, "pooling": args.pooling, "max_length": 128,
                  "batch_size": 4, "learning_rate": 2e-5, "epochs": 1, "margin": 0.5,
                  "seed": 42, "mode_token": args.mode_token, "selection_metric": "val_f1"},
        "notes": "Toy data: these numbers check the pipeline only.",
    }
    config_path = base / "toy_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    common = ["--config", str(config_path), "--output-root", str(results), "--allow-unfrozen"]

    run("evaluate_encoder.py", *common, "--run-id", "zero-shot-val")
    run("train_encoder.py", *common, "--run-id", "finetune")
    report = json.loads((results / "finetune" / "tuning_report.json").read_text(encoding="utf-8"))
    checkpoint = report["trials"][0]["best_checkpoint"]
    run("evaluate_encoder.py", *common, "--run-id", "finetuned-val", "--checkpoint", checkpoint)
    run("analyze_errors.py", "--run-dir", str(results / "finetuned-val"))
    run("evaluate_encoder.py", *common, "--run-id", "test-refused", "--split", "test",
        expect_ok=False)

    if not args.keep_checkpoint:
        shutil.rmtree(checkpoint)  # ~500 MB of toy weights
        print(f"Removed toy checkpoint {checkpoint}")
    print(f"Smoke test passed. Outputs: {base}")
    print("Toy data only: these numbers are a pipeline check, not research results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
