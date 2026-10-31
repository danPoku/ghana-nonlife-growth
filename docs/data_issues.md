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
| A12 | Name changes / mergers | WAPIC -> Coronation; Saham -> Sanlam -> SanlamAllianz (Allianz still separate to 2023; merger visible 2024) | Canonical IDs in step 02; `merger_break` flag | Fix "SanlamAllianz from 2023" on slides |
| A13 | Insurer-by-class (motor vs non-motor) data not published | Only industry-level class premiums; class results only as charts | MID re-scoped to slope-change test | Methodology change (RQ3) |
| A14 | Inflation 2015-18 and 2021 not in NIC reports | `cpi_source` column | Marked "GSS (to verify)"; affects descriptive real growth only | Verify against GSS |

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
