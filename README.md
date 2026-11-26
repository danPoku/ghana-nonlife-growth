# Premium Growth and Underwriting Losses in Ghana's Non-Life Insurance Industry

Data and analysis pipeline for the MSc Actuarial Science thesis by Bismark Kantanka Sarfo and Dan Gyinaye Poku,
University of Ghana (supervisor: Dr. Perpetual Andam Boiquaye). One command rebuilds every table and figure in the
thesis from the data in this repository.

## The question

Does an insurer's premium growth in year *t−1* predict its underwriting performance (loss, expense and combined
ratios) in year *t*? Panel of Ghana's non-life insurers, 2015–2024; estimation 2016–2022 (IFRS 4 years), two-way
fixed effects with insurer-clustered standard errors and a wild cluster bootstrap.

## Main findings

- **Own growth: no detectable effect.** +10 pp of prior-year premium growth changes an insurer's next-year combined ratio by +0.16 pp (95% CI −1.6 to +1.9 pp; wild cluster bootstrap p = 0.92; minimum detectable effect 2.5 pp). The result holds under every specification and robustness check.
- **Growth between insurers:** insurers that grow faster on average have lower average expense and combined ratios (p = 0.010 and 0.013); this is a difference between insurers, not an effect of an insurer's own growth.
- **Size:** larger insurers have lower average expense ratios (−12.1 pp per log unit of total assets, p = 0.043), but an insurer's own expense ratio does not fall as it grows (within-insurer +3.5 pp, p = 0.74).
- **Motor Insurance Database (verification phase, 2020–22):** no detectable change in the growth slope on the combined ratio (joint p = 0.84); the later tariff-enforcement enhancements fall outside the period tested.
- **Expenses dominate:** the expense ratio is 70–99% of net earned premium plus reinsurance commission, against 30–50% for the loss ratio.

Details and every robustness result: `docs/methodology_decisions.md` ("Headline results") and the appendix tables
`outputs/tables/appendix_*.csv`.

