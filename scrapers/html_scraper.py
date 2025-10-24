"""
@author Tom Butler
@date 2025-10-24
@description HTML scraper implementation for fallback when RSS is unavailable.
             Uses BeautifulSoup to extract article data from HTML pages.
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from .base_scraper import BaseScraper, logger


class HTMLScraper(BaseScraper):
    """
    HTML scraper for extracting articles from web pages.
    Used as fallback when RSS feeds are unavailable.
    """

    def __init__(self, source_name, base_url, selectors, rate_limit_delay=2):
        """
        Initialise HTML scraper with CSS selectors.
        @param {str} source_name - Name of the news source
        @param {str} base_url - Base URL of the news site
        @param {dict} selectors - CSS selectors for extracting article data
        @param {int} rate_limit_delay - Seconds between requests
        """
        super().__init__(source_name, rate_limit_delay)
        self.base_url = base_url
        self.selectors = selectors
        logger.info(f"HTML scraper initialised for {source_name}")

    def fetch_articles(self, max_articles=20):
        """
        Fetch articles by parsing HTML page.
        @param {int} max_articles - Maximum articles to fetch
        @return {list} List of normalized article dictionaries
        """
        logger.info(f"Fetching up to {max_articles} articles from {self.source_name}")

        response = self._make_request(self.base_url)
        if not response:
            logger.error(f"Failed to fetch HTML from {self.source_name}")
            return []

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            article_elements = soup.select(self.selectors.get('article_list', 'article'))
            logger.debug(f"Found {len(article_elements)} article elements")

            for elem in article_elements[:max_articles]:
                try:
                    raw_article = self._parse_article_element(elem, soup)
                    normalized = self.normalize_article(raw_article)

                    if self.validate_article(normalized):
                        articles.append(normalized)

                except Exception as e:
                    logger.debug(f"Error parsing article element: {str(e)}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} articles from {self.source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error parsing HTML from {self.source_name}: {str(e)}")
            return []

    def _parse_article_element(self, element, soup):
        """
        Parse article data from HTML element.
        @param {bs4.element.Tag} element - Article HTML element
        @param {BeautifulSoup} soup - Full page soup for context
        @return {dict} Raw article data
        """
        title = self._extract_text(element, self.selectors.get('title', 'h2, h3'))
        url = self._extract_link(element, self.selectors.get('link', 'a'))
        content = self._extract_text(element, self.selectors.get('content', 'p'))
        author = self._extract_text(element, self.selectors.get('author', '.author'))
        date = self._extract_text(element, self.selectors.get('date', 'time, .date'))
        image = self._extract_image(element, self.selectors.get('image', 'img'))

        # Make relative URLs absolute
        if url and not url.startswith('http'):
            url = urljoin(self.base_url, url)
        if image and not image.startswith('http'):
            image = urljoin(self.base_url, image)

        return {
            'title': title,
            'url': url,
            'content': content,
            'author': author,
            'published_at': date,
            'image_url': image
        }

    def _extract_text(self, element, selector):
        """
        Extract text from element using selector.
        @param {bs4.element.Tag} element - Parent element
        @param {str} selector - CSS selector
        @return {str} Extracted text or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else ''
        except:
            return ''

    def _extract_link(self, element, selector):
        """
        Extract href from link element.
        @param {bs4.element.Tag} element - Parent element
        @param {str} selector - CSS selector
        @return {str} URL or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get('href', '') if found else ''
        except:
            return ''

    def _extract_image(self, element, selector):
        """
        Extract image URL from img element.
        @param {bs4.element.Tag} element - Parent element
        @param {str} selector - CSS selector
        @return {str} Image URL or empty string
        """
        try:
            found = element.select_one(selector)
            if not found:
                return ''

            return found.get('src', found.get('data-src', ''))
        except:
            return ''

    def check_robots_txt(self):
        """
        Check robots.txt compliance.
        @return {bool} True if scraping is allowed
        """
        robots_url = urljoin(self.base_url, '/robots.txt')

        try:
            response = self._make_request(robots_url, timeout=5)
            if not response:
                logger.warning(f"Could not fetch robots.txt for {self.source_name}")
                return False

            robots_content = response.text.lower()
            parsed_url = urlparse(self.base_url)
            path = parsed_url.path or '/'

            # Check for disallowed paths
            for line in robots_content.split('\n'):
                line = line.strip()
                if line.startswith('disallow:'):
                    disallowed_path = line.split(':', 1)[1].strip()
                    if path.startswith(disallowed_path):
                        logger.warning(f"robots.txt disallows scraping {path} for {self.source_name}")
                        return False

            logger.debug(f"robots.txt allows scraping for {self.source_name}")
            return True

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {self.source_name}: {str(e)}")
            return False
