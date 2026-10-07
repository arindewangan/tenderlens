"""Tender parsing, field extraction and deduplication.

Turns raw SerpApi search hits into structured ``Tender`` records:
title, authority, portal, EMD, bid due date, estimated value, location
and category.  All extraction is regex/keyword based and deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse

from serpapi_client import RawResult, portal_for_link

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Tender:
    id: str
    title: str
    authority: str
    portal: str
    url: str
    snippet: str = ""
    emd_inr: int | None = None          # Earnest Money Deposit, rupees
    bid_due_date: date | None = None
    value_inr: int | None = None       # estimated tender value, rupees
    location: str = ""
    category: str = "General"
    published_hint: str = ""
    match_score: int = 0               # filled in by matcher.py
    match_reasons: list[str] = field(default_factory=list)

    def days_to_deadline(self, today: date | None = None) -> int | None:
        if not self.bid_due_date:
            return None
        return (self.bid_due_date - (today or date.today())).days

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["bid_due_date"] = self.bid_due_date.isoformat() if self.bid_due_date else None
        d["days_to_deadline"] = self.days_to_deadline()
        return d


# ---------------------------------------------------------------------------
# Money helpers (Indian formats: 50,000 / 2.5 Lakh / 1.2 Crore)
# ---------------------------------------------------------------------------

_AMOUNT = r"([\d,]+(?:\.\d+)?)\s*(lakh|lac|lacs|crore|crores)?"
_RUPEE = r"(?:rs\.?|₹|inr)"


def _amount_to_inr(raw_number: str, unit: str | None) -> int | None:
    try:
        number = float(raw_number.replace(",", ""))
    except ValueError:
        return None
    unit = (unit or "").lower()
    if unit.startswith("crore"):
        number *= 10_000_000
    elif unit.startswith(("lakh", "lac")):
        number *= 100_000
    return int(number)


def extract_emd(text: str) -> int | None:
    """Extract Earnest Money Deposit in INR from tender text."""
    patterns = [
        rf"(?:emd|earnest money deposit)(?:\s+of)?\s*[:\-]?\s*{_RUPEE}?\s*{_AMOUNT}",
        rf"{_RUPEE}\s*{_AMOUNT}\s*(?:as\s+)?(?:emd|earnest money)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            # groups: (number, unit) — but the rupee group is non-capturing
            number, unit = groups[-2], groups[-1]
            value = _amount_to_inr(number, unit)
            if value:
                return value
    return None


def extract_value(text: str) -> int | None:
    """Extract estimated tender value in INR from tender text."""
    patterns = [
        rf"(?:estimated\s+(?:cost|value)|tender\s+value|project\s+cost|approx(?:imate)?\s+(?:cost|value))\s*[:\-]?\s*{_RUPEE}?\s*{_AMOUNT}",
        rf"{_RUPEE}\s*{_AMOUNT}\s*(?:\(approx|approx)?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            number, unit = m.groups()[-2], m.groups()[-1]
            # skip matches that are clearly the EMD context
            start = max(0, m.start() - 30)
            if re.search(r"emd|earnest", text[start:m.start()], re.IGNORECASE):
                continue
            value = _amount_to_inr(number, unit)
            if value:
                return value
    return None


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

_MONTHS = (
    "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    "jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)
_DATE_PATTERNS = [
    r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{2,4})",
    rf"(\d{{1,2}})\s+({_MONTHS})\s*,?\s*(\d{{4}})",
]

_DEADLINE_HINTS = (
    "bid due", "last date", "submission", "closing date", "due date",
    "bid submission end", "last date of submission",
)


def _parse_date_match(m: re.Match) -> date | None:
    try:
        if len(m.groups()) == 3 and m.group(2).isdigit():
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            return date(y, mo, d)
        d = int(m.group(1))
        month = datetime.strptime(m.group(2)[:3].title(), "%b").month
        return date(int(m.group(3)), month, d)
    except (ValueError, IndexError):
        return None


def extract_bid_due_date(text: str) -> date | None:
    """Find the bid submission deadline mentioned in tender text."""
    low = text.lower()
    # Prefer dates that appear near deadline hint words.
    for hint in _DEADLINE_HINTS:
        idx = low.find(hint)
        if idx == -1:
            continue
        window = text[idx:idx + 120]
        for pat in _DATE_PATTERNS:
            m = re.search(pat, window, re.IGNORECASE)
            if m:
                parsed = _parse_date_match(m)
                if parsed:
                    return parsed
    # Fallback: first plausible future-ish date anywhere in the text.
    for pat in _DATE_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            parsed = _parse_date_match(m)
            if parsed and parsed.year >= 2024:
                return parsed
    return None


# ---------------------------------------------------------------------------
# Authority / location / category
# ---------------------------------------------------------------------------

_DOMAIN_AUTHORITY = {
    "gem.gov.in": "Government e-Marketplace",
    "eprocure.gov.in": "Central Public Procurement Portal",
    "etenders.gov.in": "eTenders",
    "ireps.gov.in": "Indian Railways",
}


def extract_authority(result: RawResult) -> str:
    """Best-effort authority name from the result link / source / title."""
    link = (result.link or "").lower()
    for domain, name in _DOMAIN_AUTHORITY.items():
        if domain in link:
            return name
    # "X invites bids / tenders for ..." pattern in the title.
    m = re.search(
        r"^(.{4,80}?)\s+(?:invites|invite|inviting)\s+(?:e?[\-\s]?tenders?|bids?)",
        result.title,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().title()
    if result.source:
        return result.source
    try:
        host = urlparse(result.link).netloc
        return host[4:] if host.startswith("www.") else host
    except Exception:  # noqa: BLE001
        return "Unknown authority"


CATEGORIES: dict[str, list[str]] = {
    "IT & Software": ["software", "it services", "computer", "laptop", "server",
                      "digit", "erp", "website", "app development", "cloud"],
    "Construction & Works": ["construction", "civil work", "building", "road",
                             "bridge", "rcc", "tender for work", "infrastructure"],
    "Healthcare & Medical": ["medical", "hospital", "medicine", "pharma",
                             "surgical", "diagnostic", "health"],
    "Transport & Logistics": ["transport", "vehicle", "bus", "truck", "logistics",
                              "fleet", "ambulance"],
    "Electrical & Power": ["electrical", "transformer", "cable", "solar",
                           "power", "substation", "lighting"],
    "Office & Supplies": ["stationery", "furniture", "office", "printing",
                          "consumables", "housekeeping consumable"],
    "Security Services": ["security", "housekeeping", "manpower", "guard",
                          "facility management"],
    "Consulting & Professional": ["consultancy", "consulting", "audit",
                                  "advisory", "dpr", "project management"],
}


def classify_category(text: str) -> str:
    low = text.lower()
    best, best_hits = "General", 0
    for category, keywords in CATEGORIES.items():
        hits = sum(1 for kw in keywords if kw in low)
        if hits > best_hits:
            best, best_hits = category, hits
    return best


INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Jammu and Kashmir", "Ladakh",
    "Puducherry", "Chandigarh",
]
INDIAN_CITIES = [
    "Bengaluru", "Bangalore", "Mumbai", "Delhi", "New Delhi", "Chennai",
    "Hyderabad", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Kochi", "Coimbatore",
]


def extract_location(text: str) -> str:
    low = text.lower()
    for city in INDIAN_CITIES:
        if city.lower() in low:
            return city
    for state in INDIAN_STATES:
        if state.lower() in low:
            return state
    if "pan india" in low or "all india" in low:
        return "PAN India"
    return ""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # drop common tender boilerplate so near-duplicates collapse
    t = re.sub(r"\b(tender|tenders|notice|inviting|invites|bid|bids|for|the|of|and|e)\b", "", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_result(result: RawResult, tender_id: str) -> Tender:
    text = f"{result.title}\n{result.snippet}"
    return Tender(
        id=tender_id,
        title=result.title.strip(),
        authority=extract_authority(result),
        portal=result.portal or portal_for_link(result.link),
        url=result.link,
        snippet=result.snippet,
        emd_inr=extract_emd(text),
        bid_due_date=extract_bid_due_date(text),
        value_inr=extract_value(text),
        location=extract_location(text),
        category=classify_category(text),
    )


def dedupe(tenders: list[Tender]) -> list[Tender]:
    """Remove duplicates: same link, same normalised title, or near-duplicate."""
    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    kept: list[Tender] = []
    for tender in tenders:
        link = (tender.url or "").rstrip("/").lower()
        if link and link in seen_links:
            continue
        norm = normalize_title(tender.title)
        if norm and norm in seen_titles:
            continue
        # near-duplicate titles (e.g. re-tendered with a new ref number)
        if norm and any(
            SequenceMatcher(None, norm, other).ratio() > 0.88
            for other in seen_titles
        ):
            continue
        seen_links.add(link)
        seen_titles.add(norm)
        kept.append(tender)
    return kept


def build_tenders(results: list[RawResult]) -> list[Tender]:
    parsed = [parse_result(r, f"T{i + 1:03d}") for i, r in enumerate(results)]
    return dedupe(parsed)
