"""Business-profile fit scoring for tenders.

Pure Python, no network calls.  An SMB owner saves a profile (sectors,
turnover band, locations, certifications) and every tender is scored
0-100 with human-readable reasons, so the owner sees *why* a tender
matters to them — not just a number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from tenders import Tender

# Turnover bands mapped to a representative annual turnover (INR).
TURNOVER_BANDS: dict[str, int] = {
    "Under ₹25 Lakh": 1_500_000,        # ₹15 Lakh
    "₹25 Lakh – ₹1 Cr": 6_000_000,      # ₹60 Lakh
    "₹1 Cr – ₹10 Cr": 40_000_000,       # ₹4 Cr
    "₹10 Cr – ₹50 Cr": 250_000_000,     # ₹25 Cr
    "Above ₹50 Cr": 750_000_000,        # ₹75 Cr
}

CERTIFICATION_KEYWORDS = {
    "MSME": ["msme", "udyam", "small enterprise", "micro enterprise"],
    "ISO": ["iso"],
    "NSIC": ["nsic"],
    "Startup India": ["startup", "dpiit"],
}


@dataclass
class BusinessProfile:
    name: str = "My Business"
    sectors: list[str] = field(default_factory=list)      # category names
    turnover_band: str = "₹25 Lakh – ₹1 Cr"
    locations: list[str] = field(default_factory=list)    # states/cities served
    certifications: list[str] = field(default_factory=list)  # e.g. MSME, ISO
    keywords: list[str] = field(default_factory=list)     # extra watch keywords

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessProfile":
        return cls(
            name=data.get("name", "My Business"),
            sectors=data.get("sectors", []),
            turnover_band=data.get("turnover_band", "₹25 Lakh – ₹1 Cr"),
            locations=data.get("locations", []),
            certifications=data.get("certifications", []),
            keywords=data.get("keywords", []),
        )


def _turnover_inr(profile: BusinessProfile) -> int:
    return TURNOVER_BANDS.get(profile.turnover_band, 6_000_000)


def score_fit(tender: Tender, profile: BusinessProfile,
              today: date | None = None) -> tuple[int, list[str]]:
    """Score a tender 0-100 for a business profile. Returns (score, reasons)."""
    today = today or date.today()
    score = 0
    reasons: list[str] = []

    # 1. Sector / category match — the strongest signal. (+40 / +20 partial)
    if tender.category in profile.sectors:
        score += 40
        reasons.append(f"Sector match: {tender.category} is one of your business sectors.")
    else:
        hay = f"{tender.title} {tender.snippet}".lower()
        if any(kw.lower() in hay for kw in profile.keywords if kw):
            score += 20
            reasons.append("Keyword match: tender mentions one of your watch keywords.")

    # 2. Location match. (+20)
    tender_loc = (tender.location or "").lower()
    if tender_loc in ("", "pan india"):
        score += 10
        reasons.append("Location: open across India (PAN India).")
    elif any(loc.lower() in tender_loc or tender_loc in loc.lower()
             for loc in profile.locations if loc):
        score += 20
        reasons.append(f"Location match: {tender.location} is in your service area.")
    elif profile.locations:
        reasons.append(f"Location note: tender is in {tender.location or 'an unspecified location'}.")

    # 3. Value vs turnover fit. (+15)  Tenders ~1-20x annual turnover are the
    #    sweet spot for SMBs; tiny ones waste bid effort, giant ones are out of reach.
    turnover = _turnover_inr(profile)
    if tender.value_inr:
        ratio = tender.value_inr / max(turnover, 1)
        if 1 <= ratio <= 20:
            score += 15
            reasons.append(
                f"Value fit: estimated ₹{tender.value_inr:,} suits your turnover band."
            )
        elif ratio < 1:
            score += 5
            reasons.append("Value note: tender value is small relative to your turnover.")
        else:
            reasons.append(
                f"Value note: estimated ₹{tender.value_inr:,} may exceed your capacity."
            )

    # 4. Certification edge. (+15)  Many Indian tenders reserve relaxations for
    #    MSME/NSIC/Startup-India bidders — a genuine competitive advantage.
    text = f"{tender.title} {tender.snippet}".lower()
    for cert in profile.certifications:
        kws = CERTIFICATION_KEYWORDS.get(cert, [cert.lower()])
        if any(kw in text for kw in kws):
            score += 15
            reasons.append(f"Certification edge: tender mentions {cert}-friendly terms.")
            break

    # 5. Deadline practicality. (+10 / -10)
    days = tender.days_to_deadline(today)
    if days is not None:
        if days < 0:
            score -= 10
            reasons.append("Deadline passed — likely closed to new bids.")
        elif days <= 3:
            score -= 5
            reasons.append(f"Urgent: only {days} day(s) left to bid.")
        elif days <= 14:
            score += 10
            reasons.append(f"Good timing: {days} days left to prepare a bid.")
        else:
            score += 5
            reasons.append(f"Comfortable timeline: {days} days left to bid.")

    # 6. EMD affordability sanity check (informational only).
    if tender.emd_inr and tender.emd_inr > turnover * 0.25:
        reasons.append(
            f"EMD note: ₹{tender.emd_inr:,} earnest money is steep for your band."
        )

    return max(0, min(100, score)), reasons


def rank_tenders(tenders: list[Tender], profile: BusinessProfile,
                 today: date | None = None) -> list[Tender]:
    """Attach scores to tenders and return them best-first."""
    for tender in tenders:
        tender.match_score, tender.match_reasons = score_fit(tender, profile, today)
    return sorted(tenders, key=lambda t: t.match_score, reverse=True)
