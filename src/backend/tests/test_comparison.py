"""Tests for article comparison grouping and API endpoint.

Run with:
    python -m unittest src.backend.tests.test_comparison -v
"""

from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "comparison.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"

database = importlib.import_module("src.backend.database")
main = importlib.import_module("src.backend.main")
models = importlib.import_module("src.backend.models")
ai_service = importlib.import_module("src.backend.services.ai_service")
title_similarity = importlib.import_module("src.backend.utils.title_similarity")


class TitleSimilarityUnitTest(unittest.TestCase):
    """Unit tests for fuzzy title matching utilities."""

    def test_normalize_removes_stop_words_and_punctuation(self):
        words = title_similarity._normalize_title(
            "The President signs a new trade deal with China!"
        )
        self.assertIn("president", words)
        self.assertIn("signs", words)
        self.assertIn("trade", words)
        self.assertIn("deal", words)
        self.assertIn("china", words)
        # Stop words and short words removed
        self.assertNotIn("the", words)
        self.assertNotIn("a", words)
        self.assertNotIn("with", words)

    def test_jaccard_identical_sets(self):
        s = {"president", "signs", "trade", "deal"}
        self.assertAlmostEqual(title_similarity._jaccard(s, s), 1.0)

    def test_jaccard_disjoint_sets(self):
        a = {"president", "trade"}
        b = {"football", "score"}
        self.assertAlmostEqual(title_similarity._jaccard(a, b), 0.0)

    def test_jaccard_partial_overlap(self):
        a = {"president", "signs", "trade", "deal"}
        b = {"president", "announces", "trade", "agreement"}
        # intersection: president, trade (2), union: 6
        self.assertAlmostEqual(title_similarity._jaccard(a, b), 2 / 6)

    def test_jaccard_empty_sets(self):
        self.assertAlmostEqual(title_similarity._jaccard(set(), {"a"}), 0.0)
        self.assertAlmostEqual(title_similarity._jaccard(set(), set()), 0.0)

    def test_group_articles_groups_similar_titles(self):
        """Articles with similar titles should be grouped together."""
        now = datetime.now(timezone.utc)
        articles = [
            _make_article("a1", "UK Prime Minister announces new climate policy", "BBC News", "gb", now),
            _make_article("a2", "Prime Minister unveils climate policy plan", "Reuters", "us", now - timedelta(hours=1)),
            _make_article("a3", "Football scores from the weekend matches", "ESPN", "us", now - timedelta(hours=2)),
            _make_article("a4", "Climate policy announcement by Prime Minister draws praise", "CNN", "us", now - timedelta(hours=1)),
        ]
        groups = title_similarity.group_articles(articles)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].article_ids), 3)
        self.assertIn("a1", groups[0].article_ids)
        self.assertIn("a2", groups[0].article_ids)
        self.assertIn("a4", groups[0].article_ids)

    def test_group_articles_no_groups_for_dissimilar(self):
        """Completely different articles should not form groups."""
        now = datetime.now(timezone.utc)
        articles = [
            _make_article("a1", "UK Prime Minister announces climate policy", "BBC News", "gb", now),
            _make_article("a2", "Apple releases new iPhone model today", "TechCrunch", "us", now),
            _make_article("a3", "Local bakery wins national award", "Local News", "gb", now),
        ]
        groups = title_similarity.group_articles(articles)
        self.assertEqual(len(groups), 0)

    def test_group_articles_preserves_source_and_country_info(self):
        """Groups should track distinct sources and countries."""
        now = datetime.now(timezone.utc)
        articles = [
            _make_article("a1", "President signs major trade deal with Europe", "BBC News", "gb", now),
            _make_article("a2", "President signs historic trade deal with European nations", "CNN", "us", now),
        ]
        groups = title_similarity.group_articles(articles)
        self.assertEqual(len(groups), 1)
        self.assertIn("BBC News", groups[0].sources)
        self.assertIn("CNN", groups[0].sources)
        self.assertIn("gb", groups[0].countries)
        self.assertIn("us", groups[0].countries)

    def test_group_articles_skips_short_titles(self):
        """Titles with fewer than 2 significant words should be skipped."""
        now = datetime.now(timezone.utc)
        articles = [
            _make_article("a1", "News", "BBC", "gb", now),
            _make_article("a2", "News", "CNN", "us", now),
        ]
        groups = title_similarity.group_articles(articles)
        self.assertEqual(len(groups), 0)

    def test_group_articles_sort_prefers_country_diversity(self):
        """Mixed-country groups must sort before larger single-country groups."""
        now = datetime.now(timezone.utc)
        articles = [
            # US-only group of 4 — would come first under the old size-only sort.
            _make_article(
                "tech1",
                "Startup unveils quantum computing chip breakthrough",
                "Wired",
                "us",
                now,
            ),
            _make_article(
                "tech2",
                "Quantum computing startup claims chip breakthrough",
                "Verge",
                "us",
                now - timedelta(hours=1),
            ),
            _make_article(
                "tech3",
                "Quantum computing chip breakthrough announced by startup",
                "Ars Technica",
                "us",
                now - timedelta(hours=2),
            ),
            _make_article(
                "tech4",
                "Breakthrough quantum computing chip revealed by startup",
                "MIT",
                "us",
                now - timedelta(hours=3),
            ),
            # Mixed-country group of 2 — must come first under the new sort.
            _make_article(
                "eq1",
                "Earthquake strikes coastal city causing widespread damage",
                "BBC News",
                "gb",
                now - timedelta(hours=4),
            ),
            _make_article(
                "eq2",
                "Coastal city earthquake causes widespread damage",
                "CNN",
                "us",
                now - timedelta(hours=5),
            ),
        ]

        groups = title_similarity.group_articles(articles)

        self.assertEqual(len(groups), 2)
        first_group, second_group = groups
        self.assertEqual(sorted(first_group.countries), ["gb", "us"])
        self.assertIn("eq1", first_group.article_ids)
        self.assertIn("eq2", first_group.article_ids)
        self.assertEqual(second_group.countries, ["us"])
        self.assertEqual(len(second_group.article_ids), 4)

    def test_group_articles_uses_transitive_similarity_chain(self):
        """A~B and B~C should form one group even when A !~ C."""
        now = datetime.now(timezone.utc)
        articles = [
            _make_article(
                "a1",
                "Earthquake hits coastal city causing widespread damage",
                "BBC News",
                "gb",
                now,
            ),
            _make_article(
                "a2",
                "Coastal city earthquake prompts rescue shelters",
                "Reuters",
                "us",
                now - timedelta(minutes=10),
            ),
            _make_article(
                "a3",
                "Earthquake survivors seek aid in rescue shelters",
                "CNN",
                "us",
                now - timedelta(minutes=20),
            ),
        ]

        groups = title_similarity.group_articles(articles)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].article_ids, ["a1", "a2", "a3"])


