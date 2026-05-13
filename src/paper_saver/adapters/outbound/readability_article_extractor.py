"""Reader Mode extractor combining readability-lxml and BeautifulSoup."""

from __future__ import annotations

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

        for a in soup.find_all("a"):
            a.unwrap()

        cleaned = soup.decode_contents().strip()
        if not cleaned:
            raise ExtractionError("No readable content found on this page")

        return Article(title=title, content_html=cleaned, source_url=source_url)
