"""Unit tests for EntityDisambiguator (mocked OpenAI embeddings)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from keplai.config import KeplAISettings
from keplai.disambiguator import EntityDisambiguator
from keplai.vectorstore.qdrant import QdrantVectorStore


DIM = 8


def _make_disambiguator() -> EntityDisambiguator:
    settings = KeplAISettings(
        openai_api_key="test-key",
        embedding_dim=DIM,
        disambiguation_threshold=0.90,
    )
    store = QdrantVectorStore(embedding_dim=DIM)
    with patch("keplai.disambiguator.AsyncOpenAI"):
        disambiguator = EntityDisambiguator(settings, store)
    return disambiguator


def _mock_embed(disambiguator: EntityDisambiguator, embedding: list[float]):
    """Mock the _embed method to return a fixed embedding."""
    disambiguator._embed = AsyncMock(return_value=embedding)


@pytest.mark.asyncio
async def test_new_entity_registered():
    d = _make_disambiguator()
    emb = [0.1] * DIM
    _mock_embed(d, emb)

    name, score, matched = await d.resolve("Alice")
    assert name == "Alice"
    assert score is None
    assert matched is None

    # Should now exist in store
    entities = d.get_all_entities()
    assert any(e["name"] == "Alice" for e in entities)


@pytest.mark.asyncio
async def test_exact_match_returns_existing():
    d = _make_disambiguator()
    emb = [0.5] * DIM
    _mock_embed(d, emb)

    # Register first
    await d.resolve("BrandPulse")

    # Same embedding should match
    name, score, matched = await d.resolve("BrandPulseAnalytics")
    assert name == "BrandPulse"
    assert score is not None
    assert score >= 0.90
    assert matched == "BrandPulse"


@pytest.mark.asyncio
async def test_no_match_below_threshold():
    d = _make_disambiguator()

    # Register with one embedding
    d._embed = AsyncMock(return_value=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    await d.resolve("Alice")

    # Search with very different embedding
    d._embed = AsyncMock(return_value=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    name, score, matched = await d.resolve("CompletelyDifferent")
    assert name == "CompletelyDifferent"
    assert score is None
    assert matched is None


@pytest.mark.asyncio
async def test_get_similar():
    d = _make_disambiguator()
    emb = [0.5] * DIM
    _mock_embed(d, emb)

    await d.resolve("Alice")
    await d.resolve("AliceSmith")  # same emb → will match Alice, so stored as Alice

    similar = await d.get_similar("Alice", top_k=5)
    assert len(similar) >= 1
    assert similar[0]["name"] == "Alice"
