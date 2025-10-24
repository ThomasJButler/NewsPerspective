"""
@author Tom Butler
@date 2025-10-25
@description Test script for RSS scraping framework.
             Validates scraper functionality and article fetching.
"""

from scrapers.scraper_manager import scraper_manager
from scrapers.content_validator import content_validator
from logger_config import setup_logger

logger = setup_logger("NewsPerspective.RSSTest")


def test_individual_scrapers():
    """Test each scraper individually."""
    print("=" * 60)
    print("Testing Individual Scrapers")
    print("=" * 60)

    available_sources = scraper_manager.get_available_sources()

    for source_key, source_name in available_sources.items():
        print(f"\nTesting {source_name}...")

        try:
            articles = scraper_manager.fetch_from_sources([source_key], max_articles_per_source=5)
            article_count = len(articles.get(source_key, []))

            print(f"  Fetched: {article_count} articles")

            if article_count > 0:
                sample_article = articles[source_key][0]
                print(f"  Sample title: {sample_article.get('title', 'N/A')[:70]}...")
                print(f"  Sample source: {sample_article.get('source', 'N/A')}")
                print(f"  Has URL: {'url' in sample_article and sample_article['url']}")
                print(f"  SUCCESS")
            else:
                print(f"  WARNING: No articles fetched")

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            logger.error(f"Error testing {source_name}: {str(e)}")


def test_scraper_manager():
    """Test scraper manager functionality."""
    print("\n" + "=" * 60)
    print("Testing Scraper Manager")
    print("=" * 60)

    try:
        print("\nFetching 10 articles from all sources...")
        articles = scraper_manager.get_all_articles_flat(max_articles_per_source=10)

        print(f"Total articles fetched: {len(articles)}")

        if articles:
            print(f"\nSample articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"  {i}. [{article.get('source', 'Unknown')}] {article.get('title', 'N/A')[:60]}...")

        stats = scraper_manager.get_stats()
        print(f"\nScraper Manager Stats:")
        print(f"  Total fetched: {stats['total_fetched']}")
        print(f"  Total errors: {stats['total_errors']}")

        print(f"\nSUCCESS: Scraper manager working correctly")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error(f"Error testing scraper manager: {str(e)}")


def test_content_validator():
    """Test content validation and deduplication."""
    print("\n" + "=" * 60)
    print("Testing Content Validator")
    print("=" * 60)

    try:
        print("\nFetching articles for validation testing...")
        articles = scraper_manager.get_all_articles_flat(max_articles_per_source=15)

        print(f"Fetched {len(articles)} articles for validation")

        # Reset validator
        content_validator.reset()

        # Validate articles
        valid_articles = content_validator.validate_articles(
            articles,
            max_age_days=7,
            title_similarity_threshold=0.85
        )

        print(f"\nValidation Results:")
        print(f"  Input articles: {len(articles)}")
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Rejected: {len(articles) - len(valid_articles)}")

        stats = content_validator.get_stats()
        print(f"\nValidator Stats:")
        print(f"  Total checked: {stats['total_checked']}")
        print(f"  Valid: {stats['valid_articles']}")
        print(f"  Duplicate URLs: {stats['duplicates_url']}")
        print(f"  Duplicate titles: {stats['duplicates_title']}")
        print(f"  Missing fields: {stats['invalid_missing_fields']}")
        print(f"  Too old: {stats['invalid_old_articles']}")

        print(f"\nSUCCESS: Content validator working correctly")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error(f"Error testing content validator: {str(e)}")


def main():
    """Run all RSS scraper tests."""
    print("\n" + "=" * 60)
    print("RSS SCRAPING FRAMEWORK TEST")
    print("=" * 60)

    test_individual_scrapers()
    test_scraper_manager()
    test_content_validator()

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
