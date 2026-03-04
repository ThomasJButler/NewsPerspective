import requests as http_requests
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Article
from ..schemas import RefreshResponse, SourceItem, SourcesResponse, StatsResponse
from ..services.article_processor import process_new_articles_background

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources", response_model=SourcesResponse)
def get_sources(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Article.source_name,
            Article.source_id,
            func.count(Article.id).label("article_count"),
        )
        .filter(Article.processing_status == "processed")
        .group_by(Article.source_name, Article.source_id)
        .order_by(func.count(Article.id).desc())
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


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_articles = (
        db.query(func.count(Article.id))
        .filter(Article.processing_status == "processed")
        .scalar()
        or 0
    )

    rewritten_count = (
        db.query(func.count(Article.id))
        .filter(Article.processing_status == "processed", Article.was_rewritten == True)
        .scalar()
        or 0
    )

    good_news_count = (
        db.query(func.count(Article.id))
        .filter(Article.processing_status == "processed", Article.is_good_news == True)
        .scalar()
        or 0
    )

    sources_count = (
        db.query(func.count(func.distinct(Article.source_name)))
        .filter(Article.processing_status == "processed")
        .scalar()
        or 0
    )

    latest_fetch = (
        db.query(func.max(Article.fetched_at))
        .filter(Article.processing_status == "processed")
        .scalar()
    )

    return StatsResponse(
        total_articles=total_articles,
        rewritten_count=rewritten_count,
        good_news_count=good_news_count,
        sources_count=sources_count,
        latest_fetch=latest_fetch,
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_articles(
    background_tasks: BackgroundTasks,
    x_news_api_key: str | None = Header(None, alias="X-News-Api-Key"),
):
    if not x_news_api_key:
        raise HTTPException(status_code=401, detail="Missing X-News-Api-Key header")

    try:
        response = http_requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "gb", "pageSize": 1, "apiKey": x_news_api_key},
        )
    except http_requests.RequestException as exc:
        raise HTTPException(
            status_code=401, detail=f"Failed to validate NewsAPI key: {exc}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid NewsAPI key: received HTTP {response.status_code}",
        )

    body = response.json()
    if body.get("status") != "ok":
        raise HTTPException(
            status_code=401,
            detail=f"Invalid NewsAPI key: {body.get('message', 'unknown error')}",
        )

    background_tasks.add_task(process_new_articles_background, x_news_api_key)

    return RefreshResponse(
        status="processing",
        message="Fetching and processing articles in the background",
    )
