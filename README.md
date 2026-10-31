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

# 2. Run everything (about 20 seconds)
python run_all.py            # resume from a step with: python run_all.py --from 4

# 3. Optional: R replication + System GMM (needs R 4.x)
Rscript R/twfe_and_system_gmm.R
```

The run ends with **26 validation checks**. All must pass before results are used.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `src/01_extract_nic.py` | Verifies raw-file checksums; parses all table blocks → `data/interim/blocks.json` |
| 2 | `src/02_build_long.py` | Validated variable mapping, canonical insurer IDs → `data/interim/nic_long_all_vintages.csv` (every value with report, table and line) |
| 3 | `src/03_build_panel.py` | Insurer-year panel → `data/processed/panel_master.csv` |
| 4 | `src/04_analysis.py` | Descriptives, TWFE models, diagnostics, wild cluster bootstrap, dynamic check → `outputs/tables/` |
| 5 | `src/05_figures.py` | Figures 1–5 → `outputs/figures/` |
| 6 | `src/06_facultative.py` | Supplementary facultative-reinsurance appendix (skipped if confidential file absent) |
| 7 | `src/07_validate.py` | Data-fidelity and pinned-result checks |
| R | `R/twfe_and_system_gmm.R` | TWFE replication + System GMM → `outputs/tables/R_results.txt` (**untested**) |

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
