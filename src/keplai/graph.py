from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from rdflib import URIRef, Literal, Namespace, XSD, RDF, RDFS, OWL
from SPARQLWrapper import SPARQLWrapper, JSON, POST, POSTDIRECTLY

from keplai.config import KeplAISettings
from keplai.engine import JenaEngine

if TYPE_CHECKING:
    from keplai.ontology import OntologyManager
    from keplai.extractor import AIExtractor
    from keplai.disambiguator import EntityDisambiguator
    from keplai.nlq import NLQueryEngine

logger = logging.getLogger(__name__)


class KeplAI:
    """Main entry point for the KeplAI knowledge graph SDK."""

    def __init__(self, engine: JenaEngine, settings: KeplAISettings) -> None:
        self._engine = engine
        self._settings = settings
        self._entity_ns = Namespace(settings.entity_namespace)
        self._ontology_ns = Namespace(settings.ontology_namespace)
        self._ontology: OntologyManager | None = None
        self._extractor: AIExtractor | None = None
        self._disambiguator: EntityDisambiguator | None = None
        self._nlq: NLQueryEngine | None = None

    @property
    def ontology(self) -> OntologyManager:
        """Access the ontology manager."""
        if self._ontology is None:
            from keplai.ontology import OntologyManager
            self._ontology = OntologyManager(self)
        return self._ontology

    @property
    def extractor(self) -> AIExtractor:
        """Access the AI triple extractor (lazy-loaded)."""
        if self._extractor is None:
            from keplai.extractor import AIExtractor
            self._extractor = AIExtractor(self._settings)
        return self._extractor

    @property
    def disambiguator(self) -> EntityDisambiguator:
        """Access the entity disambiguator (lazy-loaded)."""
        if self._disambiguator is None:
            from keplai.disambiguator import EntityDisambiguator
            from keplai.vectorstore.qdrant import QdrantVectorStore
            store = QdrantVectorStore(
                embedding_dim=self._settings.embedding_dim,
                path=self._settings.qdrant_path,
            )
            self._disambiguator = EntityDisambiguator(self._settings, store)
        return self._disambiguator

    @property
    def nlq(self) -> NLQueryEngine:
        """Access the natural-language query engine (lazy-loaded)."""
        if self._nlq is None:
            from keplai.nlq import NLQueryEngine
            self._nlq = NLQueryEngine(self._settings, self)
        return self._nlq

    async def ask(self, question: str) -> dict[str, Any]:
        """Ask a natural-language question against the knowledge graph."""
        return await self.nlq.ask(question)

    async def ask_with_explanation(self, question: str) -> dict[str, Any]:
        """Ask a question and get results with an explanation."""
        return await self.nlq.ask_with_explanation(question)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def start(
        cls,
        engine: str = "docker",
        reasoner: str = "OWL",
        **overrides: Any,
    ) -> KeplAI:
        """Provision the graph engine and return a ready-to-use instance."""
        settings = KeplAISettings(reasoner=reasoner, **overrides)

        if engine != "docker":
            raise ValueError(f"Unsupported engine: {engine!r}. Only 'docker' is supported.")

        jena = JenaEngine(settings)
        jena.start()
        return cls(engine=jena, settings=settings)

    @classmethod
    def connect(
        cls,
        endpoint: str = "http://localhost:3030",
        dataset: str = "keplai",
        **overrides: Any,
    ) -> KeplAI:
        """Connect to an existing Fuseki instance without starting Docker.

        Args:
            endpoint: The Fuseki server URL (e.g. http://localhost:3030).
            dataset: The dataset name on the Fuseki server.
        """
        settings = KeplAISettings(
            fuseki_port=int(endpoint.rsplit(":", 1)[-1]) if ":" in endpoint.rsplit("/", 1)[-1] else 3030,
            fuseki_dataset=dataset,
            **overrides,
        )
        jena = JenaEngine(settings)
        # Don't start Docker — just verify connectivity
        if not jena.is_healthy():
            from keplai.exceptions import EngineError
            raise EngineError(f"Cannot connect to Fuseki at {endpoint}")
        return cls(engine=jena, settings=settings)

    def stop(self) -> None:
        """Gracefully shut down the engine. Data persists via Docker volumes."""
        self._engine.stop()

    # ------------------------------------------------------------------
    # AI Extraction
    # ------------------------------------------------------------------

    async def extract_and_store(
        self,
        text: str,
        mode: str = "strict",
    ) -> list[dict[str, Any]]:
        """Extract triples from text, disambiguate entities, and store in graph.

        Returns the list of stored triples with disambiguation info.
        """
        schema = self.ontology.get_schema() if mode == "strict" else None
        raw_triples = await self.extractor.extract(text, mode=mode, schema=schema)

        results = []
        for t in raw_triples:
            subj, subj_score, subj_match = await self.disambiguator.resolve(t.subject)
            # Only disambiguate object if it looks like an entity (PascalCase, no spaces)
            obj = t.object
            obj_score, obj_match = None, None
            if obj and obj[0].isupper() and " " not in obj:
                obj, obj_score, obj_match = await self.disambiguator.resolve(obj)

            self.add(subj, t.predicate, obj)

            results.append({
                "subject": subj,
                "predicate": t.predicate,
                "object": obj,
                "disambiguation": {
                    "subject_original": t.subject,
                    "subject_matched": subj_match,
                    "subject_score": subj_score,
                    "object_original": t.object,
                    "object_matched": obj_match,
                    "object_score": obj_score,
                },
            })

        logger.info("Extracted and stored %d triples from text", len(results))
        return results

    async def extract_preview(
        self,
        text: str,
        mode: str = "strict",
    ) -> list[dict[str, Any]]:
        """Extract triples from text with disambiguation preview — without storing."""
        schema = self.ontology.get_schema() if mode == "strict" else None
        raw_triples = await self.extractor.extract(text, mode=mode, schema=schema)

        results = []
        for t in raw_triples:
            # Show what disambiguation *would* do without committing
            subj_similar = await self.disambiguator.get_similar(t.subject, top_k=3)
            obj_similar = []
            if t.object and t.object[0].isupper() and " " not in t.object:
                obj_similar = await self.disambiguator.get_similar(t.object, top_k=3)

            results.append({
                "subject": t.subject,
                "predicate": t.predicate,
                "object": t.object,
                "subject_candidates": subj_similar,
                "object_candidates": obj_similar,
            })

        return results

    # ------------------------------------------------------------------
    # Triple CRUD
    # ------------------------------------------------------------------

    def add(self, subject: str, predicate: str, obj: str | int | float) -> None:
        """Insert a single triple into the graph."""
        s = self._to_entity_uri(subject)
        p = self._to_predicate_uri(predicate)
        o = self._to_object(obj)
        sparql = f"INSERT DATA {{ {s.n3()} {p.n3()} {o.n3()} }}"
        self._execute_update(sparql)
        logger.debug("Added triple: %s %s %s", subject, predicate, obj)

    def find(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        obj: str | int | float | None = None,
    ) -> list[dict[str, str]]:
        """Query triples with optional filters. Returns list of {s, p, o} dicts."""
        s = self._to_entity_uri(subject).n3() if subject else "?s"
        p = self._to_predicate_uri(predicate).n3() if predicate else "?p"
        o = self._to_object(obj).n3() if obj is not None else "?o"

        sparql = f"SELECT ?s ?p ?o WHERE {{ {s} {p} {o} . }}"

        # Bind concrete values back to the variable names for uniform results
        if subject:
            sparql = sparql.replace(self._to_entity_uri(subject).n3(), f"{self._to_entity_uri(subject).n3()}")
            sparql = f"SELECT ?s ?p ?o WHERE {{ BIND({self._to_entity_uri(subject).n3()} AS ?s) ?s {p} {o} . }}"
        if predicate and not subject:
            sparql = f"SELECT ?s ?p ?o WHERE {{ ?s {p} {o} . BIND({self._to_predicate_uri(predicate).n3()} AS ?p) }}"
        if subject and predicate:
            sparql = (
                f"SELECT ?s ?p ?o WHERE {{ "
                f"BIND({self._to_entity_uri(subject).n3()} AS ?s) "
                f"BIND({self._to_predicate_uri(predicate).n3()} AS ?p) "
                f"?s ?p {o} . }}"
            )
        if subject and predicate and obj is not None:
            o_val = self._to_object(obj)
            sparql = (
                f"SELECT ?s ?p ?o WHERE {{ "
                f"BIND({self._to_entity_uri(subject).n3()} AS ?s) "
                f"BIND({self._to_predicate_uri(predicate).n3()} AS ?p) "
                f"BIND({o_val.n3()} AS ?o) "
                f"?s ?p ?o . }}"
            )

        return self._execute_query(sparql)

    def delete(self, subject: str, predicate: str, obj: str | int | float) -> None:
        """Remove a single triple from the graph."""
        s = self._to_entity_uri(subject)
        p = self._to_predicate_uri(predicate)
        o = self._to_object(obj)
        sparql = f"DELETE DATA {{ {s.n3()} {p.n3()} {o.n3()} }}"
        self._execute_update(sparql)
        logger.debug("Deleted triple: %s %s %s", subject, predicate, obj)

    def get_all_triples(self) -> list[dict[str, str]]:
        """Return every triple in the graph."""
        return self._execute_query("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")

    # ------------------------------------------------------------------
    # Namespace helpers
    # ------------------------------------------------------------------

    def _to_entity_uri(self, value: str) -> URIRef:
        """Map a plain string to an entity URI, or pass through if already a URI."""
        value = value.strip()
        if value.startswith("http://") or value.startswith("https://"):
            return URIRef(value)
        return self._entity_ns[value]

    def _to_predicate_uri(self, value: str) -> URIRef:
        """Map a plain string to an ontology predicate URI.

        Looks up existing properties in the graph first. If a property
        with a matching rdfs:label is found (e.g. from an imported ontology),
        its actual URI is used. Otherwise falls back to the KeplAI namespace.
        """
        value = value.strip()
        if value.startswith("http://") or value.startswith("https://"):
            return URIRef(value)

        # Check if a property with this label exists in the graph
        resolved = self._resolve_property_uri(value)
        if resolved is not None:
            return resolved
        return self._ontology_ns[value]

    def _resolve_property_uri(self, name: str) -> URIRef | None:
        """Find an existing property URI by label from any namespace."""
        sparql = (
            f"SELECT ?prop WHERE {{ "
            f"{{ ?prop {RDF.type.n3()} {OWL.ObjectProperty.n3()} }} "
            f"UNION "
            f"{{ ?prop {RDF.type.n3()} {OWL.DatatypeProperty.n3()} }} "
            f"?prop {RDFS.label.n3()} ?label . "
            f"FILTER(STR(?label) = \"{name}\") "
            f"}} LIMIT 1"
        )
        try:
            rows = self._execute_query(sparql)
            if rows:
                return URIRef(rows[0]["prop"])
        except Exception:
            pass
        return None

    def _to_object(self, value: str | int | float) -> URIRef | Literal:
        """Auto-detect whether an object is a literal or an entity URI."""
        if isinstance(value, int):
            return Literal(value, datatype=XSD.integer)
        if isinstance(value, float):
            return Literal(value, datatype=XSD.double)
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("http://") or value.startswith("https://"):
                return URIRef(value)
            # Heuristic: if it looks like a name/entity (capitalized, no spaces with special chars)
            # treat as entity URI; otherwise treat as literal
            if value and value[0].isupper() and " " not in value:
                # Check if this matches a known class from an imported ontology
                resolved = self._resolve_class_uri(value)
                if resolved is not None:
                    return resolved
                return self._entity_ns[value]
            return Literal(value)
        return Literal(str(value))

    def _resolve_class_uri(self, name: str) -> URIRef | None:
        """Find an existing class URI by label from any namespace."""
        sparql = (
            f"SELECT ?cls WHERE {{ "
            f"{{ ?cls {RDF.type.n3()} {OWL.Class.n3()} }} "
            f"UNION "
            f"{{ ?cls {RDF.type.n3()} {RDFS.Class.n3()} }} "
            f"?cls {RDFS.label.n3()} ?label . "
            f"FILTER(STR(?label) = \"{name}\") "
            f"}} LIMIT 1"
        )
        try:
            rows = self._execute_query(sparql)
            if rows:
                return URIRef(rows[0]["cls"])
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # SPARQL execution
    # ------------------------------------------------------------------

    def _sparql_wrapper(self, url: str) -> SPARQLWrapper:
        """Create a SPARQLWrapper with authentication configured."""
        wrapper = SPARQLWrapper(url)
        wrapper.setCredentials("admin", self._settings.fuseki_admin_password)
        return wrapper

    def _execute_update(self, sparql: str) -> None:
        """Execute a SPARQL UPDATE against Fuseki."""
        wrapper = self._sparql_wrapper(self._engine.update_url)
        wrapper.setMethod(POST)
        wrapper.setRequestMethod(POSTDIRECTLY)
        wrapper.setQuery(sparql)
        wrapper.query()

    def _execute_query(self, sparql: str) -> list[dict[str, str]]:
        """Execute a SPARQL SELECT and return results as list of dicts."""
        wrapper = self._sparql_wrapper(self._engine.sparql_url)
        wrapper.setQuery(sparql)
        wrapper.setReturnFormat(JSON)
        response = wrapper.query().convert()

        results = []
        for binding in response["results"]["bindings"]:
            row = {var: binding[var]["value"] for var in binding}
            results.append(row)
        return results
