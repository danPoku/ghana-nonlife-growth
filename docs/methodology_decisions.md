# Methodology decisions (changes from the 19 Sept 2026 defence)

Status: **proposed**. Each needs author agreement and, where marked, supervisor sign-off.

| # | Defence version | Proposed | Reason | Sign-off? |
|---|---|---|---|---|
| D1 | Size control ln(total assets) | ln(GWP, t-1) | Per-insurer assets not published (A10) | Yes |
| D2 | No leverage control | Net insurance risk ratio (NWP / equity), t-1 | Classic premium-to-surplus underwriting risk measure; published by NIC | Yes |
| D3 | Growth and market-share growth in one equation | Separate models (M1 vs M4) | With year FE, market-share growth ~ premium growth (within-corr 0.61) | Yes |
| D4 | Winsorising in sensitivity only | Exclude start-up years + winsorise 1/99 in main; raw as sensitivity | Single start-up obs at 10,950% would dominate OLS (A11) | Yes |
| D5 | CR from NIC tables | CR = LR + ER | NIC CR inconsistent in 2015-16 (A6); makes CR coefficient = LR + ER coefficients | No |
| D6 | MID difference-in-differences (motor vs non-motor, insurer-class) | Post-2020 slope change: g(t-1) x Post2020, plus industry class descriptives | Insurer-class data not public (A13). Cannot separate MID from COVID; state this | Yes |
| D7 | Clustered SEs | Clustered SEs + wild cluster bootstrap (Rademacher, 999 reps) | Only 29 clusters (28 with within-variation) | No |
| D8 | — | Driscoll-Kraay reported, not headline | Requires large T; T = 7 | No |
| D9 | "Net of market-wide growth" | Year FE do this; excess growth (g - year median) used for thresholds | Equivalent within TWFE; thresholds need a relative measure | No |
| D10 | System GMM as robustness | Kept (R pgmm + Python pydynpd step 8, collapsed instruments) + Anderson-Hsiao IV in Python. See D10 note below | Instrument proliferation risk with N = 29 | No |
| D11 | Report null without size | Report 95% CIs in +10pp-growth units and minimum detectable effects | A null must show what it rules out | No |
| D12 | Clustered-SE small-sample correction counted insurer and year effects (linearmodels default) | Count year effects but not insurer effects, which are nested within the insurer clusters (Stata xtreg / reghdfe convention; Cameron & Miller, 2015). Implemented with year effects as explicit dummies (linearmodels ignores `count_effects=False` when `time_effects=True`). See D12 note below | Counting nested effects over-inflates clustered SEs; aligns Python with R (plm) and Stata | No |
| D13 | Growth across mergers treated as ordinary growth | Growth across a merger is set to missing in the first year of the combined entity, rather than replaced by pro-forma growth, to keep unaudited data out of the main analysis. See D13 note below | RegencyNem 2016: +61.4% published, about +3.0% organic; the pro-forma base exists only in an unaudited workbook | No |

## D12 note: clustered-SE convention (changed 31 Oct 2026)
- **Effect.** Coefficients, Driscoll-Kraay SEs, wild-cluster-bootstrap p-values, `nobs` and `r2_within` are unchanged. Every insurer-clustered SE is multiplied by sqrt((N-k-G-(T-1)) / (N-k-(T-1))): 0.909 for the headline M1 models (sqrt(138/167)), and 0.890-0.911 across the sensitivity models.
- **Pins.** The four pinned SEs in 07_validate.py were updated: g_L1_w 0.0571 -> 0.0519 (LR), 0.0447 -> 0.0406 (ER), 0.0960 -> 0.0873 (CR); ER ln_gwp_L1 5.657 -> 5.1425.
- **Inference.** No growth coefficient changes significance at 5% or 10%. Size -> ER crosses 5% in two sensitivity models (M5 MID slope and raw incl. start-ups: p 0.06 -> 0.04). At 10%, lagged RET -> ER (0.13 -> 0.10) and size -> ER excl. 2020 (0.12 -> 0.08) cross. Minimum detectable effects fall about 9% (CR: 2.69 -> 2.44 pp per +10 pp growth).
- **R.** R/twfe_and_system_gmm.R Step 1 now uses `effect = "individual"` with `factor(year)`, so plm's HC1 counts the year dummies. R's clustered SEs then equal Python's to every printed digit. R's p-values use a t distribution and Python's a normal, so p differs slightly.

## D13 note: merger rule (added 31 Oct 2026)
- **Rule.** `MERGERS` in src/config.py lists each merger (insurer, first year of the combined entity, absorbed entity, source). In that year `g`, `g_excess`, `g_real`, `g_real_dec` and `d_ms` are missing and `g_source` = "not computed: merger year"; the `_L1` lags follow. The rule is applied before the year median for `g_excess` is taken. Entries: RegencyNem 2016 (NEM absorbed), SAHAM_SANLAM 2024 (Allianz absorbed; growth was already missing as 2024 is Insurance Revenue).
- **Why missing, not pro-forma.** RegencyNem's 2016 growth was +61.4% as published but about +3.0% against Regency + NEM combined. The NEM 2015 figure comes only from an unaudited quarterly returns workbook (data_issues A15), so it is kept out of the main analysis.
- **Effect.** Estimation sample 177 -> 176 (RegencyNem 2017 drops: its lagged growth is now missing). Winsorising bounds are recomputed on the 176 rows, which moves 4 clipped values per variable. Lagged growth -> LR / ER / CR: +0.0225 / +0.0303 / +0.0461 -> +0.0261 / +0.0324 / +0.0547 (WCB p 0.79 / 0.51 / 0.72 -> 0.75 / 0.48 / 0.67). No TWFE coefficient changes significance at 5%. M3 threshold (p75 of excess growth) 9.957 -> 9.926 pp. M4 sample 153 -> 152. Anderson-Hsiao n 121 -> 120, growth p-values essentially unchanged. System GMM n 144 -> 142; CR with GMM lags 2-4 moves from p = 0.57 to p = 0.083 (+0.196), so that variant is sensitive to a single insurer.
- **Pins** in 07_validate.py updated (see the comment there); 30 checks.

## Headline results under the proposed design (updated 31 Oct 2026 for D12 and D13)
- Lagged growth -> CR: +0.055 pp per 1 pp (SE 0.088); +10 pp growth CI [-1.2, +2.3] pp. Not significant (WCB p = 0.67).
- No evidence of convexity (quadratic or piecewise) under clustered SEs or WCB.
- Size -> ER: -11.4 pp per log unit (p = 0.03). Expense ratio, not loss ratio, drives aggregate CR > 100%.
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