class ComparisonEndpointTest(unittest.TestCase):
    """Integration tests for GET /api/comparison."""

    @classmethod
    def setUpClass(cls) -> None:
        database.reconfigure_engine(f"sqlite:///{_DB_PATH}")
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)

        now = datetime.now(timezone.utc)
        session = database.SessionLocal()
        try:
            session.add_all([
                models.Article(
                    id="comp-1",
                    original_title="Major earthquake strikes coastal city causing widespread damage",
                    rewritten_title="Earthquake hits coastal city",
                    source_name="BBC News",
                    source_id="bbc-news",
                    url="https://example.com/comp-1",
                    published_at=now - timedelta(hours=2),
                    fetched_at=now,
                    original_sentiment="negative",
                    sentiment_score=-0.5,
                    country="gb",
                    category="general",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-2",
                    original_title="Powerful earthquake hits coastal city with major damage reported",
                    rewritten_title="Coastal city earthquake causes damage",
                    source_name="CNN",
                    source_id="cnn",
                    url="https://example.com/comp-2",
                    published_at=now - timedelta(hours=1),
                    fetched_at=now,
                    original_sentiment="negative",
                    sentiment_score=-0.6,
                    country="us",
                    category="general",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-3",
                    original_title="Tech company launches revolutionary AI assistant product",
                    source_name="TechCrunch",
                    source_id="techcrunch",
                    url="https://example.com/comp-3",
                    published_at=now,
                    fetched_at=now,
                    original_sentiment="positive",
                    sentiment_score=0.8,
                    country="us",
                    category="technology",
                    processing_status="processed",
                ),
                # Pending article should be excluded
                models.Article(
                    id="comp-4",
                    original_title="Earthquake aftermath in coastal city",
                    source_name="Reuters",
                    source_id="reuters",
                    url="https://example.com/comp-4",
                    country="gb",
                    processing_status="pending",
                ),
                # Sports articles — should be excluded from comparison by category filter
                models.Article(
                    id="comp-sports-1",
                    original_title="Lakers defeat Warriors in overtime thriller",
                    source_name="ESPN",
                    source_id="espn",
                    url="https://example.com/comp-sports-1",
                    published_at=now - timedelta(hours=3),
                    fetched_at=now,
                    country="us",
                    category="sports",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-sports-2",
                    original_title="Warriors fall to Lakers in thrilling overtime finish",
                    source_name="NBA.com",
                    source_id="nba",
                    url="https://example.com/comp-sports-2",
                    published_at=now - timedelta(hours=3),
                    fetched_at=now,
                    country="us",
                    category="sports",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-sports-3",
                    original_title="Overtime Lakers edge out Warriors in thriller",
                    source_name="Sports Illustrated",
                    source_id="si",
                    url="https://example.com/comp-sports-3",
                    published_at=now - timedelta(hours=3),
                    fetched_at=now,
                    country="us",
                    category="sports",
                    processing_status="processed",
                ),
                # Entertainment articles — should also be excluded by category filter
                models.Article(
                    id="comp-ent-1",
                    original_title="Marvel superhero blockbuster breaks opening weekend records",
                    source_name="Variety",
                    source_id="variety",
                    url="https://example.com/comp-ent-1",
                    published_at=now - timedelta(hours=4),
                    fetched_at=now,
                    country="us",
                    category="entertainment",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-ent-2",
                    original_title="Superhero blockbuster shatters opening weekend records",
                    source_name="Hollywood Reporter",
                    source_id="hollywood",
                    url="https://example.com/comp-ent-2",
                    published_at=now - timedelta(hours=4),
                    fetched_at=now,
                    country="us",
                    category="entertainment",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-ent-3",
                    original_title="Marvel blockbuster opening weekend breaks box office records",
                    source_name="Deadline",
                    source_id="deadline",
                    url="https://example.com/comp-ent-3",
                    published_at=now - timedelta(hours=4),
                    fetched_at=now,
                    country="us",
                    category="entertainment",
                    processing_status="processed",
                ),
                # US-only tech group of 4 — larger than the earthquake group, but
                # single-country, so it must sort below the earthquake group after
                # the country-diversity sort change.
                models.Article(
                    id="comp-tech-1",
                    original_title="Startup unveils quantum computing chip breakthrough",
                    source_name="Wired",
                    source_id="wired",
                    url="https://example.com/comp-tech-1",
                    published_at=now - timedelta(hours=5),
                    fetched_at=now,
                    country="us",
                    category="technology",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-tech-2",
                    original_title="Quantum computing startup claims chip breakthrough",
                    source_name="The Verge",
                    source_id="verge",
                    url="https://example.com/comp-tech-2",
                    published_at=now - timedelta(hours=5),
                    fetched_at=now,
                    country="us",
                    category="technology",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-tech-3",
                    original_title="Quantum computing chip breakthrough announced by startup",
                    source_name="Ars Technica",
                    source_id="ars",
                    url="https://example.com/comp-tech-3",
                    published_at=now - timedelta(hours=5),
                    fetched_at=now,
                    country="us",
                    category="technology",
                    processing_status="processed",
                ),
                models.Article(
                    id="comp-tech-4",
                    original_title="Breakthrough quantum computing chip revealed by startup",
                    source_name="MIT Tech Review",
                    source_id="mit",
                    url="https://example.com/comp-tech-4",
                    published_at=now - timedelta(hours=5),
                    fetched_at=now,
                    country="us",
                    category="technology",
                    processing_status="processed",
                ),
            ])
            session.commit()
        finally:
            session.close()

        cls.client = TestClient(main.app)

    def test_comparison_returns_grouped_articles(self):
        resp = self.client.get("/api/comparison")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("groups", data)
        self.assertIn("total_groups", data)
        self.assertGreaterEqual(data["total_groups"], 1)

        # The earthquake articles should be grouped
        earthquake_group = None
        for group in data["groups"]:
            ids = [a["id"] for a in group["articles"]]
            if "comp-1" in ids and "comp-2" in ids:
                earthquake_group = group
                break

        self.assertIsNotNone(earthquake_group, "Earthquake articles should be grouped")
        self.assertEqual(len(earthquake_group["articles"]), 2)
        self.assertIn("BBC News", earthquake_group["sources"])
        self.assertIn("CNN", earthquake_group["sources"])
        self.assertIn("gb", earthquake_group["countries"])
        self.assertIn("us", earthquake_group["countries"])

    def test_comparison_excludes_pending_articles(self):
        resp = self.client.get("/api/comparison")
        data = resp.json()
        all_ids = [
            a["id"]
            for group in data["groups"]
            for a in group["articles"]
        ]
        self.assertNotIn("comp-4", all_ids)

    def test_comparison_articles_have_expected_fields(self):
        resp = self.client.get("/api/comparison")
        data = resp.json()
        if data["total_groups"] > 0:
            article = data["groups"][0]["articles"][0]
            for field in ["id", "original_title", "source_name", "country", "url"]:
                self.assertIn(field, article)

    def test_comparison_excludes_sports_and_entertainment_articles(self):
        """Sports and entertainment articles should never appear in /api/comparison."""
        resp = self.client.get("/api/comparison")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        all_ids = {
            article["id"]
            for group in data["groups"]
            for article in group["articles"]
        }
        for sports_id in ("comp-sports-1", "comp-sports-2", "comp-sports-3"):
            self.assertNotIn(
                sports_id,
                all_ids,
                f"Sports article {sports_id} must be excluded from comparison",
            )
        for ent_id in ("comp-ent-1", "comp-ent-2", "comp-ent-3"):
            self.assertNotIn(
                ent_id,
                all_ids,
                f"Entertainment article {ent_id} must be excluded from comparison",
            )

    def test_comparison_prioritises_multi_country_groups(self):
        """A mixed-country group must sort before a larger single-country group."""
        resp = self.client.get("/api/comparison")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_groups"], 2)

        first_group = data["groups"][0]
        first_ids = [a["id"] for a in first_group["articles"]]
        # The earthquake group (gb + us) should come first despite being smaller
        # than the 4-article quantum computing tech group (us only).
        self.assertGreaterEqual(len(first_group["countries"]), 2)
        self.assertIn("comp-1", first_ids)
        self.assertIn("comp-2", first_ids)


