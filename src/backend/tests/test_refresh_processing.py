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
news_fetcher = importlib.import_module("src.backend.services.news_fetcher")
refresh_tracker_module = importlib.import_module("src.backend.services.refresh_tracker")


class _DummySession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class RefreshProcessingRegressionTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        _TEMP_DIR.cleanup()

    def setUp(self) -> None:
        refresh_tracker_module.refresh_tracker.reset()

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


if __name__ == "__main__":
    unittest.main()
