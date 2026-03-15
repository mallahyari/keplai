"""Integration test: define ontology → verify in Fuseki → retrieve via API.

Requires Docker to be running. Skip with: pytest -m 'not integration'
"""

import pytest

from keplai import KeplAI


@pytest.fixture(scope="module")
def graph():
    g = KeplAI.start(
        engine="docker",
        reasoner="OWL",
        fuseki_container_name="keplai-test-fuseki",
        fuseki_port=3031,
        fuseki_dataset="keplai_test",
    )
    yield g
    g.stop()


@pytest.mark.integration
def test_define_and_list_classes(graph: KeplAI):
    graph.ontology.define_class("Person")
    graph.ontology.define_class("Company")

    classes = graph.ontology.get_classes()
    names = [c["name"] for c in classes]
    assert "Person" in names
    assert "Company" in names

    # Cleanup
    graph.ontology.remove_class("Person")
    graph.ontology.remove_class("Company")


@pytest.mark.integration
def test_define_and_list_properties(graph: KeplAI):
    graph.ontology.define_class("Person")
    graph.ontology.define_class("Company")
    graph.ontology.define_property("founded", domain="Person", range="Company")

    props = graph.ontology.get_properties()
    assert any(p["name"] == "founded" for p in props)
    founded = next(p for p in props if p["name"] == "founded")
    assert founded["domain"] == "Person"
    assert founded["range"] == "Company"

    # Cleanup
    graph.ontology.remove_property("founded")
    graph.ontology.remove_class("Person")
    graph.ontology.remove_class("Company")


@pytest.mark.integration
def test_get_schema(graph: KeplAI):
    graph.ontology.define_class("Event")
    graph.ontology.define_property("date", domain="Event", range="date")

    schema = graph.ontology.get_schema()
    assert any(c["name"] == "Event" for c in schema["classes"])
    assert any(p["name"] == "date" for p in schema["properties"])

    # Cleanup
    graph.ontology.remove_property("date")
    graph.ontology.remove_class("Event")


@pytest.mark.integration
def test_remove_class(graph: KeplAI):
    graph.ontology.define_class("Temp")
    classes = graph.ontology.get_classes()
    assert any(c["name"] == "Temp" for c in classes)

    graph.ontology.remove_class("Temp")
    classes = graph.ontology.get_classes()
    assert not any(c["name"] == "Temp" for c in classes)
