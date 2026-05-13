"""Extract a clean, print-ready article body from raw HTML."""

from __future__ import annotations

from typing import TypedDict

from bs4 import BeautifulSoup
from readability import Document

STRIP_TAGS = ("img", "picture", "figure", "video", "iframe", "svg", "script", "style")


class Article(TypedDict):
    title: str
    content_html: str
    source_url: str


class ExtractionError(Exception):
    """Raised when no meaningful article content can be extracted."""


def extract(html: str, source_url: str) -> Article:
    """Run Reader Mode on *html* and return a cleaned article dict.

    Strips media, scripts, inline styles, and unwraps links. Raises
    :class:`ExtractionError` if the result is empty.
    """
    doc = Document(html)
    title = (doc.short_title() or "Untitled").strip()
    summary_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(summary_html, "lxml")

    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            del tag["style"]

    for a in soup.find_all("a"):
        a.unwrap()

    cleaned = soup.decode_contents().strip()
    if not cleaned:
        raise ExtractionError("No readable content found on this page")

    return Article(title=title, content_html=cleaned, source_url=source_url)
