"""Tests for business-profile fit scoring."""

from datetime import date

from matcher import BusinessProfile, rank_tenders, score_fit
from tenders import Tender

TODAY = date(2026, 10, 7)


def _tender(**kw):
    base = dict(id="T1", title="Supply of computers", authority="GeM",
                portal="GeM", url="https://x", category="IT & Software",
                location="Karnataka", value_inr=5_000_000, emd_inr=100_000,
                bid_due_date=date(2026, 10, 24))
    base.update(kw)
    return Tender(**base)


def _profile(**kw):
    base = dict(name="Acme IT", sectors=["IT & Software"],
                turnover_band="₹25 Lakh – ₹1 Cr",
                locations=["Karnataka"], certifications=["MSME"],
                keywords=["laptop"])
    base.update(kw)
    return BusinessProfile(**base)


def test_perfect_fit_scores_high():
    t = _tender(snippet="MSME bidders exempt from EMD")
    score, reasons = score_fit(t, _profile(), TODAY)
    assert score >= 80
    assert any("Sector match" in r for r in reasons)


def test_wrong_sector_scores_low():
    t = _tender(category="Construction & Works", title="Road construction")
    score, _ = score_fit(t, _profile(), TODAY)
    assert score < 40


def test_location_mismatch_noted():
    t = _tender(location="Rajasthan")
    score, reasons = score_fit(t, _profile(), TODAY)
    assert any("Location note" in r for r in reasons)


def test_past_deadline_penalised():
    t = _tender(bid_due_date=date(2026, 9, 1))
    score, reasons = score_fit(t, _profile(), TODAY)
    assert any("Deadline passed" in r for r in reasons)


def test_urgent_deadline_flagged():
    t = _tender(bid_due_date=date(2026, 10, 9))
    _, reasons = score_fit(t, _profile(), TODAY)
    assert any("Urgent" in r for r in reasons)


def test_oversized_value_noted_not_hidden():
    t = _tender(value_inr=500_000_000)  # ₹50 Cr vs ₹60L turnover
    score, reasons = score_fit(t, _profile(), TODAY)
    assert any("may exceed your capacity" in r for r in reasons)
    assert score < 70


def test_keyword_partial_credit():
    t = _tender(category="General", title="laptop supply contract", snippet="")
    score, reasons = score_fit(t, _profile(sectors=[]), TODAY)
    assert any("Keyword match" in r for r in reasons)
    assert score >= 20


def test_rank_tenders_orders_best_first():
    good = _tender(id="G", category="IT & Software")
    bad = _tender(id="B", category="Construction & Works", title="Road work",
                  location="Rajasthan", value_inr=900_000_000)
    ranked = rank_tenders([bad, good], _profile(), TODAY)
    assert ranked[0].id == "G"
    assert ranked[0].match_score >= ranked[1].match_score


def test_score_bounded():
    t = _tender()
    score, _ = score_fit(t, _profile(), TODAY)
    assert 0 <= score <= 100
