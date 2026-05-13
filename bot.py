"""Paper-Saver Telegram bot entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from extractor import ExtractionError, extract
from fetcher import FetchError, fetch
from pdf_renderer import render_pdf

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

INTRO_TEXT = (
    "Send me a URL and I'll reply with a clean, print-optimized PDF of the "
    "article — no images, no ads, no clutter, just text formatted to save "
    "paper. Works best on articles, blogs, docs, and wikis."
)

logger = logging.getLogger("paper-saver")


def _slugify_for_filename(title: str, max_len: int = 60) -> str:
    """Make *title* safe to use as a filename."""
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE).strip()
    slug = re.sub(r"\s+", "_", slug)
    return (slug[:max_len] or "article").rstrip("_")


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to /start with a description of the bot."""
    if update.message is not None:
        await update.message.reply_text(INTRO_TEXT)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to /help with the same description as /start."""
    if update.message is not None:
        await update.message.reply_text(INTRO_TEXT)


async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages, extracting the first URL found."""
    message = update.message
    if message is None or not message.text:
        return

    match = URL_PATTERN.search(message.text)
    if match is None:
        await message.reply_text(
            "I didn't find a URL in that message. Send me an http(s) link and "
            "I'll turn it into a print-friendly PDF."
        )
        return

    url = match.group(0)
    status = await message.reply_text(f"Working on it… fetching {url}")

    pdf_path: Path | None = None
    try:
        html, final_url = await fetch(url)
        article = await asyncio.to_thread(extract, html, final_url)
        pdf_path = await asyncio.to_thread(
            render_pdf,
            article["title"],
            article["content_html"],
            article["source_url"],
        )

        filename = f"{_slugify_for_filename(article['title'])}.pdf"
        with pdf_path.open("rb") as fh:
            await message.reply_document(
                document=fh,
                filename=filename,
                caption=article["title"][:1024],
            )
        await status.delete()
    except FetchError as exc:
        logger.info("fetch failed for %s: %s", url, exc)
        await status.edit_text(f"Couldn't fetch that page: {exc}")
    except ExtractionError as exc:
        logger.info("extraction failed for %s: %s", url, exc)
        await status.edit_text(f"Couldn't extract an article: {exc}")
    except Exception:
        logger.exception("unexpected failure processing %s", url)
        await status.edit_text(
            "Something went wrong while building your PDF. Please try another URL."
        )
    finally:
        if pdf_path is not None:
            try:
                pdf_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("failed to remove temp PDF %s: %s", pdf_path, exc)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    """Boot the Telegram bot and run polling until interrupted."""
    load_dotenv()
    _configure_logging()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set; cannot start bot")
        sys.exit(1)

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("paper-saver bot starting")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
