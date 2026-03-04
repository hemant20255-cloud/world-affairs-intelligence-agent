import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class NewsCollector:
    """Collects world affairs news from multiple public APIs."""

    def __init__(self):
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.gdelt_base_url = "https://api.gdeltproject.org/api/v2"
        self.newsapi_base_url = "https://newsapi.org/v2"
        self.timeout = 30

    async def fetch_gdelt_events(self, query: str = "world affairs", max_records: int = 50) -> List[Dict[str, Any]]:
        """Fetch events from GDELT API (free, no key required)."""
        events = []
        try:
            url = f"{self.gdelt_base_url}/doc/doc"
            params = {
                "query": query,
                "mode": "artlist",
                "maxrecords": max_records,
                "format": "json",
                "timespan": "24h",
                "sort": "DateDesc",
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                for article in data.get("articles", []):
                    events.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("domain", "gdelt"),
                        "published_at": article.get("seendate", ""),
                        "description": article.get("title", ""),
                        "raw_source": "gdelt",
                    })
        except Exception as e:
            logger.error(f"GDELT fetch error: {e}")
        return events

    async def fetch_newsapi_articles(
        self,
        query: str = "international relations geopolitics",
        from_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch articles from NewsAPI (requires free API key)."""
        if not self.newsapi_key:
            logger.warning("NEWSAPI_KEY not set; skipping NewsAPI.")
            return []
        events = []
        try:
            if not from_date:
                from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            url = f"{self.newsapi_base_url}/everything"
            params = {
                "q": query,
                "from": from_date,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
                "apiKey": self.newsapi_key,
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                for article in data.get("articles", []):
                    events.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "newsapi"),
                        "published_at": article.get("publishedAt", ""),
                        "description": article.get("description", ""),
                        "raw_source": "newsapi",
                    })
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
        return events

    async def collect_all(self) -> List[Dict[str, Any]]:
        """Collect events from all configured sources concurrently."""
        queries = [
            "geopolitics conflict diplomacy",
            "international sanctions war",
            "economic crisis trade",
            "elections government protest",
            "climate disaster humanitarian",
        ]
        tasks = [self.fetch_gdelt_events(query=q) for q in queries]
        if self.newsapi_key:
            tasks.append(self.fetch_newsapi_articles())
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_events: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
        # Deduplicate by URL
        seen_urls = set()
        unique_events = []
        for event in all_events:
            url = event.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_events.append(event)
            elif not url:
                unique_events.append(event)
        logger.info(f"Collected {len(unique_events)} unique events.")
        return unique_events
