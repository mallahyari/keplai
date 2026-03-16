import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File

from api.dependencies import get_graph
from api.schemas import (
    ClassIn, ClassOut, PropertyIn, PropertyOut, SchemaOut,
    ImportUrlRequest, ImportResponse,
)
from keplai.graph import KeplAI

router = APIRouter(prefix="/api/ontology", tags=["ontology"])


@router.post("/classes", status_code=201)
def define_class(body: ClassIn, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.ontology.define_class(body.name)
    return {"status": "created"}


@router.get("/classes", response_model=list[ClassOut])
def list_classes(graph: KeplAI = Depends(get_graph)) -> list[dict]:
    return graph.ontology.get_classes()


@router.delete("/classes/{name}")
def remove_class(name: str, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.ontology.remove_class(name)
    return {"status": "deleted"}


@router.post("/properties", status_code=201)
def define_property(body: PropertyIn, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.ontology.define_property(body.name, body.domain, body.range)
    return {"status": "created"}


@router.get("/properties", response_model=list[PropertyOut])
def list_properties(graph: KeplAI = Depends(get_graph)) -> list[dict]:
    return graph.ontology.get_properties()


@router.delete("/properties/{name}")
def remove_property(name: str, graph: KeplAI = Depends(get_graph)) -> dict:
    graph.ontology.remove_property(name)
    return {"status": "deleted"}


@router.get("/schema", response_model=SchemaOut)
def get_schema(graph: KeplAI = Depends(get_graph)) -> dict:
    return graph.ontology.get_schema()


@router.post("/upload", response_model=ImportResponse)
async def upload_ontology(
    file: UploadFile = File(...),
    graph: KeplAI = Depends(get_graph),
) -> dict:
    """Upload an RDF ontology file and import into the graph."""
    suffix = Path(file.filename or "upload.rdf").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = graph.ontology.load_rdf(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


@router.post("/import-url", response_model=ImportResponse)
def import_ontology_url(
    body: ImportUrlRequest,
    graph: KeplAI = Depends(get_graph),
) -> dict:
    """Import a remote ontology by URL."""
    return graph.ontology.load_url(body.url)
