"""
main.py — ProbabilityLens ORM FastAPI application entry point.

The app is served behind a reverse proxy at /probability-lens.
All routes are prefixed accordingly so the proxy path is not rewritten.

Start with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter

from .models import EvaluateRequest, EvaluateResponse
from .engine import evaluate

app = FastAPI(
    title="ProbabilityLens ORM",
    description=(
        "Deterministic financial decision engine (FSM). "
        "Evaluates EXIT / REDUCE / ADD / NONE via strict rule-based logic. "
        "decision_score is informational only and does not influence the decision."
    ),
    version="2.0.0",
    docs_url="/probability-lens/docs",
    redoc_url="/probability-lens/redoc",
    openapi_url="/probability-lens/openapi.json",
)

router = APIRouter(prefix="/probability-lens")


@router.get("/", summary="Root", tags=["meta"])
def root() -> dict:
    return {
        "service": "ProbabilityLens ORM",
        "version": "2.0.0",
        "docs": "/probability-lens/docs",
        "endpoints": {
            "POST /probability-lens/evaluate": "Run the FSM decision engine",
            "GET /probability-lens/sample": "Return a pre-computed sample evaluation",
        },
    }


@router.post("/evaluate", response_model=EvaluateResponse, summary="Evaluate state", tags=["engine"])
def evaluate_endpoint(req: EvaluateRequest) -> EvaluateResponse:
    """
    Accepts the eight FSM input fields and returns:

    - **state** — explicit named scores (edge_score, timing_score, confirmation_score, network_score, reflex_score, portfolio_headroom, health, max_prop)
    - **decision** — EXIT | REDUCE | ADD | NONE (priority: EXIT > REDUCE > ADD > NONE)
    - **decision_score** — informational fraction of ADD conditions met (0–1); does NOT affect decision
    - **trigger_gap** — list of ADD conditions currently not satisfied
    - **transition_status** — PREPARATION | NEAR | TRIGGERING | ACTIONABLE (based on decision_score)
    """
    return evaluate(req)


@router.get("/sample", response_model=EvaluateResponse, summary="Sample evaluation", tags=["engine"])
def sample_endpoint() -> EvaluateResponse:
    """
    Returns a deterministic sample evaluation demonstrating the ADD / ACTIONABLE path.
    All seven ADD conditions are met in this sample.
    """
    sample_req = EvaluateRequest(
        max_prop=75.0,
        edge_score=2,
        timing_score=1.0,
        confirmation_score=1.0,
        network_score=0.72,
        reflex_score=0.45,
        portfolio_headroom=10000.0,
        health=0.82,
    )
    return evaluate(sample_req)


app.include_router(router)
