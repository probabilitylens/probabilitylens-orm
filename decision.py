"""
decision.py — Strict FSM decision engine.

Rules are purely boolean condition checks. No composite scores,
no weighted thresholds. decision_score is NOT consulted here.

Priority order:
    EXIT   > REDUCE > ADD > NONE

EXIT:
    max_prop < 50

REDUCE:
    reflex_score >= 0.8  OR  health < 0.6

ADD (all conditions must hold):
    edge_score == 2
    AND timing_score == 1.0
    AND confirmation_score == 1.0
    AND network_score >= 0.5
    AND reflex_score < 0.8
    AND portfolio_headroom > 0
    AND health >= 0.6

NONE:
    default (no rule triggered)
"""

from .models import ComputedState, DecisionType


def _exit_triggered(state: ComputedState) -> bool:
    return state.max_prop < 50


def _reduce_triggered(state: ComputedState) -> bool:
    return state.reflex_score >= 0.8 or state.health < 0.6


def _add_triggered(state: ComputedState) -> bool:
    return (
        state.edge_score == 2
        and state.timing_score == 1.0
        and state.confirmation_score == 1.0
        and state.network_score >= 0.5
        and state.reflex_score < 0.8
        and state.portfolio_headroom > 0
        and state.health >= 0.6
    )


def compute_decision(state: ComputedState) -> DecisionType:
    if _exit_triggered(state):
        return "EXIT"
    if _reduce_triggered(state):
        return "REDUCE"
    if _add_triggered(state):
        return "ADD"
    return "NONE"
