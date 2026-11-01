"""Base class for research agents.

Provides shared infrastructure: search budgeting, rate limiting, SSRF-safe URL
validation, HTTP fetch with size limits, and retry logic for transient
failures. No LLM calls happen at import time.
"""

import asyncio
import ipaddress
import socket
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.tools.search.base import SearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult

logger = get_logger("app.agents.base")

T = TypeVar("T", bound=BaseModel)

# Maximum bytes to read from any fetched page.
MAX_FETCH_BYTES = 500_000

# Default request timeout in seconds.
DEFAULT_REQUEST_TIMEOUT = 15

# Minimum delay between search requests (rate limiting).
MIN_SEARCH_INTERVAL_SECONDS = 1.0

# Default maximum number of search queries per research run.
DEFAULT_MAX_SEARCH_QUERIES = 8

# Default maximum number of pages to fetch per research run.
DEFAULT_MAX_PAGES_FETCHED = 10


class AgentBudget(BaseModel):
    """Configurable resource budget for a research run."""

    model_config = {"extra": "forbid"}

    max_search_queries: int = Field(default=DEFAULT_MAX_SEARCH_QUERIES, ge=1)
    max_pages_fetched: int = Field(default=DEFAULT_MAX_PAGES_FETCHED, ge=1)
    max_tokens_per_llm_call: int = Field(default=2048, ge=256)
    max_llm_calls: int = Field(default=12, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=2.0, ge=0.5)


class SearchResultCache:
    """In-memory cache for search results within a single research run."""

    def __init__(self) -> None:
        self._cache: Dict[str, List[SearchResult]] = {}

    def get(self, query: str) -> Optional[List[SearchResult]]:
        return self._cache.get(query.strip().lower())

    def set(self, query: str, results: List[SearchResult]) -> None:
        self._cache[query.strip().lower()] = list(results)

    def has(self, query: str) -> bool:
        return query.strip().lower() in self._cache


def validate_url_for_fetch(url: str) -> bool:
    """SSRF-safe URL validation. Returns True only for public http/https URLs."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.username or parsed.password or not parsed.hostname:
            return False
        if parsed.port not in (None, 80, 443):
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host.endswith(".localhost"):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            pass
        if host in ("localhost",) or "." not in host:
            return False
        return True
    except (ValueError, TypeError):
        return False


async def _resolve_public_addresses(host: str, port: int) -> List[str]:
    """Resolve a host once and return only addresses safe to pin for the request."""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None

    if address is not None:
        if address.is_global and not getattr(address, "scope_id", None):
            return [address.compressed]
        return []

    try:
        records = await asyncio.to_thread(
            socket.getaddrinfo, host, port, type=socket.SOCK_STREAM
        )
    except OSError:
        return []

    resolved: List[str] = []
    for record in records:
        try:
            address = ipaddress.ip_address(record[4][0])
        except (ValueError, IndexError, TypeError):
            return []
        if not address.is_global or getattr(address, "scope_id", None):
            return []
        normalized = address.compressed
        if normalized not in resolved:
            resolved.append(normalized)
    return resolved


async def fetch_page(
    url: str,
    *,
    client: httpx.AsyncClient,
    max_bytes: int = MAX_FETCH_BYTES,
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT,
) -> Optional[str]:
    """Fetch a public webpage with SSRF protection, timeout, and size limits.

    Returns the page text or None if the fetch fails. Retrieved content is
    treated as untrusted.
    """
    if not validate_url_for_fetch(url):
        logger.warning("Blocked fetch of non-public URL: %s", url)
        return None

    current_url = url
    for _ in range(6):
        if not validate_url_for_fetch(current_url):
            logger.warning("Blocked fetch of non-public URL: %s", current_url)
            return None

        parsed = urlsplit(current_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = await _resolve_public_addresses(host, port)
        if not addresses:
            logger.warning("Blocked fetch for host resolving to a non-public address.")
            return None

        address = ipaddress.ip_address(addresses[0])
        pinned_host = (
            "[%s]" % address.compressed
            if address.version == 6
            else address.compressed
        )
        pinned_netloc = pinned_host
        if parsed.port is not None:
            pinned_netloc += ":%d" % parsed.port
        pinned_url = urlunsplit(
            (parsed.scheme, pinned_netloc, parsed.path or "/", parsed.query, "")
        )

        host_header = host.encode("idna").decode("ascii")
        if ":" in host_header:
            host_header = "[%s]" % host_header
        if parsed.port is not None:
            host_header += ":%d" % parsed.port
        try:
            ipaddress.ip_address(host)
            sni_hostname = None
        except ValueError:
            sni_hostname = host.encode("idna")
        extensions = (
            {"sni_hostname": sni_hostname}
            if parsed.scheme == "https" and sni_hostname is not None
            else None
        )
        try:
            async with client.stream(
                "GET",
                pinned_url,
                headers={"Host": host_header},
                timeout=timeout_seconds,
                follow_redirects=False,
                extensions=extensions,
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        return None
                    current_url = urljoin(current_url, location)
                    if not validate_url_for_fetch(current_url):
                        logger.warning("Blocked redirect to a non-public URL.")
                        return None
                    continue
                response.raise_for_status()
                chunks = bytearray()
                async for chunk in response.aiter_bytes():
                    chunks.extend(chunk[: max_bytes - len(chunks)])
                    if len(chunks) >= max_bytes:
                        break
                return bytes(chunks).decode("utf-8", errors="replace")
        except httpx.HTTPError as exc:
            logger.warning("Fetch failed for %s: %s", current_url, exc)
            return None
    logger.warning("Blocked fetch after too many redirects.")
    return None


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    backoff_seconds: float = 2.0,
    retryable_exceptions: tuple = (httpx.HTTPError, asyncio.TimeoutError),
    **kwargs: Any,
) -> Any:
    """Retry an async function for transient failures only.

    Non-transient exceptions are re-raised immediately.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(backoff_seconds * (attempt + 1))
                continue
            raise
        except Exception:
            # Non-transient: do not retry.
            raise
    if last_exc is not None:
        raise last_exc
    raise ResearchError("retry_async exhausted without result")


