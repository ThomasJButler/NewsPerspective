import time
import re

import requests

from ..utils.logger import setup_logger
from .news_source import NewsFetchError

logger = setup_logger("NewsFetcher")

NEWSAPI_BASE = "https://newsapi.org/v2"
DEFAULT_NEWSAPI_COUNTRY = "us"
CATEGORIES = ["general", "sports", "technology", "science", "health", "business", "entertainment"]
DAILY_REQUEST_LIMIT = 100
REQUEST_WARNING_THRESHOLD = 80

# UK source IDs and their category mapping. NewsAPI's /v2/top-headlines?country=gb
# was deprecated — only country=us is accepted now — so we fetch UK headlines by
# specifying well-known UK source IDs directly. One batched request covers all
# sources. Category is assigned per source because source-based fetches do not
# return a NewsAPI category field.
UK_SOURCE_CATEGORIES: dict[str, str] = {
    "bbc-news": "general",
    "bbc-sport": "sports",
    "the-guardian-uk": "general",
    "independent": "general",
    "financial-times": "business",
    "daily-mail": "general",
    "talksport": "sports",
    "business-insider-uk": "business",
}


def _redact_api_key(value: str, api_key: str) -> str:
    """Strip the NewsAPI key from request/HTTP error strings before logging or surfacing them."""
    redacted = value.replace(api_key, "[redacted]")
    return re.sub(r"(apiKey=)[^&\\s]+", r"\1[redacted]", redacted)


class NewsFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_count = 0

    def fetch_top_headlines(
        self,
        country: str = DEFAULT_NEWSAPI_COUNTRY,
        category: str | None = None,
    ) -> list[dict]:
        """Fetch top headlines for the configured country, optionally filtered by category."""
        params = {"country": country, "apiKey": self.api_key, "pageSize": 100}
        if category:
            params["category"] = category
        return self._fetch(f"{NEWSAPI_BASE}/top-headlines", params)

    def fetch_all_categories(self, country: str = DEFAULT_NEWSAPI_COUNTRY) -> list[dict]:
        """Fetch headlines for the given country with deduplication by URL.

        For country=us, iterates CATEGORIES using /v2/top-headlines?country=us.
        For country=gb, NewsAPI has deprecated the country param (only 'us' is
        accepted on /v2/top-headlines), so we delegate to _fetch_uk_by_sources
        which batches UK source IDs in a single request.
        """
        if country == "gb":
            return self._fetch_uk_by_sources()

        all_articles = []
        seen_urls: set[str] = set()
        failed_categories = 0

        for category in CATEGORIES:
            if self.request_count >= DAILY_REQUEST_LIMIT:
                logger.warning("Daily request limit reached — stopping fetches")
                break

            try:
                articles = self.fetch_top_headlines(country=country, category=category)
            except NewsFetchError as exc:
                logger.warning("Failed to fetch %s for %s: %s — skipping", category, country, exc)
                failed_categories += 1
                continue
            for article in articles:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    article["category"] = category
                    article["country"] = country
                    all_articles.append(article)

        if not all_articles and failed_categories == len(CATEGORIES):
            raise NewsFetchError(f"All category fetches failed for country={country}.")

        logger.info(
            f"Fetched {len(all_articles)} unique articles for country={country} "
            f"across {len(CATEGORIES)} categories"
        )
        return all_articles

    def _fetch_uk_by_sources(self) -> list[dict]:
        """Fetch UK headlines via source IDs in a single batched request.

        NewsAPI's /v2/top-headlines?country=gb was deprecated; only country=us
        is valid on that endpoint now. The /v2/top-headlines?sources= variant
        still works on the free Developer tier, so we fetch all UK outlets in
        one request. Each article is tagged with country='gb' and a category
        derived from UK_SOURCE_CATEGORIES (defaulting to 'general').
        """
        sources_param = ",".join(UK_SOURCE_CATEGORIES.keys())
        params = {
            "sources": sources_param,
            "apiKey": self.api_key,
            "pageSize": 100,
        }
        try:
            articles = self._fetch(f"{NEWSAPI_BASE}/top-headlines", params)
        except NewsFetchError:
            logger.warning("UK source-based fetch failed — no UK articles this refresh")
            raise

        all_articles: list[dict] = []
        seen_urls: set[str] = set()
        for article in articles:
            url = article.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article["country"] = "gb"
            article["category"] = UK_SOURCE_CATEGORIES.get(
                article.get("source_id", ""), "general"
            )
            all_articles.append(article)

        logger.info(
            f"Fetched {len(all_articles)} unique articles for country=gb "
            f"via {len(UK_SOURCE_CATEGORIES)} UK sources"
        )
        return all_articles

    def _fetch(self, url: str, params: dict, retries: int = 3) -> list[dict]:
        """Make a NewsAPI request with retry/backoff and rate-limit awareness."""
        if self.request_count >= DAILY_REQUEST_LIMIT:
            message = "Daily request limit reached before the refresh could finish."
            logger.error(message)
            raise NewsFetchError(message)

        if self.request_count >= REQUEST_WARNING_THRESHOLD:
            logger.warning(f"Approaching daily limit: {self.request_count}/{DAILY_REQUEST_LIMIT} requests used")

        last_error_message: str | None = None
        for attempt in range(retries):
            try:
                self.request_count += 1
                resp = requests.get(url, params=params, timeout=30)

                if resp.status_code == 429:
                    last_error_message = "NewsAPI rate limited the refresh request."
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited (429), retrying in {wait}s...")
                    if attempt < retries - 1:
                        time.sleep(wait)
                    continue

                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError as exc:
                    raise NewsFetchError("NewsAPI returned an unreadable response.") from exc

                if data.get("status") != "ok":
                    message = data.get("message", "unknown")
                    logger.error(f"NewsAPI error: {message}")
                    raise NewsFetchError(f"NewsAPI returned an error: {message}")

                articles = data.get("articles", [])
                return self._filter_articles(articles)

            except requests.RequestException as e:
                safe_error = _redact_api_key(str(e), self.api_key)
                last_error_message = f"Failed to fetch articles from NewsAPI: {safe_error}"
                wait = 2 ** attempt
                logger.error(
                    "Request failed (attempt %d/%d): %s",
                    attempt + 1,
                    retries,
                    safe_error,
                )
                if attempt < retries - 1:
                    time.sleep(wait)

        raise NewsFetchError(last_error_message or "Failed to fetch articles from NewsAPI.")

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
            "country": article.get("country", "us"),
        }
