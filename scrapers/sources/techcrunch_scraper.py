"""
@author Tom Butler
@date 2025-10-25
@description TechCrunch scraper implementation.
             Fetches technology news from TechCrunch RSS feed.
"""

import sys
sys.path.append('../..')

from scrapers.rss_scraper import RSSFeedScraper


class TechCrunchScraper(RSSFeedScraper):
    """TechCrunch scraper using RSS feed."""

    def __init__(self):
        """Initialise TechCrunch scraper."""
        super().__init__(
            source_name="TechCrunch",
            rss_url="https://techcrunch.com/feed/",
            rate_limit_delay=1
        )
