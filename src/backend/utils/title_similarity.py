"""Fuzzy title matching to group articles covering the same story."""

from __future__ import annotations

import re
import string
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..models import Article

# Common English stop words to ignore when comparing headlines.
_STOP_WORDS = frozenset(
    "a an the in on at to for of is are was were be been being "
    "has have had do does did will would shall should can could may might "
    "and or but not no nor so yet by from with as if then than that this "
    "it its he she they we you i me my his her our their us them "
    "also just about over after before up down out off into very too "
    "says said new how what when where who which why all more most some "
    "any many much such each every other another few both same own "
    "here there these those now still well back".split()
)

# Minimum significant words a title must have after cleaning to be groupable.
_MIN_WORDS = 2

# Jaccard similarity threshold for considering two articles related.
_SIMILARITY_THRESHOLD = 0.30

# Minimum group size to include in results.
_MIN_GROUP_SIZE = 2


def _normalize_title(title: str) -> set[str]:
    """Lowercase, strip punctuation, remove stop words, return word set."""
    text = title.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Collapse whitespace and split.
    words = text.split()
    return {w for w in words if w not in _STOP_WORDS and len(w) > 1}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two word sets."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


@dataclass
class ArticleGroup:
    """A group of articles covering the same story."""

    representative_title: str
    article_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)


def group_articles(
    articles: Sequence[Article],
    threshold: float = _SIMILARITY_THRESHOLD,
    min_group_size: int = _MIN_GROUP_SIZE,
) -> list[ArticleGroup]:
    """Group articles by fuzzy title similarity using greedy clustering.

    Returns groups with at least ``min_group_size`` articles, sorted by
    group size descending.
    """
    # Pre-compute normalized word sets.
    word_sets: list[set[str]] = []
    for article in articles:
        words = _normalize_title(article.original_title or "")
        word_sets.append(words)

    grouped: set[int] = set()
    groups: list[ArticleGroup] = []

    for i, article_i in enumerate(articles):
        if i in grouped:
            continue
        if len(word_sets[i]) < _MIN_WORDS:
            continue

        # Find all ungrouped articles similar to this one.
        members = [i]
        for j in range(i + 1, len(articles)):
            if j in grouped:
                continue
            if len(word_sets[j]) < _MIN_WORDS:
                continue
            if _jaccard(word_sets[i], word_sets[j]) >= threshold:
                members.append(j)

        if len(members) < min_group_size:
            continue

        # Use the first article's title as the representative.
        group = ArticleGroup(
            representative_title=articles[members[0]].original_title,
            article_ids=[articles[m].id for m in members],
            sources=list(
                dict.fromkeys(
                    (articles[m].source_name or articles[m].source_id or "Unknown")
                    for m in members
                )
            ),
            countries=list(
                dict.fromkeys(articles[m].country for m in members)
            ),
        )
        groups.append(group)
        grouped.update(members)

    # Sort by group size descending, then alphabetically by representative title.
    groups.sort(key=lambda g: (-len(g.article_ids), g.representative_title))
    return groups
