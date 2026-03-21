from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ArticleResponse(BaseModel):
    """Single article serialized for JSON responses."""
    id: str
    original_title: str
    rewritten_title: str | None = None
    tldr: str | None = None
    original_description: str | None = None
    source_name: str | None = None
    source_id: str | None = None
    author: str | None = None
    url: str
    image_url: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    was_rewritten: bool = False
    original_sentiment: str | None = None
    sentiment_score: float | None = None
    is_good_news: bool = False
    category: str | None = None
    country: str = "us"
    processing_status: str = "pending"

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class SourceItem(BaseModel):
    source_name: str
    source_id: str
    article_count: int


class SourcesResponse(BaseModel):
    sources: list[SourceItem]


class CategoryItem(BaseModel):
    name: str
    count: int


class CategoriesResponse(BaseModel):
    categories: list[CategoryItem]


class StatsResponse(BaseModel):
    total_articles: int
    rewritten_count: int
    good_news_count: int
    sources_count: int
    latest_fetch: datetime | None = None


class RefreshResponse(BaseModel):
    status: str
    message: str


RefreshErrorCode = Literal[
    "missing_api_key",
    "invalid_api_key",
    "upstream_timeout",
    "upstream_transport_failure",
]


class RefreshErrorDetail(BaseModel):
    code: RefreshErrorCode
    message: str


class RefreshErrorResponse(BaseModel):
    detail: RefreshErrorDetail


class RefreshStatusResponse(BaseModel):
    status: str
    message: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    new_articles: int = 0
    processed_articles: int = 0
    failed_articles: int = 0
