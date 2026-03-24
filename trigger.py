"""
trigger.py — Compute trigger_gap and transition_status.

trigger_gap:
    Rule-based. Returns a list of ADD conditions that are not currently
    satisfied. An empty list means the engine is ready to ADD.
    trigger_gap does NOT use decision_score.

transition_status (PREPARATION → NEAR → TRIGGERING → ACTIONABLE):
    Informational readiness ladder derived from decision_score bands.
    This is the only place decision_score is used post-decision.

    PREPARATION  — decision_score < 0.40   (≤ 2 of 7 conditions met)
    NEAR         — 0.40 ≤ score < 0.57    (3 of 7 conditions met)
    TRIGGERING   — 0.57 ≤ score < 0.86    (4–5 of 7 conditions met)
    ACTIONABLE   — score ≥ 0.86            (6–7 of 7 conditions met)
"""

from .models import ComputedState, TriggerGap, TransitionStatus

_BAND_PREPARATION = 0.40
_BAND_NEAR = 0.57
_BAND_TRIGGERING = 0.86


def compute_trigger_gap(state: ComputedState) -> TriggerGap:
    """
    Evaluate each ADD condition and return the names of those not met.
    The returned list is deterministic and ordering is fixed.
    """
    missing: list[str] = []

    if state.edge_score != 2:
        missing.append(f"edge_score != 2 (current: {state.edge_score})")
    if state.timing_score != 1.0:
        missing.append(f"timing_score != 1.0 (current: {state.timing_score})")
    if state.confirmation_score != 1.0:
        missing.append(f"confirmation_score != 1.0 (current: {state.confirmation_score})")
    if state.network_score < 0.5:
        missing.append(f"network_score < 0.5 (current: {state.network_score})")
    if state.reflex_score >= 0.8:
        missing.append(f"reflex_score >= 0.8 (current: {state.reflex_score})")
    if state.portfolio_headroom <= 0:
        missing.append(f"portfolio_headroom <= 0 (current: {state.portfolio_headroom})")
    if state.health < 0.6:
        missing.append(f"health < 0.6 (current: {state.health})")

    return TriggerGap(missing_conditions=missing)


def compute_transition_status(decision_score: float) -> TransitionStatus:
    if decision_score >= _BAND_TRIGGERING:
        return "ACTIONABLE"
    if decision_score >= _BAND_NEAR:
        return "TRIGGERING"
    if decision_score >= _BAND_PREPARATION:
        return "NEAR"
    return "PREPARATION"
