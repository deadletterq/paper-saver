"""Composition root — wires ports to adapters and starts the bot."""

from __future__ import annotations

import logging
import sys

from paper_saver.adapters.inbound.telegram_bot import TelegramBotAdapter
from paper_saver.adapters.outbound.httpx_page_fetcher import HttpxPageFetcher
from paper_saver.adapters.outbound.readability_article_extractor import (
    ReadabilityArticleExtractor,
)
from paper_saver.adapters.outbound.weasyprint_pdf_renderer import WeasyPrintPdfRenderer
from paper_saver.application.convert_url import ConvertUrlToPdf
from paper_saver.config import Settings


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def run() -> None:
    """Boot the bot. Console-script entry point for ``paper-saver``."""
    _configure_logging()
    logger = logging.getLogger("paper_saver")

    try:
        settings = Settings.from_env()
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    convert = ConvertUrlToPdf(
        fetcher=HttpxPageFetcher(),
        extractor=ReadabilityArticleExtractor(),
        renderer=WeasyPrintPdfRenderer(),
    )
    TelegramBotAdapter(token=settings.telegram_bot_token, convert=convert).run()
