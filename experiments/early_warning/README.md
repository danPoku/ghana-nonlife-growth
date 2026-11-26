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

Note (25 Nov 2026): described in the thesis as a pre-specified analysis plan.

## 4. Deviations and results (added AFTER analysis; sections 1-3 unchanged since commit 98b4e34)

### Deviations from the pre-registration
- **Exp 2, Q2 2022 sheet.** Its expense-ratio column is an exact copy of its claims-ratio column
  (25 of 25 rows), so YTD CR would be 2 x claims ratio. Rule added: a sheet where >= 90% of rows have
  expense ratio = claims ratio gets its ratios set to missing (only Q2 2022 qualifies). Nothing is
  recomputed from amounts. Effect: the primary Exp 2 sample covers t = 2015-2021, not 2015-2022.
- **Exp 1, bootstrap implementation.** The first run (pandas concat per resample) was stopped for speed
  and replaced by index arrays. Same seed, same draw order, same rows: results are identical by
  construction.

### Exp 1 (primary target CR(t) > 110): MODERATE
- Test sample 52 insurer-years (26 insurers), 17 red. Red share: training 60%, test 33%.
- Continuous CR(t-1) AUC 0.803 [0.619, 0.940]. Composite (CR, ER, roa, inv_yield at t-1) 0.785
  [0.595, 0.935]. Difference -0.018, paired 95% CI [-0.078, +0.057]: **the CI includes 0**.
- Thresholds not stable: the CR(t-1) cut-off from the 2016-2017 window (129.0, n = 46) is 12 pp above
  the 2016-2020 cut-off (117.0); all later windows are within 4.5 pp.
- Binary rule CR(t-1) > 110 on the test years: flags 31%, hit rate 75%, catches 71% of red cases.
- Lagged premium growth: test AUC 0.524 [0.336, 0.703], no warning value; it was not selected for
  the composite.

### Exp 2 (primary target audited CR(t) > 110): STRONG, with a caveat
- Q2 YTD CR AUC 0.815 [0.740, 0.882], n 167 (100 red), 2015-2021. Q3 (reference) 0.860.
- But Q2 YTD CR minus audited CR(t-1), paired rows (n 146): -0.073, 95% CI [-0.142, -0.003].
  **The CI excludes 0: on the same rows, last year's audited CR ranks insurers better than the Q2
  return does.**

## 5. v2 additions (Part 4 of the methodology revision): pre-registration, 21 Nov 2026

**Written BEFORE any analysis in this section was run.** Data inspected beforehand: column names and non-missing
counts only. Rows available: training t = 2016-2020, 121 insurer-years with the target, 107 also with CR(t-1), both Q2
returns passing the checks in 4b and Q4(t-1) concordance; test t = 2021-2022, 52 and 48. No red-zone rate, outcome
value or AUC from the v2 data was looked at. Results already known before writing are those in section 4 (v1 data).
Sections 1-4 are unchanged.

The NIC quarterly returns workbook is an NIC product (source confirmed); its figures are insurers' unaudited quarterly
submissions. Insurer-level outputs stay in `outputs/confidential/` (git-ignored).

### 5.1 Common to 4a-4e
- **Data:** the v2 analysis panel (`data/processed/confidential/panel_v2.csv`) and quarterly returns panel
  (`returns_quarterly.csv`), as built by pipeline steps 12 and 03 at the commit that adds this section.
- **Target (primary):** red(t) = 1 if CR(t) > 110, where CR is the audited Tier 1 combined ratio with the two v2
  corrections: 2015-16 ER := CR_nic - LR (data_issues A16, A19) and 2020 ER replaced by the returns-based ER where the
  published value omits commission (A20) (`CR_corr2020`). The test-year targets (2021-2022) are untouched by either
  correction, so the decision rule is applied to purely audited outcomes.
- **Target (sensitivity, reported, not decisive):** `CR_t1`, audited with only the 2015-16 correction, so no
  returns-derived value enters the target anywhere.
- **Rows:** t = 2016-2022; neither t nor t-1 a start-up year. Training t = 2016-2020, test t = 2021-2022; nothing is
  fitted or chosen on test years. IFRS 4 only (2023 audited values are IFRS 17).
- **CR(t-1)** is on the same basis as the target.
- **Bootstrap:** every interval resamples INSURERS with replacement (all rows of a drawn insurer kept): 1,999 resamples,
  seed 1, percentile 95% CI; a resample with only one class is redrawn and the number redrawn is reported; paired
  differences use the same resamples for both scores. (This was already the rule for every interval in sections 3-4.)
- **AUC:** Mann-Whitney, ties counted as 0.5.

### 4a. Paired AUC difference: CR(t-1) vs premium growth
- Score A = CR(t-1). Score B = premium growth g(t-1), v2 single measure, direction fixed by its training AUC (as in
  Exp 1). Test rows complete on both. Report AUC(A), AUC(B) and AUC(A) - AUC(B) with the paired CI.
