from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.dependencies import set_graph
from api.routers import graph as graph_router
from api.routers import ontology as ontology_router
from api.routers import extraction as extraction_router
from api.routers import query as query_router
from keplai import KeplAI
from keplai.exceptions import (
    KeplAIError,
    EngineError,
    ExtractionError,
    QueryError,
    DisambiguationError,
    OntologyImportError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: provision the graph engine
    kg = KeplAI.start()
    set_graph(kg)
    yield
    # Shutdown: stop the engine (data persists)
    kg.stop()


app = FastAPI(
    title="KeplAI API",
    version="0.1.0",
    description="SDK-first knowledge graph platform powered by Apache Jena Fuseki",
    lifespan=lifespan,
)


# -- Consistent error responses --

_ERROR_STATUS = {
    EngineError: 503,
    ExtractionError: 502,
    QueryError: 400,
    DisambiguationError: 502,
    OntologyImportError: 400,
}


@app.exception_handler(KeplAIError)
async def keplai_error_handler(request: Request, exc: KeplAIError):
    status = _ERROR_STATUS.get(type(exc), 500)
    return JSONResponse(
        status_code=status,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router.router)
app.include_router(ontology_router.router)
app.include_router(extraction_router.router)
app.include_router(query_router.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
