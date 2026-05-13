"""HTTP adapter for :class:`PageFetcher` using ``httpx.AsyncClient``."""

from __future__ import annotations

import httpx

from paper_saver.domain.errors import FetchError

TIMEOUT_SECONDS = 15.0
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class HttpxPageFetcher:
    """Fetches pages over HTTPS with limits suitable for a Pi Zero 2W."""

    async def fetch(self, url: str) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT_SECONDS,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
            ) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "").lower()
                    if "html" not in content_type:
                        raise FetchError(
                            f"Unsupported content type: {content_type or 'unknown'}"
                        )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise FetchError(
                                f"Response larger than {MAX_BYTES // (1024 * 1024)} MB"
                            )
                        chunks.append(chunk)

                    response._content = b"".join(chunks)
                    return response.text, str(response.url)
        except httpx.HTTPStatusError as exc:
            raise FetchError(f"HTTP {exc.response.status_code} from {url}") from exc
        except httpx.TimeoutException as exc:
            raise FetchError(f"Timed out fetching {url}") from exc
        except httpx.HTTPError as exc:
            raise FetchError(f"Network error fetching {url}: {exc}") from exc
