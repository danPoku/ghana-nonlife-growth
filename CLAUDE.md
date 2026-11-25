# CLAUDE.md — context for Claude Code

## Project
MSc Actuarial Science thesis (University of Ghana), Bismark Kantanka Sarfo & Dan Gyinaye Poku,
supervisor Dr. Perpetual Andam Boiquaye. Question: does insurer-level premium growth (year t-1)
predict underwriting performance (loss, expense, combined ratio, year t) in Ghana's non-life sector?

## Pipeline
`python run_all.py` runs 01, 02, 12, 03, 04, ..., 11, 13, 14 (resume with `--from N`, N = script number). R/twfe_and_system_gmm.R runs after.
src/00_fetch_macro.py is run by hand only, to refresh the WDI CPI snapshot in data/raw/macro/.
The NIC quarterly returns workbook (data/raw/quarterly/; published by the NIC, insurers' unaudited quarterly submissions) is
TRACKED since the public release (25 Nov 2026): edition Q2 2026, read to Q1 2026 (config.QUARTERLY_LAST), SHA-256 in
data/raw/CHECKSUMS (all raw inputs; read by config.py). The pipeline always runs the full v1 + v2 path; only step 06 skips.
- 01 verifies SHA-256 of data/raw/nic_text/*.txt (data/raw/CHECKSUMS), parses table blocks
- 02 maps blocks to variables by (report, header line); validated against src/expected_blocks.json
- 12 returns panel (Tier 2) from the NIC quarterly returns workbook (opened via returns_io.open_workbook, SHA-256 checked)
  -> data/processed/returns_panel.csv, returns_quarterly.csv; aggregates outputs/tables/returns_*.csv, seasonality.csv. Runs before 03.
- 03 builds data/processed/panel_master.csv (29 insurers x 2015-2024, unbalanced; Tier 1 only, public); Tier 1 rules in
  src/tier1.py. Also data/processed/panel_v2.csv (v2 analysis panel: component-based
  outcomes, single growth measure, assets, 2020 ER variant)
- 04 models + diagnostics -> outputs/tables (v1 path: regressions.csv, pinned); v2 main models via src/models_v2.py ->
  main_models_v2.csv, rq3_tests_v2.csv, cre_mundlak_v2.csv, industry_trends_v2.csv, v1_v2_bridge*.csv, growth_quartiles_v2.csv,
  exits.csv, appendix_robustness.csv (ownership changes: RENAMES in src/config.py); also the gross-basis robustness (LR_g/ER_g/CR_g = ratio x RET/100,
  data_issues A16): robust_gross_basis.csv, industry_trends_gross.csv, er_ret_correlation.csv (not pinned)
- 05 thesis Figures 1-7 -> outputs/figures/Figure_N_*.png (thesis numbering; no footnotes, the captions carry the notes);
  Figure 8 from step 10. v1 figures frozen in outputs/figures/v1/ (not redrawn)
- 06 facultative appendix (skips if confidential file absent)
- 07 validation: 48 checks incl. two pinned sets, "v1 (public, Tier 1 only)" and "v2 (thesis, requires NIC workbook)"
  Must pass before results are used.
  Estimation sample: 176 insurer-years, 2016-2022 (177 before the D13 merger rule).
- 08 System GMM robustness (pydynpd); runs after 07, results not pinned; v1 -> system_gmm*.csv, v2 -> system_gmm*_v2.csv
- 09 total assets as size control from the NIC quarterly returns workbook; not pinned
- 10 leave-one-insurer-out for M1 (growth and size); not pinned; v1 and v2 (robust_leave_one_out*_v2.csv, Figure_8_leave_one_out.png)
- 11 NIC printed CR vs LR+ER mismatch analysis (2015-16) -> cr_mismatch_analysis.csv; counts pinned in 07
- 13 Hansen (1999) threshold test on g_L1 (v2): simulation validation -> threshold_simulation.csv; real data only when
  RUN_REAL_DATA = True (approved; threshold_v2.csv). Wild bootstrap under the null (departure from Hansen, D20)
- 14 assembles the thesis appendix tables outputs/tables/appendix_*.csv (8 files, each with a one-line `note`) from aggregate outputs;
  runs last and checks its own output
Shared code: src/models.py (fe with the D12 SE convention, within = exact two-way within-transformation, wcb on it (D14), twdm), src/names.py (canonical insurer IDs),
src/tier1.py (audited Tier 1 table, steps 03 and 12) and src/returns_io.py (workbook reading rules, steps 09 and 12).
All two-way FE models must use models.fe; never redefine it in a step.

## Rules
- NEVER edit data/raw/. The NIC text files are the exact extractions the line map was built on.
- Do not "fix" the line numbers in 02's MAP without regenerating and re-checking expected_blocks.json by hand.
- If a change moves a pinned result in 07, do not update the pin until the authors understand why.
- Main estimation 2016-2022 only (IFRS 4). 2023-24 are IFRS 17: descriptive / out-of-sample only.
- 2024 "GWP" column is Insurance Revenue: never compute 2024 growth from it.
- Headline inference = insurer-clustered SEs + wild cluster bootstrap. Driscoll-Kraay is unreliable at T=7.
- Never commit data/raw/production/ (client names).
- Never commit foreign_cedants.txt or anything derived from the production file (data/processed/fac_*, outputs/tables/fac_*).
  Before every commit: git status --porcelain and git diff --cached --name-only must show no path matching production, fac_, cedant.
- The NIC quarterly returns workbook IS tracked (public NIC publication): never replace it without a cell-by-cell edition
  comparison (data_issues A17) and an updated data/raw/CHECKSUMS and data/raw/quarterly/SOURCE.md.
- Growth across a merger is missing (D13): add new mergers to MERGERS in src/config.py, never hard-code them.

## Key decisions (see docs/methodology_decisions.md)
v2 (thesis): D15 two data tiers, component-based outcomes on the NEP + RIC basis (2015-16 and 2020 Tier 1 corrections as sensitivities);
D16 single exact-GWP growth measure; D17 ln(total assets) as size; D18 two-way Mundlak (within vs between); D19 year-specific MID
slopes with pre-trend test; D20 Hansen threshold (wild bootstrap); D21 quarterly returns: no incremental early-warning value.
v1 (public, superseded):
ln(lagged GWP) replaces ln(assets) (assets not published per insurer; workbook assets used only as a robustness check, step 09); net premium-to-equity leverage control;
growth and market-share growth in separate models; start-up years excluded + 1/99 winsorising (raw as sensitivity);
CR constructed as LR+ER; MID tested as a post-2020 slope change (insurer-by-class data not public);
clustered-SE correction counts year effects, not insurer effects (D12: year effects entered as explicit
dummies in models.fe(), since linearmodels ignores count_effects=False with time_effects=True).

## Open items
AR tests differ between pydynpd and R pgmm (needs a third reference, e.g. Stata xtabond2); verify methods citations;
identify the reinsurer behind the production file.
