from fastapi import APIRouter, Depends

from api.dependencies import get_graph
from api.schemas import (
    ExtractionRequest,
    ExtractedTripleOut,
    PreviewTripleOut,
    EntityOut,
    SimilarEntityOut,
    EntityContextResponse,
    TripleOut,
)
from keplai.graph import KeplAI

router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/extract", response_model=list[ExtractedTripleOut])
async def extract_and_store(req: ExtractionRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.extract_and_store(req.text, mode=req.mode)


@router.post("/extract/preview", response_model=list[PreviewTripleOut])
async def extract_preview(req: ExtractionRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.extract_preview(req.text, mode=req.mode)


@router.get("/entities", response_model=list[EntityOut])
def list_entities(graph: KeplAI = Depends(get_graph)):
    return graph.disambiguator.get_all_entities()


@router.get("/entities/{name:path}/similar", response_model=list[SimilarEntityOut])
async def similar_entities(name: str, graph: KeplAI = Depends(get_graph)):
    return await graph.disambiguator.get_similar(name)


@router.get("/entities/{name:path}/context", response_model=EntityContextResponse)
async def entity_context(name: str, graph: KeplAI = Depends(get_graph)):
    # Triples where entity is subject or object
    # Wrap in try/except: entity names that are literals (contain spaces, etc.)
    # produce invalid URIs in _to_entity_uri, causing rdflib/SPARQL errors.
    try:
        subj_rows = graph.find(subject=name)
    except Exception:
        subj_rows = []
    try:
        obj_rows = graph.find(obj=name)
    except Exception:
        obj_rows = []

    triples_as_subject = [
        {"subject": r["s"], "predicate": r["p"], "object": r["o"]}
        for r in subj_rows
    ]
    triples_as_object = [
        {"subject": r["s"], "predicate": r["p"], "object": r["o"]}
        for r in obj_rows
    ]

    # Entity type detection — look for rdf:type predicates, validate against schema
    entity_type = None
    for t in triples_as_subject:
        pred = t["predicate"]
        if pred == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" or pred.endswith("#type") or pred.endswith("/type"):
            obj_val = t["object"]
            # Extract local name from URI
            if "#" in obj_val:
                local_name = obj_val.split("#")[-1]
            elif "/" in obj_val:
                local_name = obj_val.split("/")[-1]
            else:
                local_name = obj_val
            # Validate against schema classes
            try:
                schema = graph.ontology.get_schema()
                class_names = {c["name"] for c in schema.get("classes", [])}
                if local_name in class_names:
                    entity_type = local_name
                else:
                    entity_type = local_name  # Use even if not in schema
            except Exception:
                entity_type = local_name
            break

    # Similar entities
    try:
        result = graph.disambiguator.get_similar(name)
        import asyncio
        if asyncio.iscoroutine(result):
            similar = await result
        else:
            similar = result
    except Exception:
        similar = []

    return {
        "entity": name,
        "triples_as_subject": triples_as_subject,
        "triples_as_object": triples_as_object,
        "entity_type": entity_type,
        "similar_entities": similar,
    }
