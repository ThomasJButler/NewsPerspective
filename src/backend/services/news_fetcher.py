import time
import logging

import requests

from ..utils.logger import setup_logger

logger = setup_logger("NewsFetcher")

NEWSAPI_BASE = "https://newsapi.org/v2"
CATEGORIES = ["general", "sports", "technology", "science", "health", "business", "entertainment"]
DAILY_REQUEST_LIMIT = 100
REQUEST_WARNING_THRESHOLD = 80


class NewsFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_count = 0

    def fetch_top_headlines(self, country: str = "gb", category: str | None = None) -> list[dict]:
        """Fetch UK top headlines, optionally filtered by category."""
        params = {"country": country, "apiKey": self.api_key, "pageSize": 100}
        if category:
            params["category"] = category
        return self._fetch(f"{NEWSAPI_BASE}/top-headlines", params)

    def fetch_all_categories(self, country: str = "gb") -> list[dict]:
        """Fetch headlines across all categories with deduplication by URL."""
        all_articles = []
        seen_urls: set[str] = set()

        for category in CATEGORIES:
            if self.request_count >= DAILY_REQUEST_LIMIT:
                logger.warning("Daily request limit reached — stopping fetches")
                break

            articles = self.fetch_top_headlines(country=country, category=category)
            for article in articles:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    article["category"] = category
                    all_articles.append(article)

        logger.info(f"Fetched {len(all_articles)} unique articles across {len(CATEGORIES)} categories")
        return all_articles

    def _fetch(self, url: str, params: dict, retries: int = 3) -> list[dict]:
        """Make a NewsAPI request with retry/backoff and rate-limit awareness."""
        if self.request_count >= DAILY_REQUEST_LIMIT:
            logger.warning("Daily request limit reached — refusing to fetch")
            return []

        if self.request_count >= REQUEST_WARNING_THRESHOLD:
            logger.warning(f"Approaching daily limit: {self.request_count}/{DAILY_REQUEST_LIMIT} requests used")

        for attempt in range(retries):
            try:
                self.request_count += 1
                resp = requests.get(url, params=params, timeout=30)

                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited (429), retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "ok":
                    logger.error(f"NewsAPI error: {data.get('message', 'unknown')}")
                    return []

                articles = data.get("articles", [])
                return self._filter_articles(articles)

            except requests.RequestException as e:
                wait = 2 ** attempt
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(wait)

        return []

    def _filter_articles(self, articles: list[dict]) -> list[dict]:
        """Remove empty/removed articles that NewsAPI returns as placeholders."""
        filtered = []
        for article in articles:
            title = article.get("title", "")
            if not title or title == "[Removed]":
                continue
            if article.get("description") == "[Removed]":
                continue
            filtered.append(self._normalize(article))
        return filtered

    def _normalize(self, article: dict) -> dict:
        """Normalize a NewsAPI article dict to match our DB column names."""
        source = article.get("source", {})
        return {
            "original_title": article.get("title", ""),
            "original_description": article.get("description", ""),
            "source_name": source.get("name", ""),
            "source_id": source.get("id", ""),
            "author": article.get("author"),
            "url": article.get("url", ""),
            "image_url": article.get("urlToImage"),
            "published_at": article.get("publishedAt"),
            "category": article.get("category", "general"),
        }
