# Methodology decisions (changes from the 19 Sept 2026 defence)

Status: **proposed**. Each needs author agreement and, where marked, supervisor sign-off.

| # | Defence version | Proposed | Reason | Sign-off? |
|---|---|---|---|---|
| D1 | Size control ln(total assets) | ln(GWP, t-1) in the main models; ln(total assets, t-1) from the NIC quarterly returns workbook (A15) as a robustness check (step 09) | Per-insurer assets not published (A10); the workbook (an NIC product, source confirmed 21 Nov 2026) holds insurers' unaudited quarterly submissions, so assets stayed out of the v1 main analysis **Superseded in v2 by D17 (assets as size).** | Yes |
| D2 | No leverage control | Net insurance risk ratio (NWP / equity), t-1 | Classic premium-to-surplus underwriting risk measure; published by NIC | Yes |
| D3 | Growth and market-share growth in one equation | Separate models (M1 vs M4) | With year FE, market-share growth ~ premium growth (within-corr 0.60; exact within-transformation, D14) | Yes |
| D4 | Winsorising in sensitivity only | Exclude start-up years + winsorise 1/99 in main; raw as sensitivity | Single start-up obs at 10,950% would dominate OLS (A11) | Yes |
| D5 | CR from NIC tables | CR = LR + ER | NIC CR inconsistent in 2015-16 (A6); makes CR coefficient = LR + ER coefficients | No |
| D6 | MID difference-in-differences (motor vs non-motor, insurer-class) | Post-2020 slope change: g(t-1) x Post2020, plus industry class descriptives | Insurer-class data not public (A13). Cannot separate MID from COVID; state this **Superseded in v2 by D19 (year-specific slopes).** | Yes |
| D7 | Clustered SEs | Clustered SEs + wild cluster bootstrap (Rademacher, 999 reps) | Only 29 clusters (28 with within-variation) | No |
| D8 | — | Driscoll-Kraay reported, not headline | Requires large T; T = 7 | No |
| D9 | "Net of market-wide growth" | Year FE do this; excess growth (g - year median) used for thresholds | Equivalent within TWFE; thresholds need a relative measure | No |
| D10 | System GMM as robustness | Kept (R pgmm + Python pydynpd step 8, collapsed instruments) + Anderson-Hsiao IV in Python. See D10 note below | Instrument proliferation risk with N = 29 | No |
| D11 | Report null without size | Report 95% CIs in +10pp-growth units and minimum detectable effects | A null must show what it rules out | No |
| D12 | Clustered-SE small-sample correction counted insurer and year effects (linearmodels default) | Count year effects but not insurer effects, which are nested within the insurer clusters (Stata xtreg / reghdfe convention; Cameron & Miller, 2015). Implemented with year effects as explicit dummies (linearmodels ignores `count_effects=False` when `time_effects=True`). See D12 note below | Counting nested effects over-inflates clustered SEs; aligns Python with R (plm) and Stata | No |
| D13 | Growth across mergers treated as ordinary growth | Growth across a merger is set to missing in the first year of the combined entity, rather than replaced by pro-forma growth, to keep unaudited data out of the main analysis. See D13 note below | RegencyNem 2016: +61.4% published, about +3.0% organic; the pro-forma base exists only in an unaudited workbook | No |
| D14 | Wild cluster bootstrap on closed-form two-way demeaned data (x - mean_i - mean_t + mean) | Exact within-transformation: y and every regressor partialled on insurer and year dummies by OLS, then the restricted Rademacher wild cluster bootstrap on those residuals. See D14 note below | The closed-form demeaning equals the two-way FE transformation only in a balanced panel (Wooldridge, 2021, Section 9.1); the estimation panel is unbalanced (1-7 years per insurer), so the old bootstrap tested a statistic that differed from the FE estimate, most for size | No |
| D15 | One data source (NIC annual reports); CR = LR + ER from the published ratios | Two tiers. Tier 1: audited NIC annual reports. Tier 2: the NIC quarterly returns workbook (an NIC product; insurers' unaudited quarterly submissions), used where its Q4 GWP passes concordance with audited GWP. PRIMARY outcomes = component-based ratios on the NEP + RIC basis (claims, management and commission over net earned premium + reinsurance commission income), Tier 1 where Q4 fails or is missing. Tier 1 variants with the 2015-16 ER correction (ER := CR_nic - LR) and the 2020 ER correction (commission restored) are sensitivities. See D15 note | The published ratios contain two errors the returns expose (2015-16 printed ER, A16/A19; 2020 ER omits commission, A20); the returns give components (gross ER, commission, management, true NEP) that the reports do not | Yes |
| D16 | Growth from GWP to 2019, NIC %-change table 2020-22 | Single growth measure: exact GWP growth in every year where available (audited exact GHS to 2019; returns GWP 2020-22 where concordance passes; NIC %-change table as flagged fallback and for 2015). See D16 note | One measure across years; the %-change table contradicts NIC's own GWP in places (A7) and 2020+ GWP is published in rounded GHS m (A4) | No |
| D17 | ln(GWP, t-1) as size (D1) | ln(total assets, t-1) from the returns (Q4, concordance-passing) as the size control; ln(GWP, t-1) in M1b. See D17 note, with the v1 -> v2 bridge | Defence specification restored now that the source is confirmed as NIC's; the v1 within-insurer size result rested on erroneous 2016 expense ratios | Yes |
| D18 | Classical Hausman test; FE only | Two-way Mundlak (correlated random effects) decomposition: within and between-type effects with clustered SEs; robust variable-addition test replaces the classical Hausman test. See D18 note | Separates "an insurer that grows / becomes larger" (within) from "faster-growing / larger insurers" (between); valid in unbalanced panels (Wooldridge, 2021, Theorem 3.1, Section 9.1) | No |
| D19 | MID as one post-2020 slope change (D6) | g(t-1) x year dummies for 2020, 2021, 2022 with joint and equality tests; pre-trend test on 2017-2019 relative to 2016. See D19 note | Heterogeneous timing (Wooldridge, 2021, Section 5.2); testable common trends (Section 7); 2020 (COVID) can be separated from 2021-22 | Yes |
| D20 | Convexity via quadratic and piecewise terms only | Adds a Hansen (1999) panel threshold test on g(t-1), with a wild bootstrap under the null (departure from Hansen's residual resampling, which needs a balanced, one-way panel). See D20 note | Lets the data choose the threshold; quadratic and piecewise terms impose its form | No |
| D21 | Quarterly returns as an early-warning signal ("informative", Exp 2) | Quarterly returns carry no incremental warning value over last year's CR; useful for validation and recalibration only. See D21 note | Pre-registered incremental test (3eef056): DOES NOT ADD INFORMATION | No |
| D22 | (none) | Cross-sectional dependence in the expense ratio (Pesaran CD p = 0.011, v2) recorded as a limitation; Driscoll-Kraay SEs reported in `appendix_diagnostics.csv` as an indicative check only. See D22 note | Insurer-clustered SEs do not allow for correlation across insurers within a year beyond the common year effects; Driscoll-Kraay does, but needs large T (T = 7, D8) | No |

## D1 note: size result across size measures (step 09) and leave-one-out (step 10), 31 Oct 2026
Size -> expense ratio is consistent in direction and magnitude across size measures (ln GWP, ln assets) and in 29 leave-one-out runs (about -9 to -15 per log unit), but its significance is moderate: p = 0.051 clustered / 0.032 bootstrap with ln(assets) (bootstrap p 0.075 after the D14 fix; 0.078 after the D14 addendum); it loses 5% significance without CORONATION or SERENE; the two size measures cannot be separated (within r = 0.88).

## D12 note: clustered-SE convention (changed 31 Oct 2026)
- **Effect.** Coefficients, Driscoll-Kraay SEs, wild-cluster-bootstrap p-values, `nobs` and `r2_within` are unchanged. Every insurer-clustered SE is multiplied by sqrt((N-k-G-(T-1)) / (N-k-(T-1))): 0.909 for the headline M1 models (sqrt(138/167)), and 0.890-0.911 across the sensitivity models.
- **Pins.** The four pinned SEs in 07_validate.py were updated: g_L1_w 0.0571 -> 0.0519 (LR), 0.0447 -> 0.0406 (ER), 0.0960 -> 0.0873 (CR); ER ln_gwp_L1 5.657 -> 5.1425.
- **Inference.** No growth coefficient changes significance at 5% or 10%. Size -> ER crosses 5% in two sensitivity models (M5 MID slope and raw incl. start-ups: p 0.06 -> 0.04). At 10%, lagged RET -> ER (0.13 -> 0.10) and size -> ER excl. 2020 (0.12 -> 0.08) cross. Minimum detectable effects fall about 9% (CR: 2.69 -> 2.44 pp per +10 pp growth).
- **R.** R/twfe_and_system_gmm.R Step 1 now uses `effect = "individual"` with `factor(year)`, so plm's HC1 counts the year dummies. R's clustered SEs then equal Python's to every printed digit. R's p-values use a t distribution and Python's a normal, so p differs slightly.

## D13 note: merger rule (added 31 Oct 2026)
- **Rule.** `MERGERS` in src/config.py lists each merger (insurer, first year of the combined entity, absorbed entity, source). In that year `g`, `g_excess`, `g_real`, `g_real_dec` and `d_ms` are missing and `g_source` = "not computed: merger year"; the `_L1` lags follow. The rule is applied before the year median for `g_excess` is taken. Entries: RegencyNem 2016 (NEM absorbed), SAHAM_SANLAM 2024 (Allianz absorbed; growth was already missing as 2024 is Insurance Revenue).
- **Why missing, not pro-forma.** RegencyNem's 2016 growth was +61.4% as published but about +3.0% against Regency + NEM combined. The NEM 2015 figure comes only from the NIC quarterly returns workbook, i.e. NEM's unaudited quarterly submission (data_issues A15), so it is kept out of the main analysis.
- **Effect.** Estimation sample 177 -> 176 (RegencyNem 2017 drops: its lagged growth is now missing). Winsorising bounds are recomputed on the 176 rows, which moves 4 clipped values per variable. Lagged growth -> LR / ER / CR: +0.0225 / +0.0303 / +0.0461 -> +0.0261 / +0.0324 / +0.0547 (WCB p 0.79 / 0.51 / 0.72 -> 0.75 / 0.48 / 0.67). No TWFE coefficient changes significance at 5%. M3 threshold (p75 of excess growth) 9.957 -> 9.926 pp. M4 sample 153 -> 152. Anderson-Hsiao n 121 -> 120, growth p-values essentially unchanged. System GMM n 144 -> 142; CR with GMM lags 2-4 moves from p = 0.57 to p = 0.083 (+0.196), so that variant is sensitive to a single insurer.
- **Pins** in 07_validate.py updated (see the comment there); 30 checks.

## D14 note: exact within-transformation in the wild cluster bootstrap (21 Nov 2026)
- **Problem.** `models.wcb` demeaned every variable as x - mean_i - mean_t + mean before bootstrapping. That equals the two-way fixed-effects (within) transformation only in a balanced panel (Wooldridge, 2021, Section 9.1). The estimation panel is unbalanced (29 insurers, 1-7 years each), so the bootstrap's original t-statistic was not the FE t-statistic. The gap was small for growth (CR, lagged growth: t 0.60 vs FE 0.62) but large for size (ER, M3 with RET, gross basis: 2.76 vs FE 1.30 in absolute value), which made size look more significant than it is.
- **Fix.** `models.within` partials y and every regressor on a full set of insurer dummies and year dummies by least squares (Frisch-Waugh-Lovell), which is exact in an unbalanced panel. The restricted wild cluster bootstrap (null imposed, Rademacher weights, one sign per insurer) then runs on those residuals. The t-statistic uses the models.fe clustered variance (D12), so the original t is exactly the FE t. A constant scale does not change the p-value. The weights are drawn in the same order and with the same seed as before, so every change below comes from the estimator, not from new random draws.
- **Validation.** New check in 07: the bootstrap's original t equals the models.fe t for all 12 M1 terms (4 regressors x LR, ER, CR), max difference about 1e-13 (tolerance 1e-8). The vectorised bootstrap was also checked against a slow per-replication loop: identical t and p.
- **What was re-run.** Every caller of `models.wcb`: step 04 (main models and the gross-basis table), step 09 (total assets), Akotey replication part B (`experiments/akotey_replication/timing_bridge.py`). Steps 10 and 11 and both early-warning scripts do not call `wcb`. Coefficients, SEs, clustered p-values and every other output are unchanged; only bootstrap p-values moved.
- **Quoted bootstrap p-values, before -> after:**

| Where quoted | Result | Before | After |
|---|---|---|---|
| Headline results; D13 note | Lagged growth -> CR, M1 (B = 999) | 0.67 | 0.64 |
| D13 note | Lagged growth -> LR, M1 | 0.75 | 0.68 |
| D13 note | Lagged growth -> ER, M1 | 0.48 | 0.51 |
| D1 note (step 09) | ln(assets) -> ER (172 rows) | 0.032 | 0.075 |
| Step 09 table | ln(GWP) -> ER, same 172 rows | 0.016 | 0.063 |
| A16 report (gross basis, M1, with RET) | ln(GWP) -> ER_g | 0.004 | 0.094 |
| A16 report (gross basis, M1, without RET) | ln(GWP) -> ER_g | 0.002 | 0.034 |
| Akotey README, part B (B = 1,999) | Same-year growth -> CR, B1 | 0.001 | 0.003 |
| Akotey README, part B | Lagged growth -> CR, B2 | 0.60 | 0.58 |
| Akotey README, part B | Same-year growth -> LR, B1 | 0.059 | 0.075 |
| Akotey README, part B | Same-year growth -> ER, B1 | 0.015 | 0.015 |
| Akotey README, part B (raw) | Same-year growth -> LR / ER, B1 | 0.038 / 0.021 | 0.058 / 0.016 |

  All 97 bootstrap p-values in the outputs, before and after: `docs/d14_wcb_before_after.csv`.
- **Inference.** No growth term changes significance at 5% or 10% in any thesis model (main M1-M5, gross basis, step 09). Eight p-values cross a threshold, all size terms but one: in the gross-basis models, size -> ER_g loses 5% significance in 5 of 6 fits (it keeps it only in M1 without RET, p 0.034); in step 09, size -> ER moves above 5% with either measure (ln GWP 0.063, ln assets 0.075); in Akotey B, raw same-year growth -> LR moves from 0.038 to 0.058. The headline size -> ER coefficient (M1, -11.4, clustered p 0.028) was not bootstrapped before; its corrected bootstrap p is 0.075 (B = 1,999; 0.090 with B = 999). So size -> ER is significant at 5% by the clustered SE but only at 10% by the bootstrap.
- **Akotey B verdict unchanged:** MIXED: authors decide (B1 same-year growth -> CR -0.275, bootstrap p 0.003; B2 +0.064, p 0.58).
- **Reference.** Wooldridge, J. M. (2021, September 28). *Two-way fixed effects, the two-way Mundlak regression, and difference-in-differences estimators* [Working paper]. Michigan State University. Section 9.1 (unbalanced panels).
- **Addendum (Part 3 of the v2 revision, 21 Nov 2026): bootstrap samples re-absorb the fixed effects.** The Part 1 fix built each bootstrap outcome as fitted + residual x w on the within scale, without re-absorbing the insurer and year effects. The bootstrap coefficient is unaffected, but because the sign w is constant within an insurer, residual x w is not orthogonal to the YEAR dummies, so the bootstrap residuals, and so the bootstrap t, differed slightly from a two-way FE re-estimation of the bootstrap sample. Each bootstrap outcome is now re-absorbed on the insurer and year dummies. A new check in 07 re-estimates 5 bootstrap samples with models.fe and finds the same t (max difference about 1e-13). Effect on the 97 bootstrap p-values: median change 0.011, largest 0.025; one crosses a threshold (gross basis, size -> ER_g in M5 without RET: 0.097 -> 0.116). Quoted values: lagged growth -> CR, M1 0.64 -> 0.65; size -> ER, M1 (B = 1,999) 0.075 -> 0.082; step 09 ln(assets) -> ER 0.075 -> 0.078; Akotey B1 same-year growth -> CR 0.003 -> 0.004 (verdict unchanged). Full table: `docs/d14_addendum_before_after.csv`.
- **Within-correlation (D3) switched to the exact transformation** in Part 3: 0.601 -> 0.604.
- **Not changed here.** `models.twdm` (the closed-form demeaning) is still used for one descriptive number in step 04, the within-correlation of lagged growth and market-share growth (D3: 0.601; exact within-transformation gives 0.604). To be switched in Part 3 of the v2 revision.


## v1 -> v2 bridge (Part 3; outputs/tables/v1_v2_bridge.csv, v1_v2_bridge_mundlak.csv)
One element changed at a time, M1, two-way FE, clustered SEs (D12), bootstrap p (D14). Step A reproduces v1 exactly.

| Step | Growth -> CR (SE) | Growth -> ER | Size -> ER, within (p) | n |
|---|---|---|---|---|
| A v1: published LR, ER; v1 growth; ln GWP; CR winsorised separately | +0.055 (0.088) | +0.032 | -11.4 (0.028) | 176 |
| B + additive winsorising (CR_w = LR_w + ER_w) | +0.059 (0.090) | +0.032 | -11.4 (0.028) | 176 |
| C + 2015-16 ER corrected (Tier 1) | +0.045 (0.092) | +0.019 | **-5.0 (0.29)** | 176 |
| D + single growth measure | +0.043 (0.093) | +0.017 | -4.9 (0.31) | 175 |
| E + ln(total assets) as size | +0.040 (0.102) | +0.014 | -4.7 (0.46) | 171 |
| F + component-based outcomes = v2 primary | +0.016 (0.091) | -0.004 | +3.5 (0.74) | 171 |

**The v1 within-insurer size effect on the expense ratio rested on the erroneous printed 2016 expense ratios:** the 2015-16 ER correction alone (step C) moves it from -11.4 (p = 0.028) to -5.0 (p = 0.29). The between-insurer size effect survives (Mundlak, D18): -12.9 (p = 0.010) in v1, -12.1 (p = 0.043) in v2. The growth coefficient stays null throughout; its largest move comes from the component-based outcomes (E -> F).

## D15 note: data tiers and primary outcomes (Part 2-3, Nov 2026)
- **Tier 2 source.** The NIC quarterly returns workbook is published by the NIC (source confirmed 21 Nov 2026); its figures are insurers' unaudited quarterly submissions. Since the public release (25 Nov 2026) it is tracked in git with its derived insurer-level files in `data/processed/` (A15, A17; edition Q2 2026, read to Q1 2026), so the public pipeline reproduces v1 and v2.
- **Concordance** (A19): 2015-2023, 238 Tier 1 insurer-years; 234 Q4 rows within max(5%, GHS 0.5m) of audited GWP, 3 fail, 1 has no Q4 row; 2 Q4 copy-forwards (pinned in 07).
- **Basis** (A17): the workbook's claims ratio is over NEP + RIC (NIC's own definition), so the primary denominator is NEP + RIC; true-NEP ratios and ER net of RIC are secondary.
- **Primary outcomes:** LR_c, ER_c, CR_c = component-based on the NEP + RIC basis where Q4 passes concordance, Tier 1 published where it fails or is missing (6 of 171 sample rows: 2 failed or missing Q4, 4 with the denominator not recoverable).
- **Tier 1 variants** (sensitivities): 2015-16 ER := CR_nic - LR on the 41 mismatch rows (31 corroborated by the returns within 5 pp; A16, A19); 2020 ER replaced by the returns ER for 26 rows where the published value omits commission (A20).
- **Growth -> CR under the five outcome variants (M1):** component-based +0.016 (bootstrap p 0.92); Tier 1 published +0.040 (0.77); Tier 1 corrected 2020 +0.077 (0.55); excluding 2020 outcomes -0.014 (0.94); excluding 2019 outcomes +0.061 (0.77). All null; the 2020 choice moves the coefficient by about 0.06, well inside one SE.

## D16 note: single growth measure
- Exact GWP growth: audited exact GHS 2016-2019; 2020-22 from returns GWP where Q4 passes concordance in t and t-1 (77 insurer-years; 2020 uses the audited 2019 base); NIC %-change table as fallback (2 insurer-years, flagged) and for 2015 (no 2014 GWP); 2023 as v1 (rounded GHS m); merger years missing (D13); g(t-2) missing for 2016.
- Cross-check against NIC's %-change table, 2020-22: median absolute difference 0.19-0.38 pp; 81-88% within 1 pp, 92-100% within 5 pp.
- Effect: M1 growth -> CR +0.016 (v2 measure) vs +0.019 (v1 measure, same sample); the bridge step D moves CR by -0.002.

## D17 note: total assets as size
- ln(total assets at 31 Dec of t-1) from the Q4 returns (concordance-passing rows); 171 of the 2016-2022 sample rows (5 lack lagged assets).
- Within insurers, size has no effect on any ratio (ER +3.5, p = 0.74; CR +6.6, p = 0.61); with ln(GWP) (M1b) the same (ER +0.3, p = 0.97). Between insurers, larger insurers have lower expense and combined ratios (D18). See the bridge above for why v1 differed.

## D18 note: two-way Mundlak decomposition
- Pooled OLS of each outcome on the M1 regressors, their insurer means (over observed years), year dummies and the insurer means of the year dummies (required for exact equivalence in an unbalanced panel; Wooldridge, 2021, Theorem 3.1 and Section 9.1); insurer-clustered SEs. Within coefficients equal models.fe to 1e-12 (checked in 07).
- **Within vs between** (v2): size -> ER within +3.5, between-type -12.1 per log unit (p = 0.043); size -> CR between -11.1 (p = 0.017). Growth -> ER between -0.25 (p = 0.010), growth -> CR between -0.28 (p = 0.013): insurers that grow faster on average have LOWER expense and combined ratios, while an insurer's own faster growth does not change its ratios (within +0.016, p = 0.86).
- Robust variable-addition test that all regressor means are zero (replaces the classical Hausman test): p = 0.61 (LR), 0.17 (ER), 0.35 (CR). The classical Hausman test also does not reject (p = 0.13-0.23).
- **Reading the growth-quartile figure (Figure 3):** the pattern of lower ratios in higher growth quartiles reflects between-insurer differences, not within-insurer growth effects.

## D19 note: year-specific MID test (RQ3)
- M1 + g(t-1) x D2020, D2021, D2022 (base 2016-19). CR: +0.10, +0.06, +0.03, none significant; joint = 0 p = 0.84; equality p = 0.82. ER: 2020 +0.16 (clustered p 0.018, bootstrap 0.13); joint p = 0.08.
- Pre-trend (g(t-1) x 2017..2022, base 2016; H0 2017 = 2018 = 2019 = 0): CR p = 0.12, ER p = 0.23, LR p = 0.057 (borderline).
- Exploratory g x post2020 x demeaned 2021 motor share: significant by clustered SEs only, not by the bootstrap. Figure 7.

## D20 note: Hansen (1999) threshold test
- Two-way FE threshold model on q = g(t-1) with the M1 controls; insurer and year effects partialled out exactly before the grid search (D14); grid = observed q between its 15th and 85th percentiles (114 points); F1 = (S0 - S1) / s2; CI for the threshold by LR inversion (Hansen, 2000).
- **Departure from Hansen (1999):** Hansen resamples each individual's residual vector, which requires a balanced, one-way panel. This panel is unbalanced (1-7 years per insurer) and the model is two-way, so the null distribution of F1 is obtained by a wild bootstrap under the null (one Rademacher sign per insurer, fixed effects re-absorbed in each sample, 999 replications). Documented in `src/13_threshold.py`.
- **Validation by simulation** on the real sample structure (200 panels per design): size 2.5% at 5% (5.5% at 10%; conservative); power 14.5% (slope +0.25 above the 60th percentile) and 57.5% (slope +0.5); threshold located exactly (median estimate = true value); CI coverage 97.5-98.5%.
- **Real data:** no threshold for any outcome (CR F = 6.1, bootstrap p = 0.17; ER p = 0.14; LR p = 0.40); confidence sets cover most of the grid. Point estimates run against "fast growth hurts" (positive slope only below the estimated threshold).

## D21 note: early warning (Experiments 1-3)
- **Conclusion on the quarterly returns changes** from "informative" (Exp 2: Q2 YTD CR AUC 0.815) to **"no incremental warning value; useful for validation and recalibration only"**: the pre-registered incremental test (README section 5, commit 3eef056) finds that the same-quarter change in Q2 YTD CR DOES NOT ADD INFORMATION to last year's CR (AUC difference -0.001, 95% CI [-0.016, +0.012], 48 test rows); Exp 2 had already shown last year's audited CR ranks insurers better than the Q2 return.
- **4a, dual basis:** premium growth has no warning value (AUC 0.52 under both growth measures). Whether CR(t-1) is detectably better than growth depends on the basis: with the 2020-corrected CR (primary target), +0.22 [-0.03, +0.44], no detectable difference; with the 2015-16-corrected-only or published CR, +0.28 [+0.05, +0.49], growth carries less warning value.
- **2020-correction caveat:** the corrected 2020 CR, used as CR(t-1) for the 2021 test rows, ranks insurers less well (CR(t-1) AUC 0.738 against 0.803), so the CR(t-1) result is sensitive to how the 2020 published ER is treated (A20).
- **IFRS 17:** the IFRS 4 cut-off (118) flags few insurers under IFRS 17; re-estimated cut-offs are about 103 (published 2023 -> 2024: bootstrap range 86.5 to 2,090.5; workbook 2024 -> 2025: 98.9 to 131.3), on 19-25 insurers. **Recalibration needed; current evidence too thin to set a value.**

## D22 note: cross-sectional dependence (limitation)
- **Finding.** The Pesaran CD test on the v2 M1 residuals rejects cross-sectional independence for the expense ratio (CD = -2.54, p = 0.011), not for the loss ratio (p = 0.40) or the combined ratio (p = 0.08). In v1 no outcome rejected at 5%, though LR (p = 0.058) and ER (p = 0.054) were close.
- **Why it matters.** Year fixed effects absorb shocks common to all insurers; dependence beyond them (insurers moving together in ways the year effect does not capture, e.g. groups of insurers sharing reinsurers or distribution channels) is not allowed for by insurer-clustered SEs, so the ER standard errors may be understated or overstated.
- **Indicative check.** Driscoll-Kraay SEs (Bartlett kernel, bandwidth 2) allow for cross-sectional and serial dependence, but their small-sample behaviour with T = 7 is poor (D8), so they are reported in `appendix_diagnostics.csv` as an indicative check only, not as headline inference. For M1 (v2) no term is significant under Driscoll-Kraay SEs either: growth -> ER -0.004 (DK SE 0.025, p = 0.88), growth -> CR +0.016 (DK SE 0.045, p = 0.72), size -> ER +3.5 (DK SE 7.0, p = 0.61). The conclusions do not change.
- **Write-up.** State it as a limitation of the expense-ratio inference; headline inference stays insurer-clustered SEs plus the wild cluster bootstrap.

## v1 headline results (superseded by v2; kept for the record) (updated 31 Oct 2026 for D12 and D13; bootstrap p-values 21 Nov 2026 for D14)
- Lagged growth -> CR: +0.055 pp per 1 pp (SE 0.088); +10 pp growth CI [-1.2, +2.3] pp. Not significant (WCB p = 0.65; 0.67 before D14).
- No evidence of convexity (quadratic or piecewise) under clustered SEs or WCB.
- Size -> ER: -11.4 pp per log unit (clustered p = 0.03; WCB p = 0.082, D14 with addendum). Expense ratio, not loss ratio, drives aggregate CR > 100%.
- MID slope change: not significant, including when 2020 is excluded.
- Diagnostics: serial correlation in ER and CR; heteroskedasticity; no significant cross-sectional dependence; Hausman does not reject (report RE alongside FE).

## D10 note: System GMM in Python (src/08_system_gmm.py, added 31 Oct 2026)
**What was run.** Blundell-Bond System GMM with pydynpd 0.2.2, mirroring Step 2 of R/twfe_and_system_gmm.R so the two can be compared.
- **Sample.** 2015-2022 with start-up years excluded (202 insurer-years, 29 insurers). LR, ER, CR, g and LEV_net are winsorised at the pooled 1/99 percentiles before lagging, and ln_gwp = log(gwp).
- **Model.** Y_it on Y_i,t-1, g_i,t-1, RET_it, ln_gwp_i,t-1 and LEV_net_i,t-1, for Y in {LR, ER, CR}.
- **Instruments.** GMM-style: lags 2-3 of Y and of g. IV-style: RET, L1.ln_gwp and L1.LEV_net. Year dummies and collapsed instruments. Lags are taken on the full insurer x year grid, so a missing year gives a missing lag, never a lag from two years back.
- **Estimation.** Two-step with Windmeijer-corrected SEs.
- **Variants.** GMM lags 2-4, and one-step (robust SEs).
- **Outputs.** outputs/tables/system_gmm.csv and system_gmm_diagnostics.csv.

The step runs after 07_validate.py and its results are **not pinned**.

**Environment.** pydynpd 0.2.2 does not run on numpy 2.4+ (it uses np.in1d and float() of 1x1 arrays). numpy is therefore pinned to 2.3.5. All step 01-07 tables and processed data are byte-identical under 2.3.5 and 2.4.4, and validation passes 26/26.

**Results (baseline).** In each baseline model, 144 differenced observations from 28 insurers and 16 instruments (Hansen df = 4).

| Outcome | Coefficient on lagged g (pp per pp) | SE | p |
|---|---|---|---|
| LR | +0.128 | 0.114 | 0.26 |
| ER | -0.017 | 0.053 | 0.75 |
| CR | +0.125 | 0.173 | 0.47 |

- All three variants are insignificant for all three outcomes (p >= 0.26). The sign is positive for LR and CR, as in TWFE and Anderson-Hsiao, and ER flips sign across variants around zero.
- This is consistent with the TWFE headline null (CR +0.046, p = 0.63) and with Anderson-Hsiao (CR +0.107, p = 0.42).

**Diagnostics (weak; report as such).**
- Instruments (16-18) stay below 28 insurers in every model.
- AR(2) never rejects (p >= 0.19).
- AR(1) rejects at 5% in only 1 of 9 models (ER one-step, p = 0.049). With 28 insurers the test has little power, but the usual first-order check is not met.
- Hansen p is 0.28-0.69 for ER and CR, but 0.06-0.07 for LR (below 0.10).
- The negative coefficient on lagged LR (-0.20) is implausible for a persistence parameter, so the LR model's specification is doubtful.

**Conclusion.** The System GMM supports, but cannot by itself establish, the null on lagged growth. Treat it as a secondary robustness check.

**Comparison with R pgmm (plm 2.6.7, run 31 Oct 2026).**
- **Same estimator.** On a specification where both packages build identical instruments (lagged Y and g only, GMM lags 2-3, collapsed, constant), coefficients, one-step robust SEs, two-step Windmeijer SEs and the two-step Hansen J agree to 6 decimal places, for LR, ER and CR, one-step and two-step. Both use the same 316 observations (144 differenced + 172 levels) in the full specification.
- **Different instrument conventions.** pgmm gives each IV-style variable separate columns for the differenced and levels equations, and instruments year dummies in the levels equation only (19 instruments, Sargan df 7). pydynpd uses one column per IV-style variable across both equations, the xtabond2 default (16 instruments, Hansen df 4). Neither package can express the other's convention.
- **Decision.** The thesis uses the pydynpd / xtabond2 convention (Roodman, 2009). pgmm is reported as a check that the result does not depend on the convention.
- **pgmm results (two-step).** Lagged g: LR +0.096 (p = 0.37), ER +0.012 (p = 0.80), CR +0.165 (p = 0.19). The null holds. AR(1) rejects for LR (p = 0.001) but not for ER or CR. AR(2) never rejects. Sargan p is 0.15 to 0.77. Lagged LR is again negative (-0.17). pgmm warns that a general inverse was used for the robust covariance.
- **Unresolved.** The AR(1) and AR(2) statistics differ between the packages even when the estimates are identical. One example is LR one-step AR(1): -2.58 in pgmm, -2.12 in pydynpd. pgmm also returns NaN for LR two-step. A third implementation (Stata xtabond2) is needed to settle which is right.
- **TWFE in R.** Coefficients are identical to Python. Before D12, clustered SEs were uniformly 0.893 times Python's: plm's HC1 counted only the 4 slopes (177/173), while linearmodels also counted the absorbed insurer and year effects (177/138). Since D12, both count slopes and year effects (177/167) and the SEs match exactly.

**v2 System GMM (Part 5, `system_gmm_v2.csv`).** Same specification on the v2 panel (component-based outcomes, single growth measure, ln(total assets) as size; 136 differenced observations, 26 insurers, 16-18 instruments): lagged growth is insignificant in every variant and outcome (p >= 0.22); AR(2) never rejects; Hansen p 0.09-0.90. Anderson-Hsiao (v2): growth p = 0.26 (LR), 0.95 (ER), 0.43 (CR); first-stage F 26-68.

## Headline results, v2 (21 Nov 2026; pinned in 07 as "v2 (thesis, requires NIC workbook)"; the workbook is tracked since 25 Nov 2026)
- **Lagged growth -> CR:** +0.016 pp per 1 pp (SE 0.091; bootstrap p = 0.92); +10 pp growth: 95% CI [-1.6, +1.9] pp; MDE 2.5 pp. Null under every specification, outcome variant, System GMM (p >= 0.22), Anderson-Hsiao, leave-one-out (0 of 28 runs significant) and the threshold test.
- **Size:** no within-insurer effect (ER +3.5, p = 0.74); between insurers, larger insurers have lower expense ratios (-12.1 per log unit, p = 0.043).
- **Growth between insurers:** faster-growing insurers have lower average ER and CR (Mundlak; -0.25 and -0.28, p = 0.010 and 0.013); the quartile pattern (Figure 3) is this between-insurer difference.
- **MID (RQ3):** no year-specific change in the growth slope on CR (joint p = 0.84); 2020 not different from 2021-22 (p = 0.82); no clear pre-trend.
- **Reverse regression:** no support for "weak insurers shrink" (CR(t-1) -> g(t) +0.09, p = 0.44).
- **Expenses dominate:** component-based ER is 70-99% of NEP + RIC against LR 30-50% (Figure 2, v2).
- **Diagnostics (v2):** Hausman and Mundlak tests do not reject; heteroskedasticity; serial correlation not significant for LR, ER (CR p = 0.08); cross-sectional dependence significant for ER (Pesaran p = 0.011; limitation, D22; Driscoll-Kraay as an indicative check changes nothing).
