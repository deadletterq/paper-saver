"""Test doubles (fakes) implementing the outbound ports.

A fake is a working in-memory implementation: it satisfies the port contract
with deterministic, controllable behavior, and records the calls it received.
Fakes are preferred over mocks because they are simple enough to be correct
by inspection — they cannot "lie" about an interface the way a mock can.

This module is excluded from the published wheel (see ``pyproject.toml``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from paper_saver.domain.errors import ExtractionError, FetchError, RenderError
from paper_saver.domain.models import Article

DEFAULT_HTML = "<html><body><p>real body</p></body></html>"
DEFAULT_FINAL_URL = "https://example.test/final"
DEFAULT_ARTICLE = Article(
    title="A Story",
    content_html="<p>Body.</p>",
    source_url=DEFAULT_FINAL_URL,
)


@dataclass
class FakePageFetcher:
    """In-memory fetcher: yields canned ``(html, final_url)`` or raises."""

    html: str = DEFAULT_HTML
    final_url: str = DEFAULT_FINAL_URL
    raise_with: FetchError | None = None
    calls: list[str] = field(default_factory=list)

    async def fetch(self, url: str) -> tuple[str, str]:
        self.calls.append(url)
        if self.raise_with is not None:
            raise self.raise_with
        return self.html, self.final_url


@dataclass
class FakeArticleExtractor:
    """Returns a fixed :class:`Article` or raises :class:`ExtractionError`."""

    article: Article = DEFAULT_ARTICLE
    raise_with: ExtractionError | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def extract(self, html: str, source_url: str) -> Article:
        self.calls.append((html, source_url))
        if self.raise_with is not None:
            raise self.raise_with
        return self.article


@dataclass
class FakePdfRenderer:
    """Returns a pre-created :class:`Path` or raises :class:`RenderError`."""

    pdf_path: Path
    raise_with: RenderError | None = None
    calls: list[Article] = field(default_factory=list)

    def render(self, article: Article) -> Path:
        self.calls.append(article)
        if self.raise_with is not None:
            raise self.raise_with
        return self.pdf_path
