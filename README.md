# Premium Growth and Underwriting Losses in Ghana's Non-Life Insurance Industry

Data and analysis pipeline for the MSc Actuarial Science thesis by Bismark Kantanka Sarfo and
Dan Gyinaye Poku (University of Ghana; supervisor Dr. Perpetual Andam Boiquaye).

**Question:** does insurer-level premium growth in year *t−1* predict underwriting performance
(loss, expense and combined ratios) in year *t*, 2015–2024?

## Quick start

```bash
# 1. Python 3.11+ (tested on 3.12.3)
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

# 2. Run everything (about 2 minutes)
python run_all.py            # resume at a script number: python run_all.py --from 4

# 3. Optional: R replication + System GMM (needs R 4.x)
Rscript R/twfe_and_system_gmm.R
```

The run ends with **48 validation checks** (38 plus a SKIP line when the NIC quarterly returns workbook is absent),
including two independently pinned result sets: "v1 (public, Tier 1 only)" and "v2 (thesis, requires NIC workbook)".
All must pass before results are used.

**v2 headline results require the NIC quarterly returns workbook** (an NIC product; the figures are insurers'
unaudited quarterly submissions), which is not in the repository. Without it, steps 9 and 12 are skipped and the
public pipeline reproduces the **v1 (Tier 1, audited NIC annual reports) results only**. The v1 state is tagged
`v1-methodology`.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `src/01_extract_nic.py` | Verifies raw-file checksums; parses all table blocks → `data/interim/blocks.json` |
| 2 | `src/02_build_long.py` | Validated variable mapping, canonical insurer IDs → `data/interim/nic_long_all_vintages.csv` (every value with report, table and line) |
| 12 | `src/12_returns_panel.py` | Returns panel (Tier 2) from the NIC quarterly returns workbook (skipped if absent): insurer-level → `data/processed/confidential/` (git-ignored); concordance, seasonality, survivorship, non-submission → `outputs/tables/returns_*.csv`, `seasonality.csv`. Runs before step 3 |
| 3 | `src/03_build_panel.py` | Insurer-year panel → `data/processed/panel_master.csv` |
| 4 | `src/04_analysis.py` | Descriptives, TWFE models, diagnostics, wild cluster bootstrap, dynamic check, gross-basis robustness → `outputs/tables/` |
| 5 | `src/05_figures.py` | Figures 1–5 → `outputs/figures/` |
| 6 | `src/06_facultative.py` | Supplementary facultative-reinsurance appendix (skipped if confidential file absent) |
| 7 | `src/07_validate.py` | Data-fidelity and pinned-result checks |
| 8 | `src/08_system_gmm.py` | System GMM robustness (pydynpd) → `outputs/tables/system_gmm*.csv` |
| 9 | `src/09_total_assets.py` | Total assets as size control, from the NIC quarterly returns workbook (skipped if absent) → `outputs/tables/robust_total_assets*.csv` |
| 10 | `src/10_leave_one_out.py` | Leave-one-insurer-out re-estimation of M1 → `outputs/tables/robust_leave_one_out*.csv`, Figure 6 |
| 11 | `src/11_cr_mismatch.py` | NIC printed CR vs LR + ER, 2015-16 → `outputs/tables/cr_mismatch_analysis.csv` |
| R | `R/twfe_and_system_gmm.R` | TWFE replication + System GMM → `outputs/tables/R_results.txt` |

## Data

- `data/raw/nic_text/` — NIC Annual Reports 2019, 2020, 2022 and 2024 as text extractions. Each report
  contains five-year insurer tables, so 2019 + 2024 cover 2015–2024; 2020 and 2022 act as cross-checks.
  **Do not edit or replace these files**: the parser's line map and SHA-256 checks depend on them.
- `data/raw/production/` — facultative reinsurance production report (Jun 2020–Dec 2024).
  **Confidential (contains client names) and excluded from git.** Copy it in manually to run step 6,
  together with `foreign_cedants.txt` (one foreign cedant name per line, also confidential).
  Step 6 outputs (`outputs/tables/fac_*`) are git-ignored for the same reason.
- **Macro data:** `data/raw/macro/` holds an offline snapshot of World Bank WDI `FP.CPI.TOTL.ZG`
  (Ghana annual-average CPI inflation, orig. GSS), used to deflate premium growth (`g_real`, Figure 5).
  The pipeline reads only the snapshot, so it runs offline and is reproducible. To refresh it, run
  `python src/00_fetch_macro.py` (not part of `run_all.py`), then rerun the pipeline.
- `data/raw/quarterly/` — NIC quarterly returns workbook (Q1 2013 – Q1 2026): an NIC product (source confirmed);
  the figures are insurers' unaudited quarterly submissions. **Not in git** (publication of insurer-level values not
  cleared); copy it in manually to run steps 9 and 12. Insurer-level outputs derived from it go to
  `data/processed/confidential/` (git-ignored); only aggregate tables are committed.

## Documentation

- `docs/methodology_decisions.md` — changes from the defence version, with reasons and sign-off status
- `docs/data_issues.md` — every data problem found and how it is handled
- `docs/codebook.md` — all panel variables
- `CLAUDE.md` — project context and rules for Claude Code

## Status and open items

- [ ] Authors and supervisor agree the methodology changes (D1–D11)
- [ ] Run and check the R script (System GMM)
- [ ] Verify CPI 2015–18 and 2021 against Ghana Statistical Service
- [ ] Verify methods citations (APA 7)
- [ ] Identify the reinsurer behind the production report (for citation)

## Sources

National Insurance Commission. *Annual report on the insurance industry* (2019, 2020, 2022, 2024 eds.). NIC, Accra.
Insurance Act, 2021 (Act 1061). Republic of Ghana.
