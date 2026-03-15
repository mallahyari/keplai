from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from rdflib import URIRef, Namespace, RDF, RDFS, OWL, XSD

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

    def get_classes(self) -> list[dict[str, str]]:
        """List all defined OWL classes."""
        sparql = (
            f"SELECT ?cls ?label WHERE {{ "
            f"?cls {RDF.type.n3()} {OWL.Class.n3()} . "
            f"OPTIONAL {{ ?cls {RDFS.label.n3()} ?label }} "
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

    def get_properties(self) -> list[dict[str, str]]:
        """List all defined properties with domain and range."""
        sparql = (
            f"SELECT ?prop ?label ?domain ?range WHERE {{ "
            f"{{ ?prop {RDF.type.n3()} {OWL.ObjectProperty.n3()} }} "
            f"UNION "
            f"{{ ?prop {RDF.type.n3()} {OWL.DatatypeProperty.n3()} }} "
            f"OPTIONAL {{ ?prop {RDFS.label.n3()} ?label }} "
            f"OPTIONAL {{ ?prop {RDFS.domain.n3()} ?domain }} "
            f"OPTIONAL {{ ?prop {RDFS.range.n3()} ?range }} "
            f"}}"
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

    def get_schema(self) -> dict[str, Any]:
        """Return the full ontology as a structured dict."""
        return {
            "classes": self.get_classes(),
            "properties": self.get_properties(),
        }

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
