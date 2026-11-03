"""Personal intelligence dashboard: defence, geopolitics, national/international
affairs, markets & gold, CSR/ESG, sustainable India.

Run:  streamlit run app.py
Env (optional):
  DASHBOARD_PASSWORD  - if set, the page asks for it before showing anything
  OPENAI_API_KEY      - if set, each tab gets a "Brief me" AI summary button
  OPENAI_MODEL        - default gpt-4o-mini
"""
import os
import re
import time
import html
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
import streamlit as st
import yaml
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))
FEEDS_FILE = Path(__file__).with_name("feeds.yaml")
UA = "Mozilla/5.0 (news-dashboard)"
TROY_OZ_G = 31.1035

st.set_page_config(page_title="Intel Dashboard", page_icon="🛰️", layout="wide")


# ---------- optional password gate ----------
def gate():
    pw = os.getenv("DASHBOARD_PASSWORD")
    if not pw or st.session_state.get("ok"):
        return
    entered = st.text_input("Password", type="password")
    if entered == pw:
        st.session_state.ok = True
        st.rerun()
    st.stop()


gate()


# ---------- data ----------
def gnews_url(q: str) -> str:
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
            + "&hl=en-IN&gl=IN&ceid=IN:en")


def clean(text: str, n: int = 240) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n] + ("…" if len(text) > n else "")


@st.cache_data(ttl=900, show_spinner=False)  # 15 min
def fetch_feed(url: str, source: str):
    d = feedparser.parse(url, agent=UA)
    items = []
    for e in d.entries[:40]:
        ts = e.get("published_parsed") or e.get("updated_parsed")
        dt = datetime.fromtimestamp(time.mktime(ts), tz=timezone.utc) if ts else None
        items.append({
            "title": clean(e.get("title", ""), 200),
            "link": e.get("link", ""),
            "summary": clean(e.get("summary", "")),
            "source": (e.get("source") or {}).get("title") or source,
            "dt": dt,
        })
    return items


def load_topics():
    return yaml.safe_load(FEEDS_FILE.read_text())["topics"]


def topic_items(feeds, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen, out = set(), []
    for f in feeds:
        url = gnews_url(f["gnews"]) if "gnews" in f else f["url"]
        try:
            items = fetch_feed(url, f["name"])
        except Exception:
            continue
        for it in items:
            key = re.sub(r"\W+", "", it["title"].lower())[:80]
            if key in seen or (it["dt"] and it["dt"] < cutoff):
                continue
            seen.add(key)
            out.append(it)
    out.sort(key=lambda x: x["dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return out


@st.cache_data(ttl=900, show_spinner=False)
def market_snapshot():
    tickers = {"Gold $/oz": "GC=F", "Silver $/oz": "SI=F", "USD/INR": "INR=X",
               "Nifty 50": "^NSEI", "Sensex": "^BSESN", "Brent $": "BZ=F"}
    out = {}
    for name, t in tickers.items():
        try:
            h = yf.Ticker(t).history(period="5d")["Close"].dropna()
            if len(h) >= 2:
                out[name] = (float(h.iloc[-1]), float(h.iloc[-1] - h.iloc[-2]))
        except Exception:
            pass
    if "Gold $/oz" in out and "USD/INR" in out:
        g, gd = out["Gold $/oz"]
        fx = out["USD/INR"][0]
        out["Gold ₹/10g*"] = (g * fx / TROY_OZ_G * 10, gd * fx / TROY_OZ_G * 10)
    return out


def ai_brief(topic, items):
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    heads = "\n".join(f"- {i['title']} ({i['source']})" for i in items[:25])
    prompt = (f"You brief an Indian government-exam aspirant and CSR professional. "
              f"Topic: {topic}. From ONLY these headlines, give 5 bullet key developments, "
              f"then 2 lines 'Why it matters for India', then 3 likely exam-style facts. "
              f"Do not invent facts beyond the headlines.\n\n{heads}")
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": model, "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2}, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# ---------- UI ----------
st.title("🛰️ Intel Dashboard")
c1, c2, c3 = st.columns([2, 2, 1])
hours = c1.select_slider("Window", options=[6, 12, 24, 48, 72, 168], value=24,
                         format_func=lambda h: f"last {h}h" if h < 168 else "last 7 days")
query = c2.text_input("Filter headlines", placeholder="e.g. China, Rafale, BRSR")
if c3.button("🔄 Refresh now"):
    st.cache_data.clear()
st.caption(f"Updated {datetime.now(IST):%d %b %Y, %H:%M} IST · feeds cached 15 min")

mk = market_snapshot()
if mk:
    cols = st.columns(len(mk))
    for col, (name, (val, chg)) in zip(cols, mk.items()):
        col.metric(name, f"{val:,.2f}", f"{chg:+,.2f}")
    st.caption("*Gold ₹/10g = international price × USD/INR. Excludes Indian import duty and GST, "
               "so local jeweller rates run higher.")

topics = load_topics()
tabs = st.tabs(list(topics.keys()))
for tab, (topic, feeds) in zip(tabs, topics.items()):
    with tab:
        items = topic_items(feeds, hours)
        if query:
            q = query.lower()
            items = [i for i in items if q in i["title"].lower() or q in i["summary"].lower()]
        st.write(f"**{len(items)} stories**")
        if os.getenv("OPENAI_API_KEY") and items:
            if st.button("🧠 Brief me", key=f"brief-{topic}"):
                with st.spinner("Summarising…"):
                    try:
                        st.info(ai_brief(topic, items))
                    except Exception as e:
                        st.error(f"AI brief failed: {e}")
        for it in items[:60]:
            when = it["dt"].astimezone(IST).strftime("%d %b %H:%M") if it["dt"] else ""
            st.markdown(f"**[{it['title']}]({it['link']})**  \n"
                        f"<small>{it['source']} · {when}</small>", unsafe_allow_html=True)
            if it["summary"] and it["summary"] != it["title"]:
                st.caption(it["summary"])
