# Early-warning experiment (exploratory, pre-registered)

**Status: EXPLORATORY.** Not part of the thesis pipeline (`run_all.py`, `src/`, `07_validate.py`).
It may or may not go into the paper. Pre-registered 1 Nov 2026, before any analysis was run and
before any red-zone rate or outcome value was looked at. The only data inspected beforehand were
column names and non-missing counts in `data/processed/panel_master.csv`, and the sheet names and
column headers of the quarterly returns workbook.

Scripts: `exp1_annual.py`, `exp2_quarterly.py`. Aggregate outputs in `outputs/`; insurer-level
outputs in `outputs/confidential/` (git-ignored; Experiment 2 uses the CONFIDENTIAL, unaudited NIC
quarterly returns workbook, data_issues A15).

## 1. Pre-registration (as specified by the authors, verbatim)

- Target ("red zone"): insurer's combined ratio > 110% in year t
  Sensitivity: CR > 100% in both t and t-1
- Experiment 1 (annual, audited data from data/processed/panel_master.csv):
  indicators measured at t-1: CR, ER, LR, inv_yield, roa, ln_gwp, and g (premium growth,
  included to test whether it adds warning value). Start-up years excluded.
  Training years t = 2016-2020; test years t = 2021-2022. IFRS 4 only (no 2023+).
  Compare: (a) simple rule "CR(t-1) > 110%"; (b) single-indicator thresholds chosen on
  training data by Youden's index; (c) logistic composite with at most 4 indicators,
  chosen on training data only.
  Report on the TEST years: AUC with bootstrap 95% CI (clustered by insurer), share
  flagged, hit rate, share of red cases caught.
  Stability: expanding-window recalibration of thresholds by year, with bootstrap CIs.
- Experiment 2 (quarterly nowcast, confidential workbook in data/raw/quarterly/):
  does year-to-date CR at Q2 (and Q3, for reference) predict full-year CR > 110%?
  Use all years where Q2 and Q4 exist for the insurer. Report AUC with bootstrap CI.
- Decision criteria, written before results:
  Exp 1 STRONG: composite test AUC exceeds simple rule by >= 0.05 AND thresholds stable
    (expanding-window cut-offs within +/- 10 points) -> full RQ4 section
  Exp 1 MODERATE: simple rule performs well (test AUC >= 0.70), composite adds < 0.05
    -> one paragraph + table
  Exp 1 WEAK: test AUC < 0.70 for all -> limitations / future research
  Exp 2 STRONG: Q2 AUC >= 0.80 -> practical recommendation; Q3 is reference only
- Note: test set is about 50 insurer-years; all conclusions are provisional.

## 2. Amendments agreed before any analysis (these supersede section 1 where they differ)

**Changed BEFORE any analysis was run.** The Experiment 1 criteria above compared the
composite with the binary rule "CR(t-1) > 110%". A binary rule's AUC equals (TPR + TNR) / 2,
which is mechanically lower than the AUC of any continuous score, so "composite beats the rule by
>= 0.05" would be partly an artefact. The primary comparison is therefore the composite vs the
**continuous** CR(t-1):

- **Exp 1 STRONG:** composite test AUC exceeds continuous CR(t-1) test AUC by >= 0.05 AND
  thresholds stable (expanding-window cut-offs within +/- 10 points) -> full RQ4 section
- **Exp 1 MODERATE:** continuous CR(t-1) test AUC >= 0.70, composite adds < 0.05
  -> one paragraph + table
- **Exp 1 WEAK:** all test AUCs < 0.70 -> limitations / future research
- The binary CR(t-1) > 110% rule is still reported for share flagged, hit rate and share caught.

Further amendments:

- Rules are applied in order STRONG -> MODERATE -> WEAK. A result that meets none of them is
  reported as **"MIXED: authors decide"**. Exp 2 with Q2 AUC < 0.80 is reported as **"NOT STRONG"**.
- Verdicts use point estimates. Every verdict is reported with the paired bootstrap CI for the
  relevant AUC difference, and if that CI includes 0 the report says so explicitly.
- **Exp 2 primary target: AUDITED panel CR > 110% (t = 2015-2022).** Workbook Q4 CR > 110% is the
  secondary target (all years, with 2024-25 separately). Reason: if Q2 and the outcome both come
  from the same unaudited returns, shared reporting errors would inflate the AUC.
- Composite inputs are winsorised at the TRAINING set's 1st / 99th percentiles, and the same bounds
  are applied to the test set. Single-indicator AUCs use raw values.

## 3. Operational specification (fixed before any analysis)

### Common
- CR = LR + ER as constructed in the panel (D5), in percent, unwinsorised. Red zone: CR(t) > 110.
  Sensitivity: CR(t) > 100 and CR(t-1) > 100.
- Bootstrap: 1,999 resamples of insurers with replacement (all rows of a drawn insurer kept),
  seed 1, percentile 95% CI. A resample with no red case or no non-red case is skipped and redrawn;
  the number skipped is reported. Paired CIs for AUC differences use the same resamples for both
  scores.
