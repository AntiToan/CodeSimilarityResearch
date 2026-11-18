
from pathlib import Path
from collections import Counter
import csv

DATASET_DIR = Path("data/raw/poj104")

def main():
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_DIR}")

    files = [
        path for path in DATASET_DIR.rglob("*")
        if path.is_file() and path.name != "programs.tar.gz"
    ]

    extensions = Counter()
    problem_counts = Counter()
    empty_files = []
    unreadable_files = []

    for path in files:
        extensions[path.suffix.lower() or "[no extension]"] += 1

        # Giả định thư mục cha trực tiếp là Problem ID.
        problem_id = path.parent.name
        problem_counts[problem_id] += 1

        try:
            if path.stat().st_size == 0:
                empty_files.append(str(path))
        except OSError:
            unreadable_files.append(str(path))

    print("=" * 50)
    print("POJ-104 DATASET INSPECTION")
    print("=" * 50)

    print(f"Total files: {len(files)}")
    print(f"Empty files: {len(empty_files)}")
    print(f"Unreadable files: {len(unreadable_files)}")

    print("\nFile extensions:")
    for ext, count in extensions.most_common():
        print(f"  {ext}: {count}")

    print(f"\nNumber of immediate parent folders: {len(problem_counts)}")
    print("Files per immediate parent folder:")
    for problem_id, count in sorted(problem_counts.items()):
        print(f"  {problem_id}: {count}")

    output_dir = Path("data/metadata/poj104")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "inspection_report.csv",
              "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["problem_id", "file_count"])
        for problem_id, count in sorted(problem_counts.items()):
            writer.writerow([problem_id, count])

    print("\nReport saved to data/metadata/poj104/inspection_report.csv")

if __name__ == "__main__":
    main()
