"""
Pydantic data models for the Adaptive SaaS Onboarding Framework.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Event(BaseModel):
    """Raw user action event."""
    userId: str
    action: str
    featureId: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserState(BaseModel):
    """Computed user state at a point in time."""
    userId: str
    visitedNodes: List[str]
    currentNode: Optional[str]
    coverageScore: float
    stage: str


class MetricsSnapshot(BaseModel):
    """Snapshot of user metrics logged at state computation time."""
    userId: str
    stage: str
    coverageScore: float
    taskSuccessRate: float
    timeToActivation: Optional[float]  # seconds, None if not yet activated
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserStateResponse(BaseModel):
    """Response model for GET /user/{userId}/state."""
    state: UserState
    metricsHistory: List[MetricsSnapshot]
