"""Unit tests for VectorStore ABC and QdrantVectorStore."""

from keplai.vectorstore.base import VectorStore, VectorMatch
from keplai.vectorstore.qdrant import QdrantVectorStore


def _fake_embedding(dim: int = 8) -> list[float]:
    """Return a simple deterministic embedding for testing."""
    return [0.1] * dim


def test_abc_cannot_be_instantiated():
    """VectorStore ABC cannot be directly instantiated."""
    import pytest
    with pytest.raises(TypeError):
        VectorStore()


def test_qdrant_add_and_list():
    store = QdrantVectorStore(embedding_dim=8)
    store.add("e1", "Alice", _fake_embedding(8), {"type": "entity"})
    store.add("e2", "Bob", _fake_embedding(8), {"type": "entity"})
    items = store.list_all()
    names = {item.text for item in items}
    assert "Alice" in names
    assert "Bob" in names


def test_qdrant_search():
    store = QdrantVectorStore(embedding_dim=8)
    emb = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    store.add("e1", "Alice", emb)
    results = store.search(emb, top_k=1, threshold=0.5)
    assert len(results) >= 1
    assert results[0].text == "Alice"
    assert results[0].score > 0.5


def test_qdrant_delete():
    store = QdrantVectorStore(embedding_dim=8)
    store.add("e1", "Alice", _fake_embedding(8))
    store.delete("e1")
    items = store.list_all()
    assert len(items) == 0


def test_qdrant_search_threshold():
    store = QdrantVectorStore(embedding_dim=8)
    store.add("e1", "Alice", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    # Search with a very different vector — should not match at high threshold
    results = store.search(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        top_k=1,
        threshold=0.99,
    )
    assert len(results) == 0