- Growth's AUC is reported under BOTH growth measures on the same test rows: the v2 single measure (Score B, which the
  reading below uses) and the v1 measure (`g_v1`, lagged), each with its CI and its paired difference from AUC(A).
- Reading: "growth carries less warning value than CR(t-1)" only if the paired CI lies wholly above 0; otherwise "no
  detectable difference".
- Also reported on the Exp 1 (v1) data, published CR and v1 growth, for direct comparison with section 4.

### 4b. Quarterly indicators (same quarter, year on year)
- Q2 YTD CR(t): component-based claims ratio + expense ratio on the NEP + RIC basis from the Q2 return of year t.
- **dQ2CR(t)** = Q2 YTD CR(t) - Q2 YTD CR(t-1). **gQ2(t)** = 100 x (Q2 YTD GWP(t) / Q2 YTD GWP(t-1) - 1).
- Never across the IFRS 17 boundary (t <= 2023; the test window ends in 2022).
- **Quality checks; BOTH Q2 returns (t and t-1) must pass:** (i) the row has figures; (ii) it is not a copy of the
  insurer's Q1 return; (iii) NEP + RIC, claims, management and commission are present, so the CR is computable;
  (iv) Q2 YTD GWP > 0 and not below Q1 YTD GWP. In addition (v) the Q4 return of t-1 passes concordance with audited
  GWP (known by Q2 of year t). No check uses information from after Q2 of year t. Merger years (t or t-1) are
  excluded for gQ2.
- **Expected directions, fixed here:** dQ2CR higher = riskier (a worsening Q2 combined ratio against the same quarter
  a year earlier); its AUC is computed in that direction, with no training-based reorientation. gQ2 has **no
  pre-specified direction** (two-sided, consistent with RQ2): its AUC is computed with higher growth = riskier and read
  two-sidedly (CI wholly above 0.5: faster growth signals higher risk; wholly below 0.5: lower risk; otherwise no
  detectable signal). For its flag metrics only, the direction is set by the training AUC.
- Report test AUC with CI for dQ2CR and gQ2, and flag metrics at the training Youden cut-off.

### 4c. Incremental test (decision rule fixed here)
- Model A: logistic on CR(t-1). Model B: logistic on CR(t-1) + dQ2CR(t). Same estimator as the Exp 1 composite
  (inputs winsorised at the training 1st/99th percentiles, standardised with training mean and SD, L2 penalty lambda = 1
  on the slopes, intercept free, no tuning). Fitted on training rows, scored on test rows.
- **Comparison rows:** the rows meeting model B's data requirements (complete on CR(t-1) and dQ2CR, both Q2 returns
  passing 4b), in training and in test. Model A is fitted and its test AUC computed on that SAME restricted set; it is
  not Experiment 1's full-set AUC of CR(t-1).
- **Rule:** dQ2CR **ADDS INFORMATION** only if test AUC(B) - AUC(A) >= 0.03 AND the paired 95% CI excludes 0 (lower
  bound > 0). Otherwise **DOES NOT ADD INFORMATION**. Point estimate and CI are reported either way.
- Secondary, not decisive: Model C = Model B + gQ2(t); all models on the sensitivity target.
- About 48 test rows: power is low, and a "does not add" result is not evidence of no effect.

### 4d. Exploratory: non-submission
- Indicator: quarters of year t-1 without figures (0-4), higher = riskier (fixed here). Test AUC with CI; flag
  metrics at ">= 1 quarter missing". No decision rule.

### 4e. Recalibration demonstration under IFRS 17 (descriptive, not a test)
- Data: (i) published IFRS 17 CR for 2023 and 2024 (NIC 2024 Annual Report); (ii) workbook Q4 IFRS 17 CR (printed
  claims ratio + expense ratio, units detected) for 2024 and 2025, rows with figures and not a copy-forward; for 2024
  the Q4 Insurance Revenue must be within max(5%, GHS 0.5m) of the NIC 2024 Insurance Revenue (2025 cannot be checked).
- Show: CR distribution (median, p75, share > 110) by year on each basis next to IFRS 4 2021-2022; the share flagged
  by the IFRS 4 rules (CR(t-1) > 110 and the 2016-2020 Youden cut-off) applied to IFRS 17 CR; the Youden cut-off and
  AUC re-estimated on the IFRS 17 pairs (2023 -> 2024 published; 2024 -> 2025 workbook), with insurer-bootstrap CIs.
  No verdict.

### 5.2 Outputs and deviations
- Script `exp3_v2_additions.py`, written after this section is committed. Aggregate outputs:
  `outputs/exp3_results.csv`, `outputs/exp3_ifrs17.csv`; insurer-level in `outputs/confidential/`.
- Anything changed during analysis is recorded, with its reason, in a section 6 "Deviations and results (v2
  additions)"; sections 1-5 stay unchanged after the commit that section 6 names.

Note (25 Nov 2026): described in the thesis as a pre-specified analysis plan.

## 6. Deviations and results, v2 additions (added AFTER analysis; sections 1-5 unchanged since commit 3eef056)

