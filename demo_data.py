"""Clearly-labelled DEMO data for TenderLens.

These canned tenders are realistic in shape (titles, portals, EMD / value /
deadline phrasing follow real Indian tender conventions) but are NOT live
listings.  The app serves them ONLY when no SERPAPI_API_KEY is configured,
and every screen labels the mode as "DEMO MODE — simulated data".

Never present these as live search results.
"""

from serpapi_client import RawResult

DEMO_NOTICE = (
    "DEMO MODE — simulated data. Set SERPAPI_API_KEY to search live tenders."
)

DEMO_RESULTS: list[RawResult] = [
    RawResult(
        title="Supply of 500 Desktop Computers for District e-Governance Offices, "
              "Karnataka — Bid Due Date 24-10-2026, EMD Rs. 2,00,000",
        link="https://gem.gov.in/demo/bid-computers-ka-2026",
        snippet="Government e-Marketplace invites bids for supply of 500 desktop "
                "computers (i5, 16GB RAM) for district e-Governance offices across "
                "Karnataka. Estimated value Rs. 2.5 Crore. EMD: Rs. 2,00,000. "
                "Bid due date: 24-10-2026. MSE/Startup exemption applicable.",
        source="gem.gov.in",
        portal="Government e-Marketplace (GeM)",
    ),
    RawResult(
        title="Construction of RCC Drain and CC Road in Ward 12, Indore — "
              "Estimated Cost Rs. 85 Lakh, Last Date 18-10-2026",
        link="https://eprocure.gov.in/demo/indore-road-work-2026",
        snippet="Indore Municipal Corporation invites e-tenders for construction "
                "of RCC drain and cement concrete road in Ward 12, Indore, Madhya "
                "Pradesh. Estimated cost: Rs. 85 Lakh. EMD Rs. 1,70,000. "
                "Last date of submission: 18-10-2026.",
        source="eprocure.gov.in",
        portal="Central Public Procurement Portal (CPPP)",
    ),
    RawResult(
        title="Annual Maintenance Contract for Hospital Medical Equipment, "
              "Government Medical College Thiruvananthapuram",
        link="https://etenders.gov.in/demo/gmc-tvm-amc-2026",
        snippet="Government Medical College, Thiruvananthapuram, Kerala invites "
                "tenders for annual maintenance of diagnostic and surgical "
                "equipment. Tender value approx Rs. 45 Lakh. Bid submission end "
                "date: 30-10-2026. EMD: Rs. 90,000.",
        source="etenders.gov.in",
        portal="eTenders Portal",
    ),
    RawResult(
        title="Hiring of 20 Security Guards for Secretariat Complex, Jaipur — "
              "Rajasthan",
        link="https://gem.gov.in/demo/security-jaipur-2026",
        snippet="General Administration Department, Rajasthan invites bids for "
                "hiring of 20 security guards for the Secretariat Complex, Jaipur "
                "for one year. Estimated value Rs. 60 Lakh. Bid due date: "
                "12-11-2026. EMD Rs. 1,20,000. MSME bidders exempt from EMD.",
        source="gem.gov.in",
        portal="Government e-Marketplace (GeM)",
    ),
    RawResult(
        title="Supply and Installation of 10kW Rooftop Solar Plants at 15 "
              "Primary Schools, Pune District",
        link="https://mahatenders.gov.in/demo/solar-pune-2026",
        snippet="Zilla Parishad Pune, Maharashtra invites tenders for supply and "
                "installation of 10kW rooftop solar power plants at 15 primary "
                "schools. Estimated cost Rs. 1.2 Crore. EMD: Rs. 2,40,000. "
                "Closing date: 05-11-2026.",
        source="mahatenders.gov.in",
        portal="Maharashtra e-Tendering",
    ),
    RawResult(
        title="Development of Citizen Grievance Mobile App for Municipal "
              "Corporation, Coimbatore",
        link="https://tender.tn.gov.in/demo/grievance-app-cbe-2026",
        snippet="Coimbatore City Municipal Corporation, Tamil Nadu invites bids "
                "for development of an Android/iOS citizen grievance redressal "
                "mobile app with dashboard. Project cost approx Rs. 35 Lakh. "
                "Last date: 28-10-2026. Startup India recognised bidders may "
                "claim EMD exemption.",
        source="tender.tn.gov.in",
        portal="Tamil Nadu Tenders",
    ),
    RawResult(
        title="Supply of Office Furniture for New Collectorate Building, Lucknow",
        link="https://etender.up.nic.in/demo/furniture-lko-2026",
        snippet="Office of the District Magistrate, Lucknow, Uttar Pradesh "
                "invites e-tenders for supply of office furniture (tables, "
                "chairs, storage) for the new Collectorate building. Estimated "
                "value Rs. 28 Lakh. Bid due date: 22-10-2026. EMD Rs. 56,000.",
        source="etender.up.nic.in",
        portal="Uttar Pradesh e-Tender",
    ),
    RawResult(
        title="Catering Services for 500-Bed District Hospital, Patna — 2 Year Contract",
        link="https://eprocure.gov.in/demo/catering-patna-2026",
        snippet="State Health Society, Bihar invites tenders for catering "
                "services for the 500-bed district hospital, Patna. Contract "
                "value approx Rs. 3 Crore over two years. Bid submission end: "
                "15-11-2026. EMD: Rs. 6,00,000.",
        source="eprocure.gov.in",
        portal="Central Public Procurement Portal (CPPP)",
    ),
    RawResult(
        title="Supply of LED Street Lights with 5-Year Warranty, Surat Municipal "
              "Corporation",
        link="https://gem.gov.in/demo/led-surat-2026",
        snippet="Surat Municipal Corporation, Gujarat invites GeM bids for supply "
                "of 2,000 LED street lights with 5-year warranty. Estimated "
                "value Rs. 1.8 Crore. Bid due date: 09-11-2026. EMD Rs. 3,60,000.",
        source="gem.gov.in",
        portal="Government e-Marketplace (GeM)",
    ),
    RawResult(
        title="Internal Audit and GST Consultancy for PSU Subsidiary, Hyderabad",
        link="https://eprocure.gov.in/demo/audit-hyd-2026",
        snippet="A central PSU subsidiary, Hyderabad, Telangana invites "
                "proposals for internal audit and GST consultancy for FY 2026-27. "
                "Estimated consultancy fee Rs. 18 Lakh. Last date of submission: "
                "26-10-2026. No EMD required.",
        source="eprocure.gov.in",
        portal="Central Public Procurement Portal (CPPP)",
    ),
    RawResult(
        title="Housekeeping Services for Railway Station Premises, Hubballi "
              "Division — IREPS",
        link="https://ireps.gov.in/demo/housekeeping-ubl-2026",
        snippet="South Western Railway, Hubballi Division, Karnataka invites "
                "e-tenders for mechanised housekeeping of station premises for "
                "two years. Estimated cost Rs. 95 Lakh. Bid due date: 02-11-2026. "
                "EMD Rs. 1,90,000.",
        source="ireps.gov.in",
        portal="Indian Railways e-Procurement (IREPS)",
    ),
    RawResult(
        title="Printing and Supply of Property Tax Bills, Bruhat Bengaluru "
              "Mahanagara Palike",
        link="https://eproc.karnataka.gov.in/demo/printing-bbmp-2026",
        snippet="BBMP, Bengaluru, Karnataka invites tenders for printing and "
                "supply of approximately 12 lakh property tax bills with "
                "barcodes. Estimated value Rs. 22 Lakh. Closing date: 20-10-2026. "
                "EMD: Rs. 44,000. MSE price preference applicable.",
        source="eproc.karnataka.gov.in",
        portal="Karnataka e-Procurement",
    ),
]


def get_demo_results() -> list[RawResult]:
    return list(DEMO_RESULTS)
