from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, nulls_last
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article
from ..schemas import ArticleListResponse, ArticleResponse
from ..utils.source_normalization import (
    clean_source_value,
    normalized_source_label,
    source_label_expression,
)

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _serialize_article(article: Article) -> ArticleResponse:
    return ArticleResponse.model_validate(article).model_copy(
        update={
            "source_name": normalized_source_label(
                article.source_name,
                article.source_id,
            )
        }
    )


@router.get("", response_model=ArticleListResponse)
def get_articles(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    good_news_only: bool = Query(default=False),
    source: str | None = Query(default=None),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    query = db.query(Article).filter(Article.processing_status == "processed")

    if good_news_only:
        query = query.filter(Article.is_good_news == True)

    normalized_source = clean_source_value(source)
    if normalized_source is not None:
        query = query.filter(source_label_expression(Article) == normalized_source)

    if category is not None:
        query = query.filter(Article.category == category)

    if search is not None:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Article.original_title.ilike(pattern),
                Article.rewritten_title.ilike(pattern),
            )
        )

    query = query.order_by(nulls_last(Article.published_at.desc()))

    total = query.count()

    offset = (page - 1) * per_page
    articles = query.offset(offset).limit(per_page).all()

    has_more = (offset + len(articles)) < total

    return ArticleListResponse(
        articles=[_serialize_article(article) for article in articles],
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: str,
    db: Session = Depends(get_db),
) -> ArticleResponse:
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.processing_status == "processed",
        )
        .first()
    )

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return _serialize_article(article)
