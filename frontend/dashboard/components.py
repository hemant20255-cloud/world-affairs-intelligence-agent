"""Reusable UI helper components for the World Affairs Intelligence dashboard."""

from collections import Counter

import pandas as pd
import streamlit as st


def render_event_card(event: dict) -> None:
    """Render a single event as a styled container with metric/info elements."""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{event.get('title', 'No title')}**")
            if event.get("summary"):
                st.caption(event["summary"])
        with col2:
            st.markdown(f"`{event.get('category', 'N/A')}`")
        with col3:
            severity = event.get("severity", "N/A")
            colour = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
                severity.lower() if severity else "", "⚪"
            )
            st.markdown(f"{colour} {severity}")
        st.caption(
            f"📍 {', '.join(event.get('countries', [])) or 'Unknown region'} | "
            f"🗓 {event.get('published_at', 'Unknown date')} | "
            f"🔗 {event.get('source', 'Unknown source')}"
        )
        st.divider()


def render_region_section(region: str, events: list) -> None:
    """Filter events for *region* and display a concise summary section."""
    region_events = [
        e for e in events
        if any(region.lower() in c.lower() for c in e.get("countries", []))
        or region.lower() in e.get("title", "").lower()
        or region.lower() in (e.get("summary") or "").lower()
    ]
    with st.expander(f"🌍 {region} ({len(region_events)} events)", expanded=False):
        if not region_events:
            st.info(f"No recent events found for {region}.")
            return
        for event in region_events[:5]:
            render_event_card(event)
        if len(region_events) > 5:
            st.caption(f"…and {len(region_events) - 5} more events.")


def render_category_chart(events: list) -> None:
    """Build and render a bar chart of event counts per category."""
    if not events:
        st.info("No event data available for chart.")
        return
    counts = Counter(e.get("category", "other") for e in events)
    categories = ["conflict", "diplomacy", "economy", "politics", "humanitarian", "environment", "security", "other"]
    chart_data = {cat: counts.get(cat, 0) for cat in categories if counts.get(cat, 0) > 0}
    if not chart_data:
        st.info("No categorised events to display.")
        return
    df = pd.DataFrame({"Category": list(chart_data.keys()), "Count": list(chart_data.values())})
    df = df.set_index("Category")
    st.bar_chart(df)
