from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import set_graph
from api.routers import graph as graph_router
from api.routers import ontology as ontology_router
from api.routers import extraction as extraction_router
from keplai import KeplAI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: provision the graph engine
    kg = KeplAI.start()
    set_graph(kg)
    yield
    # Shutdown: stop the engine (data persists)
    kg.stop()


app = FastAPI(title="KeplAI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router.router)
app.include_router(ontology_router.router)
app.include_router(extraction_router.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
