"""
@author Tom Butler
@date 2025-10-25
@description Unit tests for content validation and deduplication.
"""

import pytest
from datetime import datetime, timedelta
from scrapers.content_validator import ContentValidator


class TestContentValidator:
    """Test content validation and deduplication functionality."""

    def setup_method(self):
        """Set up test instance before each test."""
        self.validator = ContentValidator()
        self.validator.reset()

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        assert hasattr(self.validator, 'seen_urls')
        assert hasattr(self.validator, 'seen_titles')
        assert hasattr(self.validator, 'stats')
        assert len(self.validator.seen_urls) == 0

    def test_validate_valid_article(self, sample_article):
        """Test validation of valid article passes."""
        is_valid, reason = self.validator.validate_article(sample_article)
        assert is_valid is True
        assert reason == "Valid"
        assert self.validator.stats['valid_articles'] == 1

    def test_detect_duplicate_url(self, sample_article):
        """Test detection of duplicate URLs."""
        # First article should be valid
        is_valid1, _ = self.validator.validate_article(sample_article)
        assert is_valid1 is True

        # Second identical article should be rejected
        is_valid2, reason2 = self.validator.validate_article(sample_article)
        assert is_valid2 is False
        assert "Duplicate URL" in reason2
        assert self.validator.stats['duplicates_url'] == 1

    def test_detect_duplicate_title(self):
        """Test detection of highly similar titles."""
        article1 = {
            "title": "Breaking News: Major Event Occurs",
            "url": "https://example.com/1",
            "published_date": datetime.now().isoformat()
        }

        article2 = {
            "title": "Breaking News: Major Event Occurs",  # Identical title
            "url": "https://example.com/2",  # Different URL
            "published_date": datetime.now().isoformat()
        }

        is_valid1, _ = self.validator.validate_article(article1)
        assert is_valid1 is True

        is_valid2, reason2 = self.validator.validate_article(article2, title_similarity_threshold=0.95)
        assert is_valid2 is False
        assert "Duplicate title" in reason2
        assert self.validator.stats['duplicates_title'] == 1

    def test_reject_missing_required_fields(self):
        """Test rejection of articles with missing required fields."""
        # Missing title
        article_no_title = {
            "url": "https://example.com/test",
            "published_date": datetime.now().isoformat()
        }
        is_valid, reason = self.validator.validate_article(article_no_title)
        assert is_valid is False
        assert "Missing required field" in reason

        # Reset for next test
        self.validator.reset()

        # Missing URL
        article_no_url = {
            "title": "Test Article",
            "published_date": datetime.now().isoformat()
        }
        is_valid, reason = self.validator.validate_article(article_no_url)
        assert is_valid is False
        assert "Missing required field" in reason

    def test_reject_old_articles(self):
        """Test rejection of articles older than max age."""
        old_article = {
            "title": "Old News Article",
            "url": "https://example.com/old",
            "published_date": (datetime.now() - timedelta(days=10)).isoformat()
        }

        is_valid, reason = self.validator.validate_article(old_article, max_age_days=7)
        assert is_valid is False
        assert "too old" in reason.lower()
        assert self.validator.stats['invalid_old_articles'] == 1

    def test_allow_recent_articles(self):
        """Test recent articles pass age validation."""
        recent_article = {
            "title": "Recent News Article",
            "url": "https://example.com/recent",
            "published_date": (datetime.now() - timedelta(days=3)).isoformat()
        }

        is_valid, reason = self.validator.validate_article(recent_article, max_age_days=7)
        assert is_valid is True

    def test_validate_multiple_articles(self, sample_articles_list):
        """Test batch validation of multiple articles."""
        valid_articles = self.validator.validate_articles(sample_articles_list, max_age_days=7)

        # Should filter out old articles (> 7 days)
        assert len(valid_articles) < len(sample_articles_list)
        assert len(valid_articles) == 7  # Only articles 0-6 are < 7 days old

    def test_similarity_threshold(self):
        """Test custom similarity threshold for title matching."""
        article1 = {
            "title": "Technology News Update Today",
            "url": "https://example.com/1",
            "published_date": datetime.now().isoformat()
        }

        article2 = {
            "title": "Technology News Update Tomorrow",  # Very similar
            "url": "https://example.com/2",
            "published_date": datetime.now().isoformat()
        }

        # Add first article
        self.validator.validate_article(article1)

        # With high threshold, should be detected as duplicate
        is_valid_high, _ = self.validator.validate_article(article2, title_similarity_threshold=0.7)
        assert is_valid_high is False

        # Reset and try with low threshold
        self.validator.reset()
        self.validator.validate_article(article1)
        is_valid_low, _ = self.validator.validate_article(article2, title_similarity_threshold=0.95)
        assert is_valid_low is True  # Should pass with stricter threshold

    def test_reset_functionality(self, sample_article):
        """Test reset clears all state."""
        self.validator.validate_article(sample_article)
        assert len(self.validator.seen_urls) > 0
        assert self.validator.stats['total_checked'] > 0

        self.validator.reset()
        assert len(self.validator.seen_urls) == 0
        assert len(self.validator.seen_titles) == 0
        assert self.validator.stats['total_checked'] == 0

    def test_statistics_tracking(self, sample_articles_list):
        """Test statistics are tracked correctly."""
        self.validator.validate_articles(sample_articles_list, max_age_days=7)

        stats = self.validator.get_stats()
        assert stats['total_checked'] == len(sample_articles_list)
        assert stats['valid_articles'] > 0
        assert stats['invalid_old_articles'] > 0
        assert stats['total_checked'] == (stats['valid_articles'] +
                                           stats['duplicates_url'] +
                                           stats['duplicates_title'] +
                                           stats['invalid_missing_fields'] +
                                           stats['invalid_old_articles'])

    def test_empty_article_list(self):
        """Test handling of empty article list."""
        valid_articles = self.validator.validate_articles([])
        assert len(valid_articles) == 0

    def test_whitespace_handling_in_urls(self):
        """Test URLs with whitespace are handled correctly."""
        article1 = {
            "title": "Test Article",
            "url": "  https://example.com/test  ",  # URL with whitespace
            "published_date": datetime.now().isoformat()
        }

        article2 = {
            "title": "Test Article 2",
            "url": "https://example.com/test",  # Same URL without whitespace
            "published_date": datetime.now().isoformat()
        }

        self.validator.validate_article(article1)
        is_valid, reason = self.validator.validate_article(article2)

        # Should be detected as duplicate despite whitespace
        assert is_valid is False
        assert "Duplicate URL" in reason
