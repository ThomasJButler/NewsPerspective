from sqlalchemy.orm import Session

from ..models import Article
from ..utils.logger import setup_logger
from .ai_service import AIService
from .news_fetcher import NewsFetcher

logger = setup_logger(__name__)


class ArticleProcessor:
    def process_new_articles(self, db: Session, api_key: str):
        """Fetch, deduplicate, analyse, and persist articles."""
        fetcher = NewsFetcher(api_key=api_key)
        articles = fetcher.fetch_all_categories()

        if not articles:
            logger.info("No articles returned from NewsFetcher.")
            return

        # Build set of URLs already in the DB to deduplicate
        existing_urls = {url for (url,) in db.query(Article.url).all()}
        logger.info(
            "Fetched %d articles; %d URLs already in DB.",
            len(articles),
            len(existing_urls),
        )

        new_count = 0
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
                published_at=raw.get("published_at"),
                category=raw.get("category", "general"),
                processing_status="pending",
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            existing_urls.add(url)
            new_count += 1

            try:
                result = AIService().analyse_article(
                    title=article.original_title,
                    source=article.source_name,
                    description=article.original_description,
                )

                article.rewritten_title = result.get("rewritten_title")
                article.tldr = result.get("tldr")
                article.was_rewritten = result.get("needs_rewrite", False)
                article.original_sentiment = result.get("sentiment")
                article.sentiment_score = result.get("sentiment_score")
                article.is_good_news = result.get("is_good_news", False)
                article.processing_status = "processed"

                db.commit()
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

        logger.info("ArticleProcessor finished. New articles processed: %d", new_count)


def process_new_articles_background(api_key: str):
    """Entry point for BackgroundTasks — creates its own DB session."""
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        processor = ArticleProcessor()
        processor.process_new_articles(db, api_key)
    finally:
        db.close()
