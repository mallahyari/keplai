from fastapi import APIRouter, Depends

from api.dependencies import get_graph
from api.schemas import (
    ExtractionRequest,
    ExtractedTripleOut,
    PreviewTripleOut,
    EntityOut,
    SimilarEntityOut,
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


@router.get("/entities/{name}/similar", response_model=list[SimilarEntityOut])
async def similar_entities(name: str, graph: KeplAI = Depends(get_graph)):
    return await graph.disambiguator.get_similar(name)
