"""Unit tests for namespace mapping (string → URI, literal detection)."""

from unittest.mock import MagicMock

from rdflib import URIRef, Literal, XSD

from keplai.config import KeplAISettings
from keplai.graph import KeplAI


def _make_graph() -> KeplAI:
    """Create a KeplAI instance with a mock engine (no Docker needed)."""
    settings = KeplAISettings()
    engine = MagicMock()
    return KeplAI(engine=engine, settings=settings)


class TestEntityURI:
    def test_plain_string_becomes_entity_uri(self):
        g = _make_graph()
        uri = g._to_entity_uri("Mehdi")
        assert uri == URIRef("http://keplai.io/entity/Mehdi")

    def test_full_uri_passed_through(self):
        g = _make_graph()
        uri = g._to_entity_uri("http://example.org/Foo")
        assert uri == URIRef("http://example.org/Foo")

    def test_https_uri_passed_through(self):
        g = _make_graph()
        uri = g._to_entity_uri("https://example.org/Bar")
        assert uri == URIRef("https://example.org/Bar")


class TestPredicateURI:
    def test_plain_string_becomes_ontology_uri(self):
        g = _make_graph()
        uri = g._to_predicate_uri("founded")
        assert uri == URIRef("http://keplai.io/ontology/founded")

    def test_full_uri_passed_through(self):
        g = _make_graph()
        uri = g._to_predicate_uri("http://schema.org/name")
        assert uri == URIRef("http://schema.org/name")


class TestObjectMapping:
    def test_int_becomes_typed_literal(self):
        g = _make_graph()
        obj = g._to_object(2023)
        assert isinstance(obj, Literal)
        assert obj.datatype == XSD.integer

    def test_float_becomes_typed_literal(self):
        g = _make_graph()
        obj = g._to_object(3.14)
        assert isinstance(obj, Literal)
        assert obj.datatype == XSD.double

    def test_capitalized_string_becomes_entity_uri(self):
        g = _make_graph()
        obj = g._to_object("BrandPulse")
        assert isinstance(obj, URIRef)
        assert obj == URIRef("http://keplai.io/entity/BrandPulse")

    def test_lowercase_string_becomes_literal(self):
        g = _make_graph()
        obj = g._to_object("some text value")
        assert isinstance(obj, Literal)
        assert str(obj) == "some text value"

    def test_full_uri_string_becomes_uri(self):
        g = _make_graph()
        obj = g._to_object("http://example.org/Thing")
        assert isinstance(obj, URIRef)

    def test_empty_string_becomes_literal(self):
        g = _make_graph()
        obj = g._to_object("")
        assert isinstance(obj, Literal)
