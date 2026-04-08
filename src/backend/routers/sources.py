import re

import requests as http_requests
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy import func, not_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article
from ..schemas import (
    CategoriesResponse,
    CategoryItem,
    RefreshErrorCode,
    RefreshErrorDetail,
    RefreshErrorResponse,
    RefreshResponse,
    RefreshStatusResponse,
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
