import json
from typing import Optional
import openai
from backend.models import AgentQuery, AgentResponse, EventCategory, EventSeverity
from backend.storage.event_store import EventStore


AGENT_SYSTEM_PROMPT = """You are an expert World Affairs Intelligence Agent.
You have access to a curated, continuously updated database of analyzed geopolitical events.
Your role is to:
1. Answer questions about current world affairs accurately and concisely.
2. Identify patterns, trends, and connections between events.
3. Provide analytical context and significance assessments.
4. Cite specific events from the database when relevant.

Always be factual, balanced, and analytical. When uncertain, say so explicitly."""


class IntelligenceAgent:
    """Conversational agent for querying world affairs intelligence."""

    def __init__(self, event_store: EventStore, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.event_store = event_store
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def query(self, agent_query: AgentQuery) -> AgentResponse:
        """Process a query and return an intelligent response."""
        # Retrieve relevant events
        relevant_events = self.event_store.search(
            agent_query.query,
            limit=agent_query.max_results,
        )

        # Apply optional filters
        if agent_query.severity_filter:
            relevant_events = [
                e for e in relevant_events if e.severity == agent_query.severity_filter
            ]
        if agent_query.categories:
            relevant_events = [
                e for e in relevant_events if e.category in agent_query.categories
            ]
        if agent_query.countries:
            lower_countries = [c.lower() for c in agent_query.countries]
            relevant_events = [
                e for e in relevant_events
                if any(c.lower() in lower_countries for c in e.countries)
            ]

        # Build context from relevant events
        context_parts = []
        for i, event in enumerate(relevant_events[:10], 1):
            context_parts.append(
                f"[Event {i}]
"
                f"Title: {event.title}\n"
                f"Category: {event.category.value} | Severity: {event.severity.value}\n"
                f"Countries: {', '.join(event.countries)}\n"
                f"Key Actors: {', '.join(event.key_actors)}\n"
                f"Summary: {event.summary}\n"
                f"Source: {event.source} | Published: {event.published_at}\n"
            )

        context = "\n---\n".join(context_parts) if context_parts else "No relevant events found in database."

        user_message = f"Query: {agent_query.query}\n\nRelevant Events from Database:\n{context}"

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )

        answer = response.choices[0].message.content or ""
        sources = list({e.url for e in relevant_events if e.url})
        confidence = min(1.0, len(relevant_events) / max(agent_query.max_results, 1))

        return AgentResponse(
            query=agent_query.query,
            answer=answer,
            relevant_events=relevant_events,
            sources=sources,
            confidence=confidence,
        )
