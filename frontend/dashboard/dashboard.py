"""World Affairs Intelligence – Streamlit Dashboard."""

import os

import pandas as pd
import requests
import streamlit as st

from components import render_category_chart, render_event_card, render_region_section

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

REGIONS = ["Americas", "Europe", "Middle East", "Asia", "Africa"]

st.set_page_config(
    page_title="World Affairs Intelligence",
    page_icon="🌐",
    layout="wide",
)

st.title("🌐 World Affairs Intelligence Dashboard")
st.caption(f"Backend: `{BACKEND_URL}`")

# ---------------------------------------------------------------------------
# Helper: fetch events (cached for the session so multiple widgets share data)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def fetch_events() -> list:
    """Fetch analysed events from the backend."""
    response = requests.get(f"{BACKEND_URL}/events", timeout=10)
    response.raise_for_status()
    data = response.json()
    # The API may return a list directly or wrapped in a key
    if isinstance(data, list):
        return data
    return data.get("events", data.get("items", []))


# ---------------------------------------------------------------------------
# 1. Global Intelligence Brief
# ---------------------------------------------------------------------------
st.header("📋 Global Intelligence Brief")

try:
    brief_response = requests.post(
        f"{BACKEND_URL}/agent/query",
        json={"query": "Summarize the current global geopolitical situation."},
        timeout=30,
    )
    brief_response.raise_for_status()
    brief_data = brief_response.json()
    brief_text = brief_data.get("answer", str(brief_data))
    with st.expander("📖 Read the full intelligence brief", expanded=True):
        st.markdown(brief_text)
except requests.exceptions.RequestException as exc:
    st.error(f"Failed to load intelligence brief: {exc}")

st.divider()

# ---------------------------------------------------------------------------
# 2. Trigger News Collection
# ---------------------------------------------------------------------------
col_btn, col_spacer = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Collect Latest News", use_container_width=True):
        try:
            collect_response = requests.post(f"{BACKEND_URL}/events/collect", timeout=60)
            collect_response.raise_for_status()
            st.success("✅ News collection triggered successfully!")
            st.cache_data.clear()
        except requests.exceptions.RequestException as exc:
            st.error(f"Failed to trigger news collection: {exc}")

st.divider()

# ---------------------------------------------------------------------------
# Load events (shared across sections 3-5)
# ---------------------------------------------------------------------------
events: list = []
try:
    events = fetch_events()
except requests.exceptions.RequestException as exc:
    st.error(f"Failed to load events: {exc}")

# ---------------------------------------------------------------------------
# 3. Recent Events Feed
# ---------------------------------------------------------------------------
st.header("📰 Recent Events Feed")

if events:
    display_cols = ["title", "category", "severity", "countries", "published_at", "source"]
    table_rows = []
    for e in events:
        table_rows.append(
            {
                "Title": e.get("title", ""),
                "Category": e.get("category", ""),
                "Severity": e.get("severity", ""),
                "Countries": ", ".join(e.get("countries", [])),
                "Published": e.get("published_at", ""),
                "Source": e.get("source", ""),
            }
        )
    df_events = pd.DataFrame(table_rows)
    st.dataframe(df_events, use_container_width=True, height=300)
else:
    st.info("No events available. Try collecting the latest news first.")

st.divider()

# ---------------------------------------------------------------------------
# 4. Event Categories Chart
# ---------------------------------------------------------------------------
st.header("📊 Events by Category")
render_category_chart(events)

st.divider()

# ---------------------------------------------------------------------------
# 5. Regional Summaries
# ---------------------------------------------------------------------------
st.header("🗺️ Regional Summaries")
for region in REGIONS:
    render_region_section(region, events)
