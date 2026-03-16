from fastapi import APIRouter, Depends

from api.dependencies import get_graph
from api.schemas import (
    AskRequest,
    SparqlRequest,
    QueryResult,
    QueryResultWithExplanation,
)
from keplai.graph import KeplAI

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/ask", response_model=QueryResult)
async def ask_question(req: AskRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.ask(req.question)


@router.post("/ask/explain", response_model=QueryResultWithExplanation)
async def ask_with_explanation(req: AskRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.ask_with_explanation(req.question)


@router.post("/sparql", response_model=QueryResult)
def execute_sparql(req: SparqlRequest, graph: KeplAI = Depends(get_graph)):
    results = graph.nlq.execute_sparql(req.sparql)
    return {"results": results, "sparql": req.sparql}
