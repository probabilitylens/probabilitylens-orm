"""
scoring.py — Compute decision_score (0–1).

IMPORTANT: decision_score is INFORMATIONAL ONLY.
It does NOT influence the decision and is NOT read by decision.py.

The score measures the fraction of ADD conditions that are currently
satisfied. 1.0 means all ADD conditions are met; 0.0 means none are.

ADD conditions evaluated (7 total):
    1. edge_score == 2
    2. timing_score == 1.0
    3. confirmation_score == 1.0
    4. network_score >= 0.5
    5. reflex_score < 0.8
    6. portfolio_headroom > 0
    7. health >= 0.6
"""

from .models import ComputedState

_ADD_CONDITIONS = 7


def compute_decision_score(state: ComputedState) -> float:
    met = sum([
        state.edge_score == 2,
        state.timing_score == 1.0,
        state.confirmation_score == 1.0,
        state.network_score >= 0.5,
        state.reflex_score < 0.8,
        state.portfolio_headroom > 0,
        state.health >= 0.6,
    ])
    return round(met / _ADD_CONDITIONS, 6)