## Reproduce

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt          # Python 3.11+ (tested on 3.12.3)
python run_all.py                        # about 2 minutes
```

The run ends with **48 passed, 0 failed**: data-fidelity checks plus two pinned result sets, "v1 (public, Tier 1
only)" and "v2 (thesis, requires NIC workbook)". Step 6 prints "Production file not found; skipping step 6" (see
below). Resume at a script number with `python run_all.py --from N`. Optional R replication and System GMM (R 4.x):
`Rscript R/twfe_and_system_gmm.R`.

## Data sources

- **NIC annual reports** (`data/raw/nic_text/`): National Insurance Commission, *Annual Report on the Insurance
  Industry*, 2019, 2020, 2022 and 2024 editions, as text extractions (audited insurer-level tables; Tier 1).
- **NIC quarterly returns workbook** (`data/raw/quarterly/`): National Insurance Commission, Market Report Q2 2026,
  Non-Life, read from Q1 2013 to Q1 2026. Figures are insurers' unaudited quarterly submissions, compiled and
  published by the NIC (Tier 2). Source, URL and retrieval date in `data/raw/quarterly/SOURCE.md`.
- **CPI inflation** (`data/raw/macro/`): World Bank WDI `FP.CPI.TOTL.ZG` (Ghana Statistical Service), offline snapshot.

Every raw file is checked against its SHA-256 in `data/raw/CHECKSUMS` before it is read.

## What is excluded, and why

The supplementary facultative-reinsurance appendix (step 6) uses a reinsurer's production report that contains
client names. It is confidential and not in the repository; step 6 skips without it. No thesis result in the main
analysis depends on it.

## v1 and v2

The thesis reports the v2 methodology (component-based ratios from the quarterly returns, total assets as size; see
`docs/methodology_decisions.md`, D14–D22). The earlier v1 results are kept for the v1 → v2 comparison: frozen outputs in
`outputs/tables/v1/` and `outputs/figures/v1/`, and git tag `v1-methodology`. Step 07 pins both result sets.

## How to cite

Use the citation in `CITATION.cff` (GitHub: "Cite this repository"):

> Sarfo, B. K., & Poku, D. G. (2026). *Premium Growth and Underwriting Losses in Ghana's Non-Life Insurance Industry:
> data and analysis pipeline* (Version v2.0-thesis) [Computer software]. https://github.com/danPoku/ghana-nonlife-growth

Code: MIT (`LICENSE`). Data: NIC and World Bank publications remain theirs; derived tables and figures are CC BY 4.0
(`DATA_NOTICE.md`).

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `src/01_extract_nic.py` | Verifies raw-file checksums; parses all table blocks → `data/interim/blocks.json` |
| 2 | `src/02_build_long.py` | Validated variable mapping, canonical insurer IDs → `data/interim/nic_long_all_vintages.csv` (every value with report, table and line) |
| 12 | `src/12_returns_panel.py` | Returns panel (Tier 2) from the NIC quarterly returns workbook: insurer-level → `data/processed/`; concordance, seasonality, survivorship, non-submission → `outputs/tables/returns_*.csv`, `seasonality.csv`. Runs before step 3 |
| 3 | `src/03_build_panel.py` | Insurer-year panel → `data/processed/panel_master.csv` |
| 4 | `src/04_analysis.py` | Descriptives, TWFE models, diagnostics, wild cluster bootstrap, dynamic check, gross-basis robustness → `outputs/tables/` |
| 5 | `src/05_figures.py` | Thesis Figures 1–7 → `outputs/figures/Figure_N_*.png` (Figure 8 from step 10) |
| 6 | `src/06_facultative.py` | Supplementary facultative-reinsurance appendix (skipped if confidential file absent) |
| 7 | `src/07_validate.py` | Data-fidelity and pinned-result checks |
| 8 | `src/08_system_gmm.py` | System GMM robustness (pydynpd) → `outputs/tables/system_gmm*.csv` |
| 9 | `src/09_total_assets.py` | Total assets as size control, from the NIC quarterly returns workbook → `outputs/tables/robust_total_assets*.csv` |
| 10 | `src/10_leave_one_out.py` | Leave-one-insurer-out re-estimation of M1 → `outputs/tables/robust_leave_one_out*.csv`, thesis Figure 8 |
| 11 | `src/11_cr_mismatch.py` | NIC printed CR vs LR + ER, 2015-16 → `outputs/tables/cr_mismatch_analysis.csv` |
| 13 | `src/13_threshold.py` | Hansen (1999) threshold test (simulation validation, then real data) → `threshold_simulation.csv`, `threshold_v2.csv` |
| 14 | `src/14_appendix.py` | Thesis appendix tables `outputs/tables/appendix_*.csv` (FE models, diagnostics, GMM, replication, early warning, robustness, seasonality, concordance) |
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
  (Ghana annual-average CPI inflation, orig. GSS), used to deflate premium growth (`g_real`, Figure 3).
  The pipeline reads only the snapshot, so it runs offline and is reproducible. To refresh it, run
  `python src/00_fetch_macro.py` (not part of `run_all.py`), then rerun the pipeline.
- `data/raw/quarterly/` — NIC quarterly returns workbook, Market Report Q2 2026 edition (retrieved 21 Nov 2026; read
  from Q1 2013 to Q1 2026). Figures are insurers' unaudited quarterly submissions, compiled and published by the NIC.
  Source and URL in `data/raw/quarterly/SOURCE.md`; SHA-256 in `data/raw/CHECKSUMS` (checked by the pipeline; check by
  hand with `cd data/raw && sha256sum -c CHECKSUMS`). Insurer-level files derived from it are in `data/processed/`.

## Documentation

- `docs/methodology_decisions.md` — changes from the defence version, with reasons and sign-off status
- `docs/data_issues.md` — every data problem found and how it is handled
- `docs/codebook.md` — all panel variables (Tier 1 panel, returns panel, v2 analysis panel)
- `outputs/tables/appendix_*.csv` — the thesis appendix tables (v2), each with a one-line note on sample and inference
- `outputs/tables/v1/`, `outputs/figures/v1/` — frozen v1 outputs; git tag `v1-methodology` for the pre-D14 originals
- `CLAUDE.md` — project context and rules for Claude Code

## Status and open items

- [ ] Authors and supervisor agree the methodology changes (D1–D22; v2 = D14–D22)
- [ ] Run and check the R script (System GMM)
- [ ] AR(1)/AR(2) tests differ between pydynpd and R `pgmm`: check against a third implementation (e.g. Stata `xtabond2`)
- [ ] Verify CPI 2015–18 and 2021 against Ghana Statistical Service
- [ ] Verify methods citations (APA 7)

The supplementary facultative-reinsurance analysis (step 6) is excluded from the public pipeline because its source,
a reinsurer's production report, is confidential; the step skips when the file is absent.

## Sources

National Insurance Commission. *Annual report on the insurance industry* (2019, 2020, 2022, 2024 eds.). NIC, Accra.
Insurance Act, 2021 (Act 1061). Republic of Ghana.

## Pre-specified analysis plans

Three analyses follow a pre-specified analysis plan, written in the experiment's README and committed before any
analysis was run. The plans were committed and pushed before estimation (1 November 2026 and 21 November 2026); they
were not lodged with an independent registry. The original working repository had different commit hashes from this
published history (it was replayed to remove confidential files); the plan text is byte-identical in both, so both
hashes are listed. The experiment READMEs keep their original wording ("pre-registered") because the plan sections
are frozen; a dated note below each plan records the change of term.

| Analysis | Plan commit (date, UTC) | Results commit | Deviations |
|---|---|---|---|
| Akotey et al. (2023) replication (`experiments/akotey_replication/`) | `27f0cb3` (= `2c0df93` in the working repository), 1 Nov 2026 11:57 | `184de4e`, 2 Nov 2026 | 1: the balanced subsample was redefined because MSGR cannot exist in 2015 (README section 4). Bootstrap p-values later updated for D14 and its addendum; verdicts unchanged |
| Early warning, Experiments 1-2 (`experiments/early_warning/`) | `00a2c89` (= `98b4e34`), 1 Nov 2026 09:06 | `4595f99`, 1 Nov 2026 | 2: Exp 2 ignores the Q2 2022 expense-ratio column (a copy of the claims ratio); Exp 1 bootstrap reimplemented with identical draws (README section 4) |
| Early warning, v2 additions 4a-4e | `3eef056`, 21 Nov 2026 19:11 (pushed before analysis) | `06927a4`, 21 Nov 2026 19:18 | None (README section 6) |
