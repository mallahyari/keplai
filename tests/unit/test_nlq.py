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
        "properties": [{"uri": "http://keplai.io/ontology/founded", "name": "founded", "domain": "Person", "range": "Company"}],
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
        side_effect=[
            # _map_relations response
            _mock_completion('{"founded": "http://keplai.io/ontology/founded"}'),
            # _resolve_entities: entity extraction
            _mock_completion('["Mehdi"]'),
            # _generate_sparql response
            _mock_completion(
                "SELECT ?s ?o WHERE { ?s <http://keplai.io/ontology/founded> ?o }"
            ),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=["Mehdi", "BrandPulse"])
    engine._get_all_predicates = MagicMock(return_value=[])
    # Mock disambiguator to avoid extra async calls
    engine._graph.disambiguator.get_similar = AsyncMock(return_value=[{"name": "Mehdi", "score": 0.99}])

    result = await engine.ask("What companies did Mehdi found?")
    assert "results" in result
    assert "sparql" in result
    assert len(result["results"]) == 1
    assert "SELECT" in result["sparql"]


@pytest.mark.asyncio
async def test_ask_with_explanation():
    engine = _make_engine()
    engine._client.chat.completions.create = AsyncMock(
        side_effect=[
            # _map_relations response
            _mock_completion("{}"),
            # _generate_sparql response (no entities since sample_entities=[])
            _mock_completion("SELECT ?s ?o WHERE { ?s ?p ?o }"),
            # _explain_results response
            _mock_completion("Mehdi founded BrandPulse based on the graph data."),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])
    engine._get_all_predicates = MagicMock(return_value=[])

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
        side_effect=[
            # _map_relations response
            _mock_completion("{}"),
            # _generate_sparql response (no entities since sample=[])
            _mock_completion("SELECT ?s WHERE { ?s ?p ?o }"),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])
    engine._get_all_predicates = MagicMock(return_value=[])

    await engine.ask("test question")

    # The SPARQL generation call is the second one (index 1)
    calls = engine._client.chat.completions.create.call_args_list
    sparql_gen_call = calls[1]
    system_msg = sparql_gen_call.kwargs["messages"][0]["content"]
    assert "GRAPH" in system_msg
    assert "multiple ontologies" in system_msg


@pytest.mark.asyncio
async def test_strips_markdown_code_fences():
    engine = _make_engine()
    engine._client.chat.completions.create = AsyncMock(
        side_effect=[
            # _map_relations response
            _mock_completion("{}"),
            # _generate_sparql response
            _mock_completion(
                "```sparql\nSELECT ?s WHERE { ?s ?p ?o }\n```"
            ),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])
    engine._get_all_predicates = MagicMock(return_value=[])

    result = await engine.ask("show me everything")
    assert not result["sparql"].startswith("```")
    assert "SELECT" in result["sparql"]


@pytest.mark.asyncio
async def test_relation_mapping_injected_into_prompt():
    """Relation mappings should appear in the SPARQL generation prompt."""
    engine = _make_engine()
    # worksAt must be in allowed predicates so validation doesn't trigger repair
    engine._graph.ontology.get_schema.return_value = {
        "classes": [],
        "properties": [
            {"uri": "http://keplai.io/ontology/worksAt", "name": "worksAt", "domain": "Person", "range": "Company"},
        ],
    }
    engine._client.chat.completions.create = AsyncMock(
        side_effect=[
            # _map_relations response
            _mock_completion('{"works at": "http://keplai.io/ontology/worksAt"}'),
            # _generate_sparql response (no entities since sample=[])
            _mock_completion("SELECT ?p WHERE { ?p <http://keplai.io/ontology/worksAt> ?c }"),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])
    engine._get_all_predicates = MagicMock(return_value=[])

    await engine.ask("Who works at BrandPulse?")

    calls = engine._client.chat.completions.create.call_args_list
    sparql_gen_call = calls[1]
    system_msg = sparql_gen_call.kwargs["messages"][0]["content"]
    assert "RELATION MAPPINGS" in system_msg
    assert "worksAt" in system_msg


@pytest.mark.asyncio
async def test_predicate_validation_triggers_repair():
    """Invalid predicates should trigger a repair LLM call."""
    engine = _make_engine()
    engine._client.chat.completions.create = AsyncMock(
        side_effect=[
            # _map_relations response
            _mock_completion("{}"),
            # _generate_sparql: uses an invalid predicate
            _mock_completion(
                "SELECT ?o WHERE { GRAPH ?g { ?s <http://keplai.io/ontology/inventedProp> ?o } }"
            ),
            # _repair_sparql: fixes the predicate
            _mock_completion(
                "SELECT ?o WHERE { GRAPH ?g { ?s <http://keplai.io/ontology/founded> ?o } }"
            ),
        ]
    )
    engine._get_sample_entities = MagicMock(return_value=[])
    engine._get_all_predicates = MagicMock(return_value=[])

    result = await engine.ask("test")
    # Should have called repair (3 LLM calls total: map + generate + repair)
    assert engine._client.chat.completions.create.call_count == 3
    assert "founded" in result["sparql"]


def test_validate_predicates_detects_invalid():
    allowed = {"http://keplai.io/ontology/founded", "http://keplai.io/ontology/worksAt"}
    sparql = "SELECT ?o WHERE { ?s <http://keplai.io/ontology/badProp> ?o }"
    invalid = NLQueryEngine._validate_predicates(sparql, allowed)
    assert "http://keplai.io/ontology/badProp" in invalid


def test_validate_predicates_passes_valid():
    allowed = {"http://keplai.io/ontology/founded"}
    sparql = "SELECT ?o WHERE { ?s <http://keplai.io/ontology/founded> ?o }"
    invalid = NLQueryEngine._validate_predicates(sparql, allowed)
    assert invalid == []


def test_infer_description():
    assert "started" in NLQueryEngine._infer_description("founded")
    assert "employed" in NLQueryEngine._infer_description("worksAt")
    # Unknown names return the name split into words
    assert NLQueryEngine._infer_description("someCustomProp") == "some custom prop"
