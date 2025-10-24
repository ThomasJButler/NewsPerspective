"""
@author Tom Butler
@date 2025-10-24
@description The Guardian scraper implementation.
             Fetches articles from The Guardian RSS feeds.
"""

import sys
sys.path.append('../..')

from scrapers.rss_scraper import RSSFeedScraper


class GuardianScraper(RSSFeedScraper):
    """The Guardian scraper using RSS feeds."""

    def __init__(self):
        """Initialise The Guardian scraper."""
        super().__init__(
            source_name="The Guardian",
            rss_url="https://www.theguardian.com/world/rss",
            rate_limit_delay=1
        )
