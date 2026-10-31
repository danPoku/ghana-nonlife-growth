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

# SHA-256 of the bundled NIC text extractions. The parser relies on line
# positions, so any change to these files must be caught before parsing.
CHECKSUMS = {
    2019: "c72f47e3cca96a6af9e3156ecd06974e7ca1bf1225b621743f49f3d7f4880d96",
    2020: "9f8c0dfdb3571252fde237c93884b5413c3c1a9a39e8b027c620531583c73695",
    2022: "6bd90af2272dc3a95e1310397c66ae300438a43943637b035b64e0d20cd1d0c3",
    2024: "4c759be2fb7d60b34c323b917c49e2bea3a4e27bf81ee01716811709fbcef1ba",
}

PRODUCTION_FILE = RAW_PROD / "Production_Report_for_2025-05-08_10_32_51.xlsx"

# NIC quarterly returns workbook: unaudited, practitioner-supplied, CONFIDENTIAL (data_issues A15). Git-ignored.
QUARTERLY_FILE = ROOT / "data" / "raw" / "quarterly" / "MARKET_REPORT_2025_QUARTER_1_2026_NON_LIFE_1_196263973d_6dc3659b1d.xlsx"
CONFIDENTIAL = ROOT / "data" / "processed" / "confidential"   # outputs derived from QUARTERLY_FILE; git-ignored

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
