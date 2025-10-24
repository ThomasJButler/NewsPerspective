"""
@author Tom Butler
@date 2025-10-25
@description Scraper manager to orchestrate multiple news source scrapers.
             Coordinates fetching from all configured sources with error handling.
"""

import sys
sys.path.append('..')

from logger_config import setup_logger
from scrapers.sources.bbc_scraper import BBCScraper
from scrapers.sources.cnn_scraper import CNNScraper
from scrapers.sources.reuters_scraper import ReutersScraper
from scrapers.sources.guardian_scraper import GuardianScraper
from scrapers.sources.techcrunch_scraper import TechCrunchScraper

logger = setup_logger("NewsPerspective.ScraperManager")


class ScraperManager:
    """Manages multiple news scrapers and coordinates article fetching."""

    def __init__(self):
        """Initialise scraper manager with all available sources."""
        self.scrapers = {
            'bbc': BBCScraper(),
            'cnn': CNNScraper(),
            'reuters': ReutersScraper(),
            'guardian': GuardianScraper(),
            'techcrunch': TechCrunchScraper()
        }

        self.stats = {
            'total_fetched': 0,
            'total_errors': 0,
            'per_source': {}
        }

        for source_key in self.scrapers.keys():
            self.stats['per_source'][source_key] = {
                'fetched': 0,
                'errors': 0,
                'last_fetch_count': 0
            }

        logger.info(f"ScraperManager initialised with {len(self.scrapers)} sources")

    def fetch_from_all_sources(self, max_articles_per_source=20):
        """
        Fetch articles from all configured sources.
        @param {int} max_articles_per_source - Maximum articles to fetch per source
        @return {dict} Dictionary mapping source names to article lists
        """
        all_articles = {}

        for source_key, scraper in self.scrapers.items():
            try:
                logger.info(f"Fetching from {scraper.source_name}...")
                articles = scraper.fetch_articles(max_articles=max_articles_per_source)

                all_articles[source_key] = articles

                article_count = len(articles)
                self.stats['total_fetched'] += article_count
                self.stats['per_source'][source_key]['fetched'] += article_count
                self.stats['per_source'][source_key]['last_fetch_count'] = article_count

                logger.info(f"Successfully fetched {article_count} articles from {scraper.source_name}")

            except Exception as e:
                logger.error(f"Error fetching from {scraper.source_name}: {str(e)}")
                all_articles[source_key] = []
                self.stats['total_errors'] += 1
                self.stats['per_source'][source_key]['errors'] += 1

        return all_articles

    def fetch_from_sources(self, source_keys, max_articles_per_source=20):
        """
        Fetch articles from specific sources.
        @param {list} source_keys - List of source keys to fetch from
        @param {int} max_articles_per_source - Maximum articles to fetch per source
        @return {dict} Dictionary mapping source names to article lists
        """
        articles = {}

        for source_key in source_keys:
            if source_key not in self.scrapers:
                logger.warning(f"Unknown source key: {source_key}")
                continue

            scraper = self.scrapers[source_key]

            try:
                logger.info(f"Fetching from {scraper.source_name}...")
                source_articles = scraper.fetch_articles(max_articles=max_articles_per_source)

                articles[source_key] = source_articles

                article_count = len(source_articles)
                self.stats['total_fetched'] += article_count
                self.stats['per_source'][source_key]['fetched'] += article_count
                self.stats['per_source'][source_key]['last_fetch_count'] = article_count

                logger.info(f"Successfully fetched {article_count} articles from {scraper.source_name}")

            except Exception as e:
                logger.error(f"Error fetching from {scraper.source_name}: {str(e)}")
                articles[source_key] = []
                self.stats['total_errors'] += 1
                self.stats['per_source'][source_key]['errors'] += 1

        return articles

    def get_all_articles_flat(self, max_articles_per_source=20):
        """
        Fetch all articles from all sources as a flat list.
        @param {int} max_articles_per_source - Maximum articles to fetch per source
        @return {list} Flat list of all articles with source information
        """
        articles_by_source = self.fetch_from_all_sources(max_articles_per_source)

        flat_articles = []
        for source_key, articles in articles_by_source.items():
            for article in articles:
                # Ensure source key is included in article data
                if 'source' not in article or not article['source']:
                    article['source'] = self.scrapers[source_key].source_name
                flat_articles.append(article)

        logger.info(f"Collected {len(flat_articles)} total articles from all sources")
        return flat_articles

    def get_available_sources(self):
        """
        Get list of available source scrapers.
        @return {dict} Dictionary of source keys to source names
        """
        return {key: scraper.source_name for key, scraper in self.scrapers.items()}

    def get_stats(self):
        """
        Get scraper statistics.
        @return {dict} Statistics including totals and per-source metrics
        """
        return self.stats

    def reset_stats(self):
        """Reset all statistics counters."""
        self.stats['total_fetched'] = 0
        self.stats['total_errors'] = 0

        for source_key in self.stats['per_source'].keys():
            self.stats['per_source'][source_key] = {
                'fetched': 0,
                'errors': 0,
                'last_fetch_count': 0
            }

        logger.info("Statistics reset")

    def log_stats_summary(self):
        """Log a summary of scraper statistics."""
        logger.info("=" * 60)
        logger.info("SCRAPER MANAGER STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total articles fetched: {self.stats['total_fetched']}")
        logger.info(f"Total errors: {self.stats['total_errors']}")

        logger.info("\nPer-Source Statistics:")
        for source_key, source_stats in self.stats['per_source'].items():
            source_name = self.scrapers[source_key].source_name
            logger.info(f"  {source_name}:")
            logger.info(f"    Fetched: {source_stats['fetched']}")
            logger.info(f"    Errors: {source_stats['errors']}")
            logger.info(f"    Last fetch: {source_stats['last_fetch_count']}")

        logger.info("=" * 60)


# Global instance
scraper_manager = ScraperManager()
