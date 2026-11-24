"""Tests for reading the frozen Phase I export (fail-closed) and for pair scoring."""

import csv
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from src.data.final_dataset_exporter import FinalDatasetExporter
from src.data.pair_models import PairRecord, PairSplit, PairType
from src.models.pair_dataset import (
    INDEX_COLUMN,
    SPLIT_FILES,
    CodeStore,
    DataPaths,
    PairDatasetError,
    assert_disjoint_samples,
    fingerprint,
    load_split,
    load_split_pairs,
)
from src.models.pair_scoring import score_pairs
from src.models.toy_export import TOY_PROGRAMS, write_toy_export


@pytest.fixture
def export(tmp_path):
    data = write_toy_export(tmp_path / "export")
    return DataPaths.from_dict(data)


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def edit_csv(path: Path, change) -> None:
    rows = read_rows(path)
    change(rows)
    write_rows(path, rows)


# ---------- happy path ----------

def test_load_split_returns_checked_pairs_and_code(export):
    rows, codes = load_split(export, "train")
    assert len(rows) == 12  # 6 positives + 6 negatives
    assert {row.label for row in rows} == {0, 1}
    assert all(row.split == "train" for row in rows)
    positive = next(row for row in rows if row.label == 1)
    assert positive.extra["transformation_type"] == "whitespace"
    assert codes[positive.sample_a_id] == TOY_PROGRAMS[int(positive.problem_a_id) - 1]
    assert "\t" in codes[positive.sample_b_id]


def test_splits_are_disjoint_and_fingerprint_is_stable(export):
    splits = {split: load_split_pairs(export.pairs_dir, split)
              for split in ("train", "validation", "test")}
    assert_disjoint_samples(splits)
    first = fingerprint(export, ["train", "validation"])
    assert first == fingerprint(export, ["train", "validation"])
    assert set(first) == {"pair_index.csv", "splits/train.csv", "splits/validation.csv",
                          "samples.csv", "variant_registry.csv", "source_splits.csv"}


def test_assert_disjoint_samples_detects_leakage(export):
    train_rows = load_split_pairs(export.pairs_dir, "train")
    with pytest.raises(PairDatasetError, match="appears in both"):
        assert_disjoint_samples({"train": train_rows, "validation": train_rows[:1]})


# ---------- fail-closed cases ----------

def test_unknown_pair_in_split_file(export):
    edit_csv(export.pairs_dir / "splits" / "train.csv",
             lambda rows: rows.append({"pair_id": "pair_999999"}))
    with pytest.raises(PairDatasetError, match="not in pair_index"):
        load_split_pairs(export.pairs_dir, "train")


def test_split_file_and_index_disagree(export):
    edit_csv(export.pairs_dir / "splits" / "train.csv", lambda rows: rows.pop())
    with pytest.raises(PairDatasetError, match="disagree"):
        load_split_pairs(export.pairs_dir, "train")


def test_label_must_match_pair_type(export):
    def flip(rows):
        rows[0]["label"] = "0"
    edit_csv(export.pairs_dir / "pair_index.csv", flip)
    with pytest.raises(PairDatasetError, match="pair_type"):
        load_split_pairs(export.pairs_dir, "train")


def test_duplicate_pair_is_rejected(export):
    def duplicate(rows):
        copy = dict(rows[0])
        copy["pair_id"] = "pair_999999"
        rows.append(copy)
    edit_csv(export.pairs_dir / "pair_index.csv", duplicate)
    with pytest.raises(PairDatasetError, match="repeats"):
        load_split_pairs(export.pairs_dir, "train")


def test_missing_column_is_rejected(export):
    def drop(rows):
        for row in rows:
            del row["generation_method"]
    edit_csv(export.pairs_dir / "pair_index.csv", drop)
    with pytest.raises(PairDatasetError, match="missing columns"):
        load_split_pairs(export.pairs_dir, "train")


def test_variant_hash_mismatch(export):
    variant = export.variants_root / "toy_1_1_v1.txt"
    variant.write_text("int main() { return 1; }\n", encoding="utf-8")
    with pytest.raises(PairDatasetError, match="sha256"):
        load_split(export, "train")


def test_missing_variant_file(export):
    (export.variants_root / "toy_1_1_v1.txt").unlink()
    with pytest.raises(PairDatasetError, match="not found"):
        load_split(export, "train")


def test_path_outside_root_is_rejected(export):
    def escape(rows):
        rows[0]["source_path"] = "../../../outside.txt"
    edit_csv(export.variants_csv, escape)
    with pytest.raises(PairDatasetError, match="outside"):
        load_split(export, "train")


def test_sample_split_mismatch(export):
    def move(rows):
        rows[0]["split"] = "validation"
    edit_csv(export.source_splits_csv, move)
    with pytest.raises(PairDatasetError, match="belongs to"):
        load_split(export, "train")


def test_failed_sample_cannot_be_used(export):
    def fail(rows):
        rows[0]["status"] = "failed"
    edit_csv(export.samples_csv, fail)
    with pytest.raises(PairDatasetError, match="failed"):
        load_split(export, "train")


def test_non_pass_variant_cannot_be_used(export):
    def reject(rows):
        rows[0]["validation_status"] = "FAIL"
    edit_csv(export.variants_csv, reject)
    with pytest.raises(PairDatasetError, match="failed"):
        CodeStore(export).read("toy_1_1_v1")


