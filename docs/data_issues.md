# Data issues log

Each issue: what was found, evidence, how the pipeline handles it, and whether it needs action.

## A. NIC Annual Reports (main source)

| # | Issue | Evidence | Handling | Action needed |
|---|---|---|---|---|
| A1 | The project's NIC "PDF" files are text extractions, not PDFs | `file` reports them as data/text | Bundled as .txt with SHA-256 checks (step 01) | Keep the originals; cite the published PDFs |
| A2 | Each report holds five-year insurer tables, so 2019 + 2024 reports cover 2015-2024 | 2019 report: 2015-19; 2024 report: 2020-24 | 2020 & 2022 reports used as cross-checks | Update the defence's data-sources line |
| A3 | Overlapping years agree exactly across report editions | 0 revisions in 130-189 overlaps per variable (step 07) | Vintage rule only affects precision | None. Report as a strength |
| A4 | GWP is exact GHS to 2019, rounded GHS millions from 2020 | Report table headers | 2020-22 growth taken from NIC's % change table; 2023 computed and flagged | Mention as a limitation for small insurers |
| A5 | 2024 column is IFRS 17 Insurance Revenue, not GWP | 2024 report, Table 19 title | 2024 growth not computed | Fix "GHS 6.67bn GWP 2024" claim on slides |
| A6 | NIC published CR != LR + ER for 41 insurer-years (2015-16) and 2 in 2021 | `cr_nic_mismatch` flag | CR constructed as LR + ER; NIC CR as sensitivity | State in methodology |
| A7 | NIC % change table contradicts its own GWP figures in a few cases | e.g. Multi 2019: GHS 0.69m -> 2.07m (+199%), NIC prints -2%; Glico 2017/18 | 2016-19 growth computed from exact GWP; `g_flag_nic_disagree` | None |
| A8 | 2015 NIC total exceeds the sum of listed insurers by GHS 3,287,646 (0.4%) | step 07 | Documented | Survivorship: insurer(s) exiting before 2019 not itemised |
| A9 | NIC "industry average" is not a simple mean | Simple mean CR 2018 = 530% vs NIC 142%; NWP-weighted = 142.8% | Report NWP-weighted aggregate alongside NIC figure | Method undocumented by NIC; say so |
| A10 | Insurer total assets only published for the top 10 (charts) | 2019-2024 reports | ln(lagged GWP) used as size control | Methodology change |
| A11 | Start-up years have extreme ratios | Serene 2018 ER 10,950% on GHS 1.0m GWP | Exclude entrants' first two years; raw as sensitivity | Methodology change |
| A12 | Name changes / mergers | WAPIC -> Coronation; Saham -> Sanlam -> SanlamAllianz (Allianz still separate to 2023; merger visible 2024). Regency Insurance and NEM Insurance merged into RegencyNem in 2016: NIC annual reports list only Regency in 2015 (GHS 17,807,025), so RegencyNem's 2016 growth (+61.4%) is mostly NEM's book being added. Against both companies combined it was about +3.0% (NEM 2015 GWP GHS 10,101,455, from the NIC quarterly returns workbook; see A15) | Canonical IDs in step 02. Merger rule (D13): growth across a merger is set to missing in the first year of the combined entity (`MERGERS` in src/config.py drives `merger_break`; `g`, `g_excess`, `g_real`, `g_real_dec`, `d_ms` and their lags become missing). The +3.0% pro-forma figure is not used. The 2016 market growth (25.7%, Figure 5) and `g_mkt_matched` for 2016 likely include NEM's book as new premium; this is left uncorrected because the correction would require unaudited data | Fix "SanlamAllianz from 2023" on slides |
| A13 | Insurer-by-class (motor vs non-motor) data not published | Only industry-level class premiums; class results only as charts | MID re-scoped to slope-change test | Methodology change (RQ3) |
| A14 | Deflator for real premium growth; December inflation 2015-18 and 2021 not in NIC reports | `cpi_avg_yoy` / `cpi_avg_source`, `cpi_dec_yoy` / `cpi_dec_source` columns; `data/raw/macro/README.md` | Switched (31 Oct 2026) from December y/y to annual-average CPI inflation: premium is a flow written across the year, so the annual average is the better deflator. Source: World Bank WDI FP.CPI.TOTL.ZG (orig. GSS), offline snapshot in `data/raw/macro/` retrieved 2026-10-31. December series kept as `g_real_dec` for comparison (2016-18 from GSS December bulletins, levels-derived and corroborated; 2019, 2020, 2022-24 as stated in NIC reports). December 2015 (17.7%) and 2021 (12.6%) verified against the GSS bulletins: "Statistical Bulletin: Consumer Price Index (CPI), December 2015, New Series (2012=100)", p. 3, released 13 Jan 2016 (the cover misprints 13 Jan 2015; the date is confirmed by the GSS December 2015 CPI newsletter); and "Statistical Bulletin: Consumer Price Index (CPI), December 2021, New Series (2018=100)", p. 3, released 12 Jan 2022. Index levels reproduce both rates (2012=100: Dec 2014 136.4, Dec 2015 160.6; 2018=100: Dec 2020 121.5, Dec 2021 136.86). The 2015 newsletter prints the Dec 2015 index as 160.5, against 160.6 in the bulletin; the 17.7% rate agrees in all GSS sources. Affects descriptive `g_real` and Figure 5 only; regressions use year FE | None |
| A15 | NIC quarterly returns workbook (insurer-level quarterly returns, incl. Q4 2013-2016) | Practitioner-supplied, unaudited; original source to be confirmed. Only use so far: NEM's 2015 GWP (GHS 10,101,455) for the RegencyNem pro-forma figure in A12 | Confidential pending source confirmation. Not in the repo: kept locally in `data/raw/quarterly/`, which is git-ignored. Not used in any analysis (D13) | Confirm the workbook's source and licence before any use beyond documentation |

## B. Facultative production report (supplementary)

| # | Issue | Handling |
|---|---|---|
| B1 | The two spreadsheets in the project are byte-identical | One file kept |
| B2 | One reinsurer's facultative inward book; no claims fields | Appendix only; cannot produce loss ratios |
| B3 | Reinsurer identity unknown | **Authors to confirm for citation** |
| B4 | Starts 22 Jun 2020: 2020 is a partial year | `flag_partial_year_2020` |
| B5 | 10 empty rows; currency codes "0", "D", "NIC Levy" | Rows dropped; codes set to UNKNOWN |
| B6 | "Amount Due" is net of commission in 5,063 rows, gross in 9 | `flag_amount_due_basis` |
| B7 | Contains insured client names | Excluded from git (.gitignore). Do not publish |
