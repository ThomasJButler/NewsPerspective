"""Smoke validation for the backend API contract.

Run with:
    python -m unittest src.backend.tests.test_api_smoke -v
"""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "smoke.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

database = importlib.import_module("src.backend.database")
main = importlib.import_module("src.backend.main")
models = importlib.import_module("src.backend.models")
sources_router = importlib.import_module("src.backend.routers.sources")
refresh_tracker_module = importlib.import_module("src.backend.services.refresh_tracker")


class BackendApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)

        now = datetime.now(timezone.utc)
        session = database.SessionLocal()
        try:
            session.add_all(
                [
                    models.Article(
                        id="article-1",
                        original_title="First processed article",
                        rewritten_title="First processed article",
                        tldr="Summary one.",
                        original_description="Description one.",
                        source_name="BBC News",
                        source_id="bbc-news",
                        author="Reporter One",
                        url="https://example.com/article-1",
                        image_url="https://example.com/article-1.jpg",
                        published_at=now - timedelta(hours=2),
                        fetched_at=now - timedelta(hours=1),
                        was_rewritten=True,
                        original_sentiment="negative",
                        sentiment_score=-0.2,
                        is_good_news=False,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-2",
                        original_title="Second processed article",
                        rewritten_title="Second processed article",
                        tldr="Summary two.",
                        original_description="Description two.",
                        source_name="Reuters",
                        source_id="reuters",
                        author="Reporter Two",
                        url="https://example.com/article-2",
                        image_url="https://example.com/article-2.jpg",
                        published_at=now - timedelta(hours=1),
                        fetched_at=now,
                        was_rewritten=False,
                        original_sentiment="positive",
                        sentiment_score=0.7,
                        is_good_news=True,
                        category="business",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-3",
                        original_title="Pending article",
                        original_description="Description three.",
                        source_name="Hidden Source",
                        source_id="hidden-source",
                        url="https://example.com/article-3",
                        published_at=now,
                        fetched_at=now,
                        category="technology",
                        processing_status="pending",
                    ),
                ]
            )
            session.commit()
        finally:
            session.close()

        cls.client_context = TestClient(main.app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        database.Base.metadata.drop_all(bind=database.engine)
        _TEMP_DIR.cleanup()

    def setUp(self) -> None:
        refresh_tracker_module.refresh_tracker.reset()

    def test_articles_list_returns_only_processed_rows(self) -> None:
        response = self.client.get("/api/articles")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total"], 2)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["per_page"], 20)
        self.assertFalse(body["has_more"])
        self.assertEqual([article["id"] for article in body["articles"]], ["article-2", "article-1"])
        self.assertTrue(
            all(article["processing_status"] == "processed" for article in body["articles"])
        )

    def test_articles_filter_by_source_label(self) -> None:
        response = self.client.get("/api/articles", params={"source": "Reuters"})

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total"], 1)
        self.assertEqual([article["id"] for article in body["articles"]], ["article-2"])

    def test_article_detail_returns_seeded_article(self) -> None:
        response = self.client.get("/api/articles/article-1")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["id"], "article-1")
        self.assertEqual(body["source_name"], "BBC News")
        self.assertTrue(body["was_rewritten"])

    def test_article_detail_returns_404_for_missing_id(self) -> None:
        response = self.client.get("/api/articles/not-a-real-id")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Article not found")

    def test_sources_returns_processed_source_counts(self) -> None:
        response = self.client.get("/api/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "sources": [
                    {
                        "source_name": "BBC News",
                        "source_id": "bbc-news",
                        "article_count": 1,
                    },
                    {
                        "source_name": "Reuters",
                        "source_id": "reuters",
                        "article_count": 1,
                    },
                ]
            },
        )

    def test_stats_counts_processed_articles_only(self) -> None:
        response = self.client.get("/api/stats")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total_articles"], 2)
        self.assertEqual(body["rewritten_count"], 1)
        self.assertEqual(body["good_news_count"], 1)
        self.assertEqual(body["sources_count"], 2)
        self.assertIsNotNone(body["latest_fetch"])

    def test_refresh_status_starts_idle(self) -> None:
        response = self.client.get("/api/refresh/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "idle",
                "message": "No refresh has been started yet.",
                "started_at": None,
                "finished_at": None,
                "new_articles": 0,
                "processed_articles": 0,
                "failed_articles": 0,
            },
        )

    def test_refresh_without_key_returns_401(self) -> None:
        response = self.client.post("/api/refresh")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "code": "missing_api_key",
                    "message": "Missing X-News-Api-Key header.",
                }
            },
        )

    def test_refresh_duplicate_short_circuits_before_newsapi_validation(self) -> None:
        self.assertTrue(refresh_tracker_module.refresh_tracker.try_start())

        with patch.object(sources_router.http_requests, "get") as mock_get:
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": "duplicate-key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "processing",
                "message": "Refresh already in progress.",
            },
        )
        mock_get.assert_not_called()

    def test_refresh_validation_failure_releases_claim_and_restores_prior_status(self) -> None:
        refresh_tracker_module.refresh_tracker.mark_completed(
            new_articles=3,
            processed_articles=3,
            failed_articles=0,
        )

        invalid_response = Mock()
        invalid_response.status_code = 401
        invalid_response.json.return_value = {
            "status": "error",
            "message": "Your API key is invalid or incorrect.",
        }

        with patch.object(
            sources_router.http_requests,
            "get",
            return_value=invalid_response,
        ) as mock_get:
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": "invalid-key"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "code": "invalid_api_key",
                    "message": "Invalid NewsAPI key: Your API key is invalid or incorrect.",
                }
            },
        )
        mock_get.assert_called_once_with(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "gb", "pageSize": 1, "apiKey": "invalid-key"},
            timeout=sources_router.NEWSAPI_VALIDATION_TIMEOUT_SECONDS,
        )

        status_response = self.client.get("/api/refresh/status")
        self.assertEqual(status_response.status_code, 200)
        status_body = status_response.json()
        self.assertEqual(status_body["status"], "completed")
        self.assertEqual(status_body["message"], "Refresh completed.")
        self.assertEqual(status_body["new_articles"], 3)
        self.assertEqual(status_body["processed_articles"], 3)
        self.assertEqual(status_body["failed_articles"], 0)
        self.assertIsNotNone(status_body["started_at"])
        self.assertIsNotNone(status_body["finished_at"])

    def test_refresh_timeout_returns_structured_504_and_releases_claim(self) -> None:
        refresh_tracker_module.refresh_tracker.mark_completed(
            new_articles=2,
            processed_articles=2,
            failed_articles=0,
        )

        with patch.object(
            sources_router.http_requests,
            "get",
            side_effect=sources_router.http_requests.Timeout("timed out"),
        ):
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": "slow-key"},
            )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "code": "upstream_timeout",
                    "message": "Timed out while validating the NewsAPI key with NewsAPI.",
                }
            },
        )

        status_response = self.client.get("/api/refresh/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "completed")

    def test_refresh_transport_failure_returns_structured_502_and_releases_claim(
        self,
    ) -> None:
        refresh_tracker_module.refresh_tracker.mark_completed(
            new_articles=1,
            processed_articles=1,
            failed_articles=0,
        )

        with patch.object(
            sources_router.http_requests,
            "get",
            side_effect=sources_router.http_requests.ConnectionError("network down"),
        ):
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": "offline-key"},
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "code": "upstream_transport_failure",
                    "message": "Failed to reach NewsAPI while validating the key: network down",
                }
            },
        )

        status_response = self.client.get("/api/refresh/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
