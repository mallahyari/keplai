from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorMatch:
    """A single result from a similarity search."""

    id: str
    text: str
    score: float
    metadata: dict[str, str]


class VectorStore(ABC):
    """Abstract interface for vector similarity stores."""

    @abstractmethod
    def add(self, id: str, text: str, embedding: list[float], metadata: dict[str, str] | None = None) -> None:
        """Store an embedding with associated text and metadata."""

    @abstractmethod
    def search(self, embedding: list[float], top_k: int = 5, threshold: float = 0.0) -> list[VectorMatch]:
        """Find the most similar items by embedding vector."""

    @abstractmethod
    def delete(self, id: str) -> None:
        """Remove an item by ID."""

    @abstractmethod
    def list_all(self) -> list[VectorMatch]:
        """Return all stored items."""
