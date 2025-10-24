"""
@author Tom Butler
@date 2025-10-24
@description BBC News scraper implementation.
             Fetches articles from BBC News RSS feeds.
"""

import sys
sys.path.append('../..')

from scrapers.rss_scraper import RSSFeedScraper


class BBCScraper(RSSFeedScraper):
    """BBC News scraper using RSS feeds."""

    def __init__(self):
        """Initialise BBC News scraper."""
        super().__init__(
            source_name="BBC News",
            rss_url="http://feeds.bbci.co.uk/news/rss.xml",
            rate_limit_delay=1
        )
