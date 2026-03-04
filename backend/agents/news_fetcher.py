import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

GEOPOLITICAL_QUERIES = [
    "war conflict military",
    "sanctions diplomacy nuclear",
    "geopolitical crisis coup",
    "terrorism attack border dispute",
    "election protest uprising",
    "trade war tariff economic crisis",
    "NATO alliance treaty",
    "missile strike airstrike",
]


class GDELTFetcher:
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def fetch(self, query: str, max_records: int = 50) -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json",
            "timespan": "1d",
            "sort": "DateDesc",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                articles = data.get("articles", [])
                return self._normalize(articles)
            except Exception as e:
                logger.warning(f"GDELT fetch error for '{query}': {e}")
                return []

    def _normalize(self, articles: List[Dict]) -> List[Dict]:
        results = []
        for art in articles:
            title = art.get("title", "").strip()
            if not title:
                continue
            results.append({
                "title": title,
                "description": str(art.get("seendates", "")),
                "url": art.get("url", ""),
                "source": art.get("domain", "GDELT"),
                "published_at": art.get("seendates", datetime.utcnow().isoformat()),
                "raw_source": "gdelt",
            })
        return results

    async def fetch_all_geopolitical(self) -> List[Dict[str, Any]]:
        tasks = [self.fetch(q, max_records=30) for q in GEOPOLITICAL_QUERIES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_articles = []
        seen_urls = set()
        for batch in results:
            if isinstance(batch, list):
                for article in batch:
                    url = article.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_articles.append(article)
        logger.info(f"✅ GDELT fetched {len(all_articles)} unique articles.")
        return all_articles


class NewsAPIFetcher:
    BASE_URL = "https://newsapi.org/v2/top-headlines"
    EVERYTHING_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        self.api_key = settings.newsapi_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def fetch_top_headlines(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        params = {
            "category": "general",
            "language": "en",
            "pageSize": 50,
            "apiKey": self.api_key,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                return self._normalize(data.get("articles", []))
            except Exception as e:
                logger.warning(f"NewsAPI error: {e}")
                return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def fetch_geopolitical(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        params = {
            "q": "war OR conflict OR sanctions OR diplomacy OR coup OR missile OR nuclear",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100,
            "from": from_date,
            "apiKey": self.api_key,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(self.EVERYTHING_URL, params=params)
                response.raise_for_status()
                data = response.json()
                return self._normalize(data.get("articles", []))
            except Exception as e:
                logger.warning(f"NewsAPI geopolitical error: {e}")
                return []

    def _normalize(self, articles: List[Dict]) -> List[Dict]:
        results = []
        for art in articles:
            title = (art.get("title") or "").strip()
            if not title or title == "[Removed]":
                continue
            results.append({
                "title": title,
                "description": art.get("description") or "",
                "url": art.get("url", ""),
                "source": (art.get("source") or {}).get("name", "NewsAPI"),
                "published_at": art.get("publishedAt", datetime.utcnow().isoformat()),
                "raw_source": "newsapi",
            })
        return results

    async def fetch_all(self) -> List[Dict[str, Any]]:
        results = await asyncio.gather(
            self.fetch_top_headlines(),
            self.fetch_geopolitical(),
            return_exceptions=True,
        )
        all_articles = []
        seen_urls = set()
        for batch in results:
            if isinstance(batch, list):
                for article in batch:
                    url = article.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_articles.append(article)
        logger.info(f"✅ NewsAPI fetched {len(all_articles)} unique articles.")
        return all_articles


task fetch_all_news() -> List[Dict[str, Any]]:
    gdelt = GDELTFetcher()
    newsapi = NewsAPIFetcher()
    gdelt_articles, newsapi_articles = await asyncio.gather(
        gdelt.fetch_all_geopolitical(),
        newsapi.fetch_all(),
        return_exceptions=True,
    )
    all_articles = []
    if isinstance(gdelt_articles, list):
        all_articles.extend(gdelt_articles)
    if isinstance(newsapi_articles, list):
        all_articles.extend(newsapi_articles)
    logger.info(f"📰 Total articles fetched: {len(all_articles)}")
    return all_articles