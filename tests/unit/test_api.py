"""API tests using FastAPI TestClient with mocked KeplAI instance."""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_graph():
    """Create a mocked KeplAI instance."""
    graph = MagicMock()
    graph._engine.is_healthy.return_value = True
    graph._engine.endpoint = "http://localhost:3030"
    graph._settings.fuseki_dataset = "keplai"
    graph.find.return_value = [
        {"s": "http://keplai.io/entity/Mehdi", "p": "http://keplai.io/ontology/founded", "o": "http://keplai.io/entity/BrandPulse"}
    ]
    graph.get_all_triples.return_value = [
        {"s": "http://keplai.io/entity/Mehdi", "p": "http://keplai.io/ontology/founded", "o": "http://keplai.io/entity/BrandPulse"}
    ]
    graph.ontology.get_classes.return_value = [
        {"uri": "http://keplai.io/ontology/Person", "name": "Person"}
    ]
    graph.ontology.get_properties.return_value = [
        {"uri": "http://keplai.io/ontology/founded", "name": "founded", "domain": "Person", "range": "Company"}
    ]
    graph.ontology.get_schema.return_value = {
        "classes": [{"uri": "http://keplai.io/ontology/Person", "name": "Person"}],
        "properties": [{"uri": "http://keplai.io/ontology/founded", "name": "founded", "domain": "Person", "range": "Company"}],
    }
    return graph


@pytest.fixture
def client(mock_graph):
    """Create a TestClient with the mocked graph injected."""
    from api.dependencies import set_graph
    set_graph(mock_graph)

    @asynccontextmanager
    async def noop_lifespan(app):
        yield

    # Import app without triggering real lifespan (which starts Docker)
    with patch("api.main.KeplAI"):
        from api.main import app
        app.router.lifespan_context = noop_lifespan
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# -- Graph endpoints --

