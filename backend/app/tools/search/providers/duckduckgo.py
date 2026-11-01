"""DuckDuckGo HTML search provider."""

import ipaddress
from typing import Any, Dict, List, Optional

import httpx
from selectolax.lexbor import LexborHTMLParser

from app.agents.base import validate_url_for_fetch
from app.tools.search.base import SearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult

DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_RESPONSE_BYTES = 2_000_000
REQUEST_TIMEOUT_SECONDS = 15


def _is_private_or_internal(url: str) -> bool:
    try:
        from urllib.parse import urlsplit

        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return True
        if parsed.username or parsed.password:
            return True
        if parsed.port not in (None, 80, 443):
            return True
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost"):
            return True
        try:
            return not ipaddress.ip_address(host).is_global
        except ValueError:
            pass
        return False
    except (ValueError, TypeError):
        return True


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo HTML search provider.

    Fetches https://html.duckduckgo.com/html/?q=<query> and parses results.
    Implements SSRF protection, timeouts, size limits, and a single request
    per search query.
    """

    name = "duckduckgo"

    def __init__(
        self,
        *,
        base_url: str = DUCKDUCKGO_HTML_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        max_results: int = 5,
    ) -> None:
        self.base_url = base_url
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        if not validate_url_for_fetch(base_url):
            raise ValueError("DuckDuckGo base_url must be a public http/https URL.")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.user_agent},
                timeout=httpx.Timeout(self.timeout_seconds),
                follow_redirects=False,
            )
        return self._client

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        client = await self._get_client()
        params = {"q": query.query}
        response = await client.get(self.base_url, params=params)
        response.raise_for_status()

        html = response.text[:MAX_RESPONSE_BYTES]
        return self._parse_results(html, query)

    def _parse_results(self, html: str, query: SearchQuery) -> List[SearchResult]:
        results: List[SearchResult] = []
        parser = LexborHTMLParser(html)

        for block in parser.css("div.result")[: self.max_results]:
            title_el = block.css_first("a.result__a")
            snippet_el = block.css_first("a.result__snippet") or block.css_first(
                ".result__snippet"
            )

            if title_el is None:
                continue

            url = title_el.attributes.get("href", "")
            title = title_el.text(strip=True) or ""
            snippet = snippet_el.text(strip=True) if snippet_el else None

            if url and "uddg=" in url:
                from urllib.parse import parse_qs, urlparse

                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                if "uddg" in qs:
                    url = qs["uddg"][0]

            if not url or not title:
                continue

            if _is_private_or_internal(url):
                continue

            source_domain = ""
            try:
                from urllib.parse import urlparse

                source_domain = (urlparse(url).hostname or "").lower()
            except Exception:
                source_domain = ""

            results.append(
                SearchResult(
                    url=url,
                    title=title,
                    snippet=snippet,
                    source_domain=source_domain,
                    published_at=None,
                    query=query.query,
                    provider=self.name,
                    raw={},
                )
            )

        return results

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


__all__ = ["DuckDuckGoProvider"]