Script `exp3_v2_additions.py`; aggregate outputs `outputs/exp3_results.csv`, `outputs/exp3_ifrs17.csv`; insurer-level
scores in `outputs/confidential/`. Test rows t = 2021-2022: 52 insurer-years (26 insurers, 17 red); 48 (25 insurers,
15 red) meet the quarterly requirements. Consistency check: on the Exp 1 data the CR(t-1) AUC is 0.803 [0.619, 0.940],
as in section 4.

### Deviations from section 5
**There were no deviations from section 5.** (For the record: in 4a, both growth measures are scored on the rows complete on
CR(t-1) and on both growth measures, as section 5 requires; these are the same 52 rows as those complete on the v2 measure alone.)

### 4a. CR(t-1) vs premium growth (paired)
| Target | AUC CR(t-1) | AUC growth v2 | AUC growth v1 | CR(t-1) - growth v2 | Reading |
|---|---|---|---|---|---|
| Primary (CR_corr2020) | 0.738 [0.551, 0.878] | 0.519 [0.335, 0.699] | 0.524 [0.336, 0.703] | +0.218 [-0.028, +0.442] | **no detectable difference** (CI includes 0) |
| Sensitivity (CR_t1) | 0.803 [0.619, 0.940] | 0.519 | 0.524 | +0.284 [+0.050, +0.493] | growth carries less warning value than CR(t-1) |
| Exp 1 v1 data (published CR) | 0.803 [0.619, 0.940] | - | 0.524 [0.336, 0.703] | +0.280 [+0.055, +0.488] | growth carries less warning value than CR(t-1) |

Growth has no warning value under either measure (AUC about 0.52, direction from training: lower growth = riskier).
Whether CR(t-1) is detectably better depends on the 2020 correction: the corrected 2020 CR, used as CR(t-1) for the
2021 test rows, ranks insurers less well (AUC 0.738 against 0.803), and the paired CI then just includes 0.

### 4b. Quarterly indicators (test rows passing all checks, n = 48, 15 red)
- dQ2CR (higher = riskier, pre-specified): AUC 0.503 [0.319, 0.676]. No signal.
- gQ2 (two-sided): AUC 0.503 [0.326, 0.696] with higher growth = riskier. **No detectable signal** in either direction.

### 4c. Incremental test (pre-registered rule)
| Target | A: CR(t-1) on B rows | B: CR(t-1) + dQ2CR | B - A | Rule |
|---|---|---|---|---|
| Primary | 0.751 [0.558, 0.892] | 0.749 [0.560, 0.889] | -0.001 [-0.016, +0.012] | **DOES NOT ADD INFORMATION** |
| Sensitivity (not decisive) | 0.821 [0.654, 0.957] | 0.826 [0.661, 0.958] | +0.005 [-0.006, +0.018] | does not add |

Secondary model C (+ gQ2), not decisive: C - A = -0.013 [-0.058, +0.031] (primary). Training rows 107 (B), 105 (C).
With 48 test rows the CI is narrow around 0 only because B and A rank almost identically; the result says the Q2
change adds nothing measurable here, not that it cannot.

### 4d. Non-submission in t-1 (exploratory)
AUC 0.471 [0.424, 0.500]. Only 2 of 52 test rows had any quarter without figures in t-1 (neither red): no signal, and
too few cases to judge.

### 4e. IFRS 17 recalibration (descriptive)
| Basis | Year | n | Median CR | p75 | Share > 110 | Share above the IFRS 4 cut-off (118) |
|---|---|---|---|---|---|---|
| IFRS 4 audited (corrected) | 2021 | 26 | 98.5 | 109.5 | 27% | 12% |
| IFRS 4 audited (corrected) | 2022 | 26 | 104.0 | 124.8 | 38% | 35% |
| IFRS 17 published | 2023 | 26 | 99.0 | 104.8 | 12% | 8% |
| IFRS 17 published | 2024 | 25 | 95.0 | 111.0 | 28% | 12% |
| IFRS 17 workbook Q4 | 2024 | 20 | 93.8 | 103.6 | 15% | 5% |
| IFRS 17 workbook Q4 | 2025 | 24 | 91.9 | 105.1 | 25% | 17% |

Recalibrated on IFRS 17 pairs: published 2023 -> 2024 (n 25, 7 red): AUC 0.68 [0.39, 0.94], Youden cut-off 103.5
(bootstrap range 86.5 to 2,090: unstable); workbook 2024 -> 2025 (n 19, 4 red; 24 one-class resamples redrawn):
AUC 0.93 [0.78, 1.00], cut-off 102.7 [98.9, 131.3]. Under IFRS 17 the CR distribution sits lower, the IFRS 4 cut-off
(118) flags few insurers, and both re-estimated cut-offs fall near 103 (bootstrap ranges 86.5 to 2,090.5 and 98.9 to 131.3).
**IFRS 17 cut-off: recalibration needed; current evidence too thin to set a value.** Samples are very small; no verdict.
