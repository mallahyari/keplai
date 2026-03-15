from __future__ import annotations

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from keplai.vectorstore.base import VectorStore, VectorMatch

logger = logging.getLogger(__name__)

_DEFAULT_COLLECTION = "keplai_entities"


class QdrantVectorStore(VectorStore):
    """Qdrant-backed vector store. Uses local/in-memory mode by default."""

    def __init__(
        self,
        collection_name: str = _DEFAULT_COLLECTION,
        embedding_dim: int = 1536,
        path: str | None = None,
    ) -> None:
        self._collection = collection_name
        self._dim = embedding_dim

        if path:
            self._client = QdrantClient(path=path)
        else:
            self._client = QdrantClient(location=":memory:")

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )
            logger.debug("Created Qdrant collection: %s", self._collection)

    def add(self, id: str, text: str, embedding: list[float], metadata: dict[str, str] | None = None) -> None:
        payload = {"text": text, **(metadata or {})}
        point = PointStruct(
            id=self._stable_uuid(id),
            vector=embedding,
            payload=payload,
        )
        self._client.upsert(collection_name=self._collection, points=[point])

    def search(self, embedding: list[float], top_k: int = 5, threshold: float = 0.0) -> list[VectorMatch]:
        hits = self._client.query_points(
            collection_name=self._collection,
            query=embedding,
            limit=top_k,
            score_threshold=threshold,
        ).points
        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                VectorMatch(
                    id=str(hit.id),
                    text=payload.get("text", ""),
                    score=hit.score,
                    metadata={k: v for k, v in payload.items() if k != "text"},
                )
            )
        return results

    def delete(self, id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=[self._stable_uuid(id)],
        )

    def list_all(self) -> list[VectorMatch]:
        result = self._client.scroll(
            collection_name=self._collection,
            limit=10000,
            with_vectors=False,
        )
        points = result[0]
        items = []
        for pt in points:
            payload = pt.payload or {}
            items.append(
                VectorMatch(
                    id=str(pt.id),
                    text=payload.get("text", ""),
                    score=1.0,
                    metadata={k: v for k, v in payload.items() if k != "text"},
                )
            )
        return items

    @staticmethod
    def _stable_uuid(text: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, text))
