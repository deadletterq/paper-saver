"""Behavior specification for :class:`TelegramBotAdapter`.

The driver's user-visible behaviors:
1. Detect URLs in incoming messages and route to the use case.
2. Show a "Working on it..." status while processing.
3. On success, send the PDF and delete the status.
4. On failure, edit the status with a useful (but not leaking) message.
5. Always clean up the temporary PDF file.

We do not bring up a real Telegram bot. We construct the adapter with a dummy
token (PTB doesn't validate at build time, only on ``run_polling``), then
invoke the message handler directly with stub Update/Message objects.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from paper_saver.adapters.inbound.telegram_bot import (
    URL_PATTERN,
    TelegramBotAdapter,
    _slugify,
)
from paper_saver.application.convert_url import ConversionResult
from paper_saver.domain.errors import ExtractionError, FetchError, RenderError
from paper_saver.domain.models import Article

DUMMY_TOKEN = "123456:abcdefghijklmnopqrstuvwxyz"


# --- Pure helpers ---------------------------------------------------------- #


class TestUrlPattern:
    def test_finds_an_https_url(self) -> None:
        m = URL_PATTERN.search("read this: https://example.test/a/b?x=1")
        assert m is not None
        assert m.group(0) == "https://example.test/a/b?x=1"

    def test_finds_an_http_url(self) -> None:
        m = URL_PATTERN.search("legacy http://old.test/path here")
        assert m is not None
        assert m.group(0) == "http://old.test/path"

    def test_returns_none_when_message_has_no_url(self) -> None:
        assert URL_PATTERN.search("hello world no link") is None

    def test_does_not_match_partial_protocols(self) -> None:
        assert URL_PATTERN.search("ftp://no.test") is None
        assert URL_PATTERN.search("//no.test") is None

    def test_picks_the_first_url_when_multiple(self) -> None:
        m = URL_PATTERN.search("https://first.test/a https://second.test/b")
        assert m is not None
        assert m.group(0) == "https://first.test/a"

    def test_stops_at_whitespace(self) -> None:
        m = URL_PATTERN.search("see https://a.test/x more text")
        assert m is not None
        assert m.group(0) == "https://a.test/x"


class TestSlugify:
    def test_replaces_spaces_with_underscores(self) -> None:
        assert _slugify("Hello World") == "Hello_World"

    def test_strips_punctuation(self) -> None:
        assert _slugify("Hello, World!") == "Hello_World"

    def test_truncates_to_max_length(self) -> None:
        slug = _slugify("a" * 200, max_len=60)
        assert len(slug) == 60
        assert set(slug) == {"a"}

    def test_falls_back_to_article_when_input_is_empty(self) -> None:
        assert _slugify("") == "article"

    def test_falls_back_when_input_is_only_punctuation(self) -> None:
        assert _slugify("!!! @@@ ###") == "article"

    def test_preserves_unicode_letters(self) -> None:
        assert _slugify("Café Münster") == "Café_Münster"


# --- Driver behavior ------------------------------------------------------- #


def _stub_update(text: str) -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
    """Return (update, message, status) wired so reply_text -> status."""
    status = SimpleNamespace(
        edit_text=AsyncMock(),
        delete=AsyncMock(),
    )
    message = SimpleNamespace(
        text=text,
        reply_text=AsyncMock(return_value=status),
        reply_document=AsyncMock(),
    )
    update = SimpleNamespace(message=message)
    return update, message, status


def _adapter(convert: Any) -> TelegramBotAdapter:
    return TelegramBotAdapter(token=DUMMY_TOKEN, convert=convert)


class TestUrlDetection:
    async def test_replies_with_hint_when_no_url_in_message(self) -> None:
        convert = AsyncMock()
        update, message, _ = _stub_update("just words, no link")

        await _adapter(convert)._on_message(update, None)

        convert.assert_not_called()
        message.reply_text.assert_awaited_once()
        hint = message.reply_text.await_args.args[0]
        assert "URL" in hint or "link" in hint

    async def test_dispatches_first_url_to_use_case(self) -> None:
        convert = AsyncMock(side_effect=FetchError("stop"))
        update, _msg, _status = _stub_update(
            "check https://first.test/x and https://second.test/y"
        )

        await _adapter(convert)._on_message(update, None)

        convert.assert_awaited_once_with("https://first.test/x")


class TestHappyPath:
    async def test_sends_pdf_with_slugified_filename(self, tmp_path: Path) -> None:
        pdf = tmp_path / "rendered.pdf"
        pdf.write_bytes(b"%PDF-data")
        article = Article(
            title="Cool Title!",
            content_html="<p>c</p>",
            source_url="https://e.test",
        )
        convert = AsyncMock(
            return_value=ConversionResult(article=article, pdf_path=pdf)
        )
        update, message, _status = _stub_update("read https://e.test/p")

        await _adapter(convert)._on_message(update, None)

        message.reply_document.assert_awaited_once()
        kwargs = message.reply_document.await_args.kwargs
        assert kwargs["filename"] == "Cool_Title.pdf"
        assert kwargs["caption"] == "Cool Title!"

    async def test_deletes_status_message_after_sending(
        self, tmp_path: Path
    ) -> None:
        pdf = tmp_path / "x.pdf"
        pdf.write_bytes(b"%PDF")
        convert = AsyncMock(
            return_value=ConversionResult(
                article=Article(
                    title="x", content_html="<p>c</p>", source_url="https://e.test"
                ),
                pdf_path=pdf,
            )
        )
        update, _msg, status = _stub_update("https://e.test")

        await _adapter(convert)._on_message(update, None)

        status.delete.assert_awaited_once()

    async def test_removes_temp_pdf_after_sending(self, tmp_path: Path) -> None:
        pdf = tmp_path / "x.pdf"
        pdf.write_bytes(b"%PDF")
        convert = AsyncMock(
            return_value=ConversionResult(
                article=Article(
                    title="x", content_html="<p>c</p>", source_url="https://e.test"
                ),
                pdf_path=pdf,
            )
        )
        update, _msg, _status = _stub_update("https://e.test")

        await _adapter(convert)._on_message(update, None)

        assert not pdf.exists(), "temp PDF must be removed after the bot sends it"


class TestErrorReporting:
    async def test_fetch_error_message_is_shown_to_user(self) -> None:
        convert = AsyncMock(side_effect=FetchError("Timed out fetching https://x.test"))
        update, _msg, status = _stub_update("see https://x.test/p")

        await _adapter(convert)._on_message(update, None)

        status.edit_text.assert_awaited_once()
        text = status.edit_text.await_args.args[0]
        assert "fetch" in text.lower()
        assert "Timed out" in text

    async def test_extraction_error_message_is_shown_to_user(self) -> None:
        convert = AsyncMock(side_effect=ExtractionError("no body"))
        update, _msg, status = _stub_update("see https://x.test")

        await _adapter(convert)._on_message(update, None)

        status.edit_text.assert_awaited_once()
        assert "no body" in status.edit_text.await_args.args[0]

    async def test_render_error_is_reported(self) -> None:
        convert = AsyncMock(side_effect=RenderError("layout broke"))
        update, _msg, status = _stub_update("see https://x.test")

        await _adapter(convert)._on_message(update, None)

        status.edit_text.assert_awaited_once()
        assert "layout broke" in status.edit_text.await_args.args[0]

    async def test_unexpected_exception_does_not_leak_internals(self) -> None:
        """Untyped exceptions must not surface raw error strings to users."""
        convert = AsyncMock(side_effect=RuntimeError("AttributeError at line 42"))
        update, _msg, status = _stub_update("see https://x.test")

        await _adapter(convert)._on_message(update, None)

        status.edit_text.assert_awaited_once()
        text = status.edit_text.await_args.args[0]
        assert "AttributeError" not in text
        assert "line 42" not in text

    async def test_does_not_crash_when_message_text_is_empty(self) -> None:
        convert = AsyncMock()
        update, message, _status = _stub_update("")

        await _adapter(convert)._on_message(update, None)

        convert.assert_not_called()
        message.reply_text.assert_not_called()


class TestFilenameSlugification:
    """Filenames flow from the article title — they must always be a valid
    filename on the user's filesystem, even with hostile titles."""

    @pytest.mark.parametrize(
        "title,expected_pattern",
        [
            ("Simple Title", "Simple_Title.pdf"),
            ("Hello, World!", "Hello_World.pdf"),
            ("/etc/passwd", "etcpasswd.pdf"),
        ],
    )
    async def test_filename_is_safe(
        self, title: str, expected_pattern: str, tmp_path: Path
    ) -> None:
        pdf = tmp_path / "x.pdf"
        pdf.write_bytes(b"%PDF")
        article = Article(
            title=title, content_html="<p>c</p>", source_url="https://e.test"
        )
        convert = AsyncMock(
            return_value=ConversionResult(article=article, pdf_path=pdf)
        )
        update, message, _ = _stub_update("https://e.test")

        await _adapter(convert)._on_message(update, None)

        filename = message.reply_document.await_args.kwargs["filename"]
        # Never contains a path separator.
        assert "/" not in filename
        assert "\\" not in filename
        # Strictly word-characters + underscore + .pdf
        assert re.fullmatch(r"[\w_-]+\.pdf", filename)
