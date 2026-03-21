from __future__ import annotations

from typing import Protocol, runtime_checkable


class NewsFetchError(RuntimeError):
    """Raised when news fetching fails and the refresh should be marked failed."""


@runtime_checkable
class NewsSource(Protocol):
    """Protocol for pluggable news sources.

    Implementations fetch articles from a news provider and return them
    as normalized dicts ready for database insertion.

    Each returned dict must include these keys:
        original_title, original_description, source_name, source_id,
        author, url, image_url, published_at, category, country.

    Implementations should raise NewsFetchError on unrecoverable failures.
    """

    def fetch_all_categories(self, country: str) -> list[dict]:
        """Fetch headlines across all categories for the given country."""
        ...
