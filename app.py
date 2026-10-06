"""TenderLens — Indian public-tender intelligence for small businesses.

Flask app.  Tender discovery is powered by SerpApi's Google Search API
(see serpapi_client.py); without a SERPAPI_API_KEY the app runs in a
clearly-labelled DEMO MODE with canned data (see demo_data.py).
"""

from __future__ import annotations

import os
from datetime import date

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from demo_data import DEMO_NOTICE, get_demo_results
from llm import generate_brief
from matcher import BusinessProfile, rank_tenders
from serpapi_client import SerpApiClient
from tenders import build_tenders

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "tenderlens-dev-secret")

# In-memory store (demo-grade; a real deployment would use a database).
STORE: dict[str, dict] = {"tenders": {}, "last_search": "", "mode": "unknown"}


def get_client() -> SerpApiClient:
    return SerpApiClient()


def current_profile() -> BusinessProfile:
    return BusinessProfile.from_dict(session.get("profile", {}))


def refresh_tenders(keywords: str) -> tuple[str, str]:
    """(Re)discover tenders; returns (mode, notice)."""
    client = get_client()
    if client.is_configured:
        outcome = client.search_tenders(keywords)
        if outcome.error and not outcome.results:
            results, mode = get_demo_results(), "demo"
            notice = f"Live search failed ({outcome.error}). Showing {DEMO_NOTICE}"
        else:
            results, mode = outcome.results, "live"
            notice = outcome.credits_hint or "Live SerpApi search complete."
    else:
        results, mode = get_demo_results(), "demo"
        notice = DEMO_NOTICE

    tenders = build_tenders(results)
    if keywords.strip():
        kw = keywords.strip().lower()
        tenders = [t for t in tenders
                   if kw in f"{t.title} {t.snippet}".lower()] or tenders
    ranked = rank_tenders(tenders, current_profile())
    STORE["tenders"] = {t.id: t for t in ranked}
    STORE["last_search"] = keywords
    STORE["mode"] = mode
    return mode, notice


@app.context_processor
def inject_globals():
    return {
        "demo_mode": STORE["mode"] == "demo",
        "demo_notice": DEMO_NOTICE if STORE["mode"] == "demo" else "",
        "profile": current_profile(),
        "watchlist": session.get("watchlist", []),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tenders")
def tenders():
    q = request.args.get("q", "").strip()
    refresh = request.args.get("refresh") == "1" or not STORE["tenders"]
    notice = ""
    if refresh:
        _, notice = refresh_tenders(q)
    items = list(STORE["tenders"].values())
    return render_template("tenders.html", tenders=items, q=q or STORE["last_search"],
                           notice=notice)


@app.route("/tender/<tid>")
def tender_detail(tid: str):
    tender = STORE["tenders"].get(tid)
    if not tender:
        return redirect(url_for("tenders"))
    brief, source = generate_brief(tender)
    return render_template("tender_detail.html", tender=tender, brief=brief,
                           brief_source=source)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    from tenders import CATEGORIES
    from matcher import TURNOVER_BANDS
    if request.method == "POST":
        session["profile"] = {
            "name": request.form.get("name", "My Business").strip() or "My Business",
            "sectors": request.form.getlist("sectors"),
            "turnover_band": request.form.get("turnover_band", "₹25 Lakh – ₹1 Cr"),
            "locations": [l.strip() for l in
                          request.form.get("locations", "").split(",") if l.strip()],
            "certifications": request.form.getlist("certifications"),
            "keywords": [k.strip() for k in
                         request.form.get("keywords", "").split(",") if k.strip()],
        }
        session.modified = True
        # re-rank with the new profile
        if STORE["tenders"]:
            STORE["tenders"] = {t.id: t for t in
                                rank_tenders(list(STORE["tenders"].values()),
                                             current_profile())}
        return redirect(url_for("tenders", refresh="1"))
    return render_template("profile.html",
                           categories=sorted(CATEGORIES),
                           bands=list(TURNOVER_BANDS),
                           certs=["MSME", "ISO", "NSIC", "Startup India"])


@app.route("/watchlist")
def watchlist():
    ids = session.get("watchlist", [])
    items = [STORE["tenders"][i] for i in ids if i in STORE["tenders"]]
    return render_template("watchlist.html", tenders=items)


@app.route("/watchlist/toggle/<tid>", methods=["POST"])
def watchlist_toggle(tid: str):
    wl = session.get("watchlist", [])
    if tid in wl:
        wl.remove(tid)
    else:
        wl.append(tid)
    session["watchlist"] = wl
    session.modified = True
    return redirect(request.referrer or url_for("tenders"))


@app.route("/digest")
def digest():
    """Email-style digest: top matches first, then a deadline calendar."""
    items = sorted(STORE["tenders"].values(),
                   key=lambda t: t.match_score, reverse=True)
    calendar = sorted(
        [t for t in items if t.bid_due_date and (t.days_to_deadline() or 0) >= 0],
        key=lambda t: t.bid_due_date,
    )
    return render_template("digest.html", tenders=items[:10],
                           calendar=calendar, today=date.today())


# --- JSON API ---------------------------------------------------------------

@app.route("/api/tenders")
def api_tenders():
    return jsonify([t.to_dict() for t in STORE["tenders"].values()])


@app.route("/api/brief/<tid>")
def api_brief(tid: str):
    tender = STORE["tenders"].get(tid)
    if not tender:
        return jsonify({"error": "unknown tender"}), 404
    brief, source = generate_brief(tender)
    return jsonify({"id": tid, "brief": brief, "source": source})


@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "mode": STORE["mode"],
        "serpapi_configured": get_client().is_configured,
        "tenders_loaded": len(STORE["tenders"]),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
