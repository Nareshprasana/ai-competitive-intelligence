"""Tests for the base agent class (budgeting, rate limiting, SSRF, fetching)."""

import asyncio
import socket

import httpx
import pytest

import app.agents.base as agent_base
from app.agents.base import (
    AgentBudget,
    BaseAgent,
    SearchResultCache,
    fetch_page,
    retry_async,
    validate_url_for_fetch,
)
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult


def test_validate_url_for_fetch_blocks_private():
    assert validate_url_for_fetch("http://localhost/admin") is False
    assert validate_url_for_fetch("http://127.0.0.1:8080/") is False
    assert validate_url_for_fetch("http://192.168.1.1/") is False
    assert validate_url_for_fetch("http://10.0.0.1/") is False
    assert validate_url_for_fetch("http://169.254.169.254/") is False
    assert validate_url_for_fetch("ftp://example.com/") is False


def test_validate_url_for_fetch_allows_public():
    assert validate_url_for_fetch("https://example.com/page") is True
    assert validate_url_for_fetch("http://example.com/page") is True


def test_agent_budget_defaults():
    budget = AgentBudget()
    assert budget.max_search_queries == 8
    assert budget.max_pages_fetched == 10
    assert budget.max_retries == 3


def test_search_result_cache():
    cache = SearchResultCache()
    assert cache.has("query") is False
    results = [SearchResult(url="https://a.com", title="A", source_domain="a.com", query="q", provider="mock")]
    cache.set("query", results)
    assert cache.has("query") is True
    assert cache.get("query") == results


class DummyProvider:
    name = "dummy"

    async def search(self, query):
        return [
            SearchResult(
                url="https://example.com",
                title="Result",
                source_domain="example.com",
                query=query.query,
                provider="dummy",
            )
        ]

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_base_agent_rate_limited_search_budget():
    agent = BaseAgent(DummyProvider(), budget=AgentBudget(max_search_queries=2))
    q1 = SearchQuery(query="q1", purpose="p", priority=1)
    q2 = SearchQuery(query="q2", purpose="p", priority=2)
    q3 = SearchQuery(query="q3", purpose="p", priority=3)

    r1 = await agent._rate_limited_search(q1)
    r2 = await agent._rate_limited_search(q2)
    r3 = await agent._rate_limited_search(q3)

    assert len(r1) == 1
    assert len(r2) == 1
    assert len(r3) == 0  # budget exhausted
    assert agent._searches_done == 2


@pytest.mark.asyncio
async def test_base_agent_search_cache():
    agent = BaseAgent(DummyProvider(), budget=AgentBudget(max_search_queries=10))
    q = SearchQuery(query="cached query", purpose="p", priority=1)
    r1 = await agent._rate_limited_search(q)
    r2 = await agent._rate_limited_search(q)
    assert r1 == r2
    assert agent._searches_done == 1  # only one actual call


@pytest.mark.asyncio
async def test_retry_async_transient():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("connection refused")
        return "ok"

    result = await retry_async(flaky, max_retries=3, backoff_seconds=0.01)
    assert result == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_retry_async_non_transient_not_retried():
    calls = {"n": 0}

    async def always_fails():
        calls["n"] += 1
        raise ValueError("permanent error")

    try:
        await retry_async(always_fails, max_retries=3, backoff_seconds=0.01)
        assert False, "expected ValueError"
    except ValueError:
        pass
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_fetch_page_blocks_private_url():
    async with httpx.AsyncClient() as client:
        result = await fetch_page("http://localhost/admin", client=client)
        assert result is None


@pytest.mark.asyncio
async def test_fetch_page_pins_dns_result_and_preserves_tls_hostname(monkeypatch):
    dns_calls = []
    requests = []

    def resolve(host, port, *, type):
        dns_calls.append((host, port))
        address = "93.184.216.34" if len(dns_calls) == 1 else "127.0.0.1"
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))
        ]

    def respond(request):
        requests.append(request)
        return httpx.Response(200, text="safe response")

    monkeypatch.setattr(agent_base.socket, "getaddrinfo", resolve)
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await fetch_page("https://example.com/resource", client=client)

    assert result == "safe response"
    assert len(dns_calls) == 1
    assert str(requests[0].url) == "https://93.184.216.34/resource"
    assert requests[0].headers["host"] == "example.com"
    assert requests[0].extensions["sni_hostname"] == b"example.com"


@pytest.mark.asyncio
async def test_fetch_page_does_not_use_ip_literal_as_tls_sni():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, text="safe response")

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await fetch_page("https://93.184.216.34/resource", client=client)

    assert result == "safe response"
    assert requests[0].extensions.get("sni_hostname") is None


@pytest.mark.asyncio
async def test_fetch_page_rejects_mixed_public_and_private_dns_answers(monkeypatch):
    requests = []

    def resolve(host, port, *, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.7", port)),
        ]

    def respond(request):
        requests.append(request)
        return httpx.Response(200, text="must not be requested")

    monkeypatch.setattr(agent_base.socket, "getaddrinfo", resolve)
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await fetch_page("https://example.com/resource", client=client)

    assert result is None
    assert requests == []


@pytest.mark.asyncio
async def test_fetch_page_revalidates_redirect_destination_dns(monkeypatch):
    dns_hosts = []
    requests = []

    def resolve(host, port, *, type):
        dns_hosts.append(host)
        address = "93.184.216.34" if host == "example.com" else "169.254.169.254"
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))
        ]

    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={"location": "http://metadata.example/latest"})

    monkeypatch.setattr(agent_base.socket, "getaddrinfo", resolve)
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await fetch_page("https://example.com/resource", client=client)

    assert result is None
    assert dns_hosts == ["example.com", "metadata.example"]
    assert len(requests) == 1
    assert requests[0].headers["host"] == "example.com"


__all__ = []
