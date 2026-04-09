import re
from datetime import datetime, timedelta, timezone

import requests as http_requests
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import case, func, not_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article
from ..schemas import (
    CategoriesResponse,
    CategoryItem,
    DailyArticleCount,
    DailyRewriteRate,
    HistoricalStatsResponse,
    RefreshErrorCode,
    RefreshErrorDetail,
    RefreshErrorResponse,
    RefreshResponse,
    RefreshStatusResponse,
    SentimentMix,
    SourceItem,
    SourcesResponse,
    StatsResponse,
)
from ..services.article_processor import process_new_articles_background
from ..services.news_fetcher import DEFAULT_NEWSAPI_COUNTRY
from ..services.refresh_tracker import refresh_tracker
from ..utils.good_news import content_guardrail_expression, custom_guardrail_expression, good_news_filter_expression, load_custom_guardrail_keywords
from ..utils.source_normalization import source_id_expression, source_label_expression

router = APIRouter(prefix="/api", tags=["sources"])
NEWSAPI_VALIDATION_TIMEOUT_SECONDS = 5


def _redact_validation_error(message: str, api_key: str) -> str:
    redacted = message.replace(api_key, "[redacted]")
    return re.sub(r"(apiKey=)[^&\\s]+", r"\1[redacted]", redacted)


def _refresh_error(
    status_code: int,
    code: RefreshErrorCode,
    message: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=RefreshErrorDetail(code=code, message=message).model_dump(),
    )


