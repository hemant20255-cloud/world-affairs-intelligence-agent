"""
backend/scrapers/news_collector.py — wraps the NewsCollector from backend.collector
and exposes an async collect() method that returns List[AnalyzedEvent].
"""
from __future__ import annotations

import uuid
from typing import List

from backend.collector import NewsCollector as _BaseCollector
from backend.models import AnalyzedEvent, EventCategory, EventSeverity


class NewsCollector:
    """Thin wrapper around the base NewsCollector that returns AnalyzedEvent objects."""

    def __init__(self) -> None:
        self._collector = _BaseCollector()

    async def collect(self) -> List[AnalyzedEvent]:
        """Fetch raw events from all configured sources and return as AnalyzedEvent list."""
        raw_events = await self._collector.collect_all()
        events: List[AnalyzedEvent] = []
        for raw in raw_events:
            title = raw.get("title", "").strip()
            if not title:
                continue
            events.append(
                AnalyzedEvent(
                    id=str(uuid.uuid4()),
                    title=title,
                    url=raw.get("url", ""),
                    source=raw.get("source", ""),
                    published_at=raw.get("published_at", ""),
                    description=raw.get("description", ""),
                    category=EventCategory.OTHER,
                    severity=EventSeverity.MEDIUM,
                    summary=raw.get("description") or title,
                    significance_score=0.5,
                )
            )
        return events
