from fastapi import APIRouter, Depends

from api.dependencies import get_graph
from api.schemas import TripleIn, TripleOut, TripleQuery, StatusResponse, StatsResponse, ProvenanceResponse
from keplai.graph import KeplAI

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.post("/triples", status_code=201)
def add_triple(triple: TripleIn, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.add(triple.subject, triple.predicate, triple.object)
    return {"status": "created"}


@router.get("/triples", response_model=list[TripleOut])
def query_triples(
    subject: str | None = None,
    predicate: str | None = None,
    object: str | None = None,
    graph: KeplAI = Depends(get_graph),
) -> list[dict]:
    rows = graph.find(subject=subject, predicate=predicate, obj=object)
    return [
        {"subject": r["s"], "predicate": r["p"], "object": r["o"]}
        for r in rows
    ]


@router.delete("/triples")
def delete_triple(triple: TripleIn, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.delete(triple.subject, triple.predicate, triple.object)
    return {"status": "deleted"}


@router.get("/triples/all", response_model=list[TripleOut])
def get_all_triples(graph: KeplAI = Depends(get_graph)) -> list[dict]:
    rows = graph.get_all_triples()
    return [
        {"subject": r["s"], "predicate": r["p"], "object": r["o"]}
        for r in rows
    ]


@router.get("/status", response_model=StatusResponse)
def engine_status(graph: KeplAI = Depends(get_graph)) -> dict:
    return {
        "engine": "docker",
        "healthy": graph._engine.is_healthy(),
        "endpoint": graph._engine.endpoint,
        "dataset": graph._settings.fuseki_dataset,
    }


@router.get("/stats", response_model=StatsResponse)
def get_stats(graph: KeplAI = Depends(get_graph)):
    triples = graph.get_all_triples()
    ontologies = graph.ontology.list_ontologies()
    schema = graph.ontology.get_schema()
    entities = set()
    for t in triples:
        entities.add(t.get("s", t.get("subject", "")))
        entities.add(t.get("o", t.get("object", "")))
    return {
        "triple_count": len(triples),
        "entity_count": len(entities),
        "ontology_count": len(ontologies),
        "class_count": len(schema.get("classes", [])),
        "property_count": len(schema.get("properties", [])),
    }


@router.get("/triples/provenance", response_model=ProvenanceResponse | None)
def get_provenance(
    subject: str,
    predicate: str,
    obj: str,
    graph: KeplAI = Depends(get_graph),
):
    if graph.provenance is None:
        return None
    return graph.provenance.get(subject, predicate, obj)
