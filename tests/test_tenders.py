"""Tests for tender parsing, extraction and dedupe."""

from datetime import date

from serpapi_client import RawResult
from tenders import (
    build_tenders,
    classify_category,
    dedupe,
    extract_authority,
    extract_bid_due_date,
    extract_emd,
    extract_location,
    extract_value,
    normalize_title,
    parse_result,
)


def _res(title="Tender", snippet="", link="https://gem.gov.in/x", source=""):
    return RawResult(title=title, link=link, snippet=snippet, source=source)


# --- EMD extraction ----------------------------------------------------------

def test_extract_emd_plain_rupees():
    assert extract_emd("EMD: Rs. 50,000") == 50000


def test_extract_emd_lakh():
    assert extract_emd("Earnest Money Deposit of Rs. 2 Lakh") == 200000


def test_extract_emd_symbol():
    assert extract_emd("EMD ₹2,00,000") == 200000


def test_extract_emd_missing():
    assert extract_emd("No earnest money mentioned here") is None


# --- Value extraction -------------------------------------------------------

def test_extract_value_crore():
    assert extract_value("Estimated Cost: Rs. 2.5 Crore") == 25000000


def test_extract_value_lakh():
    assert extract_value("Tender value approx Rs. 45 Lakh") == 4500000


def test_extract_value_skips_emd_context():
    # "Rs. 50,000 as EMD" must not be mistaken for the tender value.
    assert extract_value("EMD Rs. 50,000 as earnest money") is None


# --- Date extraction ---------------------------------------------------------

def test_extract_bid_due_date_dmy():
    assert extract_bid_due_date("Bid Due Date 24-10-2026") == date(2026, 10, 24)


def test_extract_bid_due_date_text_month():
    assert extract_bid_due_date("Last date of submission: 20 Oct 2026") == date(2026, 10, 20)


def test_extract_bid_due_date_missing():
    assert extract_bid_due_date("no dates here at all") is None


# --- Authority / location / category -----------------------------------------

def test_extract_authority_known_portal():
    r = _res(link="https://gem.gov.in/bid/123")
    assert extract_authority(r) == "Government e-Marketplace"


def test_extract_authority_invites_pattern():
    r = _res(title="Indore Municipal Corporation invites e-tenders for road work",
             link="https://example.org/t")
    assert "Indore Municipal Corporation" in extract_authority(r)


def test_extract_location_city():
    assert extract_location("work at Jaipur, Rajasthan") == "Jaipur"


def test_extract_location_pan_india():
    assert extract_location("supply on PAN India basis") == "PAN India"


def test_classify_category_it():
    assert classify_category("supply of desktop computers and servers") == "IT & Software"


def test_classify_category_construction():
    assert classify_category("construction of RCC drain and road") == "Construction & Works"


# --- Dedupe -------------------------------------------------------------------

def test_dedupe_same_link():
    rs = [_res(title="Tender A", link="https://gem.gov.in/1"),
          _res(title="Tender A", link="https://gem.gov.in/1")]
    assert len(build_tenders(rs)) == 1


def test_dedupe_same_title_different_link():
    rs = [_res(title="Supply of Computers", link="https://gem.gov.in/1"),
          _res(title="Supply of Computers!", link="https://gem.gov.in/2")]
    assert len(build_tenders(rs)) == 1


def test_dedupe_near_duplicate_titles():
    rs = [_res(title="Supply of 500 Desktop Computers for Offices", link="https://a.in/1"),
          _res(title="Supply of 500 Desktop Computers for Offices Ref 2", link="https://b.in/2")]
    assert len(build_tenders(rs)) == 1


def test_dedupe_keeps_distinct():
    rs = [_res(title="Supply of Computers", link="https://gem.gov.in/1"),
          _res(title="Construction of Road", link="https://gem.gov.in/2")]
    assert len(build_tenders(rs)) == 2


def test_normalize_title_strips_boilerplate():
    assert normalize_title("Tender Notice Inviting Bids for Computers") == normalize_title("Computers")


def test_parse_result_assigns_all_fields():
    r = _res(
        title="Supply of Laptops, Bengaluru — EMD Rs. 1,00,000, Bid Due 24-10-2026",
        snippet="Estimated value Rs. 1 Crore for Bengaluru offices.",
        link="https://gem.gov.in/bid/9",
    )
    t = parse_result(r, "T001")
    assert t.id == "T001"
    assert t.emd_inr == 100000
    assert t.value_inr == 10000000
    assert t.bid_due_date == date(2026, 10, 24)
    assert t.location == "Bengaluru"
    assert t.category == "IT & Software"
