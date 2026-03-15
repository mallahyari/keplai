"""Unit tests for NLQueryEngine (mocked OpenAI calls)."""

import pytest
from unittest.mock import MagicMock, patch

from keplai.config import KeplAISettings
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
    with patch("keplai.nlq.OpenAI"):
        engine = NLQueryEngine(settings, graph)
    return engine


def _mock_completion(content: str):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_ask_generates_and_executes_sparql():
    engine = _make_engine()
    engine._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(
            "SELECT ?s ?o WHERE { ?s <http://keplai.io/ontology/founded> ?o }"
        )
    )
    engine._get_sample_entities = MagicMock(return_value=["Mehdi", "BrandPulse"])

    result = engine.ask("What companies did Mehdi found?")
    assert "results" in result
    assert "sparql" in result
    assert len(result["results"]) == 1
    assert result["sparql"].startswith("SELECT")


def test_ask_with_explanation():
    engine = _make_engine()
    # First call: SPARQL generation, second call: explanation
    engine._client.chat.completions.create = MagicMock(
        side_effect=[
            _mock_completion("SELECT ?s ?o WHERE { ?s ?p ?o }"),
            _mock_completion("Mehdi founded BrandPulse based on the graph data."),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])

    result = engine.ask_with_explanation("What did Mehdi found?")
    assert "explanation" in result
    assert "BrandPulse" in result["explanation"]


def test_validate_read_only_rejects_insert():
    with pytest.raises(ValueError, match="read-only"):
        NLQueryEngine._validate_read_only("INSERT DATA { <a> <b> <c> }")


def test_validate_read_only_rejects_delete():
    with pytest.raises(ValueError, match="read-only"):
        NLQueryEngine._validate_read_only("DELETE WHERE { ?s ?p ?o }")


def test_validate_read_only_rejects_drop():
    with pytest.raises(ValueError, match="read-only"):
        NLQueryEngine._validate_read_only("DROP GRAPH <http://example.org>")


def test_validate_read_only_allows_select():
    # Should not raise
    NLQueryEngine._validate_read_only("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")


def test_validate_read_only_allows_construct():
    NLQueryEngine._validate_read_only("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")


def test_execute_sparql_enforces_read_only():
    engine = _make_engine()
    with pytest.raises(ValueError, match="read-only"):
        engine.execute_sparql("INSERT DATA { <a> <b> <c> }")


def test_strips_markdown_code_fences():
    engine = _make_engine()
    engine._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(
            "```sparql\nSELECT ?s WHERE { ?s ?p ?o }\n```"
        )
    )
    engine._get_sample_entities = MagicMock(return_value=[])

    result = engine.ask("show me everything")
    assert not result["sparql"].startswith("```")
    assert result["sparql"].startswith("SELECT")
