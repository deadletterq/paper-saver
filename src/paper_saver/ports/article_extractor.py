"""Outbound port: extract a clean article from raw HTML."""

from __future__ import annotations

from typing import Protocol

from paper_saver.domain.models import Article


class ArticleExtractor(Protocol):
    """Extracts a print-ready :class:`Article` from raw HTML."""

    def extract(self, html: str, source_url: str) -> Article:
        """Return a cleaned article.

        Raises :class:`paper_saver.domain.errors.ExtractionError` if no
        meaningful content can be found.
        """
        ...
