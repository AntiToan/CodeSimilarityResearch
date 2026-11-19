import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

# path configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = (
    PROJECT_ROOT / "data" / "processed" / "poj104" / "source"
)
AUDIT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "poj104" / "audit"
)
REPORT_PATH = AUDIT_DIR / "dataset_profile.json"
PLOT_PATH = AUDIT_DIR / "source_length_distribution.png"

# Helpers
def calculate_sha256(content: bytes) -> str:
    """Calculate SHA-256 hash for file content."""
    return hashlib.sha256(content).hexdigest()

def calculate_statistics(values: list[int]) -> dict:
    """Calculate descriptive statistics."""
    if not values:
        return {
            "min": 0,
            "max": 0,
            "mean": 0,
            "median": 0,
        }

    return {
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
        "median": statistics.median(values),
    }

# Profiling
def profile_dataset() -> dict:
    if not DATASET_DIR.is_dir():
        raise FileNotFoundError(
            f"Dataset directory not found: {DATASET_DIR}"
        )

    source_files = sorted(
        file_path 
        for file_path in DATASET_DIR.rglob("*.txt")
        if file_path.is_file()
    )

    file_sizes = []
    line_counts = []
    character_counts = []
    problem_counts = Counter()
    hash_to_files = defaultdict(list)
    empty_files = []
    total_files = len(source_files)

    # process each source file
    for file_path in source_files:
        relative_path = file_path.relative_to(DATASET_DIR).as_posix()
        problem_id = file_path.relative_to(DATASET_DIR).parts[0]
        raw_bytes = file_path.read_bytes()
        source_text = raw_bytes.decode("utf-8")
        file_sizes.append(len(raw_bytes))
        line_counts.append(len(source_text.splitlines()))
        character_counts.append(len(source_text))
        problem_counts[problem_id] += 1
        file_hash = calculate_sha256(raw_bytes)
        hash_to_files[file_hash].append(relative_path)

        if not source_text.strip():
            empty_files.append(relative_path)

    # exact duplicate detection
    duplicate_groups = [
        paths
        for paths in hash_to_files.values()
        if len(paths) > 1
    ]

    duplicate_file_count = sum(
        len(group) for group in duplicate_groups
    )

    # problem distribution
    problem_values = list(problem_counts.values())

    problem_distribution = {
        "number_of_problems": len(problem_counts),
        "min_samples_per_problem": (
            min(problem_values) if problem_values else 0
        ),
        "max_samples_per_problem": (
            max(problem_values) if problem_values else 0
        ),
        "mean_samples_per_problem": (
            round(statistics.mean(problem_values), 2)
            if problem_values else 0
        ),
        "distribution": dict(sorted(problem_counts.items())),
    }

    # Build report
    report = {
        "dataset": "POJ-104",
        "total_samples": total_files,
        "file_size_bytes": calculate_statistics(file_sizes),
        "line_count": calculate_statistics(line_counts),
        "character_count": calculate_statistics(character_counts),
        "problem_distribution": problem_distribution,
        "empty_files": {
            "count": len(empty_files),
            "files": empty_files,
        },
        "exact_duplicates": {
            "duplicate_groups": len(duplicate_groups),
            "duplicate_files": duplicate_file_count,
            "groups": duplicate_groups,
        },
    }

    # save json report
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            report,
            report_file,
            indent=4,
            ensure_ascii=False,
        )

    # plot source length distribution
    plt.figure(figsize=(10, 6))

    plt.hist(line_counts, bins=30)

    plt.title("POJ-104 Source Length Distribution")
    plt.xlabel("Number of Lines per Source File")
    plt.ylabel("Number of Samples")
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150)
    plt.close()

    return report

# entry point
def main():
    report = profile_dataset()

    print("=" * 60)
    print("POJ-104 DATASET PROFILING")
    print("=" * 60)

    print(f"Total samples: {report['total_samples']:,}")

    print("\nFile size (bytes):")
    print(report["file_size_bytes"])

    print("\nSource lines:")
    print(report["line_count"])

    print("\nSource characters:")
    print(report["character_count"])

    print("\nProblem distribution:")
    print(
        f"  Number of problems: "
        f"{report['problem_distribution']['number_of_problems']}"
    )
    print(
        f"  Min samples/problem: "
        f"{report['problem_distribution']['min_samples_per_problem']}"
    )
    print(
        f"  Max samples/problem: "
        f"{report['problem_distribution']['max_samples_per_problem']}"
    )

    print("\nEmpty files:")
    print(report["empty_files"]["count"])

    print("\nExact duplicates:")
    print(
        f"  Duplicate groups: "
        f"{report['exact_duplicates']['duplicate_groups']}"
    )
    print(
        f"  Duplicate files: "
        f"{report['exact_duplicates']['duplicate_files']}"
    )

    print("\nReport saved to:")
    print(REPORT_PATH)

    print("\nHistogram saved to:")
    print(PLOT_PATH)

    print("=" * 60)
    print("DATASET PROFILING COMPLETED")


if __name__ == "__main__":
    main()