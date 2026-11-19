from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

class TransformationError(Exception):
    """Base exception for transformation errors."""

@dataclass(frozen=True)
class TransformationResult:
    transformation_type: str 
    source_text: str 
    transformed_text: str 
    changed: bool 
    config: dict[str, Any]

class Transformation(ABC):
    """Base interface for source-code transformations."""
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique transformation name."""
        raise NotImplementedError

    @abstractmethod
    def transform(
        self,
        source: str,
        seed: int | None = None,
    ) -> TransformationResult:
        """Transform source code and return a structured result."""
        raise NotImplementedError