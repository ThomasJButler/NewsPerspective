"""Regression coverage for background refresh processing failures.

Run with:
    python -m unittest src.backend.tests.test_refresh_processing -v
"""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "refresh-processing.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

article_processor = importlib.import_module("src.backend.services.article_processor")
database = importlib.import_module("src.backend.database")
models = importlib.import_module("src.backend.models")
news_fetcher = importlib.import_module("src.backend.services.news_fetcher")
refresh_tracker_module = importlib.import_module("src.backend.services.refresh_tracker")


class _DummySession:
    def __init__(self) -> None:
        self.closed = False

    def _unexpected_call(self, method_name: str) -> None:
        raise AssertionError(f"_DummySession.{method_name}() should not be called in this test")

    def query(self, *args, **kwargs):
        self._unexpected_call("query")

    def add(self, *args, **kwargs) -> None:
        self._unexpected_call("add")

    def commit(self) -> None:
        self._unexpected_call("commit")

    def refresh(self, *args, **kwargs) -> None:
        self._unexpected_call("refresh")

    def rollback(self) -> None:
        self._unexpected_call("rollback")

    def close(self) -> None:
        self.closed = True


class RefreshProcessingRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        database.reconfigure_engine(f"sqlite:///{_DB_PATH}")

    @classmethod
    def tearDownClass(cls) -> None:
        database.dispose_engine()
        _TEMP_DIR.cleanup()

    def setUp(self) -> None:
        refresh_tracker_module.refresh_tracker.reset()
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)

    def test_fetcher_redacts_api_key_from_request_errors(self) -> None:
        api_key = "secret-news-api-key"
        fetcher = news_fetcher.NewsFetcher(api_key=api_key)
        request_error = news_fetcher.requests.HTTPError(
            "401 Client Error: Unauthorized for url: "
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}&pageSize=100"
        )

        with patch.object(news_fetcher.requests, "get", side_effect=request_error):
            with self.assertRaises(news_fetcher.NewsFetchError) as raised:
                fetcher._fetch(
                    "https://newsapi.org/v2/top-headlines",
                    {"country": "us", "apiKey": api_key, "pageSize": 100},
                    retries=1,
                )

        message = str(raised.exception)
        self.assertNotIn(api_key, message)
        self.assertIn("apiKey=[redacted]", message)

    def test_process_new_articles_propagates_news_fetch_errors(self) -> None:
        expected_error = news_fetcher.NewsFetchError(
            "NewsAPI returned an error: post-validation quota exceeded"
        )

        with patch.object(
            article_processor.NewsFetcher,
            "fetch_all_categories",
            side_effect=expected_error,
        ):
            processor = article_processor.ArticleProcessor()

            with self.assertRaises(news_fetcher.NewsFetchError) as raised:
                processor.process_new_articles(db=_DummySession(), api_key="valid-key")

        self.assertIs(raised.exception, expected_error)

    def test_fetcher_raises_after_429_retry_exhaustion(self) -> None:
        api_key = "secret-news-api-key"
        fetcher = news_fetcher.NewsFetcher(api_key=api_key)

        class _RateLimitedResponse:
            status_code = 429

        with patch.object(
            news_fetcher.requests,
            "get",
            return_value=_RateLimitedResponse(),
        ) as mocked_get, patch.object(news_fetcher.time, "sleep") as mocked_sleep:
            with self.assertRaises(news_fetcher.NewsFetchError) as raised:
                fetcher._fetch(
                    "https://newsapi.org/v2/top-headlines",
                    {"country": "us", "apiKey": api_key, "pageSize": 100},
                )

        self.assertEqual(str(raised.exception), "NewsAPI rate limited the refresh request.")
        self.assertEqual(mocked_get.call_count, 3)
        self.assertEqual([call.args[0] for call in mocked_sleep.call_args_list], [1, 2])
        self.assertEqual(fetcher.request_count, 3)

    def test_fetcher_raises_after_transport_retry_exhaustion(self) -> None:
        api_key = "secret-news-api-key"
        fetcher = news_fetcher.NewsFetcher(api_key=api_key)
        request_error = news_fetcher.requests.ConnectionError(
            "Connection lost for "
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}&pageSize=100"
        )

        with patch.object(
            news_fetcher.requests,
            "get",
            side_effect=request_error,
        ) as mocked_get, patch.object(news_fetcher.time, "sleep") as mocked_sleep:
            with self.assertRaises(news_fetcher.NewsFetchError) as raised:
                fetcher._fetch(
                    "https://newsapi.org/v2/top-headlines",
                    {"country": "us", "apiKey": api_key, "pageSize": 100},
                )

        message = str(raised.exception)
        self.assertIn("Failed to fetch articles from NewsAPI:", message)
        self.assertNotIn(api_key, message)
        self.assertIn("apiKey=[redacted]", message)
        self.assertEqual(mocked_get.call_count, 3)
        self.assertEqual([call.args[0] for call in mocked_sleep.call_args_list], [1, 2])
        self.assertEqual(fetcher.request_count, 3)

    def test_fetch_all_categories_raises_when_later_category_fetch_fails(self) -> None:
        fetcher = news_fetcher.NewsFetcher(api_key="valid-key")
        general_articles = [
            {
                "original_title": "General success",
                "original_description": "First category article.",
                "source_name": "Example Source",
                "source_id": "example-source",
                "author": "Reporter",
                "url": "https://example.com/general-success",
                "image_url": "https://example.com/general-success.jpg",
                "published_at": "2026-03-11T10:00:00Z",
                "category": "general",
            }
        ]
        later_failure = news_fetcher.NewsFetchError(
            "sports category failed after general succeeded"
        )

        with patch.object(
            news_fetcher,
            "CATEGORIES",
            ["general", "sports"],
        ), patch.object(
            fetcher,
            "fetch_top_headlines",
            side_effect=[general_articles, later_failure],
        ) as mocked_fetch_top_headlines:
            with self.assertRaises(news_fetcher.NewsFetchError) as raised:
                fetcher.fetch_all_categories()

        self.assertIs(raised.exception, later_failure)
        self.assertEqual(mocked_fetch_top_headlines.call_count, 2)

    def test_process_new_articles_leaves_db_empty_when_category_fetch_aborts(self) -> None:
        session = database.SessionLocal()
        failure = news_fetcher.NewsFetchError("sports category failed after general succeeded")

        try:
            with patch.object(
                article_processor.NewsFetcher,
                "fetch_all_categories",
                side_effect=failure,
            ):
                processor = article_processor.ArticleProcessor()

                with self.assertRaises(news_fetcher.NewsFetchError):
                    processor.process_new_articles(db=session, api_key="valid-key")

            self.assertEqual(session.query(models.Article).count(), 0)
        finally:
            session.close()

    def test_process_new_articles_excludes_sports_from_persisted_good_news(self) -> None:
        session = database.SessionLocal()
        fetched_articles = [
            {
                "original_title": "Sports win",
                "original_description": "A sports story.",
                "source_name": "Sports Desk",
                "source_id": "sports-desk",
                "author": "Reporter One",
                "url": "https://example.com/sports-win",
                "image_url": "https://example.com/sports-win.jpg",
                "published_at": "2026-03-11T10:00:00Z",
                "category": "sports",
            },
            {
                "original_title": "Business investment",
                "original_description": "A business story.",
                "source_name": "Markets Desk",
                "source_id": "markets-desk",
                "author": "Reporter Two",
                "url": "https://example.com/business-investment",
                "image_url": "https://example.com/business-investment.jpg",
                "published_at": "2026-03-11T11:00:00Z",
                "category": "business",
            },
        ]
        analysis_result = {
            "rewritten_title": "Calmer headline",
            "tldr": "Summary.",
            "needs_rewrite": True,
            "sentiment": "positive",
            "sentiment_score": 0.8,
            "is_good_news": True,
        }

        try:
            with patch.object(
                article_processor.NewsFetcher,
                "fetch_all_categories",
                return_value=fetched_articles,
            ), patch.object(
                article_processor.AIService,
                "__init__",
                lambda self: None,
            ), patch.object(
                article_processor.AIService,
                "analyse_article",
                return_value=analysis_result,
            ):
                processor = article_processor.ArticleProcessor()
                summary = processor.process_new_articles(db=session, api_key="valid-key")

            self.assertEqual(
                summary,
                {
                    "new_articles": 2,
                    "processed_articles": 2,
                    "failed_articles": 0,
                },
            )

            sports_article = session.query(models.Article).filter_by(url="https://example.com/sports-win").one()
            business_article = (
                session.query(models.Article)
                .filter_by(url="https://example.com/business-investment")
                .one()
            )

            self.assertFalse(sports_article.is_good_news)
            self.assertTrue(business_article.is_good_news)
        finally:
            session.close()

    def test_process_new_articles_excludes_detected_politics_from_persisted_good_news(self) -> None:
        session = database.SessionLocal()
        fetched_articles = [
            {
                "original_title": "Senate advances housing package",
                "original_description": "Lawmakers described the vote as bipartisan progress.",
                "source_name": "Capitol Desk",
                "source_id": "capitol-desk",
                "author": "Reporter One",
                "url": "https://example.com/senate-housing-package",
                "image_url": "https://example.com/senate-housing-package.jpg",
                "published_at": "2026-03-11T10:00:00Z",
                "category": "general",
            },
            {
                "original_title": "Community garden expands",
                "original_description": "Volunteers opened new plots for families.",
                "source_name": "Metro Desk",
                "source_id": "metro-desk",
                "author": "Reporter Two",
                "url": "https://example.com/community-garden-expands",
                "image_url": "https://example.com/community-garden-expands.jpg",
                "published_at": "2026-03-11T11:00:00Z",
                "category": "general",
            },
        ]
        analysis_result = {
            "rewritten_title": "Calmer headline",
            "tldr": "Summary.",
            "needs_rewrite": True,
            "sentiment": "positive",
            "sentiment_score": 0.8,
            "is_good_news": True,
        }

        try:
            with patch.object(
                article_processor.NewsFetcher,
                "fetch_all_categories",
                return_value=fetched_articles,
            ), patch.object(
                article_processor.AIService,
                "__init__",
                lambda self: None,
            ), patch.object(
                article_processor.AIService,
                "analyse_article",
                return_value=analysis_result,
            ):
                processor = article_processor.ArticleProcessor()
                summary = processor.process_new_articles(db=session, api_key="valid-key")

            self.assertEqual(
                summary,
                {
                    "new_articles": 2,
                    "processed_articles": 2,
                    "failed_articles": 0,
                },
            )

            politics_article = (
                session.query(models.Article)
                .filter_by(url="https://example.com/senate-housing-package")
                .one()
            )
            community_article = (
                session.query(models.Article)
                .filter_by(url="https://example.com/community-garden-expands")
                .one()
            )

            self.assertFalse(politics_article.is_good_news)
            self.assertTrue(community_article.is_good_news)
        finally:
            session.close()

    def test_process_new_articles_excludes_guardrailed_content_from_persisted_good_news(self) -> None:
        session = database.SessionLocal()
        fetched_articles = [
            {
                "original_title": "Death toll rises in earthquake aftermath",
                "original_description": "Grief overwhelms survivors as mourning begins.",
                "source_name": "World Desk",
                "source_id": "world-desk",
                "author": "Reporter One",
                "url": "https://example.com/death-toll-earthquake",
                "image_url": "https://example.com/death-toll-earthquake.jpg",
                "published_at": "2026-03-11T10:00:00Z",
                "category": "general",
            },
            {
                "original_title": "Community garden expands across the city",
                "original_description": "Volunteers opened new plots for families.",
                "source_name": "Metro Desk",
                "source_id": "metro-desk",
                "author": "Reporter Two",
                "url": "https://example.com/community-garden-guardrail-test",
                "image_url": "https://example.com/community-garden-guardrail-test.jpg",
                "published_at": "2026-03-11T11:00:00Z",
                "category": "general",
            },
        ]
        analysis_result = {
            "rewritten_title": "Calmer headline",
            "tldr": "Summary.",
            "needs_rewrite": True,
            "sentiment": "positive",
            "sentiment_score": 0.8,
            "is_good_news": True,
        }

        try:
            with patch.object(
                article_processor.NewsFetcher,
                "fetch_all_categories",
                return_value=fetched_articles,
            ), patch.object(
                article_processor.AIService,
                "__init__",
                lambda self: None,
            ), patch.object(
                article_processor.AIService,
                "analyse_article",
                return_value=analysis_result,
            ):
                processor = article_processor.ArticleProcessor()
                summary = processor.process_new_articles(db=session, api_key="valid-key")

            self.assertEqual(
                summary,
                {
                    "new_articles": 2,
                    "processed_articles": 2,
                    "failed_articles": 0,
                },
            )

            guardrailed_article = (
                session.query(models.Article)
                .filter_by(url="https://example.com/death-toll-earthquake")
                .one()
            )
            safe_article = (
                session.query(models.Article)
                .filter_by(url="https://example.com/community-garden-guardrail-test")
                .one()
            )

            self.assertFalse(guardrailed_article.is_good_news)
            self.assertTrue(safe_article.is_good_news)
        finally:
            session.close()

    def test_background_refresh_marks_failed_when_news_fetch_raises(self) -> None:
        session = _DummySession()
        error = news_fetcher.NewsFetchError("NewsAPI returned an error: quota exceeded")

        with patch.object(database, "SessionLocal", return_value=session), patch.object(
            article_processor.ArticleProcessor,
            "process_new_articles",
            side_effect=error,
        ):
            with self.assertRaises(news_fetcher.NewsFetchError):
                article_processor.process_new_articles_background("valid-key")

        status = refresh_tracker_module.refresh_tracker.snapshot()
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["message"], "NewsAPI returned an error: quota exceeded")
        self.assertEqual(status["new_articles"], 0)
        self.assertEqual(status["processed_articles"], 0)
        self.assertEqual(status["failed_articles"], 0)
        self.assertIsNotNone(status["started_at"])
        self.assertIsNotNone(status["finished_at"])
        self.assertTrue(session.closed)


