"""Unit tests for ontology file/URL import."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from keplai.config import KeplAISettings
from keplai.exceptions import OntologyImportError
from keplai.graph import KeplAI


FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_graph() -> KeplAI:
    settings = KeplAISettings()
    engine = MagicMock()
    engine.update_url = "http://localhost:3030/keplai/update"
    engine.sparql_url = "http://localhost:3030/keplai/sparql"
    return KeplAI(engine=engine, settings=settings)


@patch("keplai.graph.SPARQLWrapper")
def test_load_rdf_parses_turtle_file(mock_wrapper_cls):
    mock_instance = MagicMock()
    mock_wrapper_cls.return_value = mock_instance
    g = _make_graph()

    result = g.ontology.load_rdf(FIXTURES / "sample.ttl")

    assert result["triples_loaded"] > 0
    assert result["format"] == "turtle"
    # Should have called _execute_update at least once for batch insert
    assert mock_instance.query.call_count >= 1


@patch("keplai.graph.SPARQLWrapper")
def test_load_rdf_auto_detects_format(mock_wrapper_cls):
    mock_instance = MagicMock()
    mock_wrapper_cls.return_value = mock_instance
    g = _make_graph()

    result = g.ontology.load_rdf(FIXTURES / "sample.ttl")
    assert result["format"] == "turtle"


@patch("keplai.graph.SPARQLWrapper")
def test_load_rdf_returns_detected_classes_and_properties(mock_wrapper_cls):
    mock_instance = MagicMock()
    mock_wrapper_cls.return_value = mock_instance
    g = _make_graph()

    result = g.ontology.load_rdf(FIXTURES / "sample.ttl")

    assert "classes" in result
    assert "properties" in result
    class_names = [c["name"] for c in result["classes"]]
    assert "Person" in class_names
    assert "Organization" in class_names
    prop_names = [p["name"] for p in result["properties"]]
    assert "worksFor" in prop_names
    assert "name" in prop_names


def test_load_rdf_rejects_nonexistent_file():
    g = _make_graph()
    with pytest.raises(OntologyImportError, match="not found"):
        g.ontology.load_rdf("/nonexistent/file.ttl")


def test_load_rdf_rejects_unsupported_format():
    g = _make_graph()
    with pytest.raises(OntologyImportError, match="Unsupported"):
        g.ontology.load_rdf(FIXTURES / "sample.ttl", format="csv")


@patch("keplai.graph.SPARQLWrapper")
def test_load_rdf_batches_large_triple_sets(mock_wrapper_cls):
    """Verify that triples are inserted in batches, not one at a time."""
    mock_instance = MagicMock()
    mock_wrapper_cls.return_value = mock_instance
    g = _make_graph()

    result = g.ontology.load_rdf(FIXTURES / "sample.ttl", batch_size=3)

    # With ~10 triples and batch_size=3, should have multiple batch inserts
    assert mock_instance.query.call_count >= 2
    assert result["triples_loaded"] > 0
