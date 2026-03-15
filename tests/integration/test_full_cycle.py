"""Integration test: start engine → add → find → delete → verify → stop.

Requires Docker to be running. Skip with: pytest -m 'not integration'
"""

import pytest

from keplai import KeplAI


@pytest.fixture(scope="module")
def graph():
    """Start a KeplAI instance for the test module, stop when done."""
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
def test_engine_is_healthy(graph: KeplAI):
    assert graph._engine.is_healthy()


@pytest.mark.integration
def test_add_find_delete_cycle(graph: KeplAI):
    # Add a triple
    graph.add("Mehdi", "founded", "BrandPulse")

    # Find it
    results = graph.find(subject="Mehdi", predicate="founded")
    assert len(results) >= 1
    match = [r for r in results if "BrandPulse" in r["o"]]
    assert len(match) == 1

    # Delete it
    graph.delete("Mehdi", "founded", "BrandPulse")

    # Verify gone
    results = graph.find(subject="Mehdi", predicate="founded")
    match = [r for r in results if "BrandPulse" in r["o"]]
    assert len(match) == 0


@pytest.mark.integration
def test_get_all_triples(graph: KeplAI):
    graph.add("Alice", "knows", "Bob")
    all_triples = graph.get_all_triples()
    assert any("Alice" in r["s"] for r in all_triples)

    # Cleanup
    graph.delete("Alice", "knows", "Bob")


@pytest.mark.integration
def test_literal_object(graph: KeplAI):
    graph.add("BrandPulse", "foundedYear", 2023)
    results = graph.find(subject="BrandPulse", predicate="foundedYear")
    assert len(results) >= 1
    assert any("2023" in r["o"] for r in results)

    graph.delete("BrandPulse", "foundedYear", 2023)