class BaseAgent:
    """Base class for research agents.

    Provides search budgeting, rate limiting, result caching, and safe HTTP
    fetching. Subclasses implement the research logic.
    """

    def __init__(
        self,
        search_provider: SearchProvider,
        *,
        budget: Optional[AgentBudget] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.search_provider = search_provider
        self.budget = budget or AgentBudget()
        self._client = client
        self._search_cache = SearchResultCache()
        self._last_search_time: Optional[float] = None
        self._searches_done = 0
        self._pages_fetched = 0
        self._llm_calls = 0

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_REQUEST_TIMEOUT),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        await self.search_provider.close()
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _rate_limited_search(self, query: SearchQuery) -> List[SearchResult]:
        """Search with budget enforcement, caching, and rate limiting."""
        if self._searches_done >= self.budget.max_search_queries:
            logger.warning("Search budget exhausted (%d queries)", self._searches_done)
            return []

        cached = self._search_cache.get(query.query)
        if cached is not None:
            return cached

        # Rate limit: enforce minimum interval between searches.
        if self._last_search_time is not None:
            elapsed = time.monotonic() - self._last_search_time
            if elapsed < MIN_SEARCH_INTERVAL_SECONDS:
                await asyncio.sleep(MIN_SEARCH_INTERVAL_SECONDS - elapsed)

        results = await retry_async(
            self.search_provider.search,
            query,
            max_retries=self.budget.max_retries,
            backoff_seconds=self.budget.retry_backoff_seconds,
        )

        self._search_cache.set(query.query, results)
        self._searches_done += 1
        self._last_search_time = time.monotonic()
        return results

    async def _fetch_safe(
        self, url: str
    ) -> Optional[str]:
        """Fetch a page with budget enforcement."""
        if getattr(self.search_provider, "name", "") == "mock":
            return None
        if self._pages_fetched >= self.budget.max_pages_fetched:
            logger.warning("Page fetch budget exhausted (%d pages)", self._pages_fetched)
            return None
        text = await fetch_page(url, client=self.client)
        if text is not None:
            self._pages_fetched += 1
        return text

    def _llm_call_allowed(self) -> bool:
        return self._llm_calls < self.budget.max_llm_calls

    def _increment_llm_call(self) -> None:
        self._llm_calls += 1


__all__ = [
    "AgentBudget",
    "BaseAgent",
    "SearchResultCache",
    "validate_url_for_fetch",
    "fetch_page",
    "retry_async",
]
