from __future__ import annotations
import random 
from collections import defaultdict
from typing import Any 

SPLIT_NAMES = ("train", "validation", "test")

class SourceSplitError(RuntimeError):
    """Raised when source splitting cannot be completed."""

def _build_groups(
    samples: list[dict],
    duplicate_groups: list[dict],
) -> list[dict]:
    """Create indivisible source groups, including singleton samples."""
    sample_ids = {str(sample["sample_id"]) for sample in samples}
    sample_to_group: dict[str, str] = {}
    for duplicate_group in duplicate_groups:
        members = [
            str(sample_id) 
            for sample_id in duplicate_group["sample_ids"]
        ]

        for sample_id in members:
            if sample_id not in sample_ids:
                raise SourceSplitError(
                    f"Duplicate group references unknown sample: {sample_id}"
                )

            if sample_id in sample_to_group:
                raise SourceSplitError(
                    f"Sample belongs to multiple duplicate groups: {sample_id}"
                )

            sample_to_group[sample_id] = str(
                duplicate_group["duplicate_group_id"]
            )

    groups: dict[str, list[dict]] = defaultdict(list)

    for sample in samples:
        sample_id = str(sample["sample_id"])
        group_id = sample_to_group.get(
            sample_id,
            f"single_{sample_id}",
        )
        groups[group_id].append(sample)

    result = []

    for group_id, members in groups.items():
        problem_counts: dict[str, int] = defaultdict(int)

        for member in members:
            problem_counts[str(member["problem_id"])] += 1

        result.append(
            {
                "group_id": group_id,
                "members": members,
                "size": len(members),
                "problem_counts": dict(problem_counts),
            }
        )

    return result 

def _assignment_delta(
    split_name: str,
    group: dict,
    counts: dict[str, int],
    problem_counts: dict[str, dict[str, int]],
    global_targets: dict[str, float],
    problem_targets: dict[str, dict[str, float]],
) -> float:
    """Compute the incremental normalized squared deviation cost."""
    delta = 0.0

    new_global = counts[split_name] + group["size"]
    target_global = global_targets[split_name]

    delta += (
        (new_global - target_global) / max(target_global, 1.0)
    ) ** 2 - (
        (counts[split_name] - target_global) / max(target_global, 1.0)
    ) ** 2 

    for problem_id, group_count in group["problem_counts"].items():
        target = problem_targets[problem_id][split_name]
        current = problem_counts[problem_id][split_name]
        new_count = current + group_count

        delta += (
            (new_count - target) / max(target, 1.0)
        ) ** 2 - (
            (current - target) / max(target, 1.0)
        ) ** 2

    return delta

def assign_source_splits(
    samples: list[dict],
    duplicate_groups: list[dict],
    ratios: dict[str, float],
    seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Assign all source samples to train/validation/test.

    Duplicate groups are atomic. Assignment attempts to minimize
    global and per-problem ratio deviations.
    """
    if not samples:
        raise SourceSplitError("Samples list is empty.")

    if set(ratios) != set(SPLIT_NAMES):
        raise SourceSplitError(
            "Ratios must contain train, validation, and test."
        )

    if any(value <= 0 for value in ratios.values()):
        raise SourceSplitError("All split ratios must be positive.")

    if abs(sum(ratios.values()) - 1.0) > 1e-8:
        raise SourceSplitError("Split ratios must sum to 1.0.")

    sample_ids = [str(sample["sample_id"]) for sample in samples]

    if len(sample_ids) != len(set(sample_ids)):
        raise SourceSplitError("Duplicate sample_id found in input.")

    groups = _build_groups(samples, duplicate_groups)

    total_samples = len(samples)
    global_targets = {
        split: total_samples * ratios[split]
        for split in SPLIT_NAMES
    }

    total_per_problem: dict[str, int] = defaultdict(int)

    for sample in samples:
        total_per_problem[str(sample["problem_id"])] += 1

    problem_targets = {
        problem_id: {
            split: total_count * ratios[split]
            for split in SPLIT_NAMES
        }
        for problem_id, total_count in total_per_problem.items()
    }

    rng = random.Random(seed)

    # Seeded random tie-break order.
    rng.shuffle(groups)

    # Large, cross-problem duplicate groups are assigned first.
    groups.sort(
        key=lambda group: (
            -group["size"],
            -len(group["problem_counts"]),
        )
    )

    counts = {split: 0 for split in SPLIT_NAMES}
    problem_counts = {
        problem_id: {split: 0 for split in SPLIT_NAMES}
        for problem_id in total_per_problem
    }

    assignments: dict[str, str] = {}

    for group in groups:
        costs = {
            split: _assignment_delta(
                split,
                group,
                counts,
                problem_counts,
                global_targets,
                problem_targets,
            )
            for split in SPLIT_NAMES
        }

        best_cost = min(costs.values())
        best_splits = [
            split
            for split, cost in costs.items()
            if abs(cost - best_cost) <= 1e-12
        ]

        selected_split = rng.choice(best_splits)

        counts[selected_split] += group["size"]

        for problem_id, group_count in group["problem_counts"].items():
            problem_counts[problem_id][selected_split] += group_count

        for member in group["members"]:
            assignments[str(member["sample_id"])] = selected_split

    if len(assignments) != total_samples:
        raise SourceSplitError(
            "Split assignment does not cover all samples."
        )

    report = {
        "seed": seed,
        "ratios": dict(ratios),
        "total_samples": total_samples,
        "total_groups": len(groups),
        "duplicate_groups": len(duplicate_groups),
        "split_counts": counts,
        "split_actual_ratios": {
            split: counts[split] / total_samples
            for split in SPLIT_NAMES
        },
        "problem_counts": dict(problem_counts),
        "problem_targets": problem_targets,
    }

    return assignments, report
