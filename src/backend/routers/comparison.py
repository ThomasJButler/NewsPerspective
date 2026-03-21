from fastapi import APIRouter, Depends
from sqlalchemy import not_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article
from ..schemas import (
    ComparisonArticleSummary,
    ComparisonGroup,
    ComparisonResponse,
)
from ..utils.good_news import content_guardrail_expression
from ..utils.source_normalization import normalized_source_label
from ..utils.title_similarity import group_articles

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


@router.get("", response_model=ComparisonResponse)
def get_comparison_groups(
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    """Return groups of related articles for side-by-side comparison."""
    articles = (
        db.query(Article)
        .filter(
            Article.processing_status == "processed",
            not_(content_guardrail_expression(Article)),
        )
        .order_by(Article.published_at.desc())
        .all()
    )

    raw_groups = group_articles(articles)

    groups: list[ComparisonGroup] = []
    for raw in raw_groups:
        # Look up the full article rows for this group.
        articles_in_group = [
            a for a in articles if a.id in set(raw.article_ids)
        ]
        group = ComparisonGroup(
            representative_title=raw.representative_title,
            articles=[
                ComparisonArticleSummary(
                    id=a.id,
                    original_title=a.original_title,
                    rewritten_title=a.rewritten_title,
                    source_name=normalized_source_label(a.source_name, a.source_id),
                    country=a.country,
                    original_sentiment=a.original_sentiment,
                    sentiment_score=a.sentiment_score,
                    url=a.url,
                    image_url=a.image_url,
                    published_at=a.published_at,
                )
                for a in articles_in_group
            ],
            sources=raw.sources,
            countries=raw.countries,
        )
        groups.append(group)

    return ComparisonResponse(groups=groups, total_groups=len(groups))
