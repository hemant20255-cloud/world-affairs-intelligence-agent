"""
Route definitions for the World Affairs Intelligence Agent API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import (
    get_event_store,
    get_intelligence_agent,
    get_news_collector,
)
from backend.api.schemas import (
    AgentQueryRequest,
    CollectResponse,
    EventListResponse,
    HealthResponse,
)
from backend.agent.intelligence_agent import IntelligenceAgent
from backend.models import AgentQuery, AgentResponse
from backend.scrapers.news_collector import NewsCollector
from backend.storage.event_store import EventStore

router = APIRouter()


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Returns API health status."""
    return HealthResponse()


# ── Events ─────────────────────────────────────────────────────────────────────

@router.get(
    "/events",
    response_model=EventListResponse,
    summary="List recent collected events",
    tags=["Events"],
)
def list_events(
    limit: int = Query(50, ge=1, le=200, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    event_store: EventStore = Depends(get_event_store),
) -> EventListResponse:
    """
    Returns a paginated list of the most recently collected geopolitical events.
    """
    events = event_store.get_recent(limit=limit, offset=offset)
    return EventListResponse(
        events=events,
        total=len(events),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/events/collect",
    response_model=CollectResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger news collection",
    tags=["Events"],
)
async def collect_events(
    news_collector: NewsCollector = Depends(get_news_collector),
    event_store: EventStore = Depends(get_event_store),
) -> CollectResponse:
    """
    Triggers the news collector to fetch new geopolitical events from
    configured sources (GDELT, NewsAPI, etc.) and persists them.
    """
    try:
        new_events = await news_collector.collect()
        saved = [event_store.save(event) for event in new_events]
        return CollectResponse(
            collected=len(saved),
            message=f"Successfully collected and stored {len(saved)} new events.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"News collection failed: {str(exc)}",
        ) from exc


# ── Agent ──────────────────────────────────────────────────────────────────────

@router.post(
    "/agent/query",
    response_model=AgentResponse,
    summary="Query the intelligence agent",
    tags=["Agent"],
)
async def agent_query(
    request: AgentQueryRequest,
    agent: IntelligenceAgent = Depends(get_intelligence_agent),
) -> AgentResponse:
    """
    Accepts a natural-language question about world affairs and returns an
    analytical response from the IntelligenceAgent, grounded in stored events.
    """
    try:
        agent_query_obj = AgentQuery(
            query=request.query,
            max_results=request.max_results,
            severity_filter=request.severity_filter,
            categories=request.categories,
            countries=request.countries,
        )
        return await agent.query(agent_query_obj)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent query failed: {str(exc)}",
        ) from exc
