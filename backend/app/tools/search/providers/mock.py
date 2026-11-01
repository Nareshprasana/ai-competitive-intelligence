"""Deterministic mock search provider for testing and offline use.

Returns canned, clearly-labelled results. Never makes network calls.
"""

from typing import Any, Dict, List

from app.tools.search.base import SearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult

# Canned results keyed by company name (lowercased). Used when the mock
# provider does not have a specific entry; returns a generic placeholder.
_MOCK_RESULTS: Dict[str, List[Dict[str, Any]]] = {
    "acme corp": [
        {
            "url": "https://example.com/acme-corp",
            "title": "Acme Corp - Official Website",
            "snippet": "Acme Corp is a leading AI software company headquartered in San Francisco.",
            "source_domain": "example.com",
            "published_at": None,
        },
        {
            "url": "https://example.com/acme-corp/about",
            "title": "About Acme Corp",
            "snippet": "Founded in 2010, Acme Corp builds enterprise AI platforms.",
            "source_domain": "example.com",
            "published_at": None,
        },
    ],
    "globex": [
        {
            "url": "https://example.com/globex",
            "title": "Globex Corporation",
            "snippet": "Globex Corporation operates in the biotechnology industry.",
            "source_domain": "example.com",
            "published_at": None,
        },
    ],
}


class MockSearchProvider(SearchProvider):
    """Deterministic mock search provider.

    Returns canned results for known companies and a generic placeholder
    otherwise. Never performs network I/O. Safe for unit tests.
    """

    name = "mock"

    def __init__(self, results: Dict[str, List[Dict[str, Any]]] | None = None) -> None:
        self._results = results or dict(_MOCK_RESULTS)
        self.call_count = 0

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Return deterministic canned results for the query."""
        self.call_count += 1
        key = query.query.strip().lower()
        results = self._results.get(key, [])

        if not results:
            results = [
                {
                    "url": "https://example.com/search",
                    "title": "Search results for " + query.query,
                    "snippet": "Generic placeholder result (mock provider).",
                    "source_domain": "example.com",
                    "published_at": None,
                }
            ]

        return [
            SearchResult(
                url=r["url"],
                title=r["title"],
                snippet=r.get("snippet"),
                source_domain=r["source_domain"],
                published_at=r.get("published_at"),
                query=query.query,
                provider=self.name,
                raw=r,
            )
            for r in results
        ]


__all__ = ["MockSearchProvider"]
