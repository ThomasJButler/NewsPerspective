"""
@author Tom Butler
@date 2025-10-25
@description Source-specific scraper implementations.
             Provides scrapers for BBC, CNN, Reuters, The Guardian, and TechCrunch.
"""

from .bbc_scraper import BBCScraper
from .cnn_scraper import CNNScraper
from .reuters_scraper import ReutersScraper
from .guardian_scraper import GuardianScraper
from .techcrunch_scraper import TechCrunchScraper

__all__ = [
    'BBCScraper',
    'CNNScraper',
    'ReutersScraper',
    'GuardianScraper',
    'TechCrunchScraper'
]
