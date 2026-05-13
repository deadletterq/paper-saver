"""Behavior specification for :class:`HttpxPageFetcher`.

No real network is used. Each test installs an ``httpx.MockTransport`` so the
fetcher routes to a handler that returns exactly the response under test.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from paper_saver.adapters.outbound import httpx_page_fetcher as fetcher_module
from paper_saver.adapters.outbound.httpx_page_fetcher import HttpxPageFetcher
from paper_saver.domain.errors import FetchError

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def mocked_http(monkeypatch: pytest.MonkeyPatch) -> Callable[[Handler], None]:
    """Patch ``httpx.AsyncClient`` so the fetcher routes through MockTransport."""
    original = httpx.AsyncClient

    def install(handler: Handler) -> None:
        def patched(*args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs["transport"] = httpx.MockTransport(handler)
            return original(*args, **kwargs)

        monkeypatch.setattr(fetcher_module.httpx, "AsyncClient", patched)

    return install


class TestSuccessfulFetch:
    async def test_returns_decoded_html(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        mocked_http(
            lambda _r: httpx.Response(
                200,
                text="<html><body>ok</body></html>",
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )
        html, _ = await HttpxPageFetcher().fetch("https://e.test/a")
        assert "<body>ok</body>" in html

    async def test_returns_original_url_when_no_redirect(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        mocked_http(
            lambda _r: httpx.Response(
                200, text="<html></html>", headers={"content-type": "text/html"}
            )
        )
        _, final = await HttpxPageFetcher().fetch("https://e.test/a")
        assert final == "https://e.test/a"

    async def test_returns_redirected_url_after_following_redirects(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/start":
                return httpx.Response(
                    302, headers={"location": "https://e.test/final"}
                )
            return httpx.Response(
                200, text="<html></html>", headers={"content-type": "text/html"}
            )

        mocked_http(handler)
        _, final = await HttpxPageFetcher().fetch("https://e.test/start")
        assert final == "https://e.test/final"


class TestRejectedResponses:
    async def test_rejects_non_html_content_type(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        mocked_http(
            lambda _r: httpx.Response(
                200, content=b"{}", headers={"content-type": "application/json"}
            )
        )
        with pytest.raises(FetchError, match="Unsupported content type"):
            await HttpxPageFetcher().fetch("https://e.test/api.json")

    async def test_rejects_missing_content_type(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        mocked_http(lambda _r: httpx.Response(200, content=b"hello"))
        with pytest.raises(FetchError, match="Unsupported content type"):
            await HttpxPageFetcher().fetch("https://e.test/raw")

    async def test_rejects_response_larger_than_limit(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        oversize = b"<html>" + b"x" * (fetcher_module.MAX_BYTES + 10) + b"</html>"
        mocked_http(
            lambda _r: httpx.Response(
                200, content=oversize, headers={"content-type": "text/html"}
            )
        )
        with pytest.raises(FetchError, match="larger than"):
            await HttpxPageFetcher().fetch("https://e.test/huge")


class TestNetworkFailures:
    async def test_wraps_http_status_errors(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        mocked_http(
            lambda _r: httpx.Response(
                500, text="server error", headers={"content-type": "text/html"}
            )
        )
        with pytest.raises(FetchError, match="HTTP 500"):
            await HttpxPageFetcher().fetch("https://e.test/dead")

    async def test_wraps_connect_errors(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        def handler(_r: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("no route")

        mocked_http(handler)
        with pytest.raises(FetchError, match="Network error"):
            await HttpxPageFetcher().fetch("https://e.test/down")

    async def test_wraps_timeouts(
        self, mocked_http: Callable[[Handler], None]
    ) -> None:
        def handler(_r: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("too slow")

        mocked_http(handler)
        with pytest.raises(FetchError, match="Timed out"):
            await HttpxPageFetcher().fetch("https://e.test/slow")
