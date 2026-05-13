"""Tests for the pure HTML document template used by the PDF renderer."""

from __future__ import annotations

from datetime import datetime

from paper_saver.adapters.outbound.pdf_document import build_document
from paper_saver.domain.models import Article


def _fixed_clock(when: datetime):
    return lambda: when


class TestStructure:
    def test_starts_with_doctype(self) -> None:
        article = Article(
            title="T", content_html="<p>c</p>", source_url="https://e.test"
        )
        doc = build_document(article)
        assert doc.startswith("<!DOCTYPE html>")

    def test_title_appears_in_head_and_h1(self) -> None:
        article = Article(
            title="My Article",
            content_html="<p>c</p>",
            source_url="https://e.test",
        )
        doc = build_document(article)
        assert "<title>My Article</title>" in doc
        assert "<h1>My Article</h1>" in doc

    def test_source_url_appears_in_dedicated_line(self) -> None:
        article = Article(
            title="T",
            content_html="<p>c</p>",
            source_url="https://e.test/very/specific?q=1",
        )
        doc = build_document(article)
        assert (
            '<p class="source-url">https://e.test/very/specific?q=1</p>' in doc
        )

    def test_content_html_is_wrapped_in_main_unmodified(self) -> None:
        """The extractor already cleaned the content; the template inlines it."""
        article = Article(
            title="T",
            content_html="<p>kept <em>as-is</em></p>",
            source_url="https://e.test",
        )
        doc = build_document(article)
        assert "<main><p>kept <em>as-is</em></p></main>" in doc

    def test_footer_includes_generation_timestamp(self) -> None:
        article = Article(
            title="T", content_html="<p>c</p>", source_url="https://e.test"
        )
        doc = build_document(article, now=_fixed_clock(datetime(2026, 5, 13, 14, 30)))
        assert "Generated 2026-05-13 14:30" in doc


class TestHtmlEscaping:
    """Title and source URL come from arbitrary remote pages, so they must be
    HTML-escaped before being injected into the document — even though
    WeasyPrint does not execute scripts, leaving raw markup unescaped would
    silently destroy the layout of any article whose title contains < or >."""

    def test_title_is_escaped(self) -> None:
        article = Article(
            title="<script>alert(1)</script>",
            content_html="<p>safe</p>",
            source_url="https://e.test",
        )
        doc = build_document(article)
        assert "<script>alert(1)</script>" not in doc
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in doc

    def test_source_url_is_escaped(self) -> None:
        article = Article(
            title="T",
            content_html="<p>c</p>",
            source_url="https://e.test/?q=<bad>&x=1",
        )
        doc = build_document(article)
        assert "<bad>" not in doc
        assert "&lt;bad&gt;" in doc
        assert "&amp;x=1" in doc

    def test_content_html_is_NOT_escaped(self) -> None:
        """content_html has already been sanitized by the extractor — it must
        be inlined as markup, not as text."""
        article = Article(
            title="T",
            content_html="<p><strong>bold</strong> text</p>",
            source_url="https://e.test",
        )
        doc = build_document(article)
        assert "<p><strong>bold</strong> text</p>" in doc
        assert "&lt;strong&gt;" not in doc