def test_data_paths_validation(tmp_path):
    with pytest.raises(PairDatasetError, match="Unknown"):
        DataPaths.from_dict({"pairs_dir": "a", "samples_csv": "b", "samples_root": "c", "x": 1})
    with pytest.raises(PairDatasetError, match="required"):
        DataPaths.from_dict({"pairs_dir": "a"})
    with pytest.raises(PairDatasetError, match="together"):
        DataPaths.from_dict({"pairs_dir": "a", "samples_csv": "b", "samples_root": "c",
                             "variants_csv": "d"})


# ---------- split source: split files or the index's split column ----------

def pair_ids(rows):
    return sorted(row.pair_id for row in rows)


def test_without_split_files_the_index_column_is_used(export):
    with_files = {split: pair_ids(load_split(export, split)[0])
                  for split in ("train", "validation", "test")}
    assert export.split_source == SPLIT_FILES
    shutil.rmtree(export.pairs_dir / "splits")
    assert export.split_source == INDEX_COLUMN
    for split, expected in with_files.items():
        assert pair_ids(load_split(export, split)[0]) == expected
    assert set(fingerprint(export, ["train"])) == {
        "pair_index.csv", "samples.csv", "variant_registry.csv", "source_splits.csv"}


def test_split_directory_with_a_missing_file_fails(export):
    (export.pairs_dir / "splits" / "test.csv").unlink()
    with pytest.raises(PairDatasetError, match="Missing file"):
        load_split_pairs(export.pairs_dir, "test")


def test_index_column_split_still_needs_both_labels(export):
    shutil.rmtree(export.pairs_dir / "splits")

    def drop_test_negatives(rows):
        rows[:] = [r for r in rows if not (r["split"] == "test" and r["label"] == "0")]

    edit_csv(export.pairs_dir / "pair_index.csv", drop_test_negatives)
    with pytest.raises(PairDatasetError, match="lacks positive or negative"):
        load_split_pairs(export.pairs_dir, "test")


def to_pair_record(row: dict) -> PairRecord:
    return PairRecord(
        pair_id=row["pair_id"], sample_a_id=row["sample_a_id"], sample_b_id=row["sample_b_id"],
        label=int(row["label"]), pair_type=PairType(row["pair_type"]),
        split=PairSplit(row["split"]), source_a_id=row["source_a_id"],
        source_b_id=row["source_b_id"], problem_a_id=row["problem_a_id"],
        problem_b_id=row["problem_b_id"], generation_method=row["generation_method"],
        created_seed=int(row["created_seed"]),
    )


def test_reads_the_csv_written_by_the_phase1_exporter(export):
    """The I.8 exporter writes one CSV (any name) and no split files."""
    records = [to_pair_record(row) for row in read_rows(export.pairs_dir / "pair_index.csv")]
    exported = export.pairs_dir / "final_dataset.csv"
    exported.write_bytes(FinalDatasetExporter.serialize_pairs(records).encode("utf-8"))
    expected = {split: pair_ids(load_split(export, split)[0])
                for split in ("train", "validation", "test")}
    (export.pairs_dir / "pair_index.csv").unlink()
    shutil.rmtree(export.pairs_dir / "splits")

    paths = replace(export, pair_index_csv=exported)
    for split, ids in expected.items():
        rows, codes = load_split(paths, split)
        assert pair_ids(rows) == ids
        assert all(row.extra["created_seed"] == "42" for row in rows)
        assert set(codes) == {s for row in rows for s in (row.sample_a_id, row.sample_b_id)}
    assert "final_dataset.csv" in fingerprint(paths, ["train"])


def test_pair_index_csv_alone_sets_pairs_dir(tmp_path):
    paths = DataPaths.from_dict({"pair_index_csv": "out/final.csv", "samples_csv": "s.csv",
                                 "samples_root": "p"}, base_dir=tmp_path)
    assert paths.pairs_dir == tmp_path / "out"
    assert paths.index_csv == tmp_path / "out" / "final.csv"


# ---------- pair scoring ----------

class OneHotEmbedder:
    """Same code -> same unit vector; different codes -> orthogonal vectors."""

    def __init__(self):
        self.calls = []

    def embed(self, codes):
        self.calls.append(list(codes))
        vocabulary = sorted(set(codes))
        vectors = np.zeros((len(codes), len(vocabulary)))
        for row, code in enumerate(codes):
            vectors[row, vocabulary.index(code)] = 1.0
        return vectors


def test_score_pairs_embeds_each_program_once():
    codes = {"a": "x", "b": "x", "c": "y"}
    embedder = OneHotEmbedder()
    scores, timing = score_pairs(embedder, [("a", "b"), ("a", "c"), ("c", "a")], codes)
    assert scores.tolist() == [1.0, 0.5, 0.5]
    assert embedder.calls == [["x", "x", "y"]]  # sorted IDs a, b, c, one call
    assert timing.programs == 3 and timing.pairs == 3


def test_score_pairs_needs_code_for_every_sample():
    with pytest.raises(KeyError):
        score_pairs(OneHotEmbedder(), [("a", "z")], {"a": "x"})