ai_service_module = importlib.import_module("src.backend.services.ai_service")


class TestAIServiceValidation(unittest.TestCase):
    """Tests for AIService._validate_result normalization."""

    def _validate(self, result: dict) -> dict:
        ai_service_module.AIService._validate_result(None, result)
        return result

    def test_needs_rewrite_cleared_when_rewritten_title_is_none(self) -> None:
        result = self._validate({
            "sentiment": "negative",
            "sentiment_score": -0.5,
            "needs_rewrite": True,
            "rewritten_title": None,
            "rewrite_reason": "Sensationalized",
            "tldr": "Summary.",
            "is_good_news": False,
        })
        self.assertFalse(result["needs_rewrite"])
        self.assertIsNone(result["rewritten_title"])

    def test_needs_rewrite_cleared_when_rewritten_title_is_empty(self) -> None:
        result = self._validate({
            "sentiment": "negative",
            "sentiment_score": -0.5,
            "needs_rewrite": True,
            "rewritten_title": "   ",
            "rewrite_reason": "Sensationalized",
            "tldr": "Summary.",
            "is_good_news": False,
        })
        self.assertFalse(result["needs_rewrite"])
        self.assertIsNone(result["rewritten_title"])

    def test_needs_rewrite_preserved_when_rewritten_title_present(self) -> None:
        result = self._validate({
            "sentiment": "negative",
            "sentiment_score": -0.5,
            "needs_rewrite": True,
            "rewritten_title": "A calmer headline",
            "rewrite_reason": "Sensationalized",
            "tldr": "Summary.",
            "is_good_news": False,
        })
        self.assertTrue(result["needs_rewrite"])
        self.assertEqual(result["rewritten_title"], "A calmer headline")


if __name__ == "__main__":
    unittest.main()
