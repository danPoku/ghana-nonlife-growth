"""Central paths and constants. Every script imports from here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_NIC = ROOT / "data" / "raw" / "nic_text"
RAW_PROD = ROOT / "data" / "raw" / "production"
RAW_MACRO = ROOT / "data" / "raw" / "macro"
WDI_CPI_FILE = RAW_MACRO / "wdi_FP.CPI.TOTL.ZG_GH.json"   # snapshot written once by src/00_fetch_macro.py
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
for p in (INTERIM, PROCESSED, TABLES, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

REPORT_YEARS = [2019, 2020, 2022, 2024]

# SHA-256 of every tracked raw input (the four NIC text extractions and the NIC quarterly returns workbook), in
# data/raw/CHECKSUMS (sha256sum format; check by hand with: cd data/raw && sha256sum -c CHECKSUMS). The parser relies on
# line positions and the returns panel on the exact workbook edition, so any change must be caught before reading.
RAW = ROOT / "data" / "raw"
SHA256 = {p.strip(): h for h, p in (l.split(None, 1) for l in (RAW / "CHECKSUMS").read_text(encoding="utf-8").splitlines() if l.strip())}
CHECKSUMS = {y: SHA256[f"nic_text/NIC_Annual_Report_{y}.txt"] for y in REPORT_YEARS}

PRODUCTION_FILE = RAW_PROD / "Production_Report_for_2025-05-08_10_32_51.xlsx"

# NIC quarterly returns workbook, published by the NIC on its website (data/raw/quarterly/SOURCE.md; data_issues A15,
# A17); the figures are insurers' unaudited quarterly submissions. Tracked in git. Edition: Q2 2026, retrieved
# 21 Nov 2026; its sheets Q1 2013 - Q1 2026 are identical to the Q1 2026 edition the analysis was built on, for every
# column the pipeline reads (A17). QUARTERLY_LAST caps the sheets read at Q1 2026, so later quarters in the edition
# (Q2 2026) do not change any output. Insurer-level files derived from it are written to data/processed/.
QUARTERLY_FILE = RAW / "quarterly" / "MARKET_REPORT_QUARTER_2_2026_NON_LIFE_bf1c110d5c.xlsx"
QUARTERLY_SHA256 = SHA256["quarterly/" + QUARTERLY_FILE.name]
QUARTERLY_LAST = (2026, 1)        # (year, quarter) of the last sheet read

# Estimation window (IFRS 4 period; Y years). 2023-24 are IFRS 17: descriptive only.
EST_START, EST_END = 2016, 2022
WINSOR = (0.01, 0.99)

# Mergers (D13): growth across a merger is not organic, so g and derived growth columns are set to
# missing in the first year of the combined entity. year = first year of the combined entity.
MERGERS = [
    dict(insurer_id="REGENCYNEM", year=2016, absorbed="NEM Insurance Ghana",
         source="NIC quarterly returns workbook (Q4 2013-2015 list Regency and NEM separately; Q4 2016 lists RegencyNem)"),
    dict(insurer_id="SAHAM_SANLAM", year=2024, absorbed="Allianz Insurance Company",
         source="NIC 2024 Annual Report (Allianz N-A in 2024)"),
]

# Ownership / brand changes (v2 sensitivity, Part 3): first year under the new name, from the year-end (Q4) names in the
# NIC quarterly returns workbook. The NIC annual reports agree except Coronation: the 2020 report already prints
# "Coronation" while the Q4 2020 return still reads "Wapic" (alt_year = 2020, run as a second variant).
RENAMES = [
    dict(insurer_id="SUNU", year=2018, old="Equity Assurance", new="SUNU Assurances"),
    dict(insurer_id="BEDROCK", year=2019, old="GN Insurance", new="Bedrock Insurance"),
    dict(insurer_id="CORONATION", year=2021, old="WAPIC Insurance", new="Coronation Insurance", alt_year=2020),
    dict(insurer_id="SAHAM_SANLAM", year=2022, old="Saham Insurance", new="Sanlam Insurance"),
]
