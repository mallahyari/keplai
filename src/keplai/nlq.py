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

# Standard prefixes auto-injected when the LLM uses them without declaring
_STANDARD_PREFIXES = {
    "rdfs:": "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
    "rdf:": "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
    "owl:": "PREFIX owl: <http://www.w3.org/2002/07/owl#>",
    "xsd:": "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>",
    "skos:": "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>",
}


class NLQueryEngine:
    """Translate natural-language questions into SPARQL and execute them."""

    def __init__(self, settings: KeplAISettings, graph: KeplAI) -> None:
        self._settings = settings
        self._graph = graph
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ask(self, question: str) -> dict[str, Any]:
        """Answer a natural-language question against the knowledge graph.

        Pipeline:
            resolve_entities → map_relations → generate_sparql
            → validate_predicates → repair (if needed) → execute
        """
        schema = self._graph.ontology.get_schema()
        sample_entities = self._get_sample_entities()
        graph_predicates = self._get_all_predicates()

        # Build the full predicate list (schema + graph)
        all_predicate_info = self._build_predicate_info(schema, graph_predicates)
        allowed_uris = {p["uri"] for p in all_predicate_info}

        # Step 1: Map natural-language phrases → graph predicates
        relation_map = await self._map_relations(question, all_predicate_info)
        logger.info("Relation map: %s", relation_map)

        # Step 2: Generate SPARQL
        sparql = await self._generate_sparql(
            question, schema, sample_entities, all_predicate_info, relation_map,
        )
        logger.info("Generated SPARQL:\n%s", sparql)

        # Step 3: Validate predicates — repair if any are invalid
        invalid = self._validate_predicates(sparql, allowed_uris)
        if invalid:
            logger.warning("Invalid predicates found: %s — attempting repair", invalid)
            sparql = await self._repair_sparql(sparql, invalid, sorted(allowed_uris))
            logger.info("Repaired SPARQL:\n%s", sparql)

        self._validate_read_only(sparql)

        try:
            results = self._graph._execute_query(sparql)
        except Exception as exc:
            logger.error("SPARQL execution failed: %s\nQuery: %s", exc, sparql)
            raise QueryError(f"SPARQL execution failed: {exc}") from exc
        return {"results": results, "sparql": sparql}

    async def ask_with_explanation(self, question: str) -> dict[str, Any]:
        """Answer a question and provide an explanation of the results."""
        answer = await self.ask(question)
        explanation = await self._explain_results(
            question, answer["results"], answer["sparql"],
        )
        answer["explanation"] = explanation
        return answer

    def execute_sparql(self, sparql: str) -> list[dict[str, str]]:
        """Execute a raw SPARQL SELECT query (read-only enforced)."""
        self._validate_read_only(sparql)
        return self._graph._execute_query(sparql)

    # ------------------------------------------------------------------
    # Step 1: Relation mapping
    # ------------------------------------------------------------------

    async def _map_relations(
        self,
        question: str,
        predicates: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Map natural-language phrases in the question to graph predicates."""
        if not predicates:
            return {}

        pred_lines = []
        for p in predicates:
            uri = p["uri"]
            name = p["name"]
            desc = p.get("description", name)
            pred_lines.append(f"- {name} <{uri}>: {desc}")

        system_prompt = (
            "You are mapping natural language phrases to knowledge graph predicates.\n\n"
            f"Available predicates:\n{chr(10).join(pred_lines)}\n\n"
            "Task:\n"
            "Map phrases in the user's question to the closest predicate from the list above.\n\n"
            "Rules:\n"
            "- Only use predicates from the list\n"
            "- Do NOT invent new predicates\n"
            "- If no predicate matches a phrase, omit it\n\n"
            "Return ONLY a JSON object mapping phrases to predicate URIs.\n"
            'Example: {"works at": "http://keplai.io/ontology/worksAt", '
            '"founded": "http://keplai.io/ontology/founded"}'
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
            raw = response.choices[0].message.content or "{}"
            raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            raw = re.sub(r"\s*```$", "", raw.strip())
            result = json.loads(raw)
            if not isinstance(result, dict):
                return {}
            return result
        except Exception:
            logger.debug("Relation mapping failed, continuing without it", exc_info=True)
            return {}

    # ------------------------------------------------------------------
    # Step 2: SPARQL generation
    # ------------------------------------------------------------------

    async def _generate_sparql(
        self,
        question: str,
        schema: dict[str, Any],
        sample_entities: list[str],
        all_predicate_info: list[dict[str, Any]],
        relation_map: dict[str, str],
    ) -> str:
        classes = schema.get("classes", [])

        # Group classes by namespace
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

        # Build enriched property lines
        prop_lines = []
        for p in all_predicate_info:
            line = f"  - {p['name']} <{p['uri']}>"
            extras = []
            if p.get("domain"):
                extras.append(f"domain={p['domain']}")
            if p.get("range"):
                extras.append(f"range={p['range']}")
            if p.get("description") and p["description"] != p["name"]:
                extras.append(f'description: "{p["description"]}"')
            if extras:
                line += f" ({', '.join(extras)})"
            prop_lines.append(line)

        has_multiple_namespaces = len(namespaces) > 1
        graph_instruction = (
            "- The graph contains multiple ontologies from different namespaces.\n"
            "  Use GRAPH clauses if needed to query within specific named graphs.\n"
        ) if has_multiple_namespaces else ""

        # Resolve entity names
        resolved_entities = await self._resolve_entities(question, sample_entities)
        entity_hint = ""
        if resolved_entities:
            mappings = ", ".join(f'"{k}" → entity:{v}' for k, v in resolved_entities.items())
            entity_hint = f"ENTITY MAPPINGS (use these exact entity names):\n{mappings}\n\n"

        # Relation mapping hint
        relation_hint = ""
        if relation_map:
            lines = []
            for phrase, uri in relation_map.items():
                lines.append(f'  "{phrase}" → <{uri}>')
            relation_hint = (
                "RELATION MAPPINGS (use these EXACTLY when constructing the query):\n"
                + chr(10).join(lines) + "\n\n"
            )

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
            f"{relation_hint}"
            "RULES:\n"
            "- Generate ONLY a SELECT query. Never INSERT, DELETE, DROP, or modify data.\n"
            "- CRITICAL: You MUST ONLY use property URIs listed above. NEVER invent or guess\n"
            "  property names like birthDate, hasName, etc. If no listed property matches the\n"
            "  question, pick the closest one from the list above.\n"
            "- If RELATION MAPPINGS are provided above, you MUST use those exact URIs.\n"
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
        sparql = self._postprocess_sparql(sparql)
        return sparql

    # ------------------------------------------------------------------
    # Step 3: Predicate validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_predicates(sparql: str, allowed_uris: set[str]) -> list[str]:
        """Extract predicate URIs from SPARQL and return any not in allowed set."""
        # Match full URIs in angle brackets
        all_uris = set(re.findall(r"<(https?://[^>]+)>", sparql))

        # Also resolve prefixed names (PREFIX foo: <ns> ... foo:bar)
        prefixes: dict[str, str] = {}
        for match in re.finditer(r"PREFIX\s+(\w+):\s*<([^>]+)>", sparql, re.IGNORECASE):
            prefixes[match.group(1)] = match.group(2)

        for match in re.finditer(r"(?<!\w)(\w+):(\w+)", sparql):
            prefix, local = match.group(1), match.group(2)
            if prefix.upper() == "PREFIX":
                continue
            if prefix in prefixes:
                all_uris.add(prefixes[prefix] + local)

        # Filter: only check URIs that look like predicates (used in triple patterns)
        # Skip well-known non-predicate URIs (namespaces, entity URIs, graph URIs)
        well_known = {
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://www.w3.org/2000/01/rdf-schema#label",
            "http://www.w3.org/2000/01/rdf-schema#comment",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.w3.org/2002/07/owl#",
        }

        invalid = []
        for uri in all_uris:
            # Skip well-known standard URIs
            if any(uri.startswith(wk) or uri == wk for wk in well_known):
                continue
            # Skip entity namespace URIs (these are subjects/objects, not predicates)
            if uri.startswith(str(allowed_uris).split("/entity/")[0] + "/entity/" if "/entity/" in str(allowed_uris) else "___never_match___"):
                continue
            # Check if this URI is in our allowed predicate set
            if uri in allowed_uris:
                continue
            # Only flag as invalid if it looks like an ontology/predicate URI
            # (not a namespace declaration or entity reference)
            if "/ontology/" in uri or "/property/" in uri or "#" in uri:
                invalid.append(uri)

        return invalid

    # ------------------------------------------------------------------
    # Step 4: Repair loop
    # ------------------------------------------------------------------

    async def _repair_sparql(
        self,
        sparql: str,
        invalid_predicates: list[str],
        allowed_predicates: list[str],
    ) -> str:
        """Ask the LLM to fix a SPARQL query that uses invalid predicates."""
        invalid_lines = "\n".join(f"  - {u}" for u in invalid_predicates)
        allowed_lines = "\n".join(f"  - {u}" for u in allowed_predicates)

        system_prompt = (
            "You are fixing a SPARQL query that contains invalid predicates.\n\n"
            f"Invalid predicates found in the query:\n{invalid_lines}\n\n"
            f"Allowed predicates (use ONLY these):\n{allowed_lines}\n\n"
            "Fix the query by replacing each invalid predicate with the closest "
            "allowed predicate from the list above.\n"
            "Return ONLY the corrected SPARQL query, no explanation."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sparql},
                ],
                temperature=0.0,
            )
        except OpenAIError as exc:
            logger.error("Repair LLM call failed: %s", exc)
            return sparql  # Return original if repair fails

        repaired = response.choices[0].message.content or sparql
        repaired = self._postprocess_sparql(repaired)
        return repaired

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_predicate_info(
        self,
        schema: dict[str, Any],
        graph_predicates: list[str],
    ) -> list[dict[str, Any]]:
        """Merge schema properties with graph predicates into a unified list."""
        schema_properties = schema.get("properties", [])
        schema_uris = {p.get("uri", "") for p in schema_properties}

        result = []
        for p in schema_properties:
            uri = p.get("uri", "")
            name = p.get("name", "")
            result.append({
                "uri": uri,
                "name": name,
                "domain": p.get("domain"),
                "range": p.get("range"),
                "description": self._infer_description(name),
            })

        for pred_uri in graph_predicates:
            if pred_uri not in schema_uris:
                if "#" in pred_uri:
                    short = pred_uri.split("#")[-1]
                elif "/" in pred_uri:
                    short = pred_uri.split("/")[-1]
                else:
                    short = pred_uri
                result.append({
                    "uri": pred_uri,
                    "name": short,
                    "domain": None,
                    "range": None,
                    "description": self._infer_description(short),
                })

        return result

    @staticmethod
    def _infer_description(name: str) -> str:
        """Generate a human-readable description from a predicate name."""
        # Split camelCase/PascalCase into words
        words = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).lower()
        # Common predicate patterns
        known = {
            "founded": "a person started or created something",
            "works at": "a person is employed by an organization",
            "worksat": "a person is employed by an organization",
            "born on": "the date someone was born",
            "bornon": "the date someone was born",
            "born in": "the place where someone was born",
            "bornin": "the place where someone was born",
            "knows": "one person knows another person",
            "type": "the class or category of an entity",
            "label": "the human-readable name of an entity",
            "industry": "the industry sector of an organization",
            "located in": "the location of something",
            "locatedin": "the location of something",
        }
        return known.get(words, words)

    def _postprocess_sparql(self, sparql: str) -> str:
        """Apply safety-net transformations to generated SPARQL."""
        # Strip markdown code fences
        sparql = re.sub(r"^```(?:sparql)?\s*", "", sparql.strip())
        sparql = re.sub(r"\s*```$", "", sparql.strip())
        sparql = sparql.strip()

        # Inject standard prefixes if used without declaration
        for prefix, declaration in _STANDARD_PREFIXES.items():
            if prefix in sparql and declaration not in sparql:
                sparql = declaration + "\n" + sparql

        # Inject GRAPH clause if missing
        if "GRAPH" not in sparql.upper():
            sparql = re.sub(
                r"(WHERE\s*\{)(.*?)(\}\s*)$",
                r"\1 GRAPH ?g {\2}\3",
                sparql,
                flags=re.DOTALL | re.IGNORECASE,
            )

        return sparql

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
        """Extract entity mentions from the question and resolve them via
        the disambiguator's vector similarity search."""
        if not sample_entities:
            return {}

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
