import csv 
import json 
import statistics
from pathlib import Path

# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "source"
)
AUDIT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "poj104"
    / "audit"
)
REPORT_PATH = AUDIT_DIR / "outlier_analysis.json"
OUTLIERS_CSV = AUDIT_DIR / "outlier_samples.csv"
LARGEST_CSV = AUDIT_DIR / "largest_samples.csv"
TOP_N = 20

# Helpers
def collect_sample_metrics() -> list[dict]:
    """Collect line count and file size for each source."""

    samples = []

    for file_path in sorted(DATASET_DIR.rglob("*.txt")):
        if not file_path.is_file():
            continue

        content = file_path.read_text(encoding="utf-8")

        relative_path = file_path.relative_to(
            DATASET_DIR
        ).as_posix()

        samples.append({
            "relative_path": relative_path,
            "problem_id": file_path.relative_to(
                DATASET_DIR
            ).parts[0],
            "line_count": len(content.splitlines()),
            "file_size_bytes": file_path.stat().st_size,
            "character_count": len(content),
        })

    return samples

def calculate_iqr_threshold(values: list[int]) -> dict:
    """Calculate upper outlier threshold using IQR."""

    if len(values) < 2:
        return {
            "q1": 0,
            "q3": 0,
            "iqr": 0,
            "upper_bound": 0,
        }

    q1, _, q3 = statistics.quantiles(
        values,
        n=4,
        method="inclusive",
    )

    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)

    return {
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "upper_bound": round(upper_bound, 2),
    }

def write_csv(
    output_path: Path,
    samples: list[dict],
) -> None:
    """Write sample metrics to CSV."""

    fields = [
        "relative_path",
        "problem_id",
        "line_count",
        "file_size_bytes",
        "character_count",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(samples)

# Analysis
def analyze_outliers() -> dict:
    if not DATASET_DIR.is_dir():
        raise FileNotFoundError(
            f"Dataset directory not found: {DATASET_DIR}"
        )

    samples = collect_sample_metrics()

    if not samples:
        raise ValueError("No source files found.")

    line_counts = [
        sample["line_count"]
        for sample in samples
    ]

    threshold = calculate_iqr_threshold(line_counts)
    upper_bound = threshold["upper_bound"]

    outliers = [
        sample
        for sample in samples
        if sample["line_count"] > upper_bound
    ]

    largest_samples = sorted(
        samples,
        key=lambda sample: (
            sample["line_count"],
            sample["file_size_bytes"],
        ),
        reverse=True,
    )[:TOP_N]

    # report
    report = {
        "dataset": "POJ-104",
        "method": "IQR",
        "metric": "line_count",
        "total_samples": len(samples),
        "threshold": threshold,
        "outlier_count": len(outliers),
        "outlier_percentage": round(
            len(outliers) / len(samples) * 100,
            4,
        ),
        "outliers": outliers,
        "largest_samples": largest_samples,
    }

    AUDIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            report,
            f,
            indent=4,
            ensure_ascii=False,
        )

    write_csv(OUTLIERS_CSV, outliers)
    write_csv(LARGEST_CSV, largest_samples)

    return report

# Entry point
def main():
    report = analyze_outliers()

    print("=" * 60)
    print("POJ-104 OUTLIER ANALYSIS")
    print("=" * 60)

    print(f"Total samples: {report['total_samples']:,}")

    print("\nIQR threshold:")
    print(report["threshold"])

    print(f"\nOutlier count: {report['outlier_count']}")
    print(f"Outlier percentage: {report['outlier_percentage']}%")

    print("\nTop 20 longest samples:")

    for index, sample in enumerate(
        report["largest_samples"],
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{sample['relative_path']} | "
            f"{sample['line_count']} lines | "
            f"{sample['file_size_bytes']} bytes"
        )

    print("\nReports saved:")
    print(REPORT_PATH)
    print(OUTLIERS_CSV)
    print(LARGEST_CSV)

    print("=" * 60)
    print("OUTLIER ANALYSIS COMPLETED")


if __name__ == "__main__":
    main()