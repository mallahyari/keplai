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
        schema_properties = schema.get("properties", [])

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

        # Build comprehensive property list: schema properties + all predicates in graph
        schema_prop_uris = {p.get("uri", "") for p in schema_properties}
        prop_lines = []
        for p in schema_properties:
            uri = p.get("uri", "")
            name = p.get("name", "")
            prop_lines.append(
                f"  - {name} <{uri}>: "
                f"domain={p.get('domain', '?')}, range={p.get('range', '?')}"
            )
        # Add predicates actually used in triples but not in the ontology schema
        graph_predicates = self._get_all_predicates()
        for pred_uri in graph_predicates:
            if pred_uri not in schema_prop_uris:
                # Extract short name from URI
                if "#" in pred_uri:
                    short = pred_uri.split("#")[-1]
                elif "/" in pred_uri:
                    short = pred_uri.split("/")[-1]
                else:
                    short = pred_uri
                prop_lines.append(f"  - {short} <{pred_uri}>")

        has_multiple_namespaces = len(namespaces) > 1
        graph_instruction = (
            "- The graph contains multiple ontologies from different namespaces.\n"
            "  Use GRAPH clauses if needed to query within specific named graphs.\n"
        ) if has_multiple_namespaces else ""

        # Resolve entity names mentioned in the question against the graph
        resolved_entities = await self._resolve_entities(question, sample_entities)
        entity_hint = ""
        if resolved_entities:
            mappings = ", ".join(f'"{k}" → entity:{v}' for k, v in resolved_entities.items())
            entity_hint = f"ENTITY MAPPINGS (use these exact entity names):\n{mappings}\n\n"

        system_prompt = (
            "You are a SPARQL query generator for a knowledge graph.\n\n"
            "GRAPH SCHEMA:\n"
            f"Default entity namespace: {self._graph._settings.entity_namespace}\n"
            f"Default ontology namespace: {self._graph._settings.ontology_namespace}\n\n"
            "Classes:\n"
            f"{chr(10).join(class_lines) if class_lines else '  (none)'}\n\n"
            "Properties (ONLY use these — do NOT invent property names):\n"
            f"{chr(10).join(prop_lines) if prop_lines else '  (none)'}\n\n"
            f"Sample entities: {', '.join(sample_entities[:20]) if sample_entities else '(none)'}\n\n"
            f"{entity_hint}"
            "RULES:\n"
            "- Generate ONLY a SELECT query. Never INSERT, DELETE, DROP, or modify data.\n"
            "- CRITICAL: You MUST ONLY use property URIs listed above. NEVER invent or guess\n"
            "  property names like birthDate, hasName, etc. If no listed property matches the\n"
            "  question, pick the closest one from the list above.\n"
            "- IMPORTANT: Use the exact full URIs shown above for classes and properties.\n"
            "  Do NOT assume all URIs use the default namespace — use the URIs from the schema.\n"
            "- For entity instances, use the default entity namespace unless you see otherwise.\n"
            "- If entity mappings are provided above, use those exact entity names.\n"
            f"{graph_instruction}"
            "- IMPORTANT: All triples are stored in named graphs, NOT the default graph.\n"
            "  You MUST wrap your WHERE patterns inside: GRAPH ?g { ... }\n"
            "  Example: SELECT ?x WHERE { GRAPH ?g { entity:Foo ontology:bar ?x } }\n"
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
        sparql = sparql.strip()

        # Safety net: if the LLM forgot the GRAPH clause, inject one.
        # All triples live in named graphs; querying the default graph returns nothing.
        if "GRAPH" not in sparql.upper():
            sparql = re.sub(
                r"(WHERE\s*\{)(.*?)(\}\s*)$",
                r"\1 GRAPH ?g {\2}\3",
                sparql,
                flags=re.DOTALL | re.IGNORECASE,
            )

        return sparql

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

    def _get_all_predicates(self) -> list[str]:
        """Fetch all distinct predicate URIs used in actual triples."""
        meta_graph = self._graph._settings.metadata_graph
        sparql = (
            f"SELECT DISTINCT ?p WHERE {{ "
            f"GRAPH ?g {{ ?s ?p ?o }} "
            f"FILTER(?g != <{meta_graph}>) "
            f"}}"
        )
        try:
            rows = self._graph._execute_query(sparql)
            return [r["p"] for r in rows if "p" in r]
        except Exception:
            return []

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

    async def _resolve_entities(
        self, question: str, sample_entities: list[str],
    ) -> dict[str, str]:
        """Extract likely entity mentions from the question and resolve them
        against the graph using the disambiguator's vector similarity search.

        Returns a mapping of mention → matched entity name (short name)."""
        if not sample_entities:
            return {}

        # Use the LLM to extract entity mentions from the question
        try:
            response = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": (
                        "Extract proper nouns and entity names from the user's question. "
                        "Return them as a JSON array of strings. "
                        "Example: [\"Tom Hanks\", \"Forrest Gump\"]\n"
                        "Return ONLY the JSON array, nothing else. "
                        "If no entities found, return []."
                    )},
                    {"role": "user", "content": question},
                ],
                temperature=0.0,
            )
            mentions_raw = response.choices[0].message.content or "[]"
            mentions = json.loads(mentions_raw.strip())
            if not isinstance(mentions, list):
                return {}
        except Exception:
            return {}

        # Resolve each mention against the graph via disambiguator
        resolved: dict[str, str] = {}
        for mention in mentions:
            if not isinstance(mention, str) or not mention.strip():
                continue
            try:
                similar = self._graph.disambiguator.get_similar(mention)
                import asyncio
                if asyncio.iscoroutine(similar):
                    similar = await similar
                if similar and len(similar) > 0:
                    best = similar[0]
                    # Accept if similarity score is reasonable
                    name = best.get("name", best.get("entity", ""))
                    score = best.get("score", 0)
                    if name and (score is None or score >= 0.3):
                        resolved[mention] = name
            except Exception:
                continue

        return resolved

    @staticmethod
    def _validate_read_only(sparql: str) -> None:
        """Reject any SPARQL that attempts to modify the graph."""
        if _FORBIDDEN_PATTERNS.search(sparql):
            raise QueryError(
                "Only read-only SPARQL queries (SELECT/ASK/CONSTRUCT/DESCRIBE) are allowed."
            )
