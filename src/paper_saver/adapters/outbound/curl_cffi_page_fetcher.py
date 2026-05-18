"""HTTP adapter for :class:`PageFetcher` using ``curl_cffi``.

We use curl_cffi (curl-impersonate under the hood) so the TLS ClientHello and
HTTP/2 SETTINGS match a real Chrome build. Anti-bot fronts like Cloudflare
fingerprint those layers, and a pure-Python ``httpx`` client gets flagged
regardless of how realistic its HTTP headers look.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import unquote, urlparse

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import HTTPError, RequestException

from paper_saver.domain.errors import FetchError

TIMEOUT_SECONDS = 15.0
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
IMPERSONATE = "chrome131"

CURL_TIMEOUT_CODE = 28

# archive.today serves the same data under several rotating ccTLDs.
_ARCHIVE_HOSTS = frozenset(
    {
        "archive.ph",
        "archive.today",
        "archive.is",
        "archive.li",
        "archive.fo",
        "archive.md",
        "archive.vn",
    }
)


def _unwrap_archive_url(url: str) -> str | None:
    """Return the original URL embedded in an archive.today-family link.

    archive.today exposes three wrapper shapes whose path embeds the original
    URL verbatim — ``/<scheme>://...``, ``/newest/<scheme>://...``, and
    ``/o/<id>/<scheme>://...``. For any of those we strip the wrapper and
    return the embedded URL. For bare snapshot IDs (``/dWANk``), there is no
    embedded URL: return ``None``.
    """
    parsed = urlparse(url)
    if parsed.netloc.lower() not in _ARCHIVE_HOSTS:
        return None
    path = parsed.path.lstrip("/")
    if path.startswith("newest/"):
        path = path[len("newest/") :]
    elif path.startswith("o/"):
        rest = path[2:]
        slash = rest.find("/")
        if slash == -1:
            return None
        path = rest[slash + 1 :]
    decoded = unquote(path)
    if not decoded.startswith(("http://", "https://")):
        return None
    suffix = ""
    if parsed.query:
        suffix += f"?{parsed.query}"
    if parsed.fragment:
        suffix += f"#{parsed.fragment}"
    return decoded + suffix


def _is_archive_snapshot_id_url(url: str) -> bool:
    """True if the URL is an archive.today-family link with only a snapshot id.

    These are reCAPTCHA-gated by Cloudflare; the original URL is intentionally
    obfuscated in the response (the visible "leaked" host is a decoy injected
    by archive.today's own anti-scrape script). We cannot follow them.
    """
    parsed = urlparse(url)
    if parsed.netloc.lower() not in _ARCHIVE_HOSTS:
        return False
    path = parsed.path.strip("/")
    if not path or "/" in path:
        return False
    return path.replace("_", "").isalnum() and 3 <= len(path) <= 12


def _format_retry_after(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        return f"retry after {value}s"
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return f"retry after {value}"
    now = datetime.now(retry_at.tzinfo or timezone.utc)
    seconds = max(0, int((retry_at - now).total_seconds()))
    return f"retry after {seconds}s"


class CurlCffiPageFetcher:
    """Fetches pages over HTTPS while impersonating Chrome at the TLS layer."""

    async def fetch(self, url: str) -> tuple[str, str]:
        unwrapped = _unwrap_archive_url(url)
        if unwrapped is not None:
            url = unwrapped
        elif _is_archive_snapshot_id_url(url):
            raise FetchError(
                f"archive.today snapshot IDs are gated by reCAPTCHA and cannot "
                f"be fetched automatically; send the original URL instead of {url}"
            )
        try:
            async with AsyncSession(impersonate=IMPERSONATE) as session:
                async with session.stream(
                    "GET", url, timeout=TIMEOUT_SECONDS, allow_redirects=True
                ) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "").lower()
                    if "html" not in content_type:
                        raise FetchError(
                            f"Unsupported content type: {content_type or 'unknown'}"
                        )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_content():
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise FetchError(
                                f"Response larger than {MAX_BYTES // (1024 * 1024)} MB"
                            )
                        chunks.append(chunk)

                    body = b"".join(chunks).decode(
                        response.encoding or "utf-8", errors="replace"
                    )
                    return body, str(response.url)
        except HTTPError as exc:
            status = exc.response.status_code
            suffix = ""
            if status == 429:
                retry_after = exc.response.headers.get("retry-after")
                if retry_after:
                    suffix = f" ({_format_retry_after(retry_after)})"
            raise FetchError(f"HTTP {status} from {url}{suffix}") from exc
        except RequestException as exc:
            if getattr(exc, "code", None) == CURL_TIMEOUT_CODE:
                raise FetchError(f"Timed out fetching {url}") from exc
            raise FetchError(f"Network error fetching {url}: {exc}") from exc
