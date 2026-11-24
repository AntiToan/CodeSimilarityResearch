"""Synthetic pair dataset in the Phase I export layout, for tests and smoke runs ONLY.

The programs are hand-written toys and the variants are trivial whitespace
edits; nothing produced from this data is a research result.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Callable, Sequence

TOY_PROGRAMS = [
    "#include <iostream>\nint main() {\n    int a, b;\n    std::cin >> a >> b;\n    std::cout << a + b;\n    return 0;\n}\n",
    "#include <iostream>\nint main() {\n    int n, x, best = -1000000;\n    std::cin >> n;\n    for (int i = 0; i < n; i++) {\n        std::cin >> x;\n        if (x > best) best = x;\n    }\n    std::cout << best;\n}\n",
    "#include <iostream>\nint main() {\n    int n;\n    long long f = 1;\n    std::cin >> n;\n    for (int i = 2; i <= n; i++) f *= i;\n    std::cout << f;\n}\n",
    "#include <iostream>\nint main() {\n    int n, a = 0, b = 1;\n    std::cin >> n;\n    for (int i = 0; i < n; i++) {\n        int t = a + b;\n        a = b;\n        b = t;\n    }\n    std::cout << a;\n}\n",
    "#include <iostream>\n#include <string>\n#include <algorithm>\nint main() {\n    std::string s;\n    std::cin >> s;\n    std::reverse(s.begin(), s.end());\n    std::cout << s;\n}\n",
    "#include <iostream>\n#include <string>\nint main() {\n    std::string s;\n    std::getline(std::cin, s);\n    int count = 0;\n    for (char c : s)\n        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') count++;\n    std::cout << count;\n}\n",
    "#include <iostream>\nint main() {\n    int n;\n    std::cin >> n;\n    bool prime = n > 1;\n    for (int d = 2; d * d <= n; d++)\n        if (n % d == 0) prime = false;\n    std::cout << (prime ? \"YES\" : \"NO\");\n}\n",
    "#include <iostream>\nint main() {\n    int n, a[100];\n    std::cin >> n;\n    for (int i = 0; i < n; i++) std::cin >> a[i];\n    for (int i = 0; i < n; i++)\n        for (int j = 0; j + 1 < n - i; j++)\n            if (a[j] > a[j + 1]) { int t = a[j]; a[j] = a[j + 1]; a[j + 1] = t; }\n    for (int i = 0; i < n; i++) std::cout << a[i] << ' ';\n}\n",
    "#include <iostream>\nint main() {\n    int x, y;\n    std::cin >> x >> y;\n    while (y != 0) {\n        int t = x % y;\n        x = y;\n        y = t;\n    }\n    std::cout << x;\n}\n",
    "#include <iostream>\n#include <string>\nint main() {\n    std::string s;\n    std::cin >> s;\n    bool ok = true;\n    for (size_t i = 0; i < s.size() / 2; i++)\n        if (s[i] != s[s.size() - 1 - i]) ok = false;\n    std::cout << (ok ? \"YES\" : \"NO\");\n}\n",
]

PAIR_COLUMNS = [
    "pair_id", "sample_a_id", "sample_b_id", "label", "pair_type", "split",
    "source_a_id", "source_b_id", "problem_a_id", "problem_b_id",
    "generation_method", "created_seed",
]
REGISTRY_COLUMNS = [
    "variant_id", "original_sample_id", "problem_id", "split", "variant_index",
    "transformation_type", "generation_seed", "validator_version", "validation_status",
    "source_path", "original_source_path", "source_hash", "created_at",
]


def whitespace_variant(code: str) -> str:
    """Tabs instead of 4 spaces and a blank line after each '{'."""
    lines = []
    for line in code.replace("    ", "\t").split("\n"):
        lines.append(line)
        if line.rstrip().endswith("{"):
            lines.append("")
    return "\n".join(lines)


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def _split_of(index: int, total: int) -> str:
    train_end = round(total * 0.6)
    validation_end = train_end + (total - train_end) // 2
    if index < train_end:
        return "train"
    return "validation" if index < validation_end else "test"


def write_toy_export(
    root: str | Path,
    programs: Sequence[str] = TOY_PROGRAMS,
    variant: Callable[[str], str] = whitespace_variant,
) -> dict[str, str]:
    """Write the toy dataset under ``root``; return a ``data`` config (absolute paths)."""
    base = Path(root)
    processed = base / "data" / "processed"
    metadata = processed / "poj104" / "metadata"
    variants_dir = processed / "poj104" / "variants"
    samples, source_splits, registry = [], [], []
    ids_by_split: dict[str, list[str]] = {"train": [], "validation": [], "test": []}
    problem_of: dict[str, str] = {}
    variant_of: dict[str, str] = {}

    for index, code in enumerate(programs):
        problem_id = str(index + 1)
        sample_id = f"toy_{problem_id}_1"
        split = _split_of(index, len(programs))
        relative = Path("poj104") / problem_id / "1.txt"
        (processed / relative).parent.mkdir(parents=True, exist_ok=True)
        (processed / relative).write_bytes(code.encode("utf-8"))  # LF kept
        samples.append({
            "sample_id": sample_id, "problem_id": problem_id, "filename": "1.txt",
            "language": "cpp", "source_path": relative.as_posix(),
            "original_path": f"poj104/ProgramData/{problem_id}/1.txt",
            "file_size_bytes": len(code.encode("utf-8")), "status": "success",
        })
        source_splits.append({"sample_id": sample_id, "problem_id": problem_id, "split": split})

        variant_id = f"{sample_id}_v1"
        text = variant(code)
        variant_path = variants_dir / f"{variant_id}.txt"
        variant_path.parent.mkdir(parents=True, exist_ok=True)
        variant_path.write_bytes(text.encode("utf-8"))
        registry.append({
            "variant_id": variant_id, "original_sample_id": sample_id, "problem_id": problem_id,
            "split": split, "variant_index": 1, "transformation_type": "whitespace",
            "generation_seed": 42, "validator_version": "toy", "validation_status": "PASS",
            "source_path": f"{variant_id}.txt", "original_source_path": relative.as_posix(),
            "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "created_at": "2026-01-01T00:00:00+00:00",
        })
        ids_by_split[split].append(sample_id)
        problem_of[sample_id] = problem_id
        variant_of[sample_id] = variant_id

    pairs: list[dict] = []

    def add(a: str, b: str, label: int, split: str, source_a: str, source_b: str) -> None:
        first, second = sorted((a, b))
        problem = {a: problem_of[source_a], b: problem_of[source_b]}
        source = {a: source_a, b: source_b}
        pairs.append({
            "pair_id": f"pair_{len(pairs) + 1:06d}", "sample_a_id": first, "sample_b_id": second,
            "label": label, "pair_type": "positive" if label else "negative", "split": split,
            "source_a_id": source[first], "source_b_id": source[second],
            "problem_a_id": problem[first], "problem_b_id": problem[second],
            "generation_method": "toy_whitespace" if label else "toy_cross_problem",
            "created_seed": 42,
        })

    for split, ids in ids_by_split.items():
        for sample_id in ids:
            add(sample_id, variant_of[sample_id], 1, split, sample_id, sample_id)
        neighbours = list(zip(ids, ids[1:] + ids[:1])) if len(ids) > 2 else list(zip(ids, ids[1:]))
        for a, b in neighbours:
            add(a, b, 0, split, a, b)

    pairs_dir = base / "data" / "pairs"
    _write_csv(pairs_dir / "pair_index.csv", PAIR_COLUMNS, pairs)
    for split in ids_by_split:
        _write_csv(
            pairs_dir / "splits" / f"{split}.csv",
            ["pair_id"],
            [{"pair_id": p["pair_id"]} for p in pairs if p["split"] == split],
        )
    _write_csv(metadata / "samples.csv", list(samples[0]), samples)
    _write_csv(metadata / "source_splits.csv", ["sample_id", "problem_id", "split"], source_splits)
    _write_csv(metadata / "variant_registry.csv", REGISTRY_COLUMNS, registry)

    return {
        "pairs_dir": str(pairs_dir.resolve()),
        "samples_csv": str((metadata / "samples.csv").resolve()),
        "samples_root": str(processed.resolve()),
        "source_splits_csv": str((metadata / "source_splits.csv").resolve()),
        "variants_csv": str((metadata / "variant_registry.csv").resolve()),
        "variants_root": str(variants_dir.resolve()),
    }
