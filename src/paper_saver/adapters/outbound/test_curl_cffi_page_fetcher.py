"""Behavior specification for :class:`CurlCffiPageFetcher`.

No real network is used. Each test installs a fake ``AsyncSession`` so the
fetcher routes to a handler that returns exactly the response under test.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager

import pytest
from curl_cffi.requests.exceptions import HTTPError, RequestException

from paper_saver.adapters.outbound import curl_cffi_page_fetcher as fetcher_module
from paper_saver.adapters.outbound.curl_cffi_page_fetcher import (
    CurlCffiPageFetcher,
    _is_archive_snapshot_id_url,
    _unwrap_archive_url,
)
from paper_saver.domain.errors import FetchError


class FakeResponse:
    def __init__(
        self,
        *,
        status: int,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        url: str = "",
        encoding: str = "utf-8",
    ) -> None:
        self.status_code = status
        self._body = body
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.url = url
        self.encoding = encoding

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            err = HTTPError(f"HTTP Error {self.status_code}")
            err.response = self  # type: ignore[attr-defined]
            raise err

    async def aiter_content(self, chunk_size: int = 8192):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]


Handler = Callable[[str, str], FakeResponse | BaseException]


class FakeAsyncSession:
    def __init__(self, handler: Handler) -> None:
        self.handler = handler

    async def __aenter__(self) -> "FakeAsyncSession":
        return self

    async def __aexit__(self, *_exc) -> None:  # noqa: ANN002
        return None

    @asynccontextmanager
    async def stream(self, method: str, url: str, **_kw):  # noqa: ANN003
        result = self.handler(method, url)
        if isinstance(result, BaseException):
            raise result
        yield result


@pytest.fixture
def mocked_curl(monkeypatch: pytest.MonkeyPatch) -> Callable[[Handler], None]:
    """Patch ``AsyncSession`` so the fetcher routes through ``FakeAsyncSession``."""

    def install(handler: Handler) -> None:
        def factory(*_a, **_kw):  # noqa: ANN002, ANN003
            return FakeAsyncSession(handler)

        monkeypatch.setattr(fetcher_module, "AsyncSession", factory)

    return install


class TestSuccessfulFetch:
    async def test_returns_decoded_html(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=200,
                body=b"<html><body>ok</body></html>",
                headers={"content-type": "text/html; charset=utf-8"},
                url=url,
            )
        )
        html, _ = await CurlCffiPageFetcher().fetch("https://e.test/a")
        assert "<body>ok</body>" in html

    async def test_returns_original_url_when_no_redirect(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=200,
                body=b"<html></html>",
                headers={"content-type": "text/html"},
                url=url,
            )
        )
        _, final = await CurlCffiPageFetcher().fetch("https://e.test/a")
        assert final == "https://e.test/a"

    async def test_returns_redirected_url_after_following_redirects(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, _url: FakeResponse(
                status=200,
                body=b"<html></html>",
                headers={"content-type": "text/html"},
                url="https://e.test/final",
            )
        )
        _, final = await CurlCffiPageFetcher().fetch("https://e.test/start")
        assert final == "https://e.test/final"


class TestRejectedResponses:
    async def test_rejects_non_html_content_type(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=200,
                body=b"{}",
                headers={"content-type": "application/json"},
                url=url,
            )
        )
        with pytest.raises(FetchError, match="Unsupported content type"):
            await CurlCffiPageFetcher().fetch("https://e.test/api.json")

    async def test_rejects_missing_content_type(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(status=200, body=b"hello", url=url)
        )
        with pytest.raises(FetchError, match="Unsupported content type"):
            await CurlCffiPageFetcher().fetch("https://e.test/raw")

    async def test_rejects_response_larger_than_limit(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        oversize = b"<html>" + b"x" * (fetcher_module.MAX_BYTES + 10) + b"</html>"
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=200,
                body=oversize,
                headers={"content-type": "text/html"},
                url=url,
            )
        )
        with pytest.raises(FetchError, match="larger than"):
            await CurlCffiPageFetcher().fetch("https://e.test/huge")


class TestNetworkFailures:
    async def test_wraps_http_status_errors(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=500,
                body=b"server error",
                headers={"content-type": "text/html"},
                url=url,
            )
        )
        with pytest.raises(FetchError, match="HTTP 500"):
            await CurlCffiPageFetcher().fetch("https://e.test/dead")

    async def test_surfaces_retry_after_seconds_on_429(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=429,
                body=b"slow down",
                headers={"content-type": "text/html", "retry-after": "42"},
                url=url,
            )
        )
        with pytest.raises(FetchError, match=r"HTTP 429.*retry after 42s"):
            await CurlCffiPageFetcher().fetch("https://e.test/throttled")

    async def test_surfaces_retry_after_http_date_on_429(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=429,
                body=b"slow down",
                headers={
                    "content-type": "text/html",
                    "retry-after": "Wed, 21 Oct 2099 07:28:00 GMT",
                },
                url=url,
            )
        )
        with pytest.raises(FetchError, match=r"HTTP 429.*retry after \d+s"):
            await CurlCffiPageFetcher().fetch("https://e.test/throttled")

    async def test_omits_retry_hint_when_header_absent_on_429(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        mocked_curl(
            lambda _m, url: FakeResponse(
                status=429,
                body=b"slow down",
                headers={"content-type": "text/html"},
                url=url,
            )
        )
        with pytest.raises(FetchError, match=r"^HTTP 429 from [^()]+$"):
            await CurlCffiPageFetcher().fetch("https://e.test/throttled")

    async def test_wraps_connect_errors(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        err = RequestException("Could not resolve host")
        err.code = 6  # type: ignore[attr-defined]
        mocked_curl(lambda _m, _u: err)
        with pytest.raises(FetchError, match="Network error"):
            await CurlCffiPageFetcher().fetch("https://e.test/down")

    async def test_wraps_timeouts(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        err = RequestException("Operation too slow")
        err.code = fetcher_module.CURL_TIMEOUT_CODE  # type: ignore[attr-defined]
        mocked_curl(lambda _m, _u: err)
        with pytest.raises(FetchError, match="Timed out"):
            await CurlCffiPageFetcher().fetch("https://e.test/slow")


class TestArchiveUrlUnwrap:
    @pytest.mark.parametrize(
        "wrapped,original",
        [
            (
                "https://archive.ph/https://gyrovague.com/post",
                "https://gyrovague.com/post",
            ),
            (
                "https://archive.today/newest/https://example.com/x",
                "https://example.com/x",
            ),
            (
                "https://archive.is/o/abc12/https://example.com/y",
                "https://example.com/y",
            ),
            (
                "https://archive.ph/https%3A%2F%2Fexample.com%2Fz",
                "https://example.com/z",
            ),
        ],
    )
    def test_unwraps_embedded_url(self, wrapped: str, original: str) -> None:
        assert _unwrap_archive_url(wrapped) == original

    def test_preserves_query_and_fragment(self) -> None:
        wrapped = "https://archive.ph/https://example.com/a?x=1#sec"
        # query and fragment ride on the wrapper URL, not inside the path
        assert _unwrap_archive_url(wrapped) == "https://example.com/a?x=1#sec"

    @pytest.mark.parametrize(
        "url",
        [
            "https://archive.ph/dWANk",
            "https://archive.today/aBcDe",
            "https://example.com/dWANk",
            "https://archive.ph/",
            "https://archive.ph/submit/?url=https://example.com",
        ],
    )
    def test_returns_none_for_non_wrapped_urls(self, url: str) -> None:
        assert _unwrap_archive_url(url) is None


class TestArchiveSnapshotDetection:
    @pytest.mark.parametrize(
        "url",
        [
            "https://archive.ph/dWANk",
            "https://archive.today/aBcDe",
            "https://archive.is/x1y2z",
            "https://archive.vn/aaaa_bb",
        ],
    )
    def test_recognises_snapshot_id_urls(self, url: str) -> None:
        assert _is_archive_snapshot_id_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://archive.ph/https://example.com",
            "https://archive.ph/newest/https://example.com",
            "https://archive.ph/",
            "https://example.com/dWANk",
            "https://archive.ph/this-id-is-way-too-long-to-be-a-snapshot",
        ],
    )
    def test_rejects_non_snapshot_urls(self, url: str) -> None:
        assert _is_archive_snapshot_id_url(url) is False


class TestArchiveSnapshotShortCircuit:
    async def test_snapshot_id_fails_with_clear_message_without_network(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        sentinel = RuntimeError("network must not be called")
        mocked_curl(lambda _m, _u: sentinel)
        with pytest.raises(FetchError, match="snapshot IDs are gated by reCAPTCHA"):
            await CurlCffiPageFetcher().fetch("https://archive.ph/dWANk")

    async def test_wrapped_url_is_unwrapped_before_fetching(
        self, mocked_curl: Callable[[Handler], None]
    ) -> None:
        seen: list[str] = []

        def handler(_method: str, url: str) -> FakeResponse:
            seen.append(url)
            return FakeResponse(
                status=200,
                body=b"<html><body>ok</body></html>",
                headers={"content-type": "text/html"},
                url=url,
            )

        mocked_curl(handler)
        html, final = await CurlCffiPageFetcher().fetch(
            "https://archive.ph/https://example.com/post"
        )
        assert seen == ["https://example.com/post"]
        assert final == "https://example.com/post"
        assert "ok" in html
