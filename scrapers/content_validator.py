"""
@author Tom Butler
@date 2025-10-25
@description Content validator for deduplication and quality assurance.
             Ensures articles meet quality standards before processing.
"""

import sys
sys.path.append('..')

from datetime import datetime, timedelta
from logger_config import setup_logger
from difflib import SequenceMatcher

logger = setup_logger("NewsPerspective.ContentValidator")


class ContentValidator:
    """Validates and deduplicates news articles."""

    def __init__(self):
        """Initialise content validator."""
        self.seen_urls = set()
        self.seen_titles = []
        self.stats = {
            'total_checked': 0,
            'duplicates_url': 0,
            'duplicates_title': 0,
            'invalid_missing_fields': 0,
            'invalid_old_articles': 0,
            'valid_articles': 0
        }

        logger.info("ContentValidator initialised")

    def validate_article(self, article, max_age_days=7, title_similarity_threshold=0.85):
        """
        Validate a single article for quality and uniqueness.
        @param {dict} article - Article dictionary to validate
        @param {int} max_age_days - Maximum age in days for articles
        @param {float} title_similarity_threshold - Threshold for title similarity (0-1)
        @return {tuple} (is_valid, reason) - Validation result and reason if invalid
        """
        self.stats['total_checked'] += 1

        # Check required fields
        required_fields = ['title', 'url', 'published_date']
        for field in required_fields:
            if field not in article or not article[field]:
                self.stats['invalid_missing_fields'] += 1
                return False, f"Missing required field: {field}"

        # Check for URL duplicates
        article_url = article['url'].strip()
        if article_url in self.seen_urls:
            self.stats['duplicates_url'] += 1
            return False, "Duplicate URL"

        # Check for title duplicates (high similarity)
        article_title = article['title'].strip()
        for seen_title in self.seen_titles:
            similarity = self._calculate_similarity(article_title, seen_title)
            if similarity >= title_similarity_threshold:
                self.stats['duplicates_title'] += 1
                return False, f"Duplicate title (similarity: {similarity:.2f})"

        # Check article age
        try:
            published_date = article['published_date']
            if isinstance(published_date, str):
                published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))

            age = datetime.now() - published_date.replace(tzinfo=None)
            if age > timedelta(days=max_age_days):
                self.stats['invalid_old_articles'] += 1
                return False, f"Article too old: {age.days} days"

        except Exception as e:
            logger.warning(f"Error parsing date for article '{article_title}': {str(e)}")
            # Allow articles with unparseable dates through rather than rejecting

        # Article is valid
        self.seen_urls.add(article_url)
        self.seen_titles.append(article_title)
        self.stats['valid_articles'] += 1

        return True, "Valid"

    def validate_articles(self, articles, max_age_days=7, title_similarity_threshold=0.85):
        """
        Validate multiple articles and return only valid ones.
        @param {list} articles - List of article dictionaries
        @param {int} max_age_days - Maximum age in days for articles
        @param {float} title_similarity_threshold - Threshold for title similarity
        @return {list} List of valid articles
        """
        valid_articles = []
        rejection_reasons = {}

        for article in articles:
            is_valid, reason = self.validate_article(
                article,
                max_age_days=max_age_days,
                title_similarity_threshold=title_similarity_threshold
            )

            if is_valid:
                valid_articles.append(article)
            else:
                # Track rejection reasons for logging
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        # Log rejection summary
        if rejection_reasons:
            logger.info(f"Validation rejected {len(articles) - len(valid_articles)} articles:")
            for reason, count in rejection_reasons.items():
                logger.info(f"  {reason}: {count}")

        logger.info(f"Validated {len(valid_articles)} of {len(articles)} articles")

        return valid_articles

    def _calculate_similarity(self, text1, text2):
        """
        Calculate similarity ratio between two strings.
        @param {str} text1 - First string
        @param {str} text2 - Second string
        @return {float} Similarity ratio between 0 and 1
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def reset(self):
        """Reset validator state and statistics."""
        self.seen_urls.clear()
        self.seen_titles.clear()

        for key in self.stats:
            self.stats[key] = 0

        logger.info("Validator state reset")

    def get_stats(self):
        """
        Get validation statistics.
        @return {dict} Statistics dictionary
        """
        return self.stats

    def log_stats_summary(self):
        """Log a summary of validation statistics."""
        logger.info("=" * 60)
        logger.info("CONTENT VALIDATOR STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total articles checked: {self.stats['total_checked']}")
        logger.info(f"Valid articles: {self.stats['valid_articles']}")
        logger.info(f"Duplicate URLs: {self.stats['duplicates_url']}")
        logger.info(f"Duplicate titles: {self.stats['duplicates_title']}")
        logger.info(f"Missing required fields: {self.stats['invalid_missing_fields']}")
        logger.info(f"Articles too old: {self.stats['invalid_old_articles']}")

        if self.stats['total_checked'] > 0:
            valid_rate = (self.stats['valid_articles'] / self.stats['total_checked']) * 100
            logger.info(f"Validation rate: {valid_rate:.1f}%")

        logger.info("=" * 60)


# Global instance
content_validator = ContentValidator()
