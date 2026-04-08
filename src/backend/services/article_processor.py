from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Article
from ..utils.logger import setup_logger
from ..utils.good_news import apply_good_news_rules
from .ai_service import AIService
from .news_source import NewsFetchError, NewsSource

logger = setup_logger(__name__)


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning("Could not parse datetime: %s", value)
        return None


class ArticleProcessor:
    def process_new_articles(self, db: Session, news_source: NewsSource) -> dict[str, int]:
        """Fetch, deduplicate, analyse, and persist articles."""
        articles: list[dict] = []
        fetch_errors: list[str] = []
        for country in ("us", "gb"):
            try:
                articles.extend(news_source.fetch_all_categories(country=country))
            except Exception as exc:
                logger.warning("Fetch failed for country=%s: %s — continuing", country, exc)
                fetch_errors.append(f"{country}: {exc}")

        if not articles and fetch_errors:
            raise NewsFetchError(f"All country fetches failed: {'; '.join(fetch_errors)}")

        if not articles:
            logger.info("No articles returned from NewsFetcher.")
            return {
                "new_articles": 0,
                "processed_articles": 0,
                "failed_articles": 0,
            }

        # Build set of URLs already in the DB to deduplicate
        existing_urls = {url for (url,) in db.query(Article.url).all()}
        logger.info(
            "Fetched %d articles; %d URLs already in DB.",
            len(articles),
            len(existing_urls),
        )

        ai_service = AIService()
        new_count = 0
        processed_count = 0
        failed_count = 0
        for raw in articles:
            url = raw.get("url")
            if not url or url in existing_urls:
                continue

            # Insert with pending status so a crash leaves a trace
            article = Article(
                url=url,
                original_title=raw.get("original_title", ""),
                original_description=raw.get("original_description", ""),
                source_name=raw.get("source_name", ""),
                source_id=raw.get("source_id", ""),
                author=raw.get("author"),
                image_url=raw.get("image_url"),
                published_at=_parse_datetime(raw.get("published_at")),
                category=raw.get("category", "general"),
                country=raw.get("country", "us"),
                processing_status="pending",
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            existing_urls.add(url)
            new_count += 1

            try:
                result = ai_service.analyse_article(
                    title=article.original_title,
                    source=article.source_name,
                    description=article.original_description,
                )

                article.rewritten_title = result.get("rewritten_title")
                article.tldr = result.get("tldr")
                article.was_rewritten = result.get("needs_rewrite", False)
                article.original_sentiment = result.get("sentiment")
                article.sentiment_score = result.get("sentiment_score")
                article.is_good_news = apply_good_news_rules(
                    result.get("is_good_news", False),
                    article.category,
                    title=article.original_title,
                    description=article.original_description,
                    source_name=article.source_name,
                )
                article.processing_status = "processed"

                db.commit()
                processed_count += 1
                logger.info("Processed article id=%s url=%s", article.id, url)

            except Exception as exc:
                logger.error(
                    "Failed to analyse article id=%s url=%s: %s",
                    article.id,
                    url,
                    exc,
                    exc_info=True,
                )
                article.processing_status = "failed"
                db.commit()
                failed_count += 1

        logger.info("ArticleProcessor finished. New articles processed: %d", new_count)
        return {
            "new_articles": new_count,
            "processed_articles": processed_count,
            "failed_articles": failed_count,
        }


def process_new_articles_background(api_key: str):
    """Entry point for BackgroundTasks — creates its own DB session."""
    from ..database import SessionLocal
    from .news_fetcher import NewsFetcher
    from .refresh_tracker import refresh_tracker

    db = SessionLocal()
    try:
        news_source = NewsFetcher(api_key=api_key)
        processor = ArticleProcessor()
        summary = processor.process_new_articles(db, news_source)
        refresh_tracker.mark_completed(**summary)
    except NewsFetchError as exc:
        logger.error("Background refresh fetch failed: %s", exc, exc_info=True)
        refresh_tracker.mark_failed(str(exc))
        raise
    except Exception as exc:
        logger.error("Background refresh failed: %s", exc, exc_info=True)
        refresh_tracker.mark_failed("Refresh failed while processing articles.")
        raise
    finally:
        db.close()
