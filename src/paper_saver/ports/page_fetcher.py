"""Outbound port: fetch raw HTML from a URL."""

from __future__ import annotations

from typing import Protocol


class PageFetcher(Protocol):
    """Fetches the raw HTML of a remote page."""

    async def fetch(self, url: str) -> tuple[str, str]:
        """Return ``(html, final_url)`` for *url*.

        The final URL reflects any redirects that were followed. Implementations
        must raise :class:`paper_saver.domain.errors.FetchError` on any failure.
        """
        ...
