from __future__ import annotations

import json
import logging
from typing import Any, TYPE_CHECKING

from openai import OpenAI, OpenAIError

from keplai.exceptions import ExtractionError

if TYPE_CHECKING:
    from keplai.config import KeplAISettings

logger = logging.getLogger(__name__)


class ExtractedTriple:
    """A triple extracted by the AI from text."""

    def __init__(self, subject: str, predicate: str, object: str) -> None:
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def to_dict(self) -> dict[str, str]:
        return {"subject": self.subject, "predicate": self.predicate, "object": self.object}

    def __repr__(self) -> str:
        return f"ExtractedTriple({self.subject!r}, {self.predicate!r}, {self.object!r})"


class AIExtractor:
    """Extract knowledge-graph triples from unstructured text using an LLM."""

    def __init__(self, settings: KeplAISettings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    def extract(
        self,
        text: str,
        mode: str = "strict",
        schema: dict[str, Any] | None = None,
    ) -> list[ExtractedTriple]:
        """Extract triples from text.

        Args:
            text: The unstructured text to extract from.
            mode: "strict" (uses ontology schema) or "open" (free extraction).
            schema: The ontology schema dict (classes + properties). Required for strict mode.
        """
        if mode == "strict":
            return self._extract_strict(text, schema or {})
        return self._extract_open(text)

    def _extract_strict(self, text: str, schema: dict[str, Any]) -> list[ExtractedTriple]:
        classes = [c["name"] for c in schema.get("classes", [])]
        properties = schema.get("properties", [])

        prop_descriptions = []
        for p in properties:
            prop_descriptions.append(
                f"- {p['name']}: domain={p.get('domain', '?')}, range={p.get('range', '?')}"
            )

        system_prompt = (
            "You are a knowledge-graph triple extractor. "
            "Extract structured triples from the given text.\n\n"
            "ONTOLOGY SCHEMA:\n"
            f"Classes: {', '.join(classes) if classes else '(none defined)'}\n"
            f"Properties:\n{'  '.join(prop_descriptions) if prop_descriptions else '  (none defined)'}\n\n"
            "RULES:\n"
            "- Only use classes and properties defined in the schema above.\n"
            "- Each triple must have: subject (an entity name), predicate (a property name), object (entity name or literal value).\n"
            "- Return a JSON array of objects with keys: subject, predicate, object.\n"
            "- If no valid triples can be extracted, return an empty array [].\n"
            "- Do NOT invent classes or properties not in the schema.\n"
        )

        return self._call_llm(system_prompt, text)

    def _extract_open(self, text: str) -> list[ExtractedTriple]:
        system_prompt = (
            "You are a knowledge-graph triple extractor. "
            "Extract structured triples from the given text.\n\n"
            "RULES:\n"
            "- Extract entities and relationships freely from the text.\n"
            "- Each triple must have: subject (an entity name), predicate (a relationship), object (entity name or literal value).\n"
            "- Use PascalCase for entity names (e.g., 'MehdiAllahyari', 'BrandPulse').\n"
            "- Use camelCase for predicates (e.g., 'foundedBy', 'worksAt', 'hasAge').\n"
            "- Return a JSON array of objects with keys: subject, predicate, object.\n"
            "- If no triples can be extracted, return an empty array [].\n"
        )

        return self._call_llm(system_prompt, text)

    def _call_llm(self, system_prompt: str, text: str) -> list[ExtractedTriple]:
        try:
            response = self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
        except OpenAIError as exc:
            raise ExtractionError(f"LLM call failed: {exc}") from exc

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON: %s", content[:200])
            return []

        # Handle both {"triples": [...]} and [...] formats
        triples_raw = data if isinstance(data, list) else data.get("triples", [])

        triples = []
        for t in triples_raw:
            if isinstance(t, dict) and "subject" in t and "predicate" in t and "object" in t:
                triples.append(
                    ExtractedTriple(
                        subject=str(t["subject"]),
                        predicate=str(t["predicate"]),
                        object=str(t["object"]),
                    )
                )
        logger.debug("Extracted %d triples from text", len(triples))
        return triples
