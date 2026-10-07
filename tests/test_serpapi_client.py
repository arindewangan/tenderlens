"""Tests for the SerpApi client (HTTP fully mocked)."""

from serpapi_client import (
    SerpApiClient,
    build_queries,
    portal_for_link,
)


def test_build_queries_site_restricted():
    qs = build_queries("computers")
    assert any("site:gem.gov.in" in q for q in qs)
    assert any("site:eprocure.gov.in" in q for q in qs)
    assert all("computers" in q for q in qs)
    assert len(qs) <= 4  # credit-frugal


def test_build_queries_default_keyword():
    assert all("tender" in q for q in build_queries(""))


def test_portal_for_link_known():
    assert portal_for_link("https://gem.gov.in/bid/1") == \
        "Government e-Marketplace (GeM)"


def test_portal_for_link_unknown():
    assert portal_for_link("https://example.com/x") == ""


def test_unconfigured_client_reports_error():
    outcome = SerpApiClient(api_key="").search_tenders("computers")
    assert outcome.results == []
    assert "SERPAPI_API_KEY" in outcome.error
    assert not SerpApiClient(api_key="").is_configured


def test_search_parses_organic_results(monkeypatch):
    payload = {
        "organic_results": [
            {"title": "T1", "link": "https://gem.gov.in/bid/1",
             "snippet": "s1", "source": "gem.gov.in"},
            {"title": "T2", "link": "https://example.com/2",
             "snippet": "s2", "source": "example.com"},
        ]
    }

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    def fake_get(url, params=None, timeout=None):
        assert "serpapi.com/search.json" in url
        assert params["engine"] == "google"
        assert params["gl"] == "in"
        assert params["api_key"] == "KEY"
        return FakeResp()

    monkeypatch.setattr("serpapi_client.requests.get", fake_get)
    monkeypatch.setattr("serpapi_client.time.sleep", lambda s: None)

    outcome = SerpApiClient(api_key="KEY").search_tenders("computers", max_queries=1)
    assert len(outcome.results) == 2
    assert outcome.results[0].portal == "Government e-Marketplace (GeM)"
    assert outcome.results[1].portal == ""
    assert outcome.error == ""


def test_search_api_error_captured(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"error": "Invalid API key"}

    monkeypatch.setattr("serpapi_client.requests.get",
                        lambda *a, **k: FakeResp())
    outcome = SerpApiClient(api_key="BAD").search_tenders("x", max_queries=1)
    assert "Invalid API key" in outcome.error
