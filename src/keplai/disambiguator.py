from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from openai import AsyncOpenAI, OpenAIError

from keplai.exceptions import DisambiguationError
from keplai.vectorstore.base import VectorStore

if TYPE_CHECKING:
    from keplai.config import KeplAISettings

logger = logging.getLogger(__name__)


class EntityDisambiguator:
    """Resolve entity names to canonical URIs using vector similarity."""

    def __init__(self, settings: KeplAISettings, store: VectorStore) -> None:
        self._settings = settings
        self._store = store
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._threshold = settings.disambiguation_threshold

    async def resolve(self, entity_name: str) -> tuple[str, float | None, str | None]:
        """Resolve an entity name to a canonical name.

        Returns:
            (canonical_name, similarity_score, matched_existing)
            If no match found, returns (entity_name, None, None) — a new entity.
        """
        embedding = await self._embed(entity_name)
        matches = self._store.search(embedding, top_k=1, threshold=self._threshold)

        if matches:
            best = matches[0]
            logger.debug(
                "Disambiguated %r → %r (score=%.3f)",
                entity_name,
                best.text,
                best.score,
            )
            return best.text, best.score, best.text
        else:
            # New entity — store its embedding for future lookups
            self._store.add(
                id=entity_name,
                text=entity_name,
                embedding=embedding,
                metadata={"type": "entity"},
            )
            logger.debug("New entity registered: %r", entity_name)
            return entity_name, None, None

    async def get_similar(self, entity_name: str, top_k: int = 5) -> list[dict[str, str | float]]:
        """Find entities similar to the given name (for debugging/UI)."""
        embedding = await self._embed(entity_name)
        matches = self._store.search(embedding, top_k=top_k, threshold=0.0)
        return [
            {"name": m.text, "score": m.score}
            for m in matches
        ]

    def get_all_entities(self) -> list[dict[str, str]]:
        """List all known entities in the vector store."""
        items = self._store.list_all()
        return [{"name": item.text, **item.metadata} for item in items]

    async def _embed(self, text: str) -> list[float]:
        try:
            response = await self._client.embeddings.create(
                model=self._settings.embedding_model,
                input=text,
            )
        except OpenAIError as exc:
            raise DisambiguationError(f"Embedding call failed: {exc}") from exc
        return response.data[0].embedding