class ComparisonAnalysisValidationTest(unittest.TestCase):
    """Unit tests for comparison analysis AI validation."""

    def test_validate_comparison_result_fills_defaults(self):
        svc = ai_service.AIService.__new__(ai_service.AIService)
        result: dict = {}
        svc._validate_comparison_result(result)
        self.assertEqual(result["summary"], "Analysis unavailable.")
        self.assertEqual(result["framing_differences"], [])
        self.assertEqual(result["source_tones"], [])

    def test_validate_comparison_result_keeps_valid_data(self):
        svc = ai_service.AIService.__new__(ai_service.AIService)
        result = {
            "summary": "A story about trade.",
            "framing_differences": ["BBC emphasises impact", "CNN focuses on politics"],
            "source_tones": [
                {"source_name": "BBC News", "country": "gb", "tone": "Measured"},
                {"source_name": "CNN", "country": "us", "tone": "Urgent"},
            ],
        }
        svc._validate_comparison_result(result)
        self.assertEqual(result["summary"], "A story about trade.")
        self.assertEqual(len(result["framing_differences"]), 2)
        self.assertEqual(len(result["source_tones"]), 2)

    def test_validate_comparison_result_filters_bad_tones(self):
        svc = ai_service.AIService.__new__(ai_service.AIService)
        result = {
            "summary": "Story.",
            "framing_differences": ["diff"],
            "source_tones": [
                {"source_name": "BBC", "country": "gb", "tone": "Calm"},
                "not a dict",
                {"source_name": "CNN"},  # missing country and tone
            ],
        }
        svc._validate_comparison_result(result)
        self.assertEqual(len(result["source_tones"]), 1)
        self.assertEqual(result["source_tones"][0]["source_name"], "BBC")

    def test_analyse_comparison_group_without_api_key(self):
        """When OPENAI_API_KEY is empty, returns comparison defaults."""
        svc = ai_service.AIService.__new__(ai_service.AIService)
        svc.client = None
        svc.model = "gpt-4o-mini"
        articles = [
            {"original_title": "Title 1", "source_name": "BBC", "country": "gb",
             "original_description": "Desc 1", "original_sentiment": "negative"},
            {"original_title": "Title 2", "source_name": "CNN", "country": "us",
             "original_description": "Desc 2", "original_sentiment": "neutral"},
        ]
        result = svc.analyse_comparison_group(articles)
        self.assertEqual(result["summary"], "Analysis unavailable.")
        self.assertEqual(result["framing_differences"], [])
        self.assertEqual(result["source_tones"], [])


