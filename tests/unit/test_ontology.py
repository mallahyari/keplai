"""Unit tests for OWL triple generation and property validation."""

from unittest.mock import MagicMock, patch, call

from rdflib import RDF, RDFS, OWL, XSD

from keplai.config import KeplAISettings
from keplai.graph import KeplAI


def _make_graph() -> KeplAI:
    settings = KeplAISettings()
    engine = MagicMock()
    engine.update_url = "http://localhost:3030/keplai/update"
    engine.sparql_url = "http://localhost:3030/keplai/sparql"
    return KeplAI(engine=engine, settings=settings)


class TestDefineClass:
    @patch("keplai.graph.SPARQLWrapper")
    def test_define_class_generates_owl_class_triple(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.define_class("Person")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert "INSERT DATA" in sparql
        assert "keplai.io/ontology/Person" in sparql
        assert str(OWL.Class) in sparql

    @patch("keplai.graph.SPARQLWrapper")
    def test_define_class_includes_label(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.define_class("Company")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert '"Company"' in sparql
        assert str(RDFS.label) in sparql


class TestDefineProperty:
    @patch("keplai.graph.SPARQLWrapper")
    def test_object_property_with_class_range(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.define_property("founded", domain="Person", range="Company")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert str(OWL.ObjectProperty) in sparql
        assert "keplai.io/ontology/founded" in sparql
        assert "keplai.io/ontology/Person" in sparql
        assert "keplai.io/ontology/Company" in sparql

    @patch("keplai.graph.SPARQLWrapper")
    def test_datatype_property_with_string_range(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.define_property("name", domain="Person", range="string")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert str(OWL.DatatypeProperty) in sparql
        assert str(XSD.string) in sparql

    @patch("keplai.graph.SPARQLWrapper")
    def test_datatype_property_with_integer_range(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.define_property("age", domain="Person", range="integer")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert str(OWL.DatatypeProperty) in sparql
        assert str(XSD.integer) in sparql


class TestRemoveClass:
    @patch("keplai.graph.SPARQLWrapper")
    def test_remove_class_generates_delete(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.ontology.remove_class("Person")

        sparql = mock_instance.setQuery.call_args[0][0]
        assert "DELETE" in sparql
        assert "keplai.io/ontology/Person" in sparql


class TestDatatypeDetection:
    def test_known_datatypes(self):
        g = _make_graph()
        ont = g.ontology
        for dt in ("string", "integer", "int", "float", "double", "boolean", "date", "datetime"):
            assert ont._is_datatype(dt), f"{dt} should be recognized as datatype"

    def test_class_names_are_not_datatypes(self):
        g = _make_graph()
        ont = g.ontology
        for name in ("Person", "Company", "Event"):
            assert not ont._is_datatype(name), f"{name} should not be a datatype"


class TestShortName:
    def test_slash_uri(self):
        g = _make_graph()
        assert g.ontology._short_name("http://keplai.io/ontology/Person") == "Person"

    def test_hash_uri(self):
        g = _make_graph()
        assert g.ontology._short_name("http://www.w3.org/2001/XMLSchema#string") == "string"

    def test_empty_string(self):
        g = _make_graph()
        assert g.ontology._short_name("") == ""
