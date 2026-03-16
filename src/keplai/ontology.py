from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.request import urlopen

from rdflib import URIRef, Graph as RDFGraph, Namespace, RDF, RDFS, OWL, XSD

if TYPE_CHECKING:
    from keplai.graph import KeplAI

logger = logging.getLogger(__name__)


class OntologyManager:
    """Manage OWL classes and properties stored in Fuseki."""

    def __init__(self, graph: KeplAI) -> None:
        self._graph = graph
        self._ont_ns = Namespace(graph._settings.ontology_namespace)

    # ------------------------------------------------------------------
    # Classes
    # ------------------------------------------------------------------

    def define_class(self, name: str) -> None:
        """Create an OWL Class in the graph."""
        cls_uri = self._ont_ns[name]
        sparql = (
            f"INSERT DATA {{ "
            f"{cls_uri.n3()} {RDF.type.n3()} {OWL.Class.n3()} . "
            f"{cls_uri.n3()} {RDFS.label.n3()} \"{name}\" . "
            f"}}"
        )
        self._graph._execute_update(sparql)
        logger.debug("Defined class: %s", name)

    def get_classes(self, graph_uri: str | None = None) -> list[dict[str, str]]:
        """List OWL classes, optionally filtered to a specific named graph."""
        if graph_uri:
            sparql = (
                f"SELECT ?cls ?label WHERE {{ "
                f"  GRAPH <{graph_uri}> {{ "
                f"    ?cls {RDF.type.n3()} {OWL.Class.n3()} . "
                f"    OPTIONAL {{ ?cls {RDFS.label.n3()} ?label }} "
                f"  }} "
                f"}}"
            )
        else:
            sparql = (
                f"SELECT DISTINCT ?cls ?label WHERE {{ "
                f"{{ ?cls {RDF.type.n3()} {OWL.Class.n3()} . "
                f"  OPTIONAL {{ ?cls {RDFS.label.n3()} ?label }} }} "
                f"UNION "
                f"{{ GRAPH ?g {{ ?cls {RDF.type.n3()} {OWL.Class.n3()} . "
                f"  OPTIONAL {{ ?cls {RDFS.label.n3()} ?label }} }} }} "
                f"}}"
            )
        rows = self._graph._execute_query(sparql)
        results = []
        for r in rows:
            uri = r.get("cls", "")
            label = r.get("label", uri.split("/")[-1] if "/" in uri else uri)
            results.append({"uri": uri, "name": label})
        return results

    def remove_class(self, name: str) -> None:
        """Remove an OWL class and its label from the graph."""
        cls_uri = self._ont_ns[name]
        sparql = (
            f"DELETE WHERE {{ "
            f"{cls_uri.n3()} ?p ?o . "
            f"}}"
        )
        self._graph._execute_update(sparql)
        logger.debug("Removed class: %s", name)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def define_property(
        self,
        name: str,
        domain: str,
        range: str,
    ) -> None:
        """Create an OWL ObjectProperty with domain and range.

        If range looks like a datatype (e.g. 'string', 'integer', 'date'),
        creates a DatatypeProperty instead.
        """
        prop_uri = self._ont_ns[name]
        domain_uri = self._ont_ns[domain]
        range_uri = self._resolve_range(range)

        prop_type = OWL.DatatypeProperty if self._is_datatype(range) else OWL.ObjectProperty

        sparql = (
            f"INSERT DATA {{ "
            f"{prop_uri.n3()} {RDF.type.n3()} {prop_type.n3()} . "
            f"{prop_uri.n3()} {RDFS.label.n3()} \"{name}\" . "
            f"{prop_uri.n3()} {RDFS.domain.n3()} {domain_uri.n3()} . "
            f"{prop_uri.n3()} {RDFS.range.n3()} {range_uri.n3()} . "
            f"}}"
        )
        self._graph._execute_update(sparql)
        logger.debug("Defined property: %s (%s → %s)", name, domain, range)

    def get_properties(self, graph_uri: str | None = None) -> list[dict[str, str]]:
        """List all defined properties with domain and range, optionally filtered."""
        if graph_uri:
            sparql = (
                f"SELECT ?prop ?label ?domain ?range WHERE {{ "
                f"  GRAPH <{graph_uri}> {{ "
                f"    {{ ?prop {RDF.type.n3()} {OWL.ObjectProperty.n3()} }} "
                f"    UNION "
                f"    {{ ?prop {RDF.type.n3()} {OWL.DatatypeProperty.n3()} }} "
                f"    OPTIONAL {{ ?prop {RDFS.label.n3()} ?label }} "
                f"    OPTIONAL {{ ?prop {RDFS.domain.n3()} ?domain }} "
                f"    OPTIONAL {{ ?prop {RDFS.range.n3()} ?range }} "
                f"  }} "
                f"}}"
            )
        else:
            sparql = (
                f"SELECT DISTINCT ?prop ?label ?domain ?range WHERE {{ "
                f"{{ "
                f"  {{ ?prop {RDF.type.n3()} {OWL.ObjectProperty.n3()} }} "
                f"  UNION "
                f"  {{ ?prop {RDF.type.n3()} {OWL.DatatypeProperty.n3()} }} "
                f"  OPTIONAL {{ ?prop {RDFS.label.n3()} ?label }} "
                f"  OPTIONAL {{ ?prop {RDFS.domain.n3()} ?domain }} "
                f"  OPTIONAL {{ ?prop {RDFS.range.n3()} ?range }} "
                f"}} UNION {{ "
                f"  GRAPH ?g {{ "
                f"    {{ ?prop {RDF.type.n3()} {OWL.ObjectProperty.n3()} }} "
                f"    UNION "
                f"    {{ ?prop {RDF.type.n3()} {OWL.DatatypeProperty.n3()} }} "
                f"    OPTIONAL {{ ?prop {RDFS.label.n3()} ?label }} "
                f"    OPTIONAL {{ ?prop {RDFS.domain.n3()} ?domain }} "
                f"    OPTIONAL {{ ?prop {RDFS.range.n3()} ?range }} "
                f"  }} "
                f"}} }}"
            )
        rows = self._graph._execute_query(sparql)
        results = []
        for r in rows:
            uri = r.get("prop", "")
            results.append({
                "uri": uri,
                "name": r.get("label", uri.split("/")[-1] if "/" in uri else uri),
                "domain": self._short_name(r.get("domain", "")),
                "range": self._short_name(r.get("range", "")),
            })
        return results

    def remove_property(self, name: str) -> None:
        """Remove a property and all its metadata from the graph."""
        prop_uri = self._ont_ns[name]
        sparql = (
            f"DELETE WHERE {{ "
            f"{prop_uri.n3()} ?p ?o . "
            f"}}"
        )
        self._graph._execute_update(sparql)
        logger.debug("Removed property: %s", name)

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def get_schema(self, graph_uri: str | None = None) -> dict[str, Any]:
        """Return the ontology schema, optionally filtered to a named graph."""
        return {
            "classes": self.get_classes(graph_uri=graph_uri),
            "properties": self.get_properties(graph_uri=graph_uri),
        }

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    _FORMAT_MAP: dict[str, str] = {
        ".ttl": "turtle",
        ".turtle": "turtle",
        ".rdf": "xml",
        ".xml": "xml",
        ".owl": "xml",
        ".nt": "nt",
        ".ntriples": "nt",
        ".jsonld": "json-ld",
        ".json": "json-ld",
    }

    _SUPPORTED_FORMATS = {"turtle", "xml", "nt", "json-ld", "n3", "trig"}

    def load_rdf(
        self,
        source: str | Path,
        format: str = "auto",
        batch_size: int = 1000,
        name: str | None = None,
        graph_uri: str | None = None,
    ) -> dict:
        """Parse an RDF file and load all triples into a named graph in Fuseki.

        Args:
            source: Path to an RDF file (OWL/XML, Turtle, N-Triples, JSON-LD).
            format: RDF serialization format. "auto" detects from file extension.
            batch_size: Number of triples per SPARQL INSERT batch.
            name: Human-readable name for this ontology. Defaults to filename.
            graph_uri: Named graph URI. Auto-generated if not provided.

        Returns:
            Summary dict with ontology_id, graph_uri, triples_loaded, format,
            classes, properties.
        """
        import uuid
        from datetime import datetime, timezone
        from keplai.exceptions import OntologyImportError

        path = Path(source)
        if not path.exists():
            raise OntologyImportError(f"File not found: {path}")

        if format == "auto":
            fmt = self._detect_format(path)
        else:
            if format not in self._SUPPORTED_FORMATS:
                raise OntologyImportError(f"Unsupported format: {format!r}")
            fmt = format

        try:
            rdf_graph = RDFGraph()
            rdf_graph.parse(str(path), format=fmt)
        except Exception as exc:
            raise OntologyImportError(f"Failed to parse {path.name}: {exc}") from exc

        # Generate ontology ID and graph URI
        ont_id = str(uuid.uuid4())
        ont_name = name or path.stem
        ont_graph = graph_uri or f"{self._graph._settings.graph_base_uri}{ont_id}"

        total = self._batch_insert(rdf_graph, batch_size=batch_size, graph_uri=ont_graph)
        detected = self._detect_schema_from_graph(rdf_graph)

        # Store metadata
        self._store_ontology_metadata(
            ontology_id=ont_id,
            name=ont_name,
            source=str(path),
            graph_uri=ont_graph,
            import_date=datetime.now(timezone.utc).isoformat(),
            classes_count=len(detected["classes"]),
            properties_count=len(detected["properties"]),
        )

        logger.info(
            "Imported %s into graph <%s>: %d triples, %d classes, %d properties",
            path.name, ont_graph, total, len(detected["classes"]), len(detected["properties"]),
        )

        return {
            "ontology_id": ont_id,
            "graph_uri": ont_graph,
            "triples_loaded": total,
            "format": fmt,
            **detected,
        }

    def load_url(
        self,
        url: str,
        format: str = "auto",
        batch_size: int = 1000,
        name: str | None = None,
        graph_uri: str | None = None,
    ) -> dict:
        """Fetch a remote ontology by URL and load it into a named graph.

        Args:
            url: HTTP(S) URL pointing to an RDF file.
            format: RDF format. "auto" detects from URL file extension.
            batch_size: Number of triples per SPARQL INSERT batch.
            name: Human-readable name. Defaults to URL.
            graph_uri: Named graph URI. Auto-generated if not provided.
        """
        from keplai.exceptions import OntologyImportError

        if not url.startswith(("http://", "https://")):
            raise OntologyImportError(f"URL must be http:// or https://, got: {url}")

        # Determine suffix from URL for format detection
        url_path = url.split("?")[0]
        suffix = Path(url_path).suffix.lower() or ".rdf"

        try:
            with urlopen(url) as resp:
                data = resp.read()
        except Exception as exc:
            raise OntologyImportError(f"Failed to fetch {url}: {exc}") from exc

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)

        try:
            return self.load_rdf(
                tmp_path, format=format, batch_size=batch_size,
                name=name or url, graph_uri=graph_uri,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    @staticmethod
    def _detect_format(path: Path) -> str:
        """Auto-detect RDF serialization format from file extension."""
        suffix = path.suffix.lower()
        fmt = OntologyManager._FORMAT_MAP.get(suffix)
        if fmt is None:
            from keplai.exceptions import OntologyImportError
            raise OntologyImportError(
                f"Unsupported file extension: {suffix}. "
                f"Supported: {', '.join(sorted(OntologyManager._FORMAT_MAP.keys()))}"
            )
        return fmt

    def _batch_insert(self, rdf_graph: RDFGraph, batch_size: int = 1000, graph_uri: str | None = None) -> int:
        """Bulk-insert triples from an rdflib Graph into Fuseki in batches."""
        triples = list(rdf_graph)
        total = len(triples)
        for i in range(0, total, batch_size):
            batch = triples[i : i + batch_size]
            parts = []
            for s, p, o in batch:
                parts.append(f"{s.n3()} {p.n3()} {o.n3()} .")
            triples_block = "\n".join(parts)
            if graph_uri:
                sparql = f"INSERT DATA {{ GRAPH <{graph_uri}> {{\n{triples_block}\n}} }}"
            else:
                sparql = f"INSERT DATA {{\n{triples_block}\n}}"
            self._graph._execute_update(sparql)
        logger.info("Batch-inserted %d triples in %d batches", total, (total + batch_size - 1) // batch_size)
        return total

    @staticmethod
    def _detect_schema_from_graph(rdf_graph: RDFGraph) -> dict:
        """Detect classes and properties from a parsed rdflib Graph."""
        classes = []
        for cls_uri in rdf_graph.subjects(RDF.type, OWL.Class):
            label = str(cls_uri).split("/")[-1].split("#")[-1]
            for lbl in rdf_graph.objects(cls_uri, RDFS.label):
                label = str(lbl)
                break
            classes.append({"uri": str(cls_uri), "name": label})

        # Also check rdfs:Class
        for cls_uri in rdf_graph.subjects(RDF.type, RDFS.Class):
            uri_str = str(cls_uri)
            if not any(c["uri"] == uri_str for c in classes):
                label = uri_str.split("/")[-1].split("#")[-1]
                for lbl in rdf_graph.objects(cls_uri, RDFS.label):
                    label = str(lbl)
                    break
                classes.append({"uri": uri_str, "name": label})

        properties = []
        for prop_type in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for prop_uri in rdf_graph.subjects(RDF.type, prop_type):
                label = str(prop_uri).split("/")[-1].split("#")[-1]
                domain = ""
                range_ = ""
                for lbl in rdf_graph.objects(prop_uri, RDFS.label):
                    label = str(lbl)
                    break
                for d in rdf_graph.objects(prop_uri, RDFS.domain):
                    domain = str(d).split("/")[-1].split("#")[-1]
                    break
                for r in rdf_graph.objects(prop_uri, RDFS.range):
                    range_ = str(r).split("/")[-1].split("#")[-1]
                    break
                properties.append({
                    "uri": str(prop_uri),
                    "name": label,
                    "domain": domain,
                    "range": range_,
                })

        return {"classes": classes, "properties": properties}

    # ------------------------------------------------------------------
    # Multi-Ontology Management
    # ------------------------------------------------------------------

    _META_NS = "http://keplai.io/ontology/metadata/"

    def list_ontologies(self) -> list[dict[str, Any]]:
        """List all imported ontologies with their metadata."""
        meta_graph = self._graph._settings.metadata_graph
        sparql = (
            f"SELECT ?id ?name ?source ?graphUri ?importDate ?classCount ?propCount "
            f"WHERE {{ "
            f"  GRAPH <{meta_graph}> {{ "
            f"    ?id <{self._META_NS}graphUri> ?graphUri . "
            f"    OPTIONAL {{ ?id <{self._META_NS}importName> ?name }} "
            f"    OPTIONAL {{ ?id <{self._META_NS}source> ?source }} "
            f"    OPTIONAL {{ ?id <{self._META_NS}importDate> ?importDate }} "
            f"    OPTIONAL {{ ?id <{self._META_NS}classCount> ?classCount }} "
            f"    OPTIONAL {{ ?id <{self._META_NS}propertyCount> ?propCount }} "
            f"  }} "
            f"}}"
        )
        rows = self._graph._execute_query(sparql)
        return [
            {
                "id": r.get("id", "").rsplit("/", 1)[-1],
                "name": r.get("name", ""),
                "source": r.get("source", ""),
                "graph_uri": r.get("graphUri", ""),
                "import_date": r.get("importDate", ""),
                "classes_count": int(r.get("classCount", 0)),
                "properties_count": int(r.get("propCount", 0)),
            }
            for r in rows
        ]

    def delete_ontology(self, ontology_id: str, graph_uri: str) -> None:
        """Remove an ontology's named graph and its metadata."""
        # Drop the ontology's named graph
        self._graph._execute_update(f"DROP SILENT GRAPH <{graph_uri}>")

        # Remove metadata
        meta_graph = self._graph._settings.metadata_graph
        meta_uri = f"{self._META_NS}{ontology_id}"
        self._graph._execute_update(
            f"DELETE WHERE {{ GRAPH <{meta_graph}> {{ <{meta_uri}> ?p ?o }} }}"
        )
        logger.info("Deleted ontology %s (graph: %s)", ontology_id, graph_uri)

    def _store_ontology_metadata(
        self,
        ontology_id: str,
        name: str,
        source: str,
        graph_uri: str,
        import_date: str,
        classes_count: int,
        properties_count: int,
    ) -> None:
        """Persist ontology metadata as RDF triples in the metadata graph."""
        meta_graph = self._graph._settings.metadata_graph
        meta_uri = f"{self._META_NS}{ontology_id}"
        sparql = (
            f"INSERT DATA {{ GRAPH <{meta_graph}> {{ "
            f"<{meta_uri}> <{self._META_NS}importName> \"{name}\" . "
            f"<{meta_uri}> <{self._META_NS}source> \"{source}\" . "
            f"<{meta_uri}> <{self._META_NS}graphUri> <{graph_uri}> . "
            f"<{meta_uri}> <{self._META_NS}importDate> \"{import_date}\" . "
            f"<{meta_uri}> <{self._META_NS}classCount> \"{classes_count}\" . "
            f"<{meta_uri}> <{self._META_NS}propertyCount> \"{properties_count}\" . "
            f"}} }}"
        )
        self._graph._execute_update(sparql)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    _DATATYPE_MAP: dict[str, URIRef] = {
        "string": XSD.string,
        "integer": XSD.integer,
        "int": XSD.integer,
        "float": XSD.float,
        "double": XSD.double,
        "boolean": XSD.boolean,
        "date": XSD.date,
        "datetime": XSD.dateTime,
    }

    def _is_datatype(self, value: str) -> bool:
        return value.lower() in self._DATATYPE_MAP

    def _resolve_range(self, value: str) -> URIRef:
        """Resolve range to XSD datatype URI or ontology class URI."""
        dt = self._DATATYPE_MAP.get(value.lower())
        if dt is not None:
            return dt
        return self._ont_ns[value]

    def _short_name(self, uri: str) -> str:
        """Extract the local name from a URI."""
        if not uri:
            return ""
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.split("/")[-1]
