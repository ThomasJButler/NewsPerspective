"""Smoke validation for the backend API contract.

Run with:
    python -m unittest src.backend.tests.test_api_smoke -v
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import BackgroundTasks, HTTPException
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
                        id="article-4",
                        original_title="Third processed article",
                        rewritten_title="Third processed article",
                        tldr="Summary four.",
                        original_description="Description four.",
                        source_name=" Reuters ",
                        source_id=" reuters ",
                        author="Reporter Four",
                        url="https://example.com/article-4",
                        image_url="https://example.com/article-4.jpg",
                        published_at=now - timedelta(minutes=30),
                        fetched_at=now + timedelta(minutes=10),
                        was_rewritten=False,
                        original_sentiment="neutral",
                        sentiment_score=0.0,
                        is_good_news=False,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-5",
                        original_title="Fourth processed article",
                        rewritten_title="Fourth processed article",
                        tldr="Summary five.",
                        original_description="Description five.",
                        source_name="   ",
                        source_id=" source-id-only ",
                        author="Reporter Five",
                        url="https://example.com/article-5",
                        image_url="https://example.com/article-5.jpg",
                        published_at=now - timedelta(minutes=15),
                        fetched_at=now + timedelta(minutes=20),
                        was_rewritten=True,
                        original_sentiment="neutral",
                        sentiment_score=0.1,
                        is_good_news=False,
                        category="science",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-6",
                        original_title="Fifth processed article",
                        rewritten_title="Fifth processed article",
                        tldr="Summary six.",
                        original_description="Description six.",
                        source_name="   ",
                        source_id="   ",
                        author="Reporter Six",
                        url="https://example.com/article-6",
                        image_url="https://example.com/article-6.jpg",
                        published_at=now - timedelta(minutes=5),
                        fetched_at=now + timedelta(minutes=30),
                        was_rewritten=False,
                        original_sentiment="neutral",
                        sentiment_score=0.0,
                        is_good_news=True,
                        category="health",
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
                    models.Article(
                        id="article-7",
                        original_title="Failed article",
                        original_description="Description seven.",
                        source_name="Failed Source",
                        source_id="failed-source",
                        url="https://example.com/article-7",
                        published_at=now - timedelta(minutes=1),
                        fetched_at=now - timedelta(minutes=1),
                        category="science",
                        processing_status="failed",
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
        database.dispose_engine()
        _TEMP_DIR.cleanup()

    def setUp(self) -> None:
        refresh_tracker_module.refresh_tracker.reset()

    def assert_utc_offset_timestamp(
        self,
        value: str | None,
        expected: datetime,
    ) -> None:
        self.assertIsNotNone(value)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        self.assertEqual(parsed.utcoffset(), timedelta(0))
        self.assertEqual(parsed, expected)

    def test_articles_list_returns_only_processed_rows(self) -> None:
        response = self.client.get("/api/articles")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total"], 5)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["per_page"], 20)
        self.assertFalse(body["has_more"])
        self.assertEqual(
            [article["id"] for article in body["articles"]],
            ["article-6", "article-5", "article-4", "article-2", "article-1"],
        )
        self.assertTrue(
            all(article["processing_status"] == "processed" for article in body["articles"])
        )

    def test_articles_list_preserves_utc_offsets_after_sqlite_round_trip(self) -> None:
        response = self.client.get("/api/articles")

        self.assertEqual(response.status_code, 200)
        by_id = {article["id"]: article for article in response.json()["articles"]}

        session = database.SessionLocal()
        try:
            latest_article = session.get(models.Article, "article-6")
            earliest_article = session.get(models.Article, "article-1")
        finally:
            session.close()

        self.assertIsNotNone(latest_article)
        self.assertIsNotNone(earliest_article)
        self.assert_utc_offset_timestamp(
            by_id["article-6"]["published_at"],
            latest_article.published_at,
        )
        self.assert_utc_offset_timestamp(
            by_id["article-6"]["fetched_at"],
            latest_article.fetched_at,
        )
        self.assert_utc_offset_timestamp(
            by_id["article-1"]["published_at"],
            earliest_article.published_at,
        )
        self.assert_utc_offset_timestamp(
            by_id["article-1"]["fetched_at"],
            earliest_article.fetched_at,
        )

    def test_backend_entrypoint_imports_as_top_level_module(self) -> None:
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        spec = importlib.util.spec_from_file_location("backend_main_direct", main_path)

        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(module.app.title, "NewsPerspective API")

    def test_articles_pagination_stays_stable_with_tied_and_null_published_at(self) -> None:
        session = database.SessionLocal()
        inserted_ids = ["article-5a", "article-5b", "null-a", "null-b"]
        try:
            tied_timestamp = session.get(models.Article, "article-5").published_at
            session.add_all(
                [
                    models.Article(
                        id="article-5a",
                        original_title="Tied published article A",
                        original_description="Tie A.",
                        source_name="Tie Source",
                        source_id="tie-source",
                        url="https://example.com/article-5a",
                        published_at=tied_timestamp,
                        fetched_at=tied_timestamp,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-5b",
                        original_title="Tied published article B",
                        original_description="Tie B.",
                        source_name="Tie Source",
                        source_id="tie-source",
                        url="https://example.com/article-5b",
                        published_at=tied_timestamp,
                        fetched_at=tied_timestamp,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="null-a",
                        original_title="Null published article A",
                        original_description="Null A.",
                        source_name="Null Source",
                        source_id="null-source",
                        url="https://example.com/null-a",
                        published_at=None,
                        fetched_at=datetime.now(timezone.utc),
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="null-b",
                        original_title="Null published article B",
                        original_description="Null B.",
                        source_name="Null Source",
                        source_id="null-source",
                        url="https://example.com/null-b",
                        published_at=None,
                        fetched_at=datetime.now(timezone.utc),
                        category="general",
                        processing_status="processed",
                    ),
                ]
            )
            session.commit()
            seen_ids: list[str] = []
            page = 1
            while True:
                response = self.client.get("/api/articles", params={"page": page, "per_page": 2})

                self.assertEqual(response.status_code, 200)
                body = response.json()
                seen_ids.extend(article["id"] for article in body["articles"])

                if not body["has_more"]:
                    break

                page += 1

            self.assertEqual(
                seen_ids,
                [
                    "article-6",
                    "article-5",
                    "article-5a",
                    "article-5b",
                    "article-4",
                    "article-2",
                    "article-1",
                    "null-a",
                    "null-b",
                ],
            )
            self.assertEqual(len(seen_ids), len(set(seen_ids)))
        finally:
            for article_id in inserted_ids:
                article = session.get(models.Article, article_id)
                if article is not None:
                    session.delete(article)
            session.commit()
            session.close()

    def test_articles_filter_by_source_label(self) -> None:
        response = self.client.get("/api/articles", params={"source": "Reuters"})

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total"], 2)
        self.assertEqual([article["id"] for article in body["articles"]], ["article-4", "article-2"])

    def test_good_news_filter_excludes_sports_and_entertainment_categories(self) -> None:
        session = database.SessionLocal()
        inserted_ids = ["article-sports-good", "article-entertainment-good"]
        now = datetime.now(timezone.utc)

        try:
            session.add_all(
                [
                    models.Article(
                        id="article-sports-good",
                        original_title="Sports win",
                        original_description="Sports story flagged as good news.",
                        source_name="Sports Desk",
                        source_id="sports-desk",
                        url="https://example.com/article-sports-good",
                        published_at=now,
                        fetched_at=now,
                        is_good_news=True,
                        category="sports",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-entertainment-good",
                        original_title="Entertainment premiere",
                        original_description="Entertainment story flagged as good news.",
                        source_name="Culture Desk",
                        source_id="culture-desk",
                        url="https://example.com/article-entertainment-good",
                        published_at=now,
                        fetched_at=now,
                        is_good_news=True,
                        category="entertainment",
                        processing_status="processed",
                    ),
                ]
            )
            session.commit()

            response = self.client.get("/api/articles", params={"good_news_only": "true"})

            self.assertEqual(response.status_code, 200)
            body = response.json()

            self.assertEqual(body["total"], 2)
            self.assertEqual([article["id"] for article in body["articles"]], ["article-6", "article-2"])
        finally:
            for article_id in inserted_ids:
                article = session.get(models.Article, article_id)
                if article is not None:
                    session.delete(article)
            session.commit()
            session.close()

    def test_good_news_filter_excludes_detected_politics_articles(self) -> None:
        session = database.SessionLocal()
        article_id = "article-politics-good"
        now = datetime.now(timezone.utc)

        try:
            session.add(
                models.Article(
                    id=article_id,
                    original_title="Senate approves infrastructure funding",
                    original_description="Lawmakers celebrated the vote as a win.",
                    source_name="Reuters Politics",
                    source_id="reuters",
                    url="https://example.com/article-politics-good",
                    published_at=now,
                    fetched_at=now,
                    is_good_news=True,
                    category="general",
                    processing_status="processed",
                )
            )
            session.commit()

            response = self.client.get("/api/articles", params={"good_news_only": "true"})

            self.assertEqual(response.status_code, 200)
            body = response.json()

            self.assertEqual(body["total"], 2)
            self.assertEqual([article["id"] for article in body["articles"]], ["article-6", "article-2"])
        finally:
            article = session.get(models.Article, article_id)
            if article is not None:
                session.delete(article)
            session.commit()
            session.close()

    def test_articles_list_returns_normalized_source_labels(self) -> None:
        response = self.client.get("/api/articles")

        self.assertEqual(response.status_code, 200)
        by_id = {article["id"]: article["source_name"] for article in response.json()["articles"]}

        self.assertEqual(by_id["article-4"], "Reuters")
        self.assertEqual(by_id["article-5"], "source-id-only")
        self.assertEqual(by_id["article-6"], "Unknown source")

    def test_article_detail_returns_normalized_source_label(self) -> None:
        response = self.client.get("/api/articles/article-5")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["id"], "article-5")
        self.assertEqual(body["source_name"], "source-id-only")
        self.assertTrue(body["was_rewritten"])

    def test_article_detail_preserves_utc_offsets_after_sqlite_round_trip(self) -> None:
        response = self.client.get("/api/articles/article-5")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        session = database.SessionLocal()
        try:
            article = session.get(models.Article, "article-5")
        finally:
            session.close()

        self.assertIsNotNone(article)
        self.assert_utc_offset_timestamp(body["published_at"], article.published_at)
        self.assert_utc_offset_timestamp(body["fetched_at"], article.fetched_at)

    def test_article_detail_masks_good_news_for_excluded_categories(self) -> None:
        session = database.SessionLocal()
        article_id = "article-sports-detail"
        now = datetime.now(timezone.utc)

        try:
            session.add(
                models.Article(
                    id=article_id,
                    original_title="Sports feature",
                    original_description="Sports feature marked as good news in storage.",
                    source_name="Sports Desk",
                    source_id="sports-desk",
                    url="https://example.com/article-sports-detail",
                    published_at=now,
                    fetched_at=now,
                    is_good_news=True,
                    category="sports",
                    processing_status="processed",
                )
            )
            session.commit()

            response = self.client.get(f"/api/articles/{article_id}")

            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["is_good_news"])
        finally:
            article = session.get(models.Article, article_id)
            if article is not None:
                session.delete(article)
            session.commit()
            session.close()

    def test_article_detail_masks_good_news_for_detected_politics_story(self) -> None:
        session = database.SessionLocal()
        article_id = "article-politics-detail"
        now = datetime.now(timezone.utc)

        try:
            session.add(
                models.Article(
                    id=article_id,
                    original_title="Parliament backs clean-energy package",
                    original_description="Government ministers hailed the legislation.",
                    source_name="World Desk",
                    source_id="world-desk",
                    url="https://example.com/article-politics-detail",
                    published_at=now,
                    fetched_at=now,
                    is_good_news=True,
                    category="business",
                    processing_status="processed",
                )
            )
            session.commit()

            response = self.client.get(f"/api/articles/{article_id}")

            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["is_good_news"])
        finally:
            article = session.get(models.Article, article_id)
            if article is not None:
                session.delete(article)
            session.commit()
            session.close()

    def test_article_detail_returns_404_for_pending_article(self) -> None:
        response = self.client.get("/api/articles/article-3")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Article not found")

    def test_article_detail_returns_404_for_failed_article(self) -> None:
        response = self.client.get("/api/articles/article-7")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Article not found")

    def test_article_detail_returns_404_for_missing_id(self) -> None:
        response = self.client.get("/api/articles/not-a-real-id")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Article not found")

    def test_sources_returns_processed_source_counts(self) -> None:
        response = self.client.get("/api/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {source["source_name"]: source for source in response.json()["sources"]},
            {
                "BBC News": {
                    "source_name": "BBC News",
                    "source_id": "bbc-news",
                    "article_count": 1,
                },
                "Reuters": {
                    "source_name": "Reuters",
                    "source_id": "reuters",
                    "article_count": 2,
                },
                "Unknown source": {
                    "source_name": "Unknown source",
                    "source_id": "",
                    "article_count": 1,
                },
                "source-id-only": {
                    "source_name": "source-id-only",
                    "source_id": "source-id-only",
                    "article_count": 1,
                },
            },
        )

    def test_stats_counts_processed_articles_and_normalized_sources_only(self) -> None:
        response = self.client.get("/api/stats")

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["total_articles"], 5)
        self.assertEqual(body["rewritten_count"], 2)
        self.assertEqual(body["good_news_count"], 2)
        self.assertEqual(body["sources_count"], 4)
        self.assertIsNotNone(body["latest_fetch"])
        parsed_latest_fetch = datetime.fromisoformat(
            body["latest_fetch"].replace("Z", "+00:00")
        )
        self.assertEqual(parsed_latest_fetch.utcoffset(), timedelta(0))

    def test_stats_good_news_count_excludes_sports_and_entertainment_categories(self) -> None:
        session = database.SessionLocal()
        inserted_ids = ["article-sports-stats", "article-entertainment-stats"]
        now = datetime.now(timezone.utc)

        try:
            session.add_all(
                [
                    models.Article(
                        id="article-sports-stats",
                        original_title="Sports stats row",
                        original_description="Sports article that should not count as good news.",
                        source_name="Sports Desk",
                        source_id="sports-desk",
                        url="https://example.com/article-sports-stats",
                        published_at=now,
                        fetched_at=now,
                        is_good_news=True,
                        category="sports",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="article-entertainment-stats",
                        original_title="Entertainment stats row",
                        original_description="Entertainment article that should not count as good news.",
                        source_name="Culture Desk",
                        source_id="culture-desk",
                        url="https://example.com/article-entertainment-stats",
                        published_at=now,
                        fetched_at=now,
                        is_good_news=True,
                        category="entertainment",
                        processing_status="processed",
                    ),
                ]
            )
            session.commit()

            response = self.client.get("/api/stats")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["good_news_count"], 2)
        finally:
            for article_id in inserted_ids:
                article = session.get(models.Article, article_id)
                if article is not None:
                    session.delete(article)
            session.commit()
            session.close()

    def test_stats_good_news_count_excludes_detected_politics_articles(self) -> None:
        session = database.SessionLocal()
        article_id = "article-politics-stats"
        now = datetime.now(timezone.utc)

        try:
            session.add(
                models.Article(
                    id=article_id,
                    original_title="Election officials certify final result",
                    original_description="Government leaders accepted the outcome.",
                    source_name="National Desk",
                    source_id="national-desk",
                    url="https://example.com/article-politics-stats",
                    published_at=now,
                    fetched_at=now,
                    is_good_news=True,
                    category="general",
                    processing_status="processed",
                )
            )
            session.commit()

            response = self.client.get("/api/stats")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["good_news_count"], 2)
        finally:
            article = session.get(models.Article, article_id)
            if article is not None:
                session.delete(article)
            session.commit()
            session.close()

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

    def test_refresh_success_runs_background_task_and_marks_completed(self) -> None:
        successful_response = Mock()
        successful_response.status_code = 200
        successful_response.json.return_value = {"status": "ok"}

        captured_keys: list[str] = []

        def fake_background_task(api_key: str) -> None:
            captured_keys.append(api_key)
            refresh_tracker_module.refresh_tracker.mark_completed(
                new_articles=4,
                processed_articles=3,
                failed_articles=1,
            )

        with patch.object(
            sources_router.http_requests,
            "get",
            return_value=successful_response,
        ) as mock_get, patch.object(
            sources_router,
            "process_new_articles_background",
            side_effect=fake_background_task,
        ) as mock_background_task:
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": "valid-key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "processing",
                "message": "Fetching and processing articles in the background.",
            },
        )
        mock_get.assert_called_once_with(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": sources_router.DEFAULT_NEWSAPI_COUNTRY,
                "pageSize": 1,
                "apiKey": "valid-key",
            },
            timeout=sources_router.NEWSAPI_VALIDATION_TIMEOUT_SECONDS,
        )
        mock_background_task.assert_called_once_with("valid-key")
        self.assertEqual(captured_keys, ["valid-key"])

        status_response = self.client.get("/api/refresh/status")
        self.assertEqual(status_response.status_code, 200)
        status_body = status_response.json()
        self.assertEqual(status_body["status"], "completed")
        self.assertEqual(status_body["message"], "Refresh completed.")
        self.assertEqual(status_body["new_articles"], 4)
        self.assertEqual(status_body["processed_articles"], 3)
        self.assertEqual(status_body["failed_articles"], 1)
        self.assertIsNotNone(status_body["started_at"])
        self.assertIsNotNone(status_body["finished_at"])

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
            params={
                "country": sources_router.DEFAULT_NEWSAPI_COUNTRY,
                "pageSize": 1,
                "apiKey": "invalid-key",
            },
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

    def test_refresh_timeout_chains_original_timeout_exception(self) -> None:
        original_error = sources_router.http_requests.Timeout("timed out")

        with patch.object(
            sources_router.http_requests,
            "get",
            side_effect=original_error,
        ):
            with self.assertRaises(HTTPException) as raised:
                sources_router.refresh_articles(
                    background_tasks=BackgroundTasks(),
                    x_news_api_key="slow-key",
                )

        self.assertEqual(raised.exception.status_code, 504)
        self.assertIs(raised.exception.__cause__, original_error)

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

    def test_refresh_transport_failure_chains_original_request_exception(self) -> None:
        original_error = sources_router.http_requests.ConnectionError("network down")

        with patch.object(
            sources_router.http_requests,
            "get",
            side_effect=original_error,
        ):
            with self.assertRaises(HTTPException) as raised:
                sources_router.refresh_articles(
                    background_tasks=BackgroundTasks(),
                    x_news_api_key="offline-key",
                )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertIs(raised.exception.__cause__, original_error)

    def test_refresh_transport_failure_redacts_api_key_from_error_detail(self) -> None:
        api_key = "top-secret-key"
        error = sources_router.http_requests.ConnectionError(
            "validation failed for "
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}&pageSize=1"
        )

        with patch.object(
            sources_router.http_requests,
            "get",
            side_effect=error,
        ):
            response = self.client.post(
                "/api/refresh",
                headers={"X-News-Api-Key": api_key},
            )

        self.assertEqual(response.status_code, 502)
        detail = response.json()["detail"]
        self.assertEqual(detail["code"], "upstream_transport_failure")
        self.assertNotIn(api_key, detail["message"])
        self.assertIn("apiKey=[redacted]", detail["message"])


if __name__ == "__main__":
    unittest.main()
