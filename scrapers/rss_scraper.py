"""
@author Tom Butler
@date 2025-10-24
@description RSS feed scraper implementation.
             Parses RSS/Atom feeds and extracts article data.
"""

import feedparser
from urllib.parse import urlparse, urljoin
from .base_scraper import BaseScraper, logger


class RSSFeedScraper(BaseScraper):
    """
    RSS/Atom feed scraper.
    Fetches and parses RSS feeds from news sources.
    """

    def __init__(self, source_name, rss_url, rate_limit_delay=2):
        """
        Initialise RSS feed scraper.
        @param {str} source_name - Name of the news source
        @param {str} rss_url - URL of the RSS feed
        @param {int} rate_limit_delay - Seconds between requests
        """
        super().__init__(source_name, rate_limit_delay)
        self.rss_url = rss_url
        self.base_url = f"{urlparse(rss_url).scheme}://{urlparse(rss_url).netloc}"
        logger.info(f"RSS scraper initialised for {source_name}: {rss_url}")

    def fetch_articles(self, max_articles=20):
        """
        Fetch articles from RSS feed.
        @param {int} max_articles - Maximum articles to fetch
        @return {list} List of normalized article dictionaries
        """
        logger.info(f"Fetching up to {max_articles} articles from {self.source_name}")

        response = self._make_request(self.rss_url)
        if not response:
            logger.error(f"Failed to fetch RSS feed from {self.source_name}")
            return []

        try:
            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"RSS feed parsing warning for {self.source_name}: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    raw_article = self._parse_rss_entry(entry)
                    normalized = self.normalize_article(raw_article)

                    if self.validate_article(normalized):
                        articles.append(normalized)
                    else:
                        logger.debug(f"Skipping invalid article: {normalized.get('title', 'NO TITLE')}")

                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {str(e)}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} articles from {self.source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error parsing RSS feed from {self.source_name}: {str(e)}")
            return []

    def _parse_rss_entry(self, entry):
        """
        Parse RSS entry into raw article format.
        @param {feedparser.FeedParserDict} entry - RSS feed entry
        @return {dict} Raw article data
        """
        title = entry.get('title', '')
        link = entry.get('link', '')
        description = self._clean_html(entry.get('description', entry.get('summary', '')))
        published = entry.get('published', entry.get('updated', ''))
        author = entry.get('author', entry.get('dc:creator', ''))

        # Extract image
        image_url = ''
        if hasattr(entry, 'media_content') and entry.media_content:
            image_url = entry.media_content[0].get('url', '')
        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url', '')
        elif 'enclosures' in entry and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', ''):
                    image_url = enclosure.get('href', '')
                    break

        # Make relative URLs absolute
        if link and not link.startswith('http'):
            link = urljoin(self.base_url, link)
        if image_url and not image_url.startswith('http'):
            image_url = urljoin(self.base_url, image_url)

        return {
            'title': title,
            'url': link,
            'content': description,
            'published_at': published,
            'author': author,
            'image_url': image_url
        }

    def _clean_html(self, html_content):
        """
        Remove HTML tags from content.
        @param {str} html_content - HTML string
        @return {str} Plain text
        """
        if not html_content:
            return ''

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True)
        except:
            import re
            clean = re.compile('<.*?>')
            return re.sub(clean, '', html_content)

    def check_robots_txt(self):
        """
        Check robots.txt for RSS feed access.
        @return {bool} True if allowed (RSS feeds are generally allowed)
        """
        robots_url = urljoin(self.base_url, '/robots.txt')

        try:
            response = self._make_request(robots_url, timeout=5)
            if not response:
                logger.warning(f"Could not fetch robots.txt for {self.source_name}, proceeding anyway")
                return True

            robots_content = response.text.lower()

            # Check if RSS feeds are explicitly disallowed
            if 'disallow: /rss' in robots_content or 'disallow: /feed' in robots_content:
                logger.warning(f"robots.txt disallows RSS scraping for {self.source_name}")
                return False

            # RSS feeds are typically allowed
            logger.debug(f"robots.txt allows scraping for {self.source_name}")
            return True

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {self.source_name}: {str(e)}")
            return True
