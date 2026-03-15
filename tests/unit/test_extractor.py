"""Unit tests for AIExtractor (mocked OpenAI calls)."""

import json
from unittest.mock import MagicMock, patch

from keplai.config import KeplAISettings
from keplai.extractor import AIExtractor, ExtractedTriple


def _make_extractor() -> AIExtractor:
    settings = KeplAISettings(openai_api_key="test-key")
    with patch("keplai.extractor.OpenAI"):
        return AIExtractor(settings)


def _mock_completion(content: str):
    """Build a mock OpenAI chat completion response."""
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_extract_open_mode():
    extractor = _make_extractor()
    triples_json = json.dumps({
        "triples": [
            {"subject": "Mehdi", "predicate": "founded", "object": "BrandPulse"},
        ]
    })
    extractor._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(triples_json)
    )

    results = extractor.extract("Mehdi founded BrandPulse", mode="open")
    assert len(results) == 1
    assert results[0].subject == "Mehdi"
    assert results[0].predicate == "founded"
    assert results[0].object == "BrandPulse"


def test_extract_strict_mode_with_schema():
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
    extractor._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(triples_json)
    )

    results = extractor.extract("Mehdi founded BrandPulse", mode="strict", schema=schema)
    assert len(results) == 1

    # Verify the system prompt mentioned the schema constraints
    call_args = extractor._client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = messages[0]["content"]
    assert "Person" in system_msg
    assert "Company" in system_msg
    assert "founded" in system_msg


def test_extract_handles_invalid_json():
    extractor = _make_extractor()
    extractor._client.chat.completions.create = MagicMock(
        return_value=_mock_completion("not valid json {{{")
    )

    results = extractor.extract("some text", mode="open")
    assert results == []


def test_extract_handles_empty_response():
    extractor = _make_extractor()
    extractor._client.chat.completions.create = MagicMock(
        return_value=_mock_completion(json.dumps({"triples": []}))
    )

    results = extractor.extract("nothing here", mode="open")
    assert results == []


def test_extracted_triple_to_dict():
    t = ExtractedTriple("Alice", "knows", "Bob")
    d = t.to_dict()
    assert d == {"subject": "Alice", "predicate": "knows", "object": "Bob"}
