"""Tests for brief generation and the Flask app (demo mode)."""

from datetime import date

import app as app_module
from llm import generate_brief, template_brief
from tenders import Tender


def _tender():
    return Tender(
        id="T1", title="Supply of computers", authority="GeM", portal="GeM",
        url="https://gem.gov.in/bid/1", category="IT & Software",
        location="Karnataka", value_inr=2_500_000, emd_inr=50_000,
        bid_due_date=date(2026, 10, 24),
        match_score=85, match_reasons=["Sector match: IT & Software."],
    )


# --- llm.py ------------------------------------------------------------------

def test_template_brief_contains_key_facts():
    brief = template_brief(_tender(), date(2026, 10, 7))
    assert "Supply of computers" in brief
    assert "EMD" in brief or "Earnest" in brief
    assert "24 Oct 2026" in brief
    assert "Sector match" in brief


def test_generate_brief_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    brief, source = generate_brief(_tender(), date(2026, 10, 7))
    assert source == "template"
    assert brief


def test_generate_brief_uses_llm_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "x")

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "AI brief here"}}]}

    monkeypatch.setattr("llm.requests.post", lambda *a, **k: FakeResp())
    brief, source = generate_brief(_tender())
    assert source == "llm"
    assert brief == "AI brief here"


# --- app.py (demo mode: no SERPAPI_API_KEY) ------------------------------------

def _client(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    app_module.app.config["TESTING"] = True
    app_module.STORE["tenders"] = {}
    return app_module.app.test_client()


def test_index_loads(monkeypatch):
    c = _client(monkeypatch)
    assert c.get("/").status_code == 200


def test_tenders_demo_mode_loads(monkeypatch):
    c = _client(monkeypatch)
    resp = c.get("/tenders?refresh=1")
    assert resp.status_code == 200
    assert b"DEMO MODE" in resp.data  # honestly labelled
    assert app_module.STORE["mode"] == "demo"
    assert len(app_module.STORE["tenders"]) >= 10


def test_tender_detail_loads(monkeypatch):
    c = _client(monkeypatch)
    c.get("/tenders?refresh=1")
    tid = next(iter(app_module.STORE["tenders"]))
    resp = c.get(f"/tender/{tid}")
    assert resp.status_code == 200
    assert b"Template brief" in resp.data  # no LLM key -> labelled template


def test_profile_save_reranks(monkeypatch):
    c = _client(monkeypatch)
    c.get("/tenders?refresh=1")
    resp = c.post("/profile", data={
        "name": "Acme IT",
        "sectors": ["IT & Software"],
        "turnover_band": "₹25 Lakh – ₹1 Cr",
        "locations": "Karnataka",
        "certifications": ["MSME"],
        "keywords": "laptop",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Acme IT" in resp.data


def test_watchlist_toggle(monkeypatch):
    c = _client(monkeypatch)
    c.get("/tenders?refresh=1")
    tid = next(iter(app_module.STORE["tenders"]))
    c.post(f"/watchlist/toggle/{tid}")
    resp = c.get("/watchlist")
    assert tid.encode() in resp.data
    c.post(f"/watchlist/toggle/{tid}")
    assert tid.encode() not in c.get("/watchlist").data


def test_digest_loads(monkeypatch):
    c = _client(monkeypatch)
    c.get("/tenders?refresh=1")
    resp = c.get("/digest")
    assert resp.status_code == 200
    assert b"Deadline calendar" in resp.data


def test_api_health_and_tenders(monkeypatch):
    c = _client(monkeypatch)
    c.get("/tenders?refresh=1")
    assert c.get("/api/health").get_json()["status"] == "ok"
    assert len(c.get("/api/tenders").get_json()) >= 10
