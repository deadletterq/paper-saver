"""Live network checks for :class:`CurlCffiPageFetcher`.

These tests hit the real internet and are skipped by default. Run with::

    uv run pytest -m network

Each test pins a specific URL we want to know works end-to-end through the
fetcher (Chrome-impersonated TLS, redirect handling, content-type, size limits).
"""

from __future__ import annotations

import pytest

from paper_saver.adapters.outbound.curl_cffi_page_fetcher import CurlCffiPageFetcher

pytestmark = pytest.mark.network


class TestArchiveDotPh:
    """archive.today behaviour we observed in practice (see fetcher docstring).

    Bare snapshot IDs like ``/dWANk`` are reCAPTCHA-gated and cannot be
    fetched. Wrapped forms that embed the original URL in the path can.
    """

    async def test_bare_snapshot_id_fails_with_clear_message(self) -> None:
        from paper_saver.domain.errors import FetchError

        with pytest.raises(FetchError, match="snapshot IDs are gated by reCAPTCHA"):
            await CurlCffiPageFetcher().fetch("https://archive.ph/dWANk")

    async def test_wrapped_form_unwraps_and_fetches_original(self) -> None:
        # archive.ph/<scheme>://... unwrap should hit the live origin, not archive.ph.
        html, final_url = await CurlCffiPageFetcher().fetch(
            "https://archive.ph/https://example.com/"
        )
        assert html, "fetcher returned empty body"
        assert "<html" in html.lower(), "response is not HTML"
        assert "example.com" in final_url, f"unexpected final URL: {final_url}"
