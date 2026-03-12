from __future__ import annotations

from sqlalchemy import and_, func, not_

GOOD_NEWS_EXCLUDED_CATEGORIES = frozenset({"sports", "entertainment"})


def normalize_category(category: str | None) -> str | None:
    if category is None:
        return None

    normalized = category.strip().lower()
    return normalized or None


def apply_good_news_rules(is_good_news: bool, category: str | None) -> bool:
    normalized_category = normalize_category(category)
    return bool(is_good_news) and normalized_category not in GOOD_NEWS_EXCLUDED_CATEGORIES


def good_news_filter_expression(article_model):
    normalized_category = func.lower(func.trim(func.coalesce(article_model.category, "")))
    return and_(
        article_model.is_good_news.is_(True),
        not_(normalized_category.in_(tuple(GOOD_NEWS_EXCLUDED_CATEGORIES))),
    )
