"""
@author Tom Butler
@date 2025-10-24
@description Abstract base class for news source scrapers.
             Defines interface and common functionality for all scrapers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import time
import requests
from logger_config import setup_logger

logger = setup_logger("NewsPerspective.Scrapers")


class BaseScraper(ABC):
    """
    Abstract base class for news scrapers.
    All source-specific scrapers must inherit from this class.
    """

    def __init__(self, source_name, rate_limit_delay=2):
        """
        Initialise base scraper.
        @param {str} source_name - Name of the news source
        @param {int} rate_limit_delay - Seconds to wait between requests
        """
        self.source_name = source_name
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsPerspective/2.0 (Educational News Analysis Tool)'
        })
        logger.info(f"Initialised scraper for {source_name}")

    def _respect_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, url, timeout=15):
        """
        Make HTTP request with rate limiting and error handling.
        @param {str} url - URL to fetch
        @param {int} timeout - Request timeout in seconds
        @return {requests.Response} Response object or None on error
        """
        self._respect_rate_limit()

        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            logger.debug(f"Successfully fetched {url}")
            return response
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            return None

    @abstractmethod
    def fetch_articles(self, max_articles=20):
        """
        Fetch articles from this source.
        @param {int} max_articles - Maximum number of articles to fetch
        @return {list} List of article dictionaries
        """
        pass

    @abstractmethod
    def check_robots_txt(self):
        """
        Check robots.txt compliance for this source.
        @return {bool} True if scraping is allowed
        """
        pass

    def normalize_article(self, raw_article):
        """
        Normalize article to standard format.
        @param {dict} raw_article - Raw article data from source
        @return {dict} Normalized article dictionary
        """
        return {
            'title': raw_article.get('title', ''),
            'content': raw_article.get('content', raw_article.get('description', '')),
            'url': raw_article.get('url', raw_article.get('link', '')),
            'source': self.source_name,
            'published_at': self._normalize_date(raw_article.get('published_at', raw_article.get('pubDate', ''))),
            'author': raw_article.get('author', ''),
            'image_url': raw_article.get('image_url', ''),
            'raw_data': raw_article
        }

    def _normalize_date(self, date_str):
        """
        Normalize date string to ISO format.
        @param {str} date_str - Date string in various formats
        @return {str} ISO format date string
        """
        if not date_str:
            return datetime.now().isoformat()

        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            try:
                from dateutil import parser
                dt = parser.parse(date_str)
                return dt.isoformat()
            except:
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.now().isoformat()

    def validate_article(self, article):
        """
        Validate article has required fields.
        @param {dict} article - Article dictionary
        @return {bool} True if valid
        """
        required_fields = ['title', 'url']
        valid = all(article.get(field) for field in required_fields)

        if not valid:
            logger.debug(f"Invalid article missing required fields: {article}")

        return valid

    def close(self):
        """Close the scraper session."""
        self.session.close()
        logger.debug(f"Closed scraper session for {self.source_name}")
