"""
FastAPI dependency injection for database sessions, EventStore,
IntelligenceAgent, and NewsCollector.
"""
import os
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.db.config import SessionLocal
from backend.storage.event_store import EventStore
from backend.agent.intelligence_agent import IntelligenceAgent
from backend.scrapers.news_collector import NewsCollector


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy database session, closing it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_event_store(db: Session = Depends(get_db)) -> EventStore:
    return EventStore(db)


def get_intelligence_agent(
    event_store: EventStore = Depends(get_event_store),
) -> IntelligenceAgent:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return IntelligenceAgent(event_store=event_store, model=model, api_key=api_key)


def get_news_collector() -> NewsCollector:
    return NewsCollector()
