"""Domain models — plain dataclasses with no external dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Article:
    """A clean, print-ready article extracted from a web page."""

    title: str
    content_html: str
    source_url: str
    references: tuple[str, ...] = field(default_factory=tuple)
