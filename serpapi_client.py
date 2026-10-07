"""SerpApi-backed tender discovery client.

Uses the SerpApi Google Search API (``engine=google``) to find Indian
public-sector tenders across the country's major e-tender portals.
Search data from SerpApi is the core data dependency of TenderLens:
without it there are no tenders to parse, match, or brief.

Get a free API key (250 searches/month) at https://serpapi.com/users/sign_up
and export it as ``SERPAPI_API_KEY``.  When no key is configured the app
runs in a clearly-labelled DEMO MODE with canned data (see demo_data.py)
and never claims that data is live.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

SEARCH_ENDPOINT = "https://serpapi.com/search.json"

# (domain, human-readable portal name) for India's major e-tender portals.
TENDER_PORTALS: list[tuple[str, str]] = [
    ("gem.gov.in", "Government e-Marketplace (GeM)"),
    ("eprocure.gov.in", "Central Public Procurement Portal (CPPP)"),
    ("etenders.gov.in", "eTenders Portal"),
    ("ireps.gov.in", "Indian Railways e-Procurement (IREPS)"),
    ("eproc.karnataka.gov.in", "Karnataka e-Procurement"),
    ("etender.up.nic.in", "Uttar Pradesh e-Tender"),
    ("mahatenders.gov.in", "Maharashtra e-Tendering"),
    ("tender.tn.gov.in", "Tamil Nadu Tenders"),
]

RESULTS_PER_QUERY = 10
REQUEST_TIMEOUT = 30


@dataclass
class RawResult:
    """One raw search hit, before field extraction."""

    title: str
    link: str
    snippet: str = ""
    source: str = ""
    portal: str = ""


@dataclass
class SearchOutcome:
    """Everything one discovery run produced."""

    results: list[RawResult] = field(default_factory=list)
    queries_run: list[str] = field(default_factory=list)
    credits_hint: str = ""
    error: str = ""


def build_queries(keywords: str) -> list[str]:
    """Build a small, credit-frugal set of site-restricted tender queries.

    The free SerpApi plan gives 250 searches/month, so we issue a handful
    of targeted queries instead of one broad crawl.
    """
    keywords = (keywords or "").strip() or "tender"
    return [
        f"site:gem.gov.in tender {keywords}",
        f"site:eprocure.gov.in tender {keywords}",
        f"tender {keywords} \"bid due date\" India",
        f"government tender {keywords} site:gov.in",
    ]


def portal_for_link(link: str) -> str:
    """Map a result URL to a known tender portal name, else ''."""
    low = (link or "").lower()
    for domain, name in TENDER_PORTALS:
        if domain in low:
            return name
    return ""


class SerpApiClient:
    """Thin wrapper around the SerpApi Google Search API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("SERPAPI_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _search_once(self, query: str) -> list[RawResult]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "gl": "in",  # geolocate to India
            "hl": "en",
            "num": RESULTS_PER_QUERY,
        }
        resp = requests.get(SEARCH_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        if "error" in data:
            raise RuntimeError(f"SerpApi error: {data['error']}")
        out: list[RawResult] = []
        for item in data.get("organic_results", []) or []:
            link = item.get("link", "")
            out.append(
                RawResult(
                    title=item.get("title", ""),
                    link=link,
                    snippet=item.get("snippet", ""),
                    source=item.get("source", "") or item.get("displayed_link", ""),
                    portal=portal_for_link(link),
                )
            )
        return out

    def search_tenders(self, keywords: str, max_queries: int = 4) -> SearchOutcome:
        """Run the portal query set and merge results.

        Never raises for transport/API problems: they are captured in
        ``SearchOutcome.error`` so the app can fall back gracefully.
        """
        outcome = SearchOutcome()
        if not self.is_configured:
            outcome.error = "SERPAPI_API_KEY is not set."
            return outcome
        queries = build_queries(keywords)[:max_queries]
        for query in queries:
            try:
                outcome.results.extend(self._search_once(query))
                outcome.queries_run.append(query)
                time.sleep(0.4)  # be polite; also keeps credit usage legible
            except Exception as exc:  # noqa: BLE001 - surfaced to the caller
                outcome.error = f"Query failed ({query!r}): {exc}"
                break
        outcome.credits_hint = (
            f"{len(outcome.queries_run)} SerpApi searches used "
            f"({len(outcome.results)} raw results)."
        )
        return outcome
