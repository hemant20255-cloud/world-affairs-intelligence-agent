"""
EventStore: persist and search AnalyzedEvent objects.
"""
from __future__ import annotations

from typing import List, Optional

from backend.models import AnalyzedEvent


class EventStore:
    """In-process store for AnalyzedEvent objects backed by an optional DB session."""

    def __init__(self, db=None) -> None:
        self.db = db
        self._store: List[AnalyzedEvent] = []

    def save(self, event: AnalyzedEvent) -> AnalyzedEvent:
        """Persist a single event and return it."""
        self._store.append(event)
        return event

    def search(self, query: str, limit: int = 10) -> List[AnalyzedEvent]:
        """Return events whose title or summary contain the query string."""
        query_lower = query.lower()
        results = [
            e for e in self._store
            if query_lower in (e.title or "").lower() or query_lower in (e.summary or "").lower()
        ]
        return results[:limit]

    def get_recent(self, limit: int = 50, offset: int = 0) -> List[AnalyzedEvent]:
        """Return events ordered by analysis time, newest first."""
        sorted_events = sorted(self._store, key=lambda e: e.analyzed_at, reverse=True)
        return sorted_events[offset : offset + limit]