- Metrics at a cut-off (flag if value is beyond the cut-off in the risk direction):
  share flagged = flagged / n; hit rate = red among flagged / flagged; share caught = red among
  flagged / red.
- Ties in AUC are counted as 0.5 (Mann-Whitney).

### Experiment 1 (annual, `exp1_annual.py`)
- Rows: insurer-years with t in 2016-2022, CR(t) present, and neither t nor t-1 a start-up year
  (`startup` flag). No 2023+ rows.
- Indicators at t-1: CR, ER, LR, inv_yield, roa, ln_gwp, g, raw. Lags are taken on the full insurer x
  year grid, so a gap year gives a missing lag (asserted equal to the panel's own `_L1` columns
  where those exist). g across a merger is already missing (D13).
- Training: t = 2016-2020. Test: t = 2021-2022. Nothing is fitted or chosen on the test years.
- (b) Single indicators: risk direction set by training AUC (if < 0.5 the indicator is negated);
  cut-off maximises Youden's J (TPR - FPR) on the training rows. Test AUC on the continuous,
  direction-adjusted indicator; test flag metrics at the training cut-off. Each indicator uses all
  rows where it is present.
- (c) Composite: indicators ranked by direction-adjusted training AUC; take the top 4. If that would
  include all three of CR, LR and ER (exact collinearity, CR = LR + ER), the lowest-ranked of the
  three is skipped and the next indicator taken. Inputs winsorised at the training 1st / 99th
  percentiles (same bounds on test), standardised with training mean and SD. Logistic regression
  with a fixed L2 penalty, lambda = 1 on the standardised slopes (intercept unpenalised), so the
  fit exists under separation; no tuning. Flag cut-off: Youden's J on training predicted
  probabilities.
- Primary comparison sample: test rows complete on CR(t-1) and all composite inputs; continuous
  CR(t-1), the binary rule, and the composite are all scored on these same rows.
- (a) Binary rule CR(t-1) > 110: share flagged, hit rate, share caught (and its AUC,
  (TPR + TNR) / 2, for information only).
- "All test AUCs" (WEAK criterion) = continuous CR(t-1), every single indicator (b), and the composite.
- Stability: thresholds refitted by Youden's J on expanding training windows t = 2016..E,
  E = 2017, ..., 2022 (windows ending 2021-22 overlap the test years; they assess stability only,
  not performance), each with a 999-resample insurer bootstrap CI of the cut-off. **Stable** = every
  refitted cut-off of CR(t-1), and of any of LR, ER, CR used in the composite, lies within +/- 10
  percentage points of its 2016-2020 cut-off. Cut-offs of the other indicators are reported only.
- Sensitivity target: all of the above rerun; the decision criteria apply to the primary target only.
- Outputs: `outputs/exp1_results.csv` (test metrics by method), `outputs/exp1_thresholds.csv`
  (training directions, AUCs, cut-offs, composite coefficients), `outputs/exp1_stability.csv`.

### Experiment 2 (quarterly nowcast, `exp2_quarterly.py`)
- If the workbook is absent: print a message and exit 0.
- Q2, Q3, Q4 sheets 2013-2025, read with the header, alias and exclusion rules of
  `src/09_total_assets.py` (copied, since `src/` is not modified) and `names.canon`. Unmapped names
  or several rows per insurer-year: STOP and show them before any mapping is added.
- Units: per sheet, if the median of the claims-ratio column is < 3 the sheet is in fractions and
  its ratio columns are multiplied by 100. The detected unit and median per sheet are printed and
  saved. YTD check: median Q2 GWP / Q4 GWP per year reported (about 0.5 if sheets are year-to-date).
- YTD CR = workbook claims ratio + expense ratio (percent). A sheet's own combined-ratio column, if
  any, is used only as a cross-check.
- Concordance: insurer-years whose Q4 GWP fails step 09's tolerance against audited panel GWP
  (2015-2019: 5%; 2020-2023: max(5%, GHS 0.5m)) are dropped. 2013-14 (no audited GWP) and 2024-25
  (panel "GWP" is Insurance Revenue) are not checked. Q4-identical-to-Q3 copy-forward flagged,
  report-only. Start-up years (panel flag) excluded.
- Primary target: audited panel CR(t) > 110, t = 2015-2022, rows with Q2 present (and Q4 present
  for the concordance check).
- Secondary target: workbook Q4 CR > 110; 2013-2023 and 2024-2025 analysed separately (IFRS 17
  columns differ in definition from 2024).
- Score: Q2 YTD CR (higher = riskier, no fitting). Q3 YTD CR for reference. AUC with insurer-
  clustered bootstrap CI; at a cut-off of 110: share flagged, hit rate, share caught.
- Paired AUC difference for the verdict: Q2 YTD CR minus audited CR(t-1), on rows with both (does
  the Q2 return add over what last year's audited accounts already show?). Q3 - Q2 for reference.
- Outputs: `outputs/exp2_results.csv` (aggregate), `outputs/exp2_units.csv` (per-sheet units);
  insurer-level data in `outputs/confidential/`.
