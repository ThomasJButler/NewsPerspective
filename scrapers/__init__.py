"""
@author Tom Butler
@date 2025-10-24
@description Scrapers package for fetching articles from multiple news sources.
             Provides RSS and HTML scraping with source-specific implementations.
"""

from .base_scraper import BaseScraper
from .rss_scraper import RSSFeedScraper
from .html_scraper import HTMLScraper
from .scraper_manager import ScraperManager

__all__ = ['BaseScraper', 'RSSFeedScraper', 'HTMLScraper', 'ScraperManager']
