from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import not_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article
from ..schemas import (
    ComparisonAnalyseRequest,
    ComparisonAnalysis,
    ComparisonArticleSummary,
    ComparisonGroup,
    ComparisonResponse,
    ComparisonSourceTone,
)
from ..services.ai_service import AIService
from ..utils.good_news import content_guardrail_expression, custom_guardrail_expression, load_custom_guardrail_keywords
from ..utils.source_normalization import normalized_source_label
from ..utils.title_similarity import group_articles

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


@router.get("", response_model=ComparisonResponse)
def get_comparison_groups(
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    """Return groups of related articles for side-by-side comparison."""
    custom_keywords = load_custom_guardrail_keywords(db)
    base_filter = [
        Article.processing_status == "processed",
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        base_filter.append(not_(custom_guardrail_expression(Article, custom_keywords)))
    articles = (
        db.query(Article)
        .filter(*base_filter)
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


@router.post("/analyse", response_model=ComparisonAnalysis)
def analyse_comparison_group(
    body: ComparisonAnalyseRequest,
    db: Session = Depends(get_db),
) -> ComparisonAnalysis:
    """Run AI framing analysis on a group of related articles."""
    if len(body.article_ids) < 2:
        raise HTTPException(status_code=422, detail="At least 2 article IDs required.")

    custom_keywords = load_custom_guardrail_keywords(db)
    guardrail_filters = [
        Article.id.in_(body.article_ids),
        Article.processing_status == "processed",
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        guardrail_filters.append(not_(custom_guardrail_expression(Article, custom_keywords)))

    articles = (
        db.query(Article)
        .filter(*guardrail_filters)
        .all()
    )

    if len(articles) < 2:
        raise HTTPException(
            status_code=404,
            detail="Fewer than 2 processed articles found for the given IDs.",
        )

    # Build the representative title from the first article (newest by published_at).
    articles_sorted = sorted(
        articles,
        key=lambda a: a.published_at or a.fetched_at,
        reverse=True,
    )
    representative_title = (
        articles_sorted[0].rewritten_title or articles_sorted[0].original_title
    )

    ai = AIService()
    article_dicts = [
        {
            "original_title": a.original_title,
            "source_name": normalized_source_label(a.source_name, a.source_id),
            "country": a.country,
            "original_description": a.original_description,
            "original_sentiment": a.original_sentiment,
        }
        for a in articles_sorted
    ]

    result = ai.analyse_comparison_group(article_dicts)

    return ComparisonAnalysis(
        representative_title=representative_title,
        summary=result["summary"],
        framing_differences=result["framing_differences"],
        source_tones=[
            ComparisonSourceTone(
                source_name=t["source_name"],
                country=t["country"],
                tone=t["tone"],
            )
            for t in result["source_tones"]
        ],
    )
