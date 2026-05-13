"""Inbound adapter: Telegram Bot driver using python-telegram-bot v22+."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from paper_saver.application.convert_url import ConvertUrlToPdf
from paper_saver.domain.errors import ExtractionError, FetchError, RenderError

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

INTRO_TEXT = (
    "Send me a URL and I'll reply with a clean, print-optimized PDF of the "
    "article — no images, no ads, no clutter, just text formatted to save "
    "paper. Works best on articles, blogs, docs, and wikis."
)

logger = logging.getLogger(__name__)


def _slugify(title: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE).strip()
    slug = re.sub(r"\s+", "_", slug)
    return (slug[:max_len] or "article").rstrip("_")


class TelegramBotAdapter:
    """Drives the bot lifecycle and routes incoming URLs to the use case."""

    def __init__(self, token: str, convert: ConvertUrlToPdf) -> None:
        self._convert = convert
        self._application = Application.builder().token(token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self._application.add_handler(CommandHandler("start", self._on_intro))
        self._application.add_handler(CommandHandler("help", self._on_intro))
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

    async def _on_intro(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is not None:
            await update.message.reply_text(INTRO_TEXT)

    async def _on_message(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if message is None or not message.text:
            return

        match = URL_PATTERN.search(message.text)
        if match is None:
            await message.reply_text(
                "I didn't find a URL in that message. Send me an http(s) link "
                "and I'll turn it into a print-friendly PDF."
            )
            return

        url = match.group(0)
        status = await message.reply_text(f"Working on it… fetching {url}")

        pdf_path: Path | None = None
        try:
            result = await self._convert(url)
            pdf_path = result.pdf_path
            filename = f"{_slugify(result.article.title)}.pdf"
            with pdf_path.open("rb") as fh:
                await message.reply_document(
                    document=fh,
                    filename=filename,
                    caption=result.article.title[:1024],
                )
            await status.delete()
        except FetchError as exc:
            logger.info("fetch failed for %s: %s", url, exc)
            await status.edit_text(f"Couldn't fetch that page: {exc}")
        except ExtractionError as exc:
            logger.info("extraction failed for %s: %s", url, exc)
            await status.edit_text(f"Couldn't extract an article: {exc}")
        except RenderError as exc:
            logger.exception("render failed for %s", url)
            await status.edit_text(f"Couldn't render the PDF: {exc}")
        except Exception:
            logger.exception("unexpected failure processing %s", url)
            await status.edit_text(
                "Something went wrong while building your PDF. "
                "Please try another URL."
            )
        finally:
            if pdf_path is not None:
                try:
                    pdf_path.unlink(missing_ok=True)
                except OSError as exc:
                    logger.warning("failed to remove temp PDF %s: %s", pdf_path, exc)

    def run(self) -> None:
        logger.info("paper-saver bot starting")
        self._application.run_polling(allowed_updates=Update.ALL_TYPES)