@router.get("/sources", response_model=SourcesResponse)
def get_sources(db: Session = Depends(get_db)):
    custom_keywords = load_custom_guardrail_keywords(db)
    source_label = source_label_expression(Article)
    source_id = source_id_expression(Article)
    filters = [
        Article.processing_status == "processed",
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        filters.append(not_(custom_guardrail_expression(Article, custom_keywords)))

    rows = (
        db.query(
            source_label.label("source_name"),
            func.coalesce(func.max(source_id), "").label("source_id"),
            func.count(Article.id).label("article_count"),
        )
        .filter(*filters)
        .group_by(source_label)
        .order_by(func.count(Article.id).desc(), source_label.asc())
        .all()
    )

    sources = [
        SourceItem(
            source_name=row.source_name,
            source_id=row.source_id,
            article_count=row.article_count,
        )
        for row in rows
    ]

    return SourcesResponse(sources=sources)


@router.get("/categories", response_model=CategoriesResponse)
def get_categories(db: Session = Depends(get_db)):
    custom_keywords = load_custom_guardrail_keywords(db)
    filters = [
        Article.processing_status == "processed",
        Article.category.isnot(None),
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        filters.append(not_(custom_guardrail_expression(Article, custom_keywords)))

    rows = (
        db.query(
            Article.category.label("name"),
            func.count(Article.id).label("count"),
        )
        .filter(*filters)
        .group_by(Article.category)
        .order_by(func.count(Article.id).desc(), Article.category.asc())
        .all()
    )

    return CategoriesResponse(
        categories=[
            CategoryItem(name=row.name, count=row.count) for row in rows
        ]
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    source_label = source_label_expression(Article)
    custom_keywords = load_custom_guardrail_keywords(db)

    base_filters = [
        Article.processing_status == "processed",
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        base_filters.append(not_(custom_guardrail_expression(Article, custom_keywords)))

    total_articles = (
        db.query(func.count(Article.id))
        .filter(*base_filters)
        .scalar()
        or 0
    )

    rewritten_count = (
        db.query(func.count(Article.id))
        .filter(*base_filters, Article.was_rewritten.is_(True))
        .scalar()
        or 0
    )

    good_news_count = (
        db.query(func.count(Article.id))
        .filter(*base_filters, good_news_filter_expression(Article))
        .scalar()
        or 0
    )

    sources_count = (
        db.query(func.count(func.distinct(source_label)))
        .filter(*base_filters)
        .scalar()
        or 0
    )

    latest_fetch = (
        db.query(func.max(Article.fetched_at))
        .filter(*base_filters)
        .scalar()
    )

    return StatsResponse(
        total_articles=total_articles,
        rewritten_count=rewritten_count,
        good_news_count=good_news_count,
        sources_count=sources_count,
        latest_fetch=latest_fetch,
    )


def _stats_base_filters(db: Session) -> list:
    """Shared filter list for stats endpoints: processed + guardrails + custom."""
    custom_keywords = load_custom_guardrail_keywords(db)
    filters = [
        Article.processing_status == "processed",
        not_(content_guardrail_expression(Article)),
    ]
    if custom_keywords:
        filters.append(not_(custom_guardrail_expression(Article, custom_keywords)))
    return filters


@router.get("/stats/historical", response_model=HistoricalStatsResponse)
def get_historical_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> HistoricalStatsResponse:
    """Time-series + distribution data for the /stats page charts.

    Returns `days` (default 30, max 365) of daily article counts and rewrite
    rates, plus a snapshot sentiment distribution. All aggregations honour
    the same processed + guardrail filters used by /api/stats so numbers
    stay consistent with the home feed and header strip.
    """
    base_filters = _stats_base_filters(db)

    today = datetime.now(timezone.utc).date()
    window_start = today - timedelta(days=days - 1)

    # Group by the day portion of fetched_at. func.date returns an ISO
    # string like "2026-04-09" in SQLite.
    day_expr = func.date(Article.fetched_at)

    rewritten_expr = func.sum(
        case((Article.was_rewritten.is_(True), 1), else_=0)
    )

    daily_rows = (
        db.query(
            day_expr.label("day"),
            func.count(Article.id).label("count"),
            rewritten_expr.label("rewritten"),
        )
        .filter(
            *base_filters,
            Article.fetched_at.isnot(None),
            day_expr >= window_start.isoformat(),
        )
        .group_by(day_expr)
        .order_by(day_expr.asc())
        .all()
    )

    # Left-fill missing days with zeros so the chart lines are continuous.
    by_day: dict[str, tuple[int, int]] = {}
    for row in daily_rows:
        day_key = row.day if isinstance(row.day, str) else str(row.day)
        rewritten = int(row.rewritten or 0)
        by_day[day_key] = (int(row.count or 0), rewritten)

    articles_over_time: list[DailyArticleCount] = []
    rewrite_rate: list[DailyRewriteRate] = []
    for offset in range(days):
        day_iso = (window_start + timedelta(days=offset)).isoformat()
        total, rewritten = by_day.get(day_iso, (0, 0))
        articles_over_time.append(DailyArticleCount(date=day_iso, count=total))
        rate = (rewritten / total) if total > 0 else 0.0
        rewrite_rate.append(
            DailyRewriteRate(
                date=day_iso,
                total=total,
                rewritten=rewritten,
                rate=rate,
            )
        )

    # Sentiment mix snapshot — same filters, no time window.
    sentiment_rows = (
        db.query(
            Article.original_sentiment.label("sentiment"),
            func.count(Article.id).label("count"),
        )
        .filter(*base_filters)
        .group_by(Article.original_sentiment)
        .all()
    )

    mix = {"positive": 0, "neutral": 0, "negative": 0}
    for row in sentiment_rows:
        key = (row.sentiment or "").lower()
        if key in mix:
            mix[key] += int(row.count or 0)

    return HistoricalStatsResponse(
        days=days,
        articles_over_time=articles_over_time,
        rewrite_rate=rewrite_rate,
        sentiment_mix=SentimentMix(**mix),
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses={
        401: {"model": RefreshErrorResponse},
        502: {"model": RefreshErrorResponse},
        504: {"model": RefreshErrorResponse},
    },
)
def refresh_articles(
    background_tasks: BackgroundTasks,
    x_news_api_key: str | None = Header(None, alias="X-News-Api-Key"),
):
    if not x_news_api_key:
        raise _refresh_error(
            status_code=401,
            code="missing_api_key",
            message="Missing X-News-Api-Key header.",
        )

    if not refresh_tracker.try_start():
        return RefreshResponse(
            status="processing",
            message="Refresh already in progress.",
        )

    try:
        response = http_requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": DEFAULT_NEWSAPI_COUNTRY,
                "pageSize": 1,
                "apiKey": x_news_api_key,
            },
            timeout=NEWSAPI_VALIDATION_TIMEOUT_SECONDS,
        )
    except http_requests.Timeout as exc:
        refresh_tracker.release_claim()
        raise _refresh_error(
            status_code=504,
            code="upstream_timeout",
            message="Timed out while validating the NewsAPI key with NewsAPI.",
        ) from exc
    except http_requests.RequestException as exc:
        refresh_tracker.release_claim()
        safe_error = _redact_validation_error(str(exc), x_news_api_key)
        raise _refresh_error(
            status_code=502,
            code="upstream_transport_failure",
            message=f"Failed to reach NewsAPI while validating the key: {safe_error}",
        ) from exc

    body = None
    try:
        body = response.json()
    except ValueError:
        body = None

    if response.status_code != 200:
        refresh_tracker.release_claim()
        if response.status_code == 401:
            message = "Invalid NewsAPI key."
            if isinstance(body, dict) and body.get("message"):
                message = f"Invalid NewsAPI key: {body['message']}"
            raise _refresh_error(
                status_code=401,
                code="invalid_api_key",
                message=message,
            )
        raise _refresh_error(
            status_code=502,
            code="upstream_transport_failure",
            message=f"NewsAPI validation failed with HTTP {response.status_code}.",
        )

    if not isinstance(body, dict):
        refresh_tracker.release_claim()
        raise _refresh_error(
            status_code=502,
            code="upstream_transport_failure",
            message="NewsAPI returned an unreadable validation response.",
        )

    if body.get("status") != "ok":
        refresh_tracker.release_claim()
        raise _refresh_error(
            status_code=401,
            code="invalid_api_key",
            message=f"Invalid NewsAPI key: {body.get('message', 'unknown error')}",
        )

    background_tasks.add_task(process_new_articles_background, x_news_api_key)

    return RefreshResponse(
        status="processing",
        message="Fetching and processing articles in the background.",
    )


@router.get("/refresh/status", response_model=RefreshStatusResponse)
def get_refresh_status():
    return RefreshStatusResponse(**refresh_tracker.snapshot())
