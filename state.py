"""
state.py — Validate and surface the explicit input dimensions.

No composite computation. Each field is returned as-is after
type validation by Pydantic. This module exists to keep the
engine orchestration clean and extensible.
"""

from .models import EvaluateRequest, ComputedState


def compute_state(req: EvaluateRequest) -> ComputedState:
    return ComputedState(
        edge_score=req.edge_score,
        timing_score=round(req.timing_score, 6),
        confirmation_score=round(req.confirmation_score, 6),
        network_score=round(req.network_score, 6),
        reflex_score=round(req.reflex_score, 6),
        portfolio_headroom=req.portfolio_headroom,
        health=round(req.health, 6),
        max_prop=req.max_prop,
    )
