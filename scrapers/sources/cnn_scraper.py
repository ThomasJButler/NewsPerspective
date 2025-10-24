"""
@author Tom Butler
@date 2025-10-24
@description CNN scraper implementation.
             Fetches articles from CNN RSS feeds.
"""

import sys
sys.path.append('../..')

from scrapers.rss_scraper import RSSFeedScraper


class CNNScraper(RSSFeedScraper):
    """CNN scraper using RSS feeds."""

    def __init__(self):
        """Initialise CNN scraper."""
        super().__init__(
            source_name="CNN",
            rss_url="http://rss.cnn.com/rss/edition.rss",
            rate_limit_delay=1
        )
