"""
@author Tom Butler
@date 2025-10-24
@description Reuters scraper implementation.
             Fetches articles from Reuters RSS feeds.
"""

import sys
sys.path.append('../..')

from scrapers.rss_scraper import RSSFeedScraper


class ReutersScraper(RSSFeedScraper):
    """Reuters scraper using RSS feeds."""

    def __init__(self):
        """Initialise Reuters scraper."""
        super().__init__(
            source_name="Reuters",
            rss_url="https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            rate_limit_delay=1
        )
