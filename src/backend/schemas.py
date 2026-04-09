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


class DailyArticleCount(BaseModel):
    """One day's total processed article count for the stats page."""
    date: str  # ISO date, e.g. "2026-04-09"
    count: int


class DailyRewriteRate(BaseModel):
    """One day's rewrite rate — total vs rewritten headlines."""
    date: str
    total: int
    rewritten: int
    rate: float  # 0.0 – 1.0


class SentimentMix(BaseModel):
    """Snapshot sentiment distribution across all filtered articles."""
    positive: int
    neutral: int
    negative: int


class HistoricalStatsResponse(BaseModel):
    """Time-series + distribution data for the /stats page charts."""
    days: int
    articles_over_time: list[DailyArticleCount]
    rewrite_rate: list[DailyRewriteRate]
    sentiment_mix: SentimentMix


class ComparisonArticleSummary(BaseModel):
    """Abbreviated article within a comparison group."""
    id: str
    original_title: str
    rewritten_title: str | None = None
    source_name: str | None = None
    country: str = "us"
    original_sentiment: str | None = None
    sentiment_score: float | None = None
    url: str
    image_url: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class ComparisonGroup(BaseModel):
    """A group of articles covering the same story."""
    representative_title: str
    articles: list[ComparisonArticleSummary]
    sources: list[str]
    countries: list[str]


class ComparisonResponse(BaseModel):
    groups: list[ComparisonGroup]
    total_groups: int


class ComparisonAnalyseRequest(BaseModel):
    """Request body for POST /api/comparison/analyse."""
    article_ids: list[str]


class ComparisonSourceTone(BaseModel):
    """Per-source tone summary within a comparison analysis."""
    source_name: str
    country: str
    tone: str


class ComparisonAnalysis(BaseModel):
    """AI-generated framing analysis for a group of related articles."""
    representative_title: str
    summary: str
    framing_differences: list[str]
    source_tones: list[ComparisonSourceTone]


class GuardrailsResponse(BaseModel):
    keywords: list[str]


class GuardrailsUpdateRequest(BaseModel):
    keywords: list[str]


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
