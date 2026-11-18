
from pathlib import Path
from collections import defaultdict
import csv
import hashlib

ROOT = Path("data/raw/poj104/ProgramData")
OUT = Path("data/metadata/poj104")
OUT.mkdir(parents=True, exist_ok=True)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

files = sorted(ROOT.rglob("*.txt"))

invalid_utf8 = []
non_code = []
hash_groups = defaultdict(list)

markers = [
    "#include", "int main", "void main",
    "printf(", "scanf(", "cout", "cin",
    "using namespace", "std::"
]

for path in files:
    raw = path.read_bytes()

    # Hash trên dữ liệu byte gốc
    hash_groups[sha256(raw)].append(str(path))

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = None
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                content = raw.decode(encoding)
                invalid_utf8.append({
                    "path": str(path),
                    "fallback_encoding": encoding,
                    "preview": content[:300].replace("\n", " ")
                })
                break
            except UnicodeDecodeError:
                continue

    if content is None:
        invalid_utf8.append({
            "path": str(path),
            "fallback_encoding": "unknown",
            "preview": ""
        })
        continue

    if not any(marker in content for marker in markers):
        non_code.append({
            "path": str(path),
            "preview": content[:500].replace("\n", " ")
        })

duplicates = [
    paths for paths in hash_groups.values()
    if len(paths) > 1
]

def save_csv(filename, rows, fields):
    with open(OUT / filename, "w",
              newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

save_csv(
    "encoding_issues.csv",
    invalid_utf8,
    ["path", "fallback_encoding", "preview"]
)

save_csv(
    "non_code_review.csv",
    non_code,
    ["path", "preview"]
)

duplicate_rows = []
for group_id, paths in enumerate(duplicates, 1):
    for path in paths:
        duplicate_rows.append({
            "group_id": group_id,
            "path": path
        })

save_csv(
    "duplicate_review.csv",
    duplicate_rows,
    ["group_id", "path"]
)

print("INVESTIGATION SUMMARY")
print("Total files:", len(files))
print("Encoding issues:", len(invalid_utf8))
print("Non-code candidates:", len(non_code))
print("Exact duplicate groups:", len(duplicates))
print("Files in duplicate groups:",
      sum(len(g) for g in duplicates))

print("\nReports saved in:", OUT)
