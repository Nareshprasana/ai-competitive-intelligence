"""Tests for the search provider abstraction and mock provider."""

import asyncio

from app.tools.search.base import SearchProvider
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult


def test_search_provider_is_abstract():
    """SearchProvider should not be directly instantiatable for search."""
    provider = SearchProvider()
    try:
        asyncio.run(provider.search(SearchQuery(query="q", purpose="p")))
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass


def test_mock_search_provider_returns_canned_results():
    provider = MockSearchProvider()
    results = asyncio.run(
        provider.search(SearchQuery(query="acme corp", purpose="overview"))
    )
    assert len(results) == 2
    assert results[0].title == "Acme Corp - Official Website"
    assert results[0].source_domain == "example.com"
    assert results[0].provider == "mock"
    assert results[0].query == "acme corp"


def test_mock_search_provider_unknown_query_placeholder():
    provider = MockSearchProvider()
    results = asyncio.run(
        provider.search(SearchQuery(query="unknown company xyz", purpose="overview"))
    )
    assert len(results) == 1
    assert "unknown company xyz" in results[0].title


def test_mock_search_provider_counts_calls():
    provider = MockSearchProvider()
    asyncio.run(provider.search(SearchQuery(query="acme corp", purpose="overview")))
    asyncio.run(provider.search(SearchQuery(query="globex", purpose="overview")))
    assert provider.call_count == 2


def test_mock_search_provider_is_deterministic():
    provider1 = MockSearchProvider()
    provider2 = MockSearchProvider()
    r1 = asyncio.run(provider1.search(SearchQuery(query="acme corp", purpose="overview")))
    r2 = asyncio.run(provider2.search(SearchQuery(query="acme corp", purpose="overview")))
    assert [r.url for r in r1] == [r.url for r in r2]


__all__ = []
