from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EventSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    CONFLICT = "conflict"
    DIPLOMACY = "diplomacy"
    ECONOMY = "economy"
    POLITICS = "politics"
    HUMANITARIAN = "humanitarian"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    OTHER = "other"


class RawEvent(BaseModel):
    title: str
    url: str
    source: str
    published_at: str
    description: Optional[str] = ""
    raw_source: str


class AnalyzedEvent(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published_at: str
    description: Optional[str] = ""
    category: EventCategory
    severity: EventSeverity
    countries: List[str] = Field(default_factory=list)
    key_actors: List[str] = Field(default_factory=list)
    summary: str
    significance_score: float = Field(ge=0.0, le=1.0)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class TrendReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    period_hours: int = 24
    top_categories: List[dict]
    top_countries: List[dict]
    top_actors: List[dict]
    critical_events: List[AnalyzedEvent]
    high_events: List[AnalyzedEvent]
    total_events_analyzed: int
    executive_summary: str


class AgentQuery(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    max_results: int = Field(default=10, ge=1, le=50)
    categories: Optional[List[EventCategory]] = None
    severity_filter: Optional[EventSeverity] = None
    countries: Optional[List[str]] = None


class AgentResponse(BaseModel):
    query: str
    answer: str
    relevant_events: List[AnalyzedEvent]
    sources: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0)