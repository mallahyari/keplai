"""Unit tests for ProvenanceStore."""

import json
import os
import tempfile

import pytest

from keplai.provenance import ProvenanceStore, triple_hash


class TestTripleHash:
    def test_deterministic(self):
        h1 = triple_hash("http://keplai.io/entity/Mehdi", "http://keplai.io/ontology/founded", "http://keplai.io/entity/BrandPulse")
        h2 = triple_hash("http://keplai.io/entity/Mehdi", "http://keplai.io/ontology/founded", "http://keplai.io/entity/BrandPulse")
        assert h1 == h2

    def test_different_triples_differ(self):
        h1 = triple_hash("A", "B", "C")
        h2 = triple_hash("A", "B", "D")
        assert h1 != h2

    def test_separator_prevents_collision(self):
        h1 = triple_hash("A", "B", "C")
        h2 = triple_hash("A\x00B", "C", "")
        assert h1 != h2


class TestProvenanceStore:
    @pytest.fixture
    def store(self, tmp_path):
        path = str(tmp_path / "provenance.json")
        return ProvenanceStore(path=path)

    def test_record_and_get(self, store):
        store.record("s", "p", "o", method="manual", created_at="2026-03-16T00:00:00Z")
        result = store.get("s", "p", "o")
        assert result is not None
        assert result["method"] == "manual"
        assert result["created_at"] == "2026-03-16T00:00:00Z"

    def test_get_nonexistent_returns_none(self, store):
        assert store.get("x", "y", "z") is None

    def test_delete(self, store):
        store.record("s", "p", "o", method="manual", created_at="2026-03-16T00:00:00Z")
        store.delete("s", "p", "o")
        assert store.get("s", "p", "o") is None

    def test_delete_nonexistent_is_noop(self, store):
        store.delete("x", "y", "z")  # should not raise

    def test_overwrite(self, store):
        store.record("s", "p", "o", method="manual", created_at="t1")
        store.record("s", "p", "o", method="extraction", created_at="t2")
        result = store.get("s", "p", "o")
        assert result["method"] == "extraction"

    def test_persists_to_disk(self, tmp_path):
        path = str(tmp_path / "provenance.json")
        store1 = ProvenanceStore(path=path)
        store1.record("s", "p", "o", method="manual", created_at="t1")
        store2 = ProvenanceStore(path=path)
        result = store2.get("s", "p", "o")
        assert result is not None
        assert result["method"] == "manual"

    def test_creates_file_if_absent(self, tmp_path):
        path = str(tmp_path / "new_dir" / "provenance.json")
        store = ProvenanceStore(path=path)
        store.record("s", "p", "o", method="manual", created_at="t1")
        assert os.path.exists(path)

    def test_extraction_metadata(self, store):
        store.record(
            "s", "p", "o",
            method="extraction",
            created_at="t1",
            source_text="Mehdi founded BrandPulse",
            extraction_mode="strict",
            disambiguation={
                "subject_original": "Mehdi",
                "subject_matched": "MehdiAllahyari",
                "subject_score": 0.92,
                "object_original": "BrandPulse",
                "object_matched": "BrandPulseAnalytics",
                "object_score": 0.88,
            },
        )
        result = store.get("s", "p", "o")
        assert result["source_text"] == "Mehdi founded BrandPulse"
        assert result["disambiguation"]["subject_score"] == 0.92
