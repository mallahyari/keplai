from __future__ import annotations

import json
import logging
import re
from typing import Any, TYPE_CHECKING

from openai import AsyncOpenAI, OpenAIError

from keplai.exceptions import QueryError

if TYPE_CHECKING:
    from keplai.config import KeplAISettings
    from keplai.graph import KeplAI

logger = logging.getLogger(__name__)

_FORBIDDEN_PATTERNS = re.compile(
    r"\b(INSERT|DELETE|DROP|CLEAR|LOAD|CREATE|COPY|MOVE|ADD)\b",
    re.IGNORECASE,
)


class NLQueryEngine:
    """Translate natural-language questions into SPARQL and execute them."""

    def __init__(self, settings: KeplAISettings, graph: KeplAI) -> None:
        self._settings = settings
        self._graph = graph
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def ask(self, question: str) -> dict[str, Any]:
        """Answer a natural-language question against the knowledge graph.

        Returns:
            {"results": [...], "sparql": "<generated query>"}
        """
        schema = self._graph.ontology.get_schema()
        sample_entities = self._get_sample_entities()

        sparql = await self._generate_sparql(question, schema, sample_entities)
        self._validate_read_only(sparql)

        try:
            results = self._graph._execute_query(sparql)
        except Exception as exc:
            logger.error("SPARQL execution failed: %s\nQuery: %s", exc, sparql)
            raise QueryError(f"SPARQL execution failed: {exc}") from exc
        return {"results": results, "sparql": sparql}

    async def ask_with_explanation(self, question: str) -> dict[str, Any]:
        """Answer a question and provide an explanation of the results.

        Returns:
            {"results": [...], "sparql": "<generated query>", "explanation": "..."}
        """
        answer = await self.ask(question)
        explanation = await self._explain_results(question, answer["results"], answer["sparql"])
        answer["explanation"] = explanation
        return answer

    def execute_sparql(self, sparql: str) -> list[dict[str, str]]:
        """Execute a raw SPARQL SELECT query (read-only enforced)."""
        self._validate_read_only(sparql)
        return self._graph._execute_query(sparql)

    async def _generate_sparql(
        self,
        question: str,
        schema: dict[str, Any],
        sample_entities: list[str],
    ) -> str:
        classes = schema.get("classes", [])
        properties = schema.get("properties", [])

        # Group classes by namespace for clarity
        namespaces: dict[str, list[str]] = {}
        for c in classes:
            uri = c.get("uri", "")
            name = c.get("name", "")
            ns = uri.rsplit("#", 1)[0] + "#" if "#" in uri else uri.rsplit("/", 1)[0] + "/"
            namespaces.setdefault(ns, [])
            namespaces[ns].append(f"{name} <{uri}>")

        class_lines = []
        for ns, items in namespaces.items():
            class_lines.append(f"  Namespace {ns}:")
            for item in items:
                class_lines.append(f"    - {item}")

        prop_lines = []
        for p in properties:
            uri = p.get("uri", "")
            name = p.get("name", "")
            prop_lines.append(
                f"  - {name} <{uri}>: "
                f"domain={p.get('domain', '?')}, range={p.get('range', '?')}"
            )

        has_multiple_namespaces = len(namespaces) > 1
        graph_instruction = (
            "- The graph contains multiple ontologies from different namespaces.\n"
            "  Use GRAPH clauses if needed to query within specific named graphs.\n"
        ) if has_multiple_namespaces else ""

        system_prompt = (
            "You are a SPARQL query generator for a knowledge graph.\n\n"
            "GRAPH SCHEMA:\n"
            f"Default entity namespace: {self._graph._settings.entity_namespace}\n"
            f"Default ontology namespace: {self._graph._settings.ontology_namespace}\n\n"
            f"Classes:\n"
            f"{''.join(class_lines) if class_lines else '  (none)'}\n"
            f"Properties:\n"
            f"{''.join(prop_lines) if prop_lines else '  (none)'}\n"
            f"Sample entities: {', '.join(sample_entities[:20]) if sample_entities else '(none)'}\n\n"
            "RULES:\n"
            "- Generate ONLY a SELECT query. Never INSERT, DELETE, DROP, or modify data.\n"
            "- IMPORTANT: Use the exact full URIs shown above for classes and properties.\n"
            "  Do NOT assume all URIs use the default namespace — use the URIs from the schema.\n"
            "- For entity instances, use the default entity namespace unless you see otherwise.\n"
            f"{graph_instruction}"
            "- Return ONLY the SPARQL query, no explanation or markdown.\n"
            "- Use PREFIX declarations for cleaner queries.\n"
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.0,
            )
        except OpenAIError as exc:
            logger.error(
                "OpenAI call failed during SPARQL generation: %s (type=%s, cause=%r)",
                exc, type(exc).__name__, exc.__cause__,
            )
            raise QueryError(f"LLM call failed during SPARQL generation: {exc}") from exc

        sparql = response.choices[0].message.content or ""
        # Strip markdown code fences if present
        sparql = re.sub(r"^```(?:sparql)?\s*", "", sparql.strip())
        sparql = re.sub(r"\s*```$", "", sparql.strip())
        return sparql.strip()

    async def _explain_results(
        self,
        question: str,
        results: list[dict[str, str]],
        sparql: str,
    ) -> str:
        system_prompt = (
            "You are explaining knowledge graph query results to a user. "
            "Be concise and clear. Mention if results come from inferred (reasoned) vs. asserted facts."
        )
        user_msg = (
            f"Question: {question}\n"
            f"SPARQL used: {sparql}\n"
            f"Results: {json.dumps(results[:50])}\n\n"
            "Explain these results in 2-3 sentences."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
            )
        except OpenAIError as exc:
            logger.error("OpenAI call failed during explanation: %s", exc)
            raise QueryError(f"LLM call failed during explanation: {exc}") from exc
        return response.choices[0].message.content or ""

    def _get_sample_entities(self, limit: int = 20) -> list[str]:
        """Fetch a sample of entity names from across all data graphs."""
        ent_ns = self._graph._settings.entity_namespace
        meta_graph = self._graph._settings.metadata_graph
        sparql = (
            f"SELECT DISTINCT ?s WHERE {{ "
            f"{{ ?s ?p ?o . FILTER(STRSTARTS(STR(?s), \"{ent_ns}\")) }} "
            f"UNION "
            f"{{ GRAPH ?g {{ ?s ?p ?o . FILTER(STRSTARTS(STR(?s), \"{ent_ns}\")) }} "
            f"   FILTER(?g != <{meta_graph}>) }} "
            f"}} LIMIT {limit}"
        )
        try:
            rows = self._graph._execute_query(sparql)
            return [r["s"].replace(ent_ns, "") for r in rows if "s" in r]
        except Exception:
            return []

    @staticmethod
    def _validate_read_only(sparql: str) -> None:
        """Reject any SPARQL that attempts to modify the graph."""
        if _FORBIDDEN_PATTERNS.search(sparql):
            raise QueryError(
                "Only read-only SPARQL queries (SELECT/ASK/CONSTRUCT/DESCRIBE) are allowed."
            )
