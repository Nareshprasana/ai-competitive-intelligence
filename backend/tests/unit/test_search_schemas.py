"""Tests for search result and query schemas."""

from app.tools.search.schemas import SearchQuery, SearchResult


def test_search_result_creation():
    result = SearchResult(
        url="https://example.com/page",
        title="Example Page",
        snippet="A snippet about the page.",
        source_domain="example.com",
        query="test query",
        provider="mock",
    )
    assert result.url == "https://example.com/page"
    assert result.title == "Example Page"
    assert result.source_domain == "example.com"
    assert result.provider == "mock"
    assert result.retrieved_at is not None


def test_search_result_normalizes_domain():
    result = SearchResult(
        url="https://Example.COM/page",
        title="Page",
        source_domain="EXAMPLE.COM",
        query="q",
        provider="mock",
    )
    assert result.source_domain == "example.com"


def test_search_result_rejects_empty_url():
    try:
        SearchResult(url="", title="Page", source_domain="example.com", query="q", provider="mock")
        assert False, "expected validation error"
    except Exception:
        pass


def test_search_query_creation():
    query = SearchQuery(
        query="Acme Corp headquarters",
        purpose="headquarters_geography",
        priority=1,
    )
    assert query.query == "Acme Corp headquarters"
    assert query.priority == 1
    assert query.executed is False
    assert query.results == []


def test_search_query_priority_bounds():
    try:
        SearchQuery(query="q", purpose="p", priority=0)
        assert False, "expected validation error for priority=0"
    except Exception:
        pass
    try:
        SearchQuery(query="q", purpose="p", priority=6)
        assert False, "expected validation error for priority=6"
    except Exception:
        pass


__all__ = []
