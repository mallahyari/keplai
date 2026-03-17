"""Provenance store — records how each triple was created."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def triple_hash(subject: str, predicate: str, obj: str) -> str:
    """Deterministic hash for a triple using null-byte separator."""
    key = f"{subject}\x00{predicate}\x00{obj}"
    return hashlib.sha256(key.encode()).hexdigest()


class ProvenanceStore:
    """JSON-file backed provenance store for triple metadata."""

    def __init__(self, path: str = "./provenance.json") -> None:
        self._path = Path(path)
        self._data: dict[str, dict[str, Any]] = {}
        if self._path.exists():
            with open(self._path) as f:
                self._data = json.load(f)

    def record(self, subject: str, predicate: str, obj: str, **metadata: Any) -> None:
        """Record provenance for a triple. Overwrites if exists."""
        key = triple_hash(subject, predicate, obj)
        self._data[key] = metadata
        self._flush()

    def get(self, subject: str, predicate: str, obj: str) -> dict[str, Any] | None:
        """Return provenance record for a triple, or None."""
        key = triple_hash(subject, predicate, obj)
        return self._data.get(key)

    def delete(self, subject: str, predicate: str, obj: str) -> None:
        """Remove provenance for a triple."""
        key = triple_hash(subject, predicate, obj)
        if key in self._data:
            del self._data[key]
            self._flush()

    def _flush(self) -> None:
        """Write data to disk, creating parent dirs if needed."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f)
