"""Tests for user-configurable content guardrails.

Run with:
    python -m unittest src.backend.tests.test_custom_guardrails -v
"""

from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "guardrails.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

database = importlib.import_module("src.backend.database")
main = importlib.import_module("src.backend.main")
models = importlib.import_module("src.backend.models")


class CustomGuardrailsTest(unittest.TestCase):
    """Tests for GET/PUT /api/settings/guardrails and custom keyword filtering."""

    @classmethod
    def setUpClass(cls) -> None:
        database.reconfigure_engine(f"sqlite:///{_DB_PATH}")
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)

        now = datetime.now(timezone.utc)
        session = database.SessionLocal()
        try:
            session.add_all(
                [
                    models.Article(
                        id="art-normal",
                        original_title="Normal everyday story",
                        original_description="Nothing controversial here.",
                        source_name="BBC News",
                        source_id="bbc-news",
                        url="https://example.com/art-normal",
                        published_at=now - timedelta(hours=1),
                        fetched_at=now,
                        was_rewritten=False,
                        original_sentiment="neutral",
                        sentiment_score=0.0,
                        is_good_news=True,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="art-crypto",
                        original_title="Bitcoin surges past new record",
                        original_description="Cryptocurrency markets rally.",
                        source_name="Reuters",
                        source_id="reuters",
                        url="https://example.com/art-crypto",
                        published_at=now - timedelta(hours=2),
                        fetched_at=now,
                        was_rewritten=False,
                        original_sentiment="positive",
                        sentiment_score=0.5,
                        is_good_news=True,
                        category="business",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="art-election",
                        original_title="New policy announced by mayor",
                        original_description="City election results spark debate.",
                        source_name="CNN",
                        source_id="cnn",
                        url="https://example.com/art-election",
                        published_at=now - timedelta(hours=3),
                        fetched_at=now,
                        was_rewritten=False,
                        original_sentiment="neutral",
                        sentiment_score=0.0,
                        is_good_news=False,
                        category="general",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="art-builtin-guardrail",
                        original_title="Bombing reported in distant region",
                        original_description="Military offensive continues.",
                        source_name="AP News",
                        source_id="ap-news",
                        url="https://example.com/art-guardrail",
                        published_at=now - timedelta(hours=4),
                        fetched_at=now,
                        was_rewritten=False,
                        original_sentiment="negative",
                        sentiment_score=-0.8,
                        is_good_news=False,
                        category="world",
                        processing_status="processed",
                    ),
                    models.Article(
                        id="art-pending",
                        original_title="Pending article about bitcoin",
                        original_description="Should not appear.",
                        source_name="Test",
                        source_id="test",
                        url="https://example.com/art-pending",
                        published_at=now,
                        fetched_at=now,
                        category="general",
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
        database.dispose_engine()
        _TEMP_DIR.cleanup()

    def _clear_custom_guardrails(self) -> None:
        """Reset custom guardrails to empty between tests."""
        self.client.put("/api/settings/guardrails", json={"keywords": []})

    def setUp(self) -> None:
        self._clear_custom_guardrails()

    # ---- Settings endpoint tests ----

    def test_get_guardrails_returns_empty_by_default(self) -> None:
        response = self.client.get("/api/settings/guardrails")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"keywords": []})

    def test_put_guardrails_stores_and_returns_keywords(self) -> None:
        response = self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin", "crypto"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"keywords": ["bitcoin", "crypto"]})

        # Verify persistence via GET.
        get_response = self.client.get("/api/settings/guardrails")
        self.assertEqual(get_response.json(), {"keywords": ["bitcoin", "crypto"]})

    def test_put_guardrails_normalizes_keywords(self) -> None:
        response = self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["  Bitcoin  ", "CRYPTO", "bitcoin", "", "  "]},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Should be lowercase, stripped, deduplicated, blanks removed.
        self.assertEqual(body["keywords"], ["bitcoin", "crypto"])

    def test_put_guardrails_limits_to_50_keywords(self) -> None:
        many_keywords = [f"keyword{i}" for i in range(60)]
        response = self.client.put(
            "/api/settings/guardrails",
            json={"keywords": many_keywords},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["keywords"]), 50)

    def test_put_guardrails_replaces_previous_keywords(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["old-word"]},
        )
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["new-word"]},
        )
        response = self.client.get("/api/settings/guardrails")
        self.assertEqual(response.json(), {"keywords": ["new-word"]})

    # ---- Article filtering tests ----

    def test_articles_without_custom_guardrails_returns_all_processed(self) -> None:
        response = self.client.get("/api/articles")
        self.assertEqual(response.status_code, 200)
        ids = [a["id"] for a in response.json()["articles"]]
        self.assertIn("art-normal", ids)
        self.assertIn("art-crypto", ids)
        self.assertIn("art-election", ids)
        self.assertNotIn("art-pending", ids)

    def test_articles_with_custom_guardrails_excludes_matching(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response = self.client.get("/api/articles")
        self.assertEqual(response.status_code, 200)
        ids = [a["id"] for a in response.json()["articles"]]
        self.assertIn("art-normal", ids)
        self.assertNotIn("art-crypto", ids)
        self.assertIn("art-election", ids)

    def test_articles_custom_guardrails_match_description(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["election"]},
        )
        response = self.client.get("/api/articles")
        ids = [a["id"] for a in response.json()["articles"]]
        self.assertNotIn("art-election", ids)
        self.assertIn("art-normal", ids)

    def test_articles_multiple_custom_keywords(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin", "election"]},
        )
        response = self.client.get("/api/articles")
        ids = [a["id"] for a in response.json()["articles"]]
        self.assertIn("art-normal", ids)
        self.assertNotIn("art-crypto", ids)
        self.assertNotIn("art-election", ids)

    def test_clearing_custom_guardrails_restores_articles(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response1 = self.client.get("/api/articles")
        self.assertNotIn("art-crypto", [a["id"] for a in response1.json()["articles"]])

        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": []},
        )
        response2 = self.client.get("/api/articles")
        self.assertIn("art-crypto", [a["id"] for a in response2.json()["articles"]])

    # ---- Good news count in stats ----

    def test_stats_good_news_count_excludes_custom_guardrailed(self) -> None:
        # art-crypto is is_good_news=True. Without custom guardrails it should count.
        response1 = self.client.get("/api/stats")
        good_news_before = response1.json()["good_news_count"]

        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response2 = self.client.get("/api/stats")
        good_news_after = response2.json()["good_news_count"]

        self.assertGreater(good_news_before, good_news_after)

    # ---- Single-article endpoint guardrails ----

    def test_single_article_returns_normal_article(self) -> None:
        response = self.client.get("/api/articles/art-normal")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "art-normal")

    def test_single_article_hides_builtin_guardrailed(self) -> None:
        response = self.client.get("/api/articles/art-builtin-guardrail")
        self.assertEqual(response.status_code, 404)

    def test_single_article_hides_custom_guardrailed(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response = self.client.get("/api/articles/art-crypto")
        self.assertEqual(response.status_code, 404)

    def test_single_article_accessible_after_clearing_custom_guardrail(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        self.assertEqual(self.client.get("/api/articles/art-crypto").status_code, 404)

        self.client.put("/api/settings/guardrails", json={"keywords": []})
        self.assertEqual(self.client.get("/api/articles/art-crypto").status_code, 200)

    # ---- Categories endpoint guardrails ----

    def test_categories_excludes_builtin_guardrailed(self) -> None:
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        categories = {c["name"]: c["count"] for c in response.json()["categories"]}
        # "world" category only has the guardrailed article, so it should be absent.
        self.assertNotIn("world", categories)

    def test_categories_excludes_custom_guardrailed(self) -> None:
        response_before = self.client.get("/api/categories")
        counts_before = {c["name"]: c["count"] for c in response_before.json()["categories"]}

        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response_after = self.client.get("/api/categories")
        counts_after = {c["name"]: c["count"] for c in response_after.json()["categories"]}

        # business category had art-crypto; should now be absent.
        self.assertIn("business", counts_before)
        self.assertNotIn("business", counts_after)

    # ---- Sources endpoint guardrails ----

    def test_sources_excludes_builtin_guardrailed(self) -> None:
        response = self.client.get("/api/sources")
        source_names = [s["source_name"] for s in response.json()["sources"]]
        # AP News only has the guardrailed article, so it should be absent.
        self.assertNotIn("AP News", source_names)

    def test_sources_excludes_custom_guardrailed(self) -> None:
        response_before = self.client.get("/api/sources")
        names_before = [s["source_name"] for s in response_before.json()["sources"]]

        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response_after = self.client.get("/api/sources")
        names_after = [s["source_name"] for s in response_after.json()["sources"]]

        # Reuters only has art-crypto; should now be absent.
        self.assertIn("Reuters", names_before)
        self.assertNotIn("Reuters", names_after)

    # ---- Stats endpoint guardrails ----

    def test_stats_total_excludes_builtin_guardrailed(self) -> None:
        response = self.client.get("/api/stats")
        data = response.json()
        # 3 non-guardrailed processed articles (normal, crypto, election).
        # art-builtin-guardrail should be excluded.
        self.assertEqual(data["total_articles"], 3)

    def test_stats_total_excludes_custom_guardrailed(self) -> None:
        self.client.put(
            "/api/settings/guardrails",
            json={"keywords": ["bitcoin"]},
        )
        response = self.client.get("/api/stats")
        data = response.json()
        # art-crypto excluded by custom guardrail → 2 remain.
        self.assertEqual(data["total_articles"], 2)


if __name__ == "__main__":
    unittest.main()
