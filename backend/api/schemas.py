"""
API-layer Pydantic schemas for request bodies and response envelopes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.models import (
    AgentResponse,
    AnalyzedEvent,
    EventCategory,
    EventSeverity,
)


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Events ─────────────────────────────────────────────────────────────────────

class EventListResponse(BaseModel):
    events: List[AnalyzedEvent]
    total: int
    limit: int
    offset: int


# ── Agent Query ────────────────────────────────────────────────────────────────

class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000, description="Natural-language question about world affairs")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of events to retrieve for context")
    severity_filter: Optional[EventSeverity] = Field(None, description="Filter events by severity level")
    categories: Optional[List[EventCategory]] = Field(None, description="Filter events by category")
    countries: Optional[List[str]] = Field(None, description="Filter events by country name")


# ── Collect ────────────────────────────────────────────────────────────────────

class CollectResponse(BaseModel):
    collected: int = Field(..., description="Number of new events collected and stored")
    message: str
