"""Abstract search provider interface.

All search providers implement :class:`SearchProvider`. Providers are
replaceable: the agent depends only on this interface, not on any concrete
search API.
"""

from typing import Any, List, Optional

from app.tools.search.schemas import SearchQuery, SearchResult


class SearchProvider:
    """Abstract base class for search providers."""

    name: str = "base"

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Execute a search query and return normalized results.

        Args:
            query: The search query to execute.

        Returns:
            A list of normalized search results.
        """
        raise NotImplementedError

    async def close(self) -> None:
        """Release any provider resources (e.g. HTTP clients)."""
        return None

    def is_configured(self) -> bool:
        """Return True if the provider is ready to serve requests."""
        return True

    async def __aenter__(self) -> "SearchProvider":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


__all__ = ["SearchProvider"]
