"""Read the frozen Phase I pair dataset for Phase II training and evaluation.

Expected layout (docs/pair_design_merged_v3.md, "Output Structure"):

    data/pairs/pair_index.csv                         master pair records
    data/pairs/splits/<split>.csv                     optional; one column: pair_id
    data/processed/poj104/metadata/samples.csv        originals; source_path is
                                                      relative to data/processed
    data/processed/poj104/metadata/variant_registry.csv  variant registry
    data/processed/poj104/metadata/source_splits.csv  split of every original

The pair index is the CSV written by ``src.data.final_dataset_exporter``
(I.8): one file, columns ``PAIR_EXPORT_FIELDS``, the split in its ``split``
column. Its location is ``data.pair_index_csv`` in the config, or
``<pairs_dir>/pair_index.csv`` by default.

Split membership comes from one of two sources, recorded in run reports:

- ``split_files``: ``<pairs_dir>/splits/`` exists, so every split file must
  exist and agree exactly with the index's ``split`` column;
- ``index_column``: no ``splits/`` directory (the I.8 exporter writes none),
  so the ``split`` column of the index is used.

Fail-closed (CLAUDE.md, rule 8): a missing reference, unreadable file, hash
mismatch, split mismatch or inconsistent index raises ``PairDatasetError``.
Code files are only read, never executed.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SPLITS = ("train", "validation", "test")
REQUIRED_PAIR_COLUMNS = (
    "pair_id",
    "sample_a_id",
    "sample_b_id",
    "label",
    "pair_type",
    "split",
    "problem_a_id",
    "problem_b_id",
    "generation_method",
)
PAIR_TYPE_LABEL = {"positive": 1, "negative": 0}
VARIANT_ACCEPTED_STATUS = "PASS"  # VariantRegistry only stores PASS records


class PairDatasetError(ValueError):
    """Raised when the exported dataset is incomplete or inconsistent."""


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise PairDatasetError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _require_columns(path: Path, columns: Iterable[str], required: Iterable[str]) -> None:
    missing = [name for name in required if name not in columns]
    if missing:
        raise PairDatasetError(f"{path} is missing columns: {missing}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


SPLIT_FILES = "split_files"
INDEX_COLUMN = "index_column"


def split_source(pairs_dir: str | Path) -> str:
    """``split_files`` when ``<pairs_dir>/splits`` exists, else ``index_column``."""
    return SPLIT_FILES if (Path(pairs_dir) / "splits").is_dir() else INDEX_COLUMN


@dataclass(frozen=True)
class DataPaths:
    pairs_dir: Path
    samples_csv: Path
    samples_root: Path
    variants_csv: Path | None = None
    variants_root: Path | None = None
    source_splits_csv: Path | None = None
    pair_index_csv: Path | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], base_dir: str | Path = ".") -> "DataPaths":
        allowed = {item.name for item in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise PairDatasetError(f"Unknown data path keys: {sorted(unknown)}")
        base = Path(base_dir)
        values: dict[str, Path | None] = {}
        for name in allowed:
            raw = data.get(name)
            values[name] = None if raw in (None, "") else (base / str(raw))
        if values["pairs_dir"] is None and values["pair_index_csv"] is not None:
            values["pairs_dir"] = values["pair_index_csv"].parent
        if values["pairs_dir"] is None:
            raise PairDatasetError("Data path 'pairs_dir' or 'pair_index_csv' is required.")
        for name in ("samples_csv", "samples_root"):
            if values[name] is None:
                raise PairDatasetError(f"Data path {name!r} is required.")
        if (values["variants_csv"] is None) != (values["variants_root"] is None):
            raise PairDatasetError("variants_csv and variants_root must be given together.")
        return cls(**values)  # type: ignore[arg-type]

    @property
    def index_csv(self) -> Path:
        return self.pair_index_csv or self.pairs_dir / "pair_index.csv"

    @property
    def split_source(self) -> str:
        return split_source(self.pairs_dir)

    def files_to_fingerprint(self, splits: Sequence[str]) -> dict[str, Path]:
        files = {self.index_csv.name: self.index_csv}
        if self.split_source == SPLIT_FILES:
            for split in splits:
                files[f"splits/{split}.csv"] = self.pairs_dir / "splits" / f"{split}.csv"
        for path in (self.samples_csv, self.variants_csv, self.source_splits_csv):
            if path is not None:
                if path.name in files:
                    raise PairDatasetError(f"Two dataset files share the name {path.name!r}.")
                files[path.name] = path
        return files


def fingerprint(paths: DataPaths, splits: Sequence[str]) -> dict[str, str]:
    """sha256 of every dataset file a run depends on (stored in run reports)."""
    result = {}
    for name, path in paths.files_to_fingerprint(splits).items():
        if not path.is_file():
            raise PairDatasetError(f"Missing file: {path}")
        result[name] = sha256_file(path)
    return result


@dataclass(frozen=True)
class PairRow:
    pair_id: str
    sample_a_id: str
    sample_b_id: str
    label: int
    pair_type: str
    split: str
    problem_a_id: str
    problem_b_id: str
    generation_method: str
    extra: Mapping[str, str] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = {name: getattr(self, name) for name in REQUIRED_PAIR_COLUMNS}
        record.update(self.extra)
        return record


def _pair_row(raw: Mapping[str, str], source: Path) -> PairRow:
    pair_id = raw["pair_id"]
    try:
        label = int(raw["label"])
    except (TypeError, ValueError):
        raise PairDatasetError(f"{source}: pair {pair_id} has a non-integer label.") from None
    pair_type = raw["pair_type"]
    if PAIR_TYPE_LABEL.get(pair_type) != label:
        raise PairDatasetError(
            f"{source}: pair {pair_id} has pair_type={pair_type!r} but label={label}."
        )
    if raw["sample_a_id"] == raw["sample_b_id"]:
        raise PairDatasetError(f"{source}: pair {pair_id} is a self-pair.")
    if raw["split"] not in SPLITS:
        raise PairDatasetError(f"{source}: pair {pair_id} has unknown split {raw['split']!r}.")
    for name in REQUIRED_PAIR_COLUMNS:
        if not str(raw[name]).strip():
            raise PairDatasetError(f"{source}: pair {pair_id} has an empty {name!r}.")
    extra = {key: value for key, value in raw.items() if key not in REQUIRED_PAIR_COLUMNS}
    return PairRow(
        pair_id=pair_id,
        sample_a_id=raw["sample_a_id"],
        sample_b_id=raw["sample_b_id"],
        label=label,
        pair_type=pair_type,
        split=raw["split"],
        problem_a_id=raw["problem_a_id"],
        problem_b_id=raw["problem_b_id"],
        generation_method=raw["generation_method"],
        extra=extra,
    )


def load_split_pairs(
    pairs_dir: str | Path, split: str, index_csv: str | Path | None = None
) -> list[PairRow]:
    """Pairs of one split, checked against the master index.

    Order: split-file order when ``<pairs_dir>/splits`` exists, else index order.
    """
    if split not in SPLITS:
        raise PairDatasetError(f"Unknown split {split!r}; expected one of {SPLITS}.")
    root = Path(pairs_dir)
    index_path = Path(index_csv) if index_csv is not None else root / "pair_index.csv"
    columns, index_rows = _read_csv(index_path)
    _require_columns(index_path, columns, REQUIRED_PAIR_COLUMNS)

    index: dict[str, PairRow] = {}
    reverse_keys: set[tuple[str, str]] = set()
    for raw in index_rows:
        row = _pair_row(raw, index_path)
        if row.pair_id in index:
            raise PairDatasetError(f"{index_path}: duplicate pair_id {row.pair_id}.")
        key = tuple(sorted((row.sample_a_id, row.sample_b_id)))
        if key in reverse_keys:
            raise PairDatasetError(f"{index_path}: pair {row.pair_id} repeats an existing pair.")
        reverse_keys.add(key)  # type: ignore[arg-type]
        index[row.pair_id] = row

    if split_source(root) == INDEX_COLUMN:
        selected = [row for row in index.values() if row.split == split]
        return _check_selected(split, selected)

    split_path = root / "splits" / f"{split}.csv"
    split_columns, split_rows = _read_csv(split_path)
    _require_columns(split_path, split_columns, ("pair_id",))
    ids = [raw["pair_id"] for raw in split_rows]
    if len(ids) != len(set(ids)):
        raise PairDatasetError(f"{split_path}: duplicate pair_id entries.")

    selected = []
    for pair_id in ids:
        row = index.get(pair_id)
        if row is None:
            raise PairDatasetError(f"{split_path}: pair {pair_id} is not in {index_path.name}.")
        if row.split != split:
            raise PairDatasetError(
                f"{split_path}: pair {pair_id} is recorded as split {row.split!r}."
            )
        selected.append(row)

    expected = {pid for pid, row in index.items() if row.split == split}
    if expected != set(ids):
        raise PairDatasetError(
            f"{split_path} and {index_path.name} disagree on {len(expected ^ set(ids))} pairs."
        )
    return _check_selected(split, selected)


def _check_selected(split: str, selected: list[PairRow]) -> list[PairRow]:
    if not selected:
        raise PairDatasetError(f"Split {split!r} has no pairs.")
    if {row.label for row in selected} != {0, 1}:
        raise PairDatasetError(f"Split {split!r} lacks positive or negative pairs.")
    return selected


def assert_disjoint_samples(splits: Mapping[str, Sequence[PairRow]]) -> None:
    """Leakage guard (rule 6): a sample may appear in one split only."""
    owner: dict[str, str] = {}
    for split, rows in splits.items():
        for row in rows:
            for sample_id in (row.sample_a_id, row.sample_b_id):
                previous = owner.setdefault(sample_id, split)
                if previous != split:
                    raise PairDatasetError(
                        f"Sample {sample_id} appears in both {previous!r} and {split!r}."
                    )


@dataclass(frozen=True)
class SampleInfo:
    sample_id: str
    kind: str  # "original" or "variant"
    path: Path
    root: Path
    sha256: str | None
    split: str | None
    transformation_type: str


class CodeStore:
    """Resolve sample/variant IDs to source text, with path and hash checks."""

    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths
        self._info: dict[str, SampleInfo] = {}
        self._failed: set[str] = set()
        self._cache: dict[str, str] = {}
        self._load_originals()
        if paths.variants_csv is not None:
            self._load_variants()

    def _load_originals(self) -> None:
        path = self.paths.samples_csv
        columns, rows = _read_csv(path)
        _require_columns(path, columns, ("sample_id", "source_path", "status"))
        splits: dict[str, str] = {}
        if self.paths.source_splits_csv is not None:
            split_path = self.paths.source_splits_csv
            split_columns, split_rows = _read_csv(split_path)
            _require_columns(split_path, split_columns, ("sample_id", "split"))
            splits = {row["sample_id"]: row["split"] for row in split_rows}
        root = self.paths.samples_root
        for row in rows:
            sample_id = row["sample_id"]
            if sample_id in self._info or sample_id in self._failed:
                raise PairDatasetError(f"{path}: duplicate sample_id {sample_id}.")
            if row["status"] != "success":
                self._failed.add(sample_id)
                continue
            self._info[sample_id] = SampleInfo(
                sample_id=sample_id,
                kind="original",
                path=root / row["source_path"],
                root=root,
                sha256=None,
                split=splits.get(sample_id),
                transformation_type="",
            )

    def _load_variants(self) -> None:
        path = self.paths.variants_csv
        assert path is not None and self.paths.variants_root is not None
        columns, rows = _read_csv(path)
        _require_columns(
            path,
            columns,
            ("variant_id", "split", "transformation_type", "validation_status",
             "source_path", "source_hash"),
        )
        root = self.paths.variants_root
        for row in rows:
            variant_id = row["variant_id"]
            if variant_id in self._info or variant_id in self._failed:
                raise PairDatasetError(f"{path}: ID {variant_id} is already used.")
            if row["validation_status"] != VARIANT_ACCEPTED_STATUS:
                self._failed.add(variant_id)
                continue
            source = Path(row["source_path"])
            # The registry currently stores absolute, machine-specific paths;
            # relative paths are resolved against variants_root.
            self._info[variant_id] = SampleInfo(
                sample_id=variant_id,
                kind="variant",
                path=source if source.is_absolute() else root / source,
                root=root,
                sha256=row["source_hash"] or None,
                split=row["split"],
                transformation_type=row["transformation_type"],
            )

    def info(self, sample_id: str) -> SampleInfo:
        if sample_id in self._failed:
            raise PairDatasetError(f"Sample {sample_id} failed preprocessing/validation.")
        try:
            return self._info[sample_id]
        except KeyError:
            raise PairDatasetError(f"Unknown sample {sample_id}.") from None

    def read(self, sample_id: str) -> str:
        if sample_id in self._cache:
            return self._cache[sample_id]
        info = self.info(sample_id)
        path = info.path.resolve()
        if not path.is_relative_to(info.root.resolve()):
            raise PairDatasetError(f"Sample {sample_id}: {path} is outside {info.root}.")
        if not path.is_file():
            raise PairDatasetError(f"Sample {sample_id}: file not found: {path}")
        data = path.read_bytes()
        if info.sha256 is not None and hashlib.sha256(data).hexdigest() != info.sha256:
            raise PairDatasetError(f"Sample {sample_id}: sha256 does not match the registry.")
        try:
            text = data.decode("utf-8")  # processed/generated files are UTF-8
        except UnicodeDecodeError:
            raise PairDatasetError(f"Sample {sample_id}: file is not valid UTF-8.") from None
        if not text.strip():
            raise PairDatasetError(f"Sample {sample_id}: file is empty.")
        self._cache[sample_id] = text
        return text

    def check_pair(self, row: PairRow) -> PairRow:
        """Split checks for both members; returns the row with transformation info added."""
        transformations = []
        for sample_id in (row.sample_a_id, row.sample_b_id):
            info = self.info(sample_id)
            if info.split is not None and info.split != row.split:
                raise PairDatasetError(
                    f"Pair {row.pair_id}: {sample_id} belongs to {info.split!r}, "
                    f"pair is in {row.split!r}."
                )
            if info.transformation_type:
                transformations.append(info.transformation_type)
        extra = dict(row.extra)
        extra.setdefault("transformation_type", "+".join(transformations))
        return replace(row, extra=extra)


def load_split(
    paths: DataPaths, split: str, store: CodeStore | None = None
) -> tuple[list[PairRow], dict[str, str]]:
    """Checked pairs of one split plus the source text of every sample they use."""
    store = store or CodeStore(paths)
    rows = [
        store.check_pair(row)
        for row in load_split_pairs(paths.pairs_dir, split, paths.index_csv)
    ]
    codes: dict[str, str] = {}
    for row in rows:
        for sample_id in (row.sample_a_id, row.sample_b_id):
            if sample_id not in codes:
                codes[sample_id] = store.read(sample_id)
    return rows, codes
