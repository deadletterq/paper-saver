"""Use case: convert a URL into a print-ready PDF."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from paper_saver.domain.models import Article
from paper_saver.ports.article_extractor import ArticleExtractor
from paper_saver.ports.page_fetcher import PageFetcher
from paper_saver.ports.pdf_renderer import PdfRenderer


@dataclass(frozen=True, slots=True)
class ConversionResult:
    article: Article
    pdf_path: Path


class ConvertUrlToPdf:
    """Coordinates fetch → extract → render for a single URL."""

    def __init__(
        self,
        fetcher: PageFetcher,
        extractor: ArticleExtractor,
        renderer: PdfRenderer,
    ) -> None:
        self._fetcher = fetcher
        self._extractor = extractor
        self._renderer = renderer

    async def __call__(self, url: str) -> ConversionResult:
        html, final_url = await self._fetcher.fetch(url)
        article = await asyncio.to_thread(self._extractor.extract, html, final_url)
        pdf_path = await asyncio.to_thread(self._renderer.render, article)
        return ConversionResult(article=article, pdf_path=pdf_path)
