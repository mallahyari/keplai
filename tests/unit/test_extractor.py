"""Unit tests for AIExtractor (mocked OpenAI calls)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from keplai.config import KeplAISettings
from keplai.extractor import AIExtractor, ExtractedTriple


def _make_extractor() -> AIExtractor:
    settings = KeplAISettings(openai_api_key="test-key")
    with patch("keplai.extractor.AsyncOpenAI"):
        return AIExtractor(settings)


def _mock_completion(content: str):
    """Build a mock OpenAI chat completion response."""
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_extract_open_mode():
    extractor = _make_extractor()
    triples_json = json.dumps({
        "triples": [
            {"subject": "Mehdi", "predicate": "founded", "object": "BrandPulse"},
        ]
    })
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(triples_json)
    )

    results = await extractor.extract("Mehdi founded BrandPulse", mode="open")
    assert len(results) == 1
    assert results[0].subject == "Mehdi"
    assert results[0].predicate == "founded"
    assert results[0].object == "BrandPulse"


@pytest.mark.asyncio
async def test_extract_strict_mode_with_schema():
    extractor = _make_extractor()
    schema = {
        "classes": [{"name": "Person"}, {"name": "Company"}],
        "properties": [{"name": "founded", "domain": "Person", "range": "Company"}],
    }
    triples_json = json.dumps({
        "triples": [
            {"subject": "Mehdi", "predicate": "founded", "object": "BrandPulse"},
        ]
    })
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(triples_json)
    )

    results = await extractor.extract("Mehdi founded BrandPulse", mode="strict", schema=schema)
    assert len(results) == 1

    # Verify the system prompt mentioned the schema constraints
    call_args = extractor._client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = messages[0]["content"]
    assert "Person" in system_msg
    assert "Company" in system_msg
    assert "founded" in system_msg


@pytest.mark.asyncio
async def test_extract_handles_invalid_json():
    extractor = _make_extractor()
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion("not valid json {{{")
    )

    results = await extractor.extract("some text", mode="open")
    assert results == []


@pytest.mark.asyncio
async def test_extract_handles_empty_response():
    extractor = _make_extractor()
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(json.dumps({"triples": []}))
    )

    results = await extractor.extract("nothing here", mode="open")
    assert results == []


@pytest.mark.asyncio
async def test_extract_handles_flat_single_triple():
    """LLM sometimes returns a single triple as a flat object instead of wrapped in 'triples' key."""
    extractor = _make_extractor()
    flat_json = json.dumps({"subject": "Alice", "predicate": "knows", "object": "Bob"})
    extractor._client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(flat_json)
    )

    results = await extractor.extract("Alice knows Bob", mode="open")
    assert len(results) == 1
    assert results[0].subject == "Alice"
    assert results[0].predicate == "knows"
    assert results[0].object == "Bob"


def test_extracted_triple_to_dict():
    t = ExtractedTriple("Alice", "knows", "Bob")
    d = t.to_dict()
    assert d == {"subject": "Alice", "predicate": "knows", "object": "Bob"}
