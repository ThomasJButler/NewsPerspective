from __future__ import annotations

from sqlalchemy import and_, func, not_, or_

GOOD_NEWS_EXCLUDED_CATEGORIES = frozenset({"sports", "entertainment"})
POLITICS_TOPIC_KEYWORDS = (
    "politic",
    "election",
    "electoral",
    "ballot",
    "voting",
    "senate",
    "congress",
    "parliament",
    "lawmakers",
    "white house",
    "government",
    "prime minister",
    "governor",
    "mayor",
    "cabinet",
    "democrat",
    "republican",
)


def normalize_category(category: str | None) -> str | None:
    if category is None:
        return None

    normalized = category.strip().lower()
    return normalized or None


def normalize_text(*values: str | None) -> str:
    parts = [
        value.strip().lower()
        for value in values
        if isinstance(value, str) and value.strip()
    ]
    return " ".join(parts)


def is_politics_story(
    category: str | None,
    title: str | None = None,
    description: str | None = None,
    source_name: str | None = None,
) -> bool:
    normalized_category = normalize_category(category)
    if normalized_category == "politics":
        return True

    normalized_text = normalize_text(title, description, source_name)
    return any(keyword in normalized_text for keyword in POLITICS_TOPIC_KEYWORDS)


def apply_good_news_rules(
    is_good_news: bool,
    category: str | None,
    title: str | None = None,
    description: str | None = None,
    source_name: str | None = None,
) -> bool:
    normalized_category = normalize_category(category)
    return bool(is_good_news) and not (
        normalized_category in GOOD_NEWS_EXCLUDED_CATEGORIES
        or is_politics_story(
            category,
            title=title,
            description=description,
            source_name=source_name,
        )
    )


def politics_story_expression(article_model):
    normalized_category = func.lower(func.trim(func.coalesce(article_model.category, "")))
    normalized_text = func.lower(
        func.trim(
            func.coalesce(article_model.original_title, "")
            + " "
            + func.coalesce(article_model.original_description, "")
            + " "
            + func.coalesce(article_model.source_name, "")
        )
    )
    keyword_matches = [
        normalized_text.like(f"%{keyword}%") for keyword in POLITICS_TOPIC_KEYWORDS
    ]
    return or_(normalized_category == "politics", *keyword_matches)


def good_news_filter_expression(article_model):
    normalized_category = func.lower(func.trim(func.coalesce(article_model.category, "")))
    return and_(
        article_model.is_good_news.is_(True),
        not_(
            or_(
                normalized_category.in_(tuple(GOOD_NEWS_EXCLUDED_CATEGORIES)),
                politics_story_expression(article_model),
            )
        ),
    )
