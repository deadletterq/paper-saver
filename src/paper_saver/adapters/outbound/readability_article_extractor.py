"""Reader Mode extractor combining readability-lxml and BeautifulSoup."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from readability import Document

from paper_saver.domain.errors import ExtractionError
from paper_saver.domain.models import Article

STRIP_TAGS = ("img", "picture", "figure", "video", "iframe", "svg", "script", "style")


class ReadabilityArticleExtractor:
    """Extracts the main article body and strips non-printable elements."""

    def extract(self, html: str, source_url: str) -> Article:
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

        references = _replace_anchors_with_references(soup, source_url)

        if not soup.get_text(strip=True):
            raise ExtractionError("No readable content found on this page")

        cleaned = soup.decode_contents().strip()
        return Article(
            title=title,
            content_html=cleaned,
            source_url=source_url,
            references=tuple(references),
        )


def _replace_anchors_with_references(soup: BeautifulSoup, source_url: str) -> list[str]:
    """Replace ``<a href>`` with ``text<sup class="ref">[n]</sup>``.

    URLs are collected in first-appearance order and deduplicated, so the same
    citation gets the same number. Anchors without a usable target (no href,
    fragment-only, ``mailto:`` / ``javascript:`` etc.) are unwrapped silently —
    they can't help a reader on paper, so no need to clutter the appendix.
    """
    references: list[str] = []
    url_to_index: dict[str, int] = {}

    for a in soup.find_all("a"):
        absolute = _useful_href(a.get("href", ""), source_url)
        if absolute is None or not a.get_text(strip=True):
            # No usable target, or no visible text to attach the marker to
            # (e.g. anchor wrapped only an image that was just stripped).
            a.unwrap()
            continue

        index = url_to_index.get(absolute)
        if index is None:
            index = len(references) + 1
            url_to_index[absolute] = index
            references.append(absolute)

        marker = soup.new_tag("sup", attrs={"class": "ref"})
        marker.string = f"[{index}]"
        a.append(marker)
        a.unwrap()

    return references


def _useful_href(raw_href: str, source_url: str) -> str | None:
    href = (raw_href or "").strip()
    if not href or href.startswith("#"):
        return None
    absolute = urljoin(source_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return absolute
