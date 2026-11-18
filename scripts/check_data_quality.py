from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json

DATASET_DIR = Path("data/raw/poj104")
OUTPUT_DIR = Path("data/metadata/poj104")

def sha256(content):
    return hashlib.sha256(content).hexdigest()

def main():
    files = sorted(DATASET_DIR.rglob("*.txt"))

    stats = {
        "total_files": len(files),
        "readable_files": 0,
        "empty_files": [],
        "invalid_utf8_files": [],
        "very_small_files": [],
        "very_large_files": [],
        "non_code_files": [],
    }

    extensions = Counter()
    duplicate_groups = defaultdict(list)
    sizes = []

    for path in files:
        try:
            raw = path.read_bytes()
            size = len(raw)
            sizes.append(size)

            if size == 0:
                stats["empty_files"].append(str(path))
                continue

            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                stats["invalid_utf8_files"].append(str(path))
                continue

            stats["readable_files"] += 1
            extensions[path.suffix.lower()] += 1

            if size < 50:
                stats["very_small_files"].append(str(path))

            if size > 100_000:
                stats["very_large_files"].append(str(path))

            # Heuristic check dấu hiệu mã C/C++
            code_markers = [
                "#include", "int main", "void main",
                "printf(", "scanf(", "cout", "cin",
                "using namespace", "std::"
            ]

            if not any(marker in content for marker in code_markers):
                stats["non_code_files"].append(str(path))

            duplicate_groups[sha256(raw)].append(str(path))

        except OSError:
            stats.setdefault("unreadable_files", []).append(str(path))

    duplicate_groups = [
        paths for paths in duplicate_groups.values()
        if len(paths) > 1 
    ]

    stats["duplicate_group_count"] = len(duplicate_groups)
    stats["duplicate_file_count"] = sum(
        len(group) for group in duplicate_groups
    )

    stats["file_size_bytes"] = {
        "min": min(sizes) if sizes else 0,
        "max": max(sizes) if sizes else 0,
        "average": round(sum(sizes) / len(sizes), 2)
        if sizes else 0,
    }

    stats["duplicate_groups"] = duplicate_groups

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "data_quality_report.json"
    output_file.write_text(
        json.dumps(stats, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("=" * 50)
    print("POJ-104 DATA QUALITY REPORT")
    print("=" * 50)

    for key, value in stats.items():
        if key != "duplicate_groups":
            print(f"{key}: {value}")

    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()