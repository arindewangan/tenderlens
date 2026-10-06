# TenderLens — Devpost submission copy

**Track:** Knowledge & Public Interest
**Event:** SerpApi India Hackathon 2026

---

## Title
TenderLens — Indian public-tender intelligence for small businesses

## Tagline
Government tenders you'll actually win: live SerpApi search across India's
e-procurement portals, matched to your business.

## Inspiration
Every year the Indian government floats lakhs of crores in public tenders — but
for a small business owner in Indore or Coimbatore, finding the *right* tender
means manually trawling GeM, the CPP portal and a dozen state e-procure sites,
then decoding dense tender documents for the EMD, deadlines and eligibility
clauses that decide whether bidding is even worth it. Big contractors have
teams for this; SMBs don't. We wanted to give every small business a tender
analyst in their pocket.

## What it does
TenderLens aggregates Indian public-sector tenders discovered **live through
SerpApi's Google Search API** (site-restricted queries across GeM, CPPP,
eTenders, IREPS and state portals), then:

- **Extracts** what matters: EMD, bid due date, estimated value (₹/lakh/crore
  aware), issuing authority, location and category — parsed deterministically
  from every listing.
- **Scores** each tender 0–100 against your saved business profile (sectors,
  turnover band, service locations, MSME/ISO/NSIC/Startup-India certifications)
  with human-readable reasons — "why this tender matters to *you*".
- **Briefs** every tender in plain English: key facts, why-it-matters, and a
  bid-readiness checklist (AI-written when an LLM key is set, otherwise a
  clearly-labelled template brief).
- **Tracks**: watchlists, an email-style digest of top matches, and a deadline
  calendar so no bid date slips.

## How we built it
Python + Flask. `serpapi_client.py` wraps SerpApi's Google Search API with a
credit-frugal query set (4 targeted queries per search — the free plan's 250
credits/month go a long way). `tenders.py` does regex-based field extraction
and near-duplicate detection. `matcher.py` is a pure-Python scoring engine that
weighs sector fit, location, value-vs-turnover, certification advantages (MSME
EMD exemptions are a real edge) and deadline practicality. `llm.py` calls any
OpenAI-compatible endpoint for briefs with graceful template fallback. 48 pytest
tests cover extraction, dedupe, matching and the app itself, with SerpApi HTTP
fully mocked. When no API key is present the app runs in an honestly-labelled
demo mode with simulated data — it never pretends demo data is live.

## Challenges we ran into
Indian tender text is gloriously inconsistent: "Rs. 2 Lakh", "₹2,00,000" and
"2.5 Crore" all mean money, and bid dates hide behind a dozen phrasings ("bid
due date", "last date of submission", "closing date"). Building extraction that
is robust without hallucinating values took the most care. We also designed
around SerpApi's free-tier budget from the start: a handful of surgical
site-restricted queries instead of broad crawls.

## Accomplishments that we're proud of
- Search data isn't decoration here — it's the entire data pipeline. No SerpApi
  results, no product.
- The matcher explains itself: every score ships with reasons, including honest
  warnings ("value may exceed your capacity", "deadline passed").
- The app is fully usable with zero API keys thanks to labelled demo mode and
  template briefs.

## What we learned
Public procurement data is a search problem before it's an AI problem. The
highest-leverage work was query design and extraction — the LLM brief is the
cherry on top, not the cake.

## What's next
- Scheduled crawls + email digests; historical win-rate analytics per authority.
- Hindi/Tamil/Kannada brief translations for non-metro SMB owners.
- Document-level parsing: download the actual NIT PDFs and extract eligibility
  criteria automatically.

## Built with
Python, Flask, SerpApi (Google Search API), pytest, Jinja2

---

## Links
- GitHub repo: https://github.com/arindewangan/tenderlens
- Live demo: https://arindewangan.github.io/tenderlens/demo/
- Demo video (<3 min): TBD

## Disclosures
- AI tools used: an AI coding assistant helped write this codebase.
- This project was built new for this hackathon (October 2026).