def test_get_status(client, mock_graph):
    resp = client.get("/api/graph/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["healthy"] is True
    assert data["engine"] == "docker"


def test_get_all_triples(client):
    resp = client.get("/api/graph/triples/all")
    assert resp.status_code == 200
    triples = resp.json()
    assert len(triples) == 1
    assert triples[0]["subject"] == "http://keplai.io/entity/Mehdi"


def test_add_triple(client, mock_graph):
    resp = client.post("/api/graph/triples", json={
        "subject": "Alice",
        "predicate": "knows",
        "object": "Bob",
    })
    assert resp.status_code == 201
    mock_graph.add.assert_called_once_with("Alice", "knows", "Bob")


def test_delete_triple(client, mock_graph):
    resp = client.request("DELETE", "/api/graph/triples", json={
        "subject": "Alice",
        "predicate": "knows",
        "object": "Bob",
    })
    assert resp.status_code == 200
    mock_graph.delete.assert_called_once_with("Alice", "knows", "Bob")


# -- Ontology endpoints --

def test_get_classes(client):
    resp = client.get("/api/ontology/classes")
    assert resp.status_code == 200
    classes = resp.json()
    assert len(classes) == 1
    assert classes[0]["name"] == "Person"


def test_define_class(client, mock_graph):
    resp = client.post("/api/ontology/classes", json={"name": "Company"})
    assert resp.status_code == 201
    mock_graph.ontology.define_class.assert_called_once_with("Company")


def test_get_properties(client):
    resp = client.get("/api/ontology/properties")
    assert resp.status_code == 200
    props = resp.json()
    assert len(props) == 1
    assert props[0]["name"] == "founded"


def test_get_schema(client):
    resp = client.get("/api/ontology/schema")
    assert resp.status_code == 200
    schema = resp.json()
    assert "classes" in schema
    assert "properties" in schema


# -- Import endpoints --

def test_upload_ontology_file(client, mock_graph):
    mock_graph.ontology.load_rdf.return_value = {
        "ontology_id": "test-uuid",
        "graph_uri": "http://keplai.io/graph/test-uuid",
        "triples_loaded": 10,
        "format": "turtle",
        "classes": [{"uri": "http://example.org/Person", "name": "Person"}],
        "properties": [{"uri": "http://example.org/knows", "name": "knows", "domain": "Person", "range": "Person"}],
    }
    resp = client.post(
        "/api/ontology/upload",
        files={"file": ("test.ttl", b"@prefix ex: <http://example.org/> .", "text/turtle")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["triples_loaded"] == 10
    assert data["ontology_id"] == "test-uuid"
    assert len(data["classes"]) == 1


def test_import_ontology_from_url(client, mock_graph):
    mock_graph.ontology.load_url.return_value = {
        "ontology_id": "url-uuid",
        "graph_uri": "http://keplai.io/graph/url-uuid",
        "triples_loaded": 5,
        "format": "xml",
        "classes": [],
        "properties": [],
    }
    resp = client.post("/api/ontology/import-url", json={"url": "http://example.org/onto.owl"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["triples_loaded"] == 5
    mock_graph.ontology.load_url.assert_called_once_with("http://example.org/onto.owl", name=None)


def test_upload_rejects_no_file(client):
    resp = client.post("/api/ontology/upload")
    assert resp.status_code == 422


# -- Multi-ontology management --

def test_list_ontologies(client, mock_graph):
    mock_graph.ontology.list_ontologies.return_value = [
        {
            "id": "test-id",
            "name": "Test Ontology",
            "source": "test.ttl",
            "graph_uri": "http://keplai.io/graph/test",
            "import_date": "2026-03-15T00:00:00Z",
            "classes_count": 2,
            "properties_count": 3,
        }
    ]
    resp = client.get("/api/ontology/ontologies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Ontology"
    assert data[0]["graph_uri"] == "http://keplai.io/graph/test"


def test_delete_ontology(client, mock_graph):
    mock_graph.ontology.delete_ontology = MagicMock()
    resp = client.delete(
        "/api/ontology/ontologies/test-id",
        params={"graph_uri": "http://keplai.io/graph/test"}
    )
    assert resp.status_code == 200
    mock_graph.ontology.delete_ontology.assert_called_once_with("test-id", "http://keplai.io/graph/test")


def test_get_ontology_schema(client, mock_graph):
    mock_graph.ontology.get_schema.return_value = {
        "classes": [{"uri": "http://example.org/Cat", "name": "Cat"}],
        "properties": [],
    }
    resp = client.get(
        "/api/ontology/ontologies/test-id/schema",
        params={"graph_uri": "http://keplai.io/graph/test"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["classes"]) == 1
    assert data["classes"][0]["name"] == "Cat"


def test_get_stats(client, mock_graph):
    mock_graph.ontology.list_ontologies.return_value = [
        {"id": "test-id", "name": "Test", "source": "test.ttl",
         "graph_uri": "http://keplai.io/graph/test",
         "import_date": "2026-03-15T00:00:00Z",
         "classes_count": 2, "properties_count": 3}
    ]
    resp = client.get("/api/graph/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["triple_count"] == 1
    assert data["entity_count"] == 2
    assert data["ontology_count"] == 1
    assert data["class_count"] == 1
    assert data["property_count"] == 1


# -- Provenance endpoints --

def test_get_provenance_found(client, mock_graph):
    mock_graph.provenance.get.return_value = {
        "method": "manual",
        "created_at": "2026-03-16T00:00:00Z",
    }
    resp = client.get("/api/graph/triples/provenance", params={
        "subject": "http://keplai.io/entity/Mehdi",
        "predicate": "http://keplai.io/ontology/founded",
        "obj": "http://keplai.io/entity/BrandPulse",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["method"] == "manual"


def test_get_provenance_not_found(client, mock_graph):
    mock_graph.provenance.get.return_value = None
    resp = client.get("/api/graph/triples/provenance", params={
        "subject": "x", "predicate": "y", "obj": "z",
    })
    assert resp.status_code == 200
    assert resp.json() is None


def test_get_provenance_no_store(client, mock_graph):
    mock_graph.provenance = None
    resp = client.get("/api/graph/triples/provenance", params={
        "subject": "x", "predicate": "y", "obj": "z",
    })
    assert resp.status_code == 200
    assert resp.json() is None
