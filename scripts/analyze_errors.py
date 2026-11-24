"""II.8: false positive / false negative analysis of an evaluation run.

Reads <run-dir>/scores.csv and the threshold in <run-dir>/metrics.json,
writes <run-dir>/error_analysis.json and <run-dir>/errors.csv (never overwritten).

Example:
    python scripts/analyze_errors.py --run-dir experiments/results/II7-codebert-zs-val-01
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.error_analysis import analyze_errors, error_rows  # noqa: E402
from src.models.experiment import utf8_console  # noqa: E402

DEFAULT_GROUPS = ["pair_type", "generation_method", "transformation_type", "problem_a_id"]


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description="FP/FN analysis of an evaluation run (II.8)")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--group-by", nargs="*", default=DEFAULT_GROUPS)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    outputs = [run_dir / "error_analysis.json", run_dir / "errors.csv"]
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        print(f"Refusing to overwrite {existing}.", file=sys.stderr)
        return 2

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    threshold = float(metrics["threshold"])
    with (run_dir / "scores.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    analysis = analyze_errors(rows, threshold, group_fields=args.group_by, top_k=args.top)
    analysis.update(
        split=metrics.get("split"),
        model=metrics.get("model"),
        source_run=str(run_dir),
        note="Scores rank pairs for review; they are not a plagiarism verdict.",
    )
    outputs[0].write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    errors = error_rows(rows, threshold)
    columns = ["pair_id", "outcome", "label", "score", "margin"]
    columns += [key for key in (rows[0].keys() if rows else []) if key not in columns]
    with outputs[1].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(errors)

    counts = analysis["counts"]
    print(f"threshold={threshold:.4f} FP={counts['fp']} FN={counts['fn']} "
          f"(TP={counts['tp']}, TN={counts['tn']})")
    print(f"Saved: {outputs[0]} and {outputs[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
