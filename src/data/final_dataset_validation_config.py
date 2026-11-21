from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinalDatasetValidationConfig:
    require_non_empty: bool = True
    require_both_labels: bool = True
    check_duplicate_pair_ids: bool = True
    check_duplicate_sample_pairs: bool = True
    check_split_integrity: bool = True
    check_selection_integrity: bool = True

    def __post_init__(self) -> None:
        boolean_fields = (
            "require_non_empty",
            "require_both_labels",
            "check_duplicate_pair_ids",
            "check_duplicate_sample_pairs",
            "check_split_integrity",
            "check_selection_integrity",
        )

        for field_name in boolean_fields:
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(
                    f"{field_name} must be a boolean"
                )