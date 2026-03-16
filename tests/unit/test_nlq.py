"""Unit tests for NLQueryEngine (mocked OpenAI calls)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from keplai.config import KeplAISettings
from keplai.exceptions import QueryError
from keplai.nlq import NLQueryEngine


def _make_engine() -> NLQueryEngine:
    settings = KeplAISettings(openai_api_key="test-key")
    graph = MagicMock()
    graph._settings = settings
    graph.ontology.get_schema.return_value = {
        "classes": [{"name": "Person"}, {"name": "Company"}],
        "properties": [{"name": "founded", "domain": "Person", "range": "Company"}],
    }
    graph._execute_query.return_value = [
        {"s": "http://keplai.io/entity/Mehdi", "o": "http://keplai.io/entity/BrandPulse"}
    ]
    with patch("keplai.nlq.AsyncOpenAI"):
        engine = NLQueryEngine(settings, graph)
    return engine


def _mock_completion(content: str):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_ask_generates_and_executes_sparql():
    engine = _make_engine()
    engine._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(
            "SELECT ?s ?o WHERE { ?s <http://keplai.io/ontology/founded> ?o }"
        )
    )
    engine._get_sample_entities = MagicMock(return_value=["Mehdi", "BrandPulse"])

    result = await engine.ask("What companies did Mehdi found?")
    assert "results" in result
    assert "sparql" in result
    assert len(result["results"]) == 1
    assert result["sparql"].startswith("SELECT")


@pytest.mark.asyncio
async def test_ask_with_explanation():
    engine = _make_engine()
    # First call: SPARQL generation, second call: explanation
    engine._client.chat.completions.create = AsyncMock(
        side_effect=[
            _mock_completion("SELECT ?s ?o WHERE { ?s ?p ?o }"),
            _mock_completion("Mehdi founded BrandPulse based on the graph data."),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])

    result = await engine.ask_with_explanation("What did Mehdi found?")
    assert "explanation" in result
    assert "BrandPulse" in result["explanation"]


def test_validate_read_only_rejects_insert():
    with pytest.raises(QueryError, match="read-only"):
        NLQueryEngine._validate_read_only("INSERT DATA { <a> <b> <c> }")


def test_validate_read_only_rejects_delete():
    with pytest.raises(QueryError, match="read-only"):
        NLQueryEngine._validate_read_only("DELETE WHERE { ?s ?p ?o }")


def test_validate_read_only_rejects_drop():
    with pytest.raises(QueryError, match="read-only"):
        NLQueryEngine._validate_read_only("DROP GRAPH <http://example.org>")


def test_validate_read_only_allows_select():
    # Should not raise
    NLQueryEngine._validate_read_only("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")


def test_validate_read_only_allows_construct():
    NLQueryEngine._validate_read_only("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")


def test_execute_sparql_enforces_read_only():
    engine = _make_engine()
    with pytest.raises(QueryError, match="read-only"):
        engine.execute_sparql("INSERT DATA { <a> <b> <c> }")


@pytest.mark.asyncio
async def test_generate_sparql_includes_graph_context_for_multi_namespace():
    """System prompt should mention GRAPH clauses when multiple namespaces exist."""
    engine = _make_engine()
    engine._graph.ontology.get_schema.return_value = {
        "classes": [
            {"uri": "http://ontology.example.org/cat#Person", "name": "Person"},
            {"uri": "http://xmlns.com/foaf/0.1/Person", "name": "Person"},
        ],
        "properties": [
            {"uri": "http://ontology.example.org/cat#owns", "name": "owns", "domain": "Person", "range": "Cat"},
        ],
    }
    engine._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion("SELECT ?s WHERE { ?s ?p ?o }")
    )
    engine._get_sample_entities = MagicMock(return_value=[])

    await engine.ask("test question")

    call_args = engine._client.chat.completions.create.call_args
    system_msg = call_args.kwargs["messages"][0]["content"]
    assert "GRAPH" in system_msg
    assert "multiple ontologies" in system_msg


@pytest.mark.asyncio
async def test_strips_markdown_code_fences():
    engine = _make_engine()
    engine._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(
            "```sparql\nSELECT ?s WHERE { ?s ?p ?o }\n```"
        )
    )
    engine._get_sample_entities = MagicMock(return_value=[])

    result = await engine.ask("show me everything")
    assert not result["sparql"].startswith("```")
    assert result["sparql"].startswith("SELECT")
