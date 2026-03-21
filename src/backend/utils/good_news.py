from __future__ import annotations

import json

from sqlalchemy import and_, func, not_, or_
from sqlalchemy.orm import Session

GOOD_NEWS_EXCLUDED_CATEGORIES = frozenset({"sports", "entertainment"})

# Content guardrail keywords — applied to both the normal feed and Good News mode.
# Rationale: these topics are difficult to rewrite safely, can be emotionally
# triggering, and increase the risk of harmful misinterpretation.
CONTENT_GUARDRAIL_WAR_KEYWORDS = (
    "warfare",
    "warzone",
    "war zone",
    "airstrike",
    "air strike",
    "bombing",
    "bombed",
    "missile strike",
    "missile attack",
    "shelling",
    "military offensive",
    "armed conflict",
    "troops deployed",
)
CONTENT_GUARDRAIL_SUICIDE_KEYWORDS = (
    "suicide",
    "suicidal",
    "self-harm",
    "self harm",
)
CONTENT_GUARDRAIL_DEPRESSION_KEYWORDS = (
    "depression",
    "depressed",
    "mental health crisis",
)
CONTENT_GUARDRAIL_DEATH_KEYWORDS = (
    "death toll",
    "killed",
    "murder",
    "homicide",
    "fatal shooting",
    "fatally",
    "found dead",
)
CONTENT_GUARDRAIL_GRIEF_KEYWORDS = (
    "grief",
    "grieving",
    "mourning",
    "mourners",
    "funeral",
    "vigil",
)
CONTENT_GUARDRAIL_KEYWORDS = (
    CONTENT_GUARDRAIL_WAR_KEYWORDS
    + CONTENT_GUARDRAIL_SUICIDE_KEYWORDS
    + CONTENT_GUARDRAIL_DEPRESSION_KEYWORDS
    + CONTENT_GUARDRAIL_DEATH_KEYWORDS
    + CONTENT_GUARDRAIL_GRIEF_KEYWORDS
)

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


def is_guardrailed_story(
    title: str | None = None,
    description: str | None = None,
    source_name: str | None = None,
) -> bool:
    normalized = normalize_text(title, description, source_name)
    return any(keyword in normalized for keyword in CONTENT_GUARDRAIL_KEYWORDS)


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
        or is_guardrailed_story(
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


def content_guardrail_expression(article_model):
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
        normalized_text.like(f"%{keyword}%") for keyword in CONTENT_GUARDRAIL_KEYWORDS
    ]
    return or_(*keyword_matches)


def custom_guardrail_expression(article_model, keywords: list[str]):
    """SQL expression that matches articles containing any of the given keywords."""
    if not keywords:
        # Always-false expression — nothing extra to exclude.
        return and_(False)
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
        normalized_text.like(f"%{kw.strip().lower()}%")
        for kw in keywords
        if kw.strip()
    ]
    if not keyword_matches:
        return and_(False)
    return or_(*keyword_matches)


CUSTOM_GUARDRAILS_SETTING_KEY = "custom_guardrail_keywords"


def load_custom_guardrail_keywords(db: Session) -> list[str]:
    """Load user-defined guardrail keywords from the settings table."""
    from ..models import Setting

    row = db.query(Setting).filter(Setting.key == CUSTOM_GUARDRAILS_SETTING_KEY).first()
    if row is None:
        return []
    try:
        keywords = json.loads(row.value)
        if isinstance(keywords, list):
            return [str(k) for k in keywords if str(k).strip()]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def good_news_filter_expression(article_model):
    normalized_category = func.lower(func.trim(func.coalesce(article_model.category, "")))
    return and_(
        article_model.is_good_news.is_(True),
        not_(
            or_(
                normalized_category.in_(tuple(GOOD_NEWS_EXCLUDED_CATEGORIES)),
                politics_story_expression(article_model),
                content_guardrail_expression(article_model),
            )
        ),
    )
