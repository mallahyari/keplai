from fastapi import APIRouter, Depends, Request

from api.dependencies import get_graph
from api.main import limiter
from api.schemas import (
    AskRequest,
    SparqlRequest,
    QueryResult,
    QueryResultWithExplanation,
)
from keplai.graph import KeplAI

router = APIRouter(prefix="/api/query", tags=["query"])


@limiter.limit("50/hour")
@router.post("/ask", response_model=QueryResult)
async def ask_question(request: Request, req: AskRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.ask(req.question)


@limiter.limit("50/hour")
@router.post("/ask/explain", response_model=QueryResultWithExplanation)
async def ask_with_explanation(request: Request, req: AskRequest, graph: KeplAI = Depends(get_graph)):
    return await graph.ask_with_explanation(req.question)


@limiter.limit("50/hour")
@router.post("/sparql", response_model=QueryResult)
def execute_sparql(request: Request, req: SparqlRequest, graph: KeplAI = Depends(get_graph)):
    results = graph.nlq.execute_sparql(req.sparql)
    return {"results": results, "sparql": req.sparql}
