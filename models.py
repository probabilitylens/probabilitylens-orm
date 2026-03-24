from pydantic import BaseModel, Field
from typing import Literal


class EvaluateRequest(BaseModel):
    max_prop: float = Field(..., description="Maximum portfolio proportion (%). EXIT triggered if < 50.")
    edge_score: int = Field(..., ge=0, le=2, description="Discrete edge score: 0, 1, or 2. ADD requires == 2.")
    timing_score: float = Field(..., ge=0.0, le=1.0, description="Timing alignment (0–1). ADD requires == 1.0.")
    confirmation_score: float = Field(..., ge=0.0, le=1.0, description="Confirmation signal (0–1). ADD requires == 1.0.")
    network_score: float = Field(..., ge=0.0, le=1.0, description="Network alignment (0–1). ADD requires >= 0.5.")
    reflex_score: float = Field(..., ge=0.0, le=1.0, description="Reflexivity/momentum (0–1). REDUCE if >= 0.8; ADD requires < 0.8.")
    portfolio_headroom: float = Field(..., description="Available portfolio capacity. ADD requires > 0.")
    health: float = Field(..., ge=0.0, le=1.0, description="Position health (0–1). REDUCE if < 0.6; ADD requires >= 0.6.")


class ComputedState(BaseModel):
    edge_score: int
    timing_score: float
    confirmation_score: float
    network_score: float
    reflex_score: float
    portfolio_headroom: float
    health: float
    max_prop: float


DecisionType = Literal["ADD", "REDUCE", "EXIT", "NONE"]
TransitionStatus = Literal["PREPARATION", "NEAR", "TRIGGERING", "ACTIONABLE"]


class TriggerGap(BaseModel):
    missing_conditions: list[str] = Field(
        description="ADD conditions not currently satisfied. Empty when decision is ADD."
    )


class EvaluateResponse(BaseModel):
    state: ComputedState
    decision: DecisionType
    decision_score: float = Field(..., ge=0.0, le=1.0, description="Informational only — fraction of ADD conditions met.")
    trigger_gap: TriggerGap
    transition_status: TransitionStatus
