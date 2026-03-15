"""Unit tests for SPARQL query generation."""

from unittest.mock import MagicMock, patch

from keplai.config import KeplAISettings
from keplai.graph import KeplAI


def _make_graph() -> KeplAI:
    settings = KeplAISettings()
    engine = MagicMock()
    engine.update_url = "http://localhost:3030/keplai/update"
    engine.sparql_url = "http://localhost:3030/keplai/sparql"
    return KeplAI(engine=engine, settings=settings)


class TestAddGeneratesSPARQL:
    @patch("keplai.graph.SPARQLWrapper")
    def test_add_generates_insert_data(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.add("Mehdi", "founded", "BrandPulse")

        # Verify SPARQLWrapper was called with the update URL
        mock_wrapper_cls.assert_called_with(g._engine.update_url)

        # Verify the SPARQL query contains INSERT DATA
        call_args = mock_instance.setQuery.call_args[0][0]
        assert "INSERT DATA" in call_args
        assert "keplai.io/entity/Mehdi" in call_args
        assert "keplai.io/ontology/founded" in call_args
        assert "keplai.io/entity/BrandPulse" in call_args


class TestDeleteGeneratesSPARQL:
    @patch("keplai.graph.SPARQLWrapper")
    def test_delete_generates_delete_data(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.delete("Mehdi", "founded", "BrandPulse")

        call_args = mock_instance.setQuery.call_args[0][0]
        assert "DELETE DATA" in call_args
        assert "keplai.io/entity/Mehdi" in call_args


class TestAddLiteralObject:
    @patch("keplai.graph.SPARQLWrapper")
    def test_add_integer_object(self, mock_wrapper_cls):
        mock_instance = MagicMock()
        mock_wrapper_cls.return_value = mock_instance

        g = _make_graph()
        g.add("BrandPulse", "foundedYear", 2023)

        call_args = mock_instance.setQuery.call_args[0][0]
        assert "INSERT DATA" in call_args
        assert "2023" in call_args
