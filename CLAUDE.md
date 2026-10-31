# CLAUDE.md — context for Claude Code

## Project
MSc Actuarial Science thesis (University of Ghana), Bismark Kantanka Sarfo & Dan Gyinaye Poku,
supervisor Dr. Perpetual Andam Boiquaye. Question: does insurer-level premium growth (year t-1)
predict underwriting performance (loss, expense, combined ratio, year t) in Ghana's non-life sector?

## Pipeline
`python run_all.py` runs src/01..08 in order (resume with `--from N`). R/twfe_and_system_gmm.R runs after.
src/00_fetch_macro.py is run by hand only, to refresh the WDI CPI snapshot in data/raw/macro/.
- 01 verifies SHA-256 of data/raw/nic_text/*.txt, parses table blocks
- 02 maps blocks to variables by (report, header line); validated against src/expected_blocks.json
- 03 builds data/processed/panel_master.csv (29 insurers x 2015-2024, unbalanced)
- 04 models + diagnostics -> outputs/tables
- 05 figures -> outputs/figures
- 06 facultative appendix (skips if confidential file absent)
- 07 validation: 29 checks incl. pinned headline coefficients. Must pass before results are used.
- 08 System GMM robustness (pydynpd); runs after 07, results not pinned

## Rules
- NEVER edit data/raw/. The NIC text files are the exact extractions the line map was built on.
- Do not "fix" the line numbers in 02's MAP without regenerating and re-checking expected_blocks.json by hand.
- If a change moves a pinned result in 07, do not update the pin until the authors understand why.
- Main estimation 2016-2022 only (IFRS 4). 2023-24 are IFRS 17: descriptive / out-of-sample only.
- 2024 "GWP" column is Insurance Revenue: never compute 2024 growth from it.
- Headline inference = insurer-clustered SEs + wild cluster bootstrap. Driscoll-Kraay is unreliable at T=7.
- Never commit data/raw/production/ (client names).

## Key decisions (see docs/methodology_decisions.md)
ln(lagged GWP) replaces ln(assets) (assets not published per insurer); net premium-to-equity leverage control;
growth and market-share growth in separate models; start-up years excluded + 1/99 winsorising (raw as sensitivity);
CR constructed as LR+ER; MID tested as a post-2020 slope change (insurer-by-class data not public);
clustered-SE correction counts year effects, not insurer effects (D12: year effects entered as explicit
dummies in 04's fe(), since linearmodels ignores count_effects=False with time_effects=True).

## Open items
AR tests differ between pydynpd and R pgmm (needs a third reference, e.g. Stata xtabond2); verify methods citations;
identify the reinsurer behind the production file.