class ComparisonAnalyseEndpointTest(unittest.TestCase):
    """Integration tests for POST /api/comparison/analyse."""

    MOCK_AI_RESPONSE = {
        "summary": "An earthquake struck a coastal city causing major damage.",
        "framing_differences": [
            "BBC uses 'strikes' suggesting sudden impact while CNN uses 'hits' with emphasis on damage reports",
            "CNN quantifies damage as 'major' while BBC describes it as 'widespread'",
        ],
        "source_tones": [
            {"source_name": "BBC News", "country": "gb", "tone": "Measured and factual, focusing on the event itself."},
            {"source_name": "CNN", "country": "us", "tone": "More urgent, emphasising the scale of damage."},
        ],
    }

    @classmethod
    def setUpClass(cls) -> None:
        database.reconfigure_engine(f"sqlite:///{_DB_PATH}")
        database.Base.metadata.create_all(bind=database.engine)

        now = datetime.now(timezone.utc)
        session = database.SessionLocal()
        try:
            # Ensure the test articles exist (idempotent with ComparisonEndpointTest)
            existing = {
                r[0]
                for r in session.query(models.Article.id)
                .filter(
                    models.Article.id.in_(
                        [
                            "comp-1",
                            "comp-2",
                            "comp-4",
                            "comp-sports-1",
                            "comp-sports-2",
                        ]
                    )
                )
                .all()
            }
            new_rows = []
            if "comp-1" not in existing:
                new_rows.append(
                    models.Article(
                        id="comp-1",
                        original_title="Major earthquake strikes coastal city causing widespread damage",
                        rewritten_title="Earthquake hits coastal city",
                        source_name="BBC News",
                        source_id="bbc-news",
                        url="https://example.com/comp-1",
                        published_at=now - timedelta(hours=2),
                        fetched_at=now,
                        original_sentiment="negative",
                        sentiment_score=-0.5,
                        country="gb",
                        category="general",
                        processing_status="processed",
                    )
                )
            if "comp-2" not in existing:
                new_rows.append(
                    models.Article(
                        id="comp-2",
                        original_title="Powerful earthquake hits coastal city with major damage reported",
                        rewritten_title="Coastal city earthquake causes damage",
                        source_name="CNN",
                        source_id="cnn",
                        url="https://example.com/comp-2",
                        published_at=now - timedelta(hours=1),
                        fetched_at=now,
                        original_sentiment="negative",
                        sentiment_score=-0.6,
                        country="us",
                        category="general",
                        processing_status="processed",
                    )
                )
            if "comp-4" not in existing:
                new_rows.append(
                    models.Article(
                        id="comp-4",
                        original_title="Earthquake aftermath in coastal city",
                        source_name="Reuters",
                        source_id="reuters",
                        url="https://example.com/comp-4",
                        country="gb",
                        processing_status="pending",
                    )
                )
            if "comp-sports-1" not in existing:
                new_rows.append(
                    models.Article(
                        id="comp-sports-1",
                        original_title="Lakers defeat Warriors in overtime thriller",
                        source_name="ESPN",
                        source_id="espn",
                        url="https://example.com/comp-sports-1",
                        published_at=now - timedelta(hours=3),
                        fetched_at=now,
                        country="us",
                        category="sports",
                        processing_status="processed",
                    )
                )
            if "comp-sports-2" not in existing:
                new_rows.append(
                    models.Article(
                        id="comp-sports-2",
                        original_title="Warriors fall to Lakers in thrilling overtime finish",
                        source_name="NBA.com",
                        source_id="nba",
                        url="https://example.com/comp-sports-2",
                        published_at=now - timedelta(hours=3),
                        fetched_at=now,
                        country="us",
                        category="sports",
                        processing_status="processed",
                    )
                )
            if new_rows:
                session.add_all(new_rows)
                session.commit()
        finally:
            session.close()

        cls.client = TestClient(main.app)

    @patch.object(ai_service.AIService, "__init__", lambda self: None)
    @patch.object(ai_service.AIService, "analyse_comparison_group")
    def test_analyse_returns_framing_analysis(self, mock_analyse):
        mock_analyse.return_value = self.MOCK_AI_RESPONSE

        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["comp-1", "comp-2"]},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("representative_title", data)
        self.assertIn("summary", data)
        self.assertIn("framing_differences", data)
        self.assertIn("source_tones", data)
        self.assertEqual(len(data["framing_differences"]), 2)
        self.assertEqual(len(data["source_tones"]), 2)
        self.assertEqual(data["source_tones"][0]["source_name"], "BBC News")

        mock_analyse.assert_called_once()
        call_articles = mock_analyse.call_args[0][0]
        self.assertEqual(len(call_articles), 2)

    def test_analyse_rejects_single_article(self):
        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["comp-1"]},
        )
        self.assertEqual(resp.status_code, 422)

    def test_analyse_returns_404_for_missing_articles(self):
        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["nonexistent-1", "nonexistent-2"]},
        )
        self.assertEqual(resp.status_code, 404)

    def test_analyse_excludes_pending_articles(self):
        """If one ID is pending and the other processed, fewer than 2 → 404."""
        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["comp-1", "comp-4"]},
        )
        self.assertEqual(resp.status_code, 404)

    def test_analyse_rejects_excluded_category_articles(self):
        """Sports/entertainment articles must be filtered out before analysis."""
        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["comp-sports-1", "comp-sports-2"]},
        )
        self.assertEqual(resp.status_code, 404)

    @patch.object(ai_service.AIService, "__init__", lambda self: None)
    @patch.object(ai_service.AIService, "analyse_comparison_group")
    def test_analyse_representative_title_uses_rewritten(self, mock_analyse):
        """Representative title should prefer the rewritten title of the newest article."""
        mock_analyse.return_value = self.MOCK_AI_RESPONSE
        resp = self.client.post(
            "/api/comparison/analyse",
            json={"article_ids": ["comp-1", "comp-2"]},
        )
        data = resp.json()
        # comp-2 is newer (published_at - 1h vs -2h) and has rewritten_title
        self.assertEqual(data["representative_title"], "Coastal city earthquake causes damage")


def _make_article(
    article_id: str,
    title: str,
    source: str,
    country: str,
    published_at: datetime,
) -> models.Article:
    """Create an in-memory Article for unit tests (not persisted)."""
    return models.Article(
        id=article_id,
        original_title=title,
        source_name=source,
        source_id=source.lower().replace(" ", "-"),
        url=f"https://example.com/{article_id}",
        published_at=published_at,
        country=country,
        processing_status="processed",
    )


if __name__ == "__main__":
    unittest.main()
