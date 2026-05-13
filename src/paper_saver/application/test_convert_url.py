"""Behavioral specification for the :class:`ConvertUrlToPdf` use case.

The use case is the heart of the application — it orchestrates fetcher →
extractor → renderer. These tests exercise that orchestration with fakes
for each port, so we specify the contract independently of any adapter.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from paper_saver._fakes import (
    FakeArticleExtractor,
    FakePageFetcher,
    FakePdfRenderer,
)
from paper_saver.application.convert_url import ConversionResult, ConvertUrlToPdf
from paper_saver.domain.errors import ExtractionError, FetchError, RenderError
from paper_saver.domain.models import Article


def _make_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "rendered.pdf"
    pdf.write_bytes(b"%PDF-fake")
    return pdf


class TestHappyPath:
    async def test_calls_fetcher_with_requested_url(self, tmp_path: Path) -> None:
        fetcher = FakePageFetcher()
        convert = ConvertUrlToPdf(
            fetcher, FakeArticleExtractor(), FakePdfRenderer(_make_pdf(tmp_path))
        )

        await convert("https://example.test/post")

        assert fetcher.calls == ["https://example.test/post"]

    async def test_passes_fetched_html_and_final_url_to_extractor(
        self, tmp_path: Path
    ) -> None:
        """The extractor must see *the redirected URL*, not the original one,
        so the rendered PDF cites the canonical source."""
        fetcher = FakePageFetcher(
            html="<html>hello</html>", final_url="https://canonical.test/x"
        )
        extractor = FakeArticleExtractor()
        convert = ConvertUrlToPdf(
            fetcher, extractor, FakePdfRenderer(_make_pdf(tmp_path))
        )

        await convert("https://t.co/abc")

        assert extractor.calls == [("<html>hello</html>", "https://canonical.test/x")]

    async def test_renders_the_extracted_article(self, tmp_path: Path) -> None:
        article = Article(
            title="Deep Work",
            content_html="<p>c</p>",
            source_url="https://x.test",
        )
        renderer = FakePdfRenderer(_make_pdf(tmp_path))
        convert = ConvertUrlToPdf(
            FakePageFetcher(), FakeArticleExtractor(article=article), renderer
        )

        await convert("https://x.test")

        assert renderer.calls == [article]

    async def test_returns_result_pairing_article_with_pdf(
        self, tmp_path: Path
    ) -> None:
        pdf = _make_pdf(tmp_path)
        article = Article(
            title="T", content_html="<p>c</p>", source_url="https://x.test"
        )
        convert = ConvertUrlToPdf(
            FakePageFetcher(),
            FakeArticleExtractor(article=article),
            FakePdfRenderer(pdf),
        )

        result = await convert("https://x.test")

        assert isinstance(result, ConversionResult)
        assert result.article is article
        assert result.pdf_path == pdf


class TestErrorPropagation:
    async def test_fetch_error_is_raised_and_extractor_is_not_called(
        self, tmp_path: Path
    ) -> None:
        fetcher = FakePageFetcher(raise_with=FetchError("HTTP 404"))
        extractor = FakeArticleExtractor()
        renderer = FakePdfRenderer(_make_pdf(tmp_path))
        convert = ConvertUrlToPdf(fetcher, extractor, renderer)

        with pytest.raises(FetchError, match="HTTP 404"):
            await convert("https://gone.test")

        assert extractor.calls == [], "extractor must not run if fetch failed"
        assert renderer.calls == [], "renderer must not run if fetch failed"

    async def test_extraction_error_is_raised_and_renderer_is_not_called(
        self, tmp_path: Path
    ) -> None:
        extractor = FakeArticleExtractor(raise_with=ExtractionError("empty page"))
        renderer = FakePdfRenderer(_make_pdf(tmp_path))
        convert = ConvertUrlToPdf(FakePageFetcher(), extractor, renderer)

        with pytest.raises(ExtractionError, match="empty page"):
            await convert("https://thin.test")

        assert renderer.calls == [], "renderer must not run if extraction failed"

    async def test_render_error_propagates_to_caller(self, tmp_path: Path) -> None:
        renderer = FakePdfRenderer(
            _make_pdf(tmp_path), raise_with=RenderError("css blew up")
        )
        convert = ConvertUrlToPdf(
            FakePageFetcher(), FakeArticleExtractor(), renderer
        )

        with pytest.raises(RenderError, match="css blew up"):
            await convert("https://x.test")


class TestSyncPortsAreOffloadedToThread:
    """The extractor and renderer are synchronous, but the bot's event loop
    must not block. The use case must invoke them via ``asyncio.to_thread``."""

    async def test_extractor_runs_off_the_event_loop_thread(
        self, tmp_path: Path
    ) -> None:
        seen: list[int] = []

        class ThreadRecordingExtractor:
            def extract(self, html: str, source_url: str) -> Article:
                seen.append(threading.get_ident())
                return Article(
                    title="x", content_html="<p>c</p>", source_url=source_url
                )

        convert = ConvertUrlToPdf(
            FakePageFetcher(),
            ThreadRecordingExtractor(),
            FakePdfRenderer(_make_pdf(tmp_path)),
        )
        await convert("https://x.test")

        assert seen and seen[0] != threading.get_ident()

    async def test_renderer_runs_off_the_event_loop_thread(
        self, tmp_path: Path
    ) -> None:
        seen: list[int] = []
        pdf = _make_pdf(tmp_path)

        class ThreadRecordingRenderer:
            def render(self, article: Article) -> Path:
                seen.append(threading.get_ident())
                return pdf

        convert = ConvertUrlToPdf(
            FakePageFetcher(), FakeArticleExtractor(), ThreadRecordingRenderer()
        )
        await convert("https://x.test")

        assert seen and seen[0] != threading.get_ident()
