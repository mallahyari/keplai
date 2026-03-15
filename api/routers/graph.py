from fastapi import APIRouter, Depends

from api.dependencies import get_graph
from api.schemas import TripleIn, TripleOut, TripleQuery, StatusResponse
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
