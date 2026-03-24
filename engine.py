"""
engine.py — Orchestrates all modules into a single evaluate() call.

Flow:
    1. state    — validate and surface explicit input fields
    2. decision — FSM rule evaluation (EXIT > REDUCE > ADD > NONE)
    3. score    — informational fraction of ADD conditions met (NOT used by decision)
    4. trigger  — list of unmet ADD conditions
    5. status   — readiness band derived from score
"""

from .models import EvaluateRequest, EvaluateResponse
from .state import compute_state
from .decision import compute_decision
from .scoring import compute_decision_score
from .trigger import compute_trigger_gap, compute_transition_status


def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    state = compute_state(req)
    decision = compute_decision(state)
    decision_score = compute_decision_score(state)
    trigger_gap = compute_trigger_gap(state)
    transition_status = compute_transition_status(decision_score)

    return EvaluateResponse(
        state=state,
        decision=decision,
        decision_score=decision_score,
        trigger_gap=trigger_gap,
        transition_status=transition_status,
    )
