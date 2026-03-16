"""Tests for multi-ontology management."""

import pytest
from unittest.mock import MagicMock, patch

from keplai.config import KeplAISettings
from keplai.graph import KeplAI
from keplai.ontology import OntologyManager


def _make_graph():
    """Create a mocked KeplAI graph instance."""
    settings = KeplAISettings(openai_api_key="test-key")
    graph = MagicMock()
    graph._settings = settings
    graph._execute_query = MagicMock(return_value=[])
    graph._execute_update = MagicMock()
    return graph


def test_list_ontologies_returns_empty_when_none_loaded():
    graph = _make_graph()
    manager = OntologyManager(graph)
    result = manager.list_ontologies()
    assert result == []


def test_load_rdf_stores_metadata_in_metadata_graph():
    """load_rdf should persist ontology metadata in the metadata graph."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    updates = []
    graph._execute_update = MagicMock(side_effect=lambda s: updates.append(s))

    with patch.object(manager, "_batch_insert", return_value=10):
        with patch.object(manager, "_detect_schema_from_graph", return_value={"classes": [], "properties": []}):
            with patch("keplai.ontology.RDFGraph") as MockGraph:
                MockGraph.return_value.parse = MagicMock()
                result = manager.load_rdf(
                    "tests/fixtures/sample.ttl",
                    name="Test Ontology",
                )

    # Should have metadata INSERT into metadata graph
    meta_updates = [u for u in updates if graph._settings.metadata_graph in u]
    assert len(meta_updates) >= 1
    assert result.get("ontology_id") is not None
    assert result.get("graph_uri") is not None
    assert result["graph_uri"].startswith("http://keplai.io/graph/")


def test_load_rdf_returns_ontology_id_and_graph_uri():
    """load_rdf should return ontology_id and graph_uri in results."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    with patch.object(manager, "_batch_insert", return_value=5):
        with patch.object(manager, "_detect_schema_from_graph", return_value={"classes": [{"uri": "u", "name": "C"}], "properties": []}):
            with patch("keplai.ontology.RDFGraph") as MockGraph:
                MockGraph.return_value.parse = MagicMock()
                result = manager.load_rdf("tests/fixtures/sample.ttl", name="My Ontology")

    assert "ontology_id" in result
    assert "graph_uri" in result
    assert "triples_loaded" in result
    assert result["triples_loaded"] == 5


def test_load_rdf_with_explicit_graph_uri():
    """load_rdf should use provided graph_uri instead of auto-generating."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    with patch.object(manager, "_batch_insert", return_value=3):
        with patch.object(manager, "_detect_schema_from_graph", return_value={"classes": [], "properties": []}):
            with patch("keplai.ontology.RDFGraph") as MockGraph:
                MockGraph.return_value.parse = MagicMock()
                result = manager.load_rdf(
                    "tests/fixtures/sample.ttl",
                    graph_uri="http://example.org/my-graph",
                )

    assert result["graph_uri"] == "http://example.org/my-graph"


def test_batch_insert_uses_graph_uri():
    """_batch_insert should wrap INSERT DATA in GRAPH clause when graph_uri provided."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    from rdflib import Graph as RDFGraph, URIRef, Literal
    rdf_graph = RDFGraph()
    rdf_graph.add((URIRef("http://example.org/A"), URIRef("http://example.org/p"), Literal("val")))

    updates = []
    graph._execute_update = MagicMock(side_effect=lambda s: updates.append(s))

    manager._batch_insert(rdf_graph, graph_uri="http://example.org/graph/test")

    assert len(updates) == 1
    assert "GRAPH <http://example.org/graph/test>" in updates[0]


def test_delete_ontology_removes_graph_and_metadata():
    graph = _make_graph()
    manager = OntologyManager(graph)

    updates = []
    graph._execute_update = MagicMock(side_effect=lambda s: updates.append(s))

    manager.delete_ontology("test-uuid", graph_uri="http://keplai.io/graph/test-uuid")

    # Should DROP the named graph
    assert any("DROP" in u and "http://keplai.io/graph/test-uuid" in u for u in updates)
    # Should DELETE metadata
    meta_graph = graph._settings.metadata_graph
    assert any(meta_graph in u and "DELETE" in u for u in updates)


def test_get_schema_with_graph_uri_filters_by_graph():
    """get_schema(graph_uri=...) should query only that named graph."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    queries = []
    graph._execute_query = MagicMock(side_effect=lambda s: queries.append(s) or [])

    manager.get_schema(graph_uri="http://example.org/graph/foaf")

    # All queries should reference the graph URI
    for q in queries:
        assert "http://example.org/graph/foaf" in q


def test_get_schema_without_graph_uri_queries_all_graphs():
    """get_schema() without graph_uri should query default + named graphs."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    queries = []
    graph._execute_query = MagicMock(side_effect=lambda s: queries.append(s) or [])

    manager.get_schema()

    # Should use UNION with GRAPH ?g pattern
    for q in queries:
        assert "GRAPH ?g" in q


def test_full_multi_ontology_workflow():
    """Verify: load two ontologies, they get different IDs and graph URIs."""
    graph = _make_graph()
    manager = OntologyManager(graph)

    updates = []
    graph._execute_update = MagicMock(side_effect=lambda s: updates.append(s))

    with patch.object(manager, "_batch_insert", return_value=10):
        with patch.object(manager, "_detect_schema_from_graph", return_value={"classes": [{"uri": "u", "name": "C"}], "properties": []}):
            with patch("keplai.ontology.RDFGraph") as MockGraph:
                MockGraph.return_value.parse = MagicMock()

                r1 = manager.load_rdf("tests/fixtures/sample.ttl", name="Cat Ontology")
                r2 = manager.load_rdf("tests/fixtures/sample.ttl", name="FOAF")

    assert r1["ontology_id"] != r2["ontology_id"]
    assert r1["graph_uri"] != r2["graph_uri"]
    assert r1["graph_uri"].startswith("http://keplai.io/graph/")

    # Metadata should have been stored for both
    meta_inserts = [u for u in updates if graph._settings.metadata_graph in u]
    assert len(meta_inserts) == 2
