# TenderLens 🔍

**Indian public-tender intelligence for small businesses.**
Built for the **SerpApi India Hackathon 2026** — track: *Knowledge & Public Interest*.

Indian government tenders are scattered across GeM, the Central Public Procurement
Portal, and dozens of state e-procurement sites. TenderLens aggregates them using
**SerpApi's Google Search API** (search data is the core of the app — no search,
no tenders), extracts the fields that matter (EMD, bid due date, estimated value,
authority, location, category), and scores every tender 0–100 against *your*
business profile — sector, turnover band, locations, certifications — with
human-readable reasons, plain-English briefs, watchlists, a digest view and a
deadline calendar.

## How it works

1. **Discover** — `serpapi_client.py` runs a credit-frugal set of site-restricted
   Google queries (`site:gem.gov.in`, `site:eprocure.gov.in`, …) through SerpApi.
2. **Extract** — `tenders.py` parses EMD / value (₹, lakh, crore), bid due dates,
   authority, location and category from each hit, then dedupes.
3. **Match** — `matcher.py` scores each tender against your saved business profile
   (pure Python, no API needed).
4. **Brief** — `llm.py` writes a plain-English brief per tender: via a configured
   OpenAI-compatible LLM, or a deterministic template brief (always labelled).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your keys (see below)
python app.py          # → http://127.0.0.1:5000
```

### Get a free SerpApi key (250 searches/month)

1. Sign up at https://serpapi.com/users/sign_up
2. Copy your API key from the dashboard
3. Put it in `.env` as `SERPAPI_API_KEY=...`

Without a key the app runs in **clearly-labelled DEMO MODE** with simulated
tender data (`demo_data.py`) — it never pretends demo data is live.

### Optional: AI-written briefs

Set `LLM_API_KEY` (and optionally `LLM_BASE_URL` / `LLM_MODEL` for any
OpenAI-compatible endpoint) in `.env`. Without it, briefs use the built-in
template and the UI labels them as such.

## Run the tests

```bash
.venv/bin/python -m pytest tests/ -q   # 48 tests
```

## Project layout

| File | What it does |
|---|---|
| `app.py` | Flask app: search, detail, profile, watchlist, digest, JSON API |
| `serpapi_client.py` | SerpApi Google Search wrapper + portal query builder |
| `tenders.py` | Field extraction (EMD/value/dates), classification, dedupe |
| `matcher.py` | Business-profile fit scoring (0–100 + reasons) |
| `llm.py` | Tender briefs: LLM when configured, labelled template fallback |
| `demo_data.py` | **Labelled** simulated tenders for demo mode |
| `templates/` / `static/` | Jinja templates + stylesheet |
| `demo/index.html` | Standalone static showcase (simulated data, clearly labelled) |
| `tests/` | 48 pytest tests (mocked SerpApi, extraction, matcher, app) |

## API

- `GET /api/health` — status, mode (`live`/`demo`), SerpApi configured?
- `GET /api/tenders` — ranked tenders as JSON
- `GET /api/brief/<id>` — brief markdown + source (`llm`/`template`)

## Disclosures

- **AI tools used:** an AI coding assistant helped write this codebase.
- **New project:** built fresh for this hackathon (Oct 2026), not pre-existing.
- Demo data in `demo_data.py` and `demo/` is simulated and always labelled as such.

## License

MIT — see `LICENSE`.
