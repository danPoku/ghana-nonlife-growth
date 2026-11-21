# Akotey et al. (2023) replication (throwaway experiment, pre-registered)

**Status: THROWAWAY REPLICATION EXPERIMENT.** Not part of the thesis pipeline (`run_all.py`, `src/`,
`07_validate.py`); may be kept or discarded depending on the outcome. Pre-registered 1 Nov 2026, before any
model was run. Data: `data/processed/panel_master.csv` only (public, audited NIC data).
Scripts: `replicate_gmm.py` (A), `timing_bridge.py` (B). Outputs (aggregate only): `outputs/`.

## Background

Akotey, Aawaar & Boamah (2023), "What accounts for the high underwriting losses in the Ghanaian insurance
industry?", AJEMS 14(1), 34-52, found that premium growth and market-share growth were negatively associated
with underwriting profit (Ghana, 2007-2017, 18 non-life insurers). Their non-life results (Table 5): premium
growth -0.022 (p=0.015), market-share growth -0.050 (p<0.001), Arellano-Bond difference GMM, robust SEs.
Key design differences from this thesis:
- they relate growth to profit in the SAME year; the thesis uses growth in the PREVIOUS year
- their outcome is underwriting profit / GWP; the thesis uses loss, expense and combined ratios on earned premium
- they used only insurers with complete data for all years

The question: does the thesis's null result differ from Akotey et al. because of TIMING (same-year vs lagged),
or because of the PERIOD/POPULATION (2015-2022, all insurers)?

## 1. Pre-registered specification (as specified by the authors, verbatim)

Variables (state every approximation explicitly):
- UP_GWP (outcome, percent): underwriting profit / GWP. Not observed directly. Approximate
  as (100 - CR) x RET / 100, i.e. underwriting margin on earned premium times net-to-gross
  premium, treating net earned premium as roughly net written premium. Also report
  UW_margin = 100 - CR (profit per 100 of earned premium) as a second outcome.
- PGR (same-year premium growth, as a FRACTION, e.g. 0.25 = 25%, matching Akotey Table 1)
- MSGR (same-year market-share growth, relative change in ms, as a fraction)
- MANCOMP: expense ratio ER, as a proxy for their compensation ratio (state the mismatch)
- UWRISK: dummy = 1 if CR > 100. NOTE in the README: with an outcome built from CR, this
  dummy is close to mechanical; it is included only to mirror their specification
- Controls: REINS = 100 - RET (% ceded); inflation (cpi_avg_yoy)
- Sample: years 2015-2022 (IFRS 4), start-ups excluded, merger years missing (D13)

Specifications:
A) Akotey-style: Arellano-Bond DIFFERENCE GMM (pydynpd, nolevel), outcome UP_GWP,
   regressors L1.outcome, PGR, MSGR, MANCOMP, UWRISK (their Table 5 col. 2), then + REINS
   + inflation (col. 3). Two-step, Windmeijer SEs, collapsed instruments, lags 2-3 of the
   outcome. Report AR(1), AR(2), Hansen p and instrument count vs number of insurers.
   Run on (i) the thesis sample and (ii) a BALANCED subsample of insurers present in every
   year, mimicking their selection.
B) Timing bridge (two-way FE, models.fe, D12 convention, clustered SEs + wild cluster
   bootstrap via models.wcb): for each outcome in {UW_margin, CR, LR, ER} estimate
   B1: same-year growth (g) + RET + ln_gwp_L1 + LEV_net_L1
   B2: lagged growth (g_L1) + same controls  [the thesis specification]
   B3: both g and g_L1 together
   Winsorise at 1/99 on the B sample (state this), and also report raw.

Interpretation rules (applied to B1/B2 on CR, using wild cluster bootstrap p-values):
- TIMING: same-year growth is associated with a significantly WORSE result (CR higher,
  p < 0.05) while lagged growth is not -> the difference from Akotey et al. is explained by
  timing, consistent with a same-year accounting effect
- PERIOD/POPULATION: neither same-year nor lagged growth is significant -> the difference
  reflects the later period and/or full population, not timing
- REPLICATION OF SIGN: in A, PGR negative with p < 0.05 -> their sign is reproduced on
  2015-2022 data; otherwise not reproduced. Report the PGR coefficient in their units next
  to their -0.022, and its economic size (effect of doubling premium, PGR +1.0)
- Anything else -> "MIXED: authors decide"
- A GMM result whose AR(2) test rejects or whose Hansen p is below 0.10 or above 0.99 is
  reported as "diagnostics fail" and does not count toward REPLICATION OF SIGN
- Units caveat to state: Akotey Table 1 suggests growth as a fraction (mean 0.39) and
  profit in percent (mean -7.30); this reading is assumed, not confirmed

## 2. Amendments agreed before analysis

- **A without year dummies** (replication). A common inflation rate is collinear with year dummies, so
  col. 3 cannot have both; col. 2 is run without them too, so the two columns differ only by the added
  controls. This appears to match Akotey et al.; it is an approximation.
- **Secondary variant A-yd (pre-registered, does NOT count toward the A verdict):** col. 2 specification
  plus year dummies (`timedumm`), without the inflation control, on both samples, reported beside the
  replication. Why: without year effects, common shocks (COVID 2020, high inflation 2022) can be partly
  attributed to growth.
- **A verdict over the 4 headline models** (col. 2 and col. 3 x thesis and balanced samples, outcome
  UP_GWP). Each model is labelled replicated / not replicated / diagnostics fail. Overall:
  REPLICATED if every model passing diagnostics has PGR negative with p < 0.05 (and at least one passes);
  NOT REPLICATED if none of the models passing diagnostics does; DIAGNOSTICS FAIL if no model passes;
  otherwise "MIXED: authors decide". **Every A verdict states how many models passed diagnostics**, e.g.
  "REPLICATED (2 of 4 models passing diagnostics)".

## 3. Operational specification (fixed before analysis)

### Approximations and mismatches (stated as required)
- **UP_GWP = (100 - CR) x RET / 100.** Underwriting profit is not published per insurer. CR is on earned
  premium; RET = NWP / GWP. Treating net earned premium as net written premium ignores the change in the
  unearned premium reserve, which is largest exactly when growth is high, so the approximation is worst
  where it matters. Because RET enters UP_GWP, REINS = 100 - RET is mechanically linked to the outcome.
- **UW_margin = 100 - CR.** In the two-way FE models every UW_margin coefficient is exactly minus the CR
  coefficient (same SEs and p-values); it is reported but adds no information.
- **MANCOMP = ER** (management expenses + net commissions over earned premium). Akotey et al.'s compensation
  ratio covers management compensation only; ER is broader and is itself a component of CR, so it is close
  to mechanical with an outcome built from CR.
- **UWRISK = 1 if CR > 100.** With an outcome built from CR this dummy is close to mechanical; it is included
  only to mirror their specification.
- **PGR = g / 100** (g already missing in merger years, D13; 2024 not used).
- **MSGR = ms(t) / ms(t-1) - 1**, computed on the full insurer x year grid (a gap year gives missing), and
  set missing in merger years (`merger_break`). The panel's `d_ms` is a change in percentage points, not a
  relative change, so it is not used.
- **Inflation = cpi_avg_yoy** (percent, WDI annual average).
- **Units caveat:** Akotey Table 1 suggests growth as a fraction (mean 0.39) and profit in percent
  (mean -7.30); this reading is assumed, not confirmed. Under it, their -0.022 means a doubling of premium
  (PGR +1.0) lowers underwriting profit by 0.022 pp of GWP.

### A: difference GMM (`replicate_gmm.py`)
- Rows: 2015-2022, start-ups excluded. No winsorising (Akotey et al. report none).
- Command (pydynpd 0.2.2, wrapper copied from src/08_system_gmm.py: rows sorted by insurer and year,
  `SystemExit` turned into an error, own count of usable observations asserted equal to pydynpd's):
  - col. 2: `Y L1.Y PGR MSGR MANCOMP UWRISK | gmm(Y, 2:3) iv(PGR MSGR MANCOMP UWRISK) | nolevel collapse`
  - col. 3: as col. 2 plus `REINS infl` in the regressors and in `iv()`
  - A-yd: col. 2 with options `nolevel collapse timedumm`
  Two-step with Windmeijer-corrected SEs (pydynpd default). PGR, MSGR, MANCOMP, UWRISK, REINS and inflation
  are IV-style (treated as strictly exogenous), as specified; this treats same-year growth as exogenous,
  a strong assumption.
- Outcomes: UP_GWP (primary, counts toward the verdict); UW_margin (secondary, reported only).
- Samples: (i) thesis sample; (ii) balanced: insurers with every col. 3 variable present in all 8 years
  2015-2022. RegencyNem cannot be balanced (PGR missing in 2016 under D13).
- Diagnostics: AR(1), AR(2), Hansen J, df and p, instrument count vs insurers (flagged if count >= insurers).
  Diagnostics fail = AR(2) p < 0.05, or Hansen p < 0.10, or Hansen p > 0.99.
- If pydynpd cannot express difference GMM with this specification: STOP; no substitute estimator.

### B: timing bridge (`timing_bridge.py`)
- Sample: `data/processed/estimation_sample.csv` rows (2016-2022, start-ups excluded) with both g and
  g_L1 present, so B1, B2 and B3 use identical rows.
- Winsorised versions: g, g_L1, CR, LR, ER and LEV_net_L1 clipped at the 1st / 99th percentiles of this
  B sample (UW_margin = 100 - winsorised CR). Raw versions also reported. **The verdict uses the
  winsorised models.**
- Models: `models.fe` (two-way FE, insurer-clustered SEs, D12 convention). Wild cluster bootstrap
  `models.wcb` (Rademacher, 1,999 reps, seed 1) for g in B1 and B3 and g_L1 in B2 and B3.
- Check: B2 on CR is compared with the thesis M1 result (+0.0547); any difference comes from the
  winsorising sample and is reported.
- Verdict from B1 (g) and B2 (g_L1) on CR, wild-cluster-bootstrap p-values, rules in section 1.
  For B1 vs B2 the LR and ER results are reported to show whether a same-year effect runs through
  claims or expenses.
- Outputs: `outputs/gmm_results.csv`, `outputs/gmm_diagnostics.csv`, `outputs/bridge_results.csv`.

## 4. Deviation and results (added AFTER analysis; sections 1-3 unchanged since commit 2c0df93)

### Deviation (found before any model was run)
- **Balanced subsample.** "Every col. 3 variable present in all 8 years 2015-2022" selects no insurer:
  MSGR cannot exist in 2015 (the panel has no 2014 market shares). Used instead: outcome present in every
  year 2015-2022 and every col. 3 regressor in every year 2016-2022. In difference GMM with L1.Y, 2015
  only supplies the lagged outcome, so no usable row is lost. Result: 22 balanced insurers.

### A (difference GMM): NOT REPLICATED (4 of 4 models passing diagnostics)
| Sample | Spec | PGR (UP_GWP) | SE | p | Doubling premium (PGR +1.0) |
|---|---|---|---|---|---|
| thesis (28 insurers, 143 obs) | col. 2 | -4.94 | 10.57 | 0.64 | -4.9 pp of GWP |
| thesis | col. 3 | -6.74 | 12.17 | 0.58 | -6.7 pp |
| balanced (22 insurers, 132 obs) | col. 2 | +0.56 | 7.00 | 0.94 | +0.6 pp |
| balanced | col. 3 | +0.90 | 9.37 | 0.92 | +0.9 pp |
Akotey et al.: -0.022 (p = 0.015). AR(2) p 0.37-0.99, Hansen p 0.19-0.49 (df 1), 6-8 instruments.
Secondary A-yd (year dummies, not counted): PGR +1.56 (p 0.95) thesis; -11.84 (p 0.77) balanced, whose
Hansen p 0.024 fails diagnostics. MSGR is never significant (p >= 0.29).

### B (timing bridge): MIXED: authors decide
- B sample 175 insurer-years, 29 insurers, 2016-2022. B2 reproduces the thesis closely (CR +0.064 vs M1 +0.055).
- Same-year growth -> CR (B1): **-0.275 pp per pp, WCB p 0.001**: higher same-year growth goes with a
  BETTER combined ratio, the opposite direction to the TIMING rule. Lagged growth (B2): +0.064, WCB p 0.60.
- Same-year effect splits about evenly: LR -0.115 (WCB p 0.059), ER -0.121 (WCB p 0.015). Raw: LR -0.113
  (p 0.038), ER -0.149 (p 0.021). B3 (both together) gives the same picture.

### Update after the bootstrap fix (D14, 21 Nov 2026; added after analysis, sections 1-3 unchanged)
`models.wcb` now uses the exact two-way within-transformation (docs/methodology_decisions.md, D14). Part B was
re-run with the same seed and draw order; coefficients and clustered SEs are unchanged, bootstrap p-values change:
B1 same-year growth -> CR 0.001 -> 0.003; B2 lagged growth -> CR 0.60 -> 0.58; B1 -> LR 0.059 -> 0.075;
B1 -> ER 0.015 -> 0.015; raw B1 -> LR 0.038 -> 0.058, raw B1 -> ER 0.021 -> 0.016. **The B verdict is unchanged:
MIXED: authors decide.** Part A (difference GMM) does not use the bootstrap.

### Update after the D14 addendum (Part 3 of the v2 revision, 21 Nov 2026; added after analysis)
Each bootstrap sample now re-absorbs the insurer and year effects (docs/methodology_decisions.md, D14 addendum).
Coefficients and clustered SEs unchanged. B1 same-year growth -> CR 0.003 -> 0.004; B2 lagged growth -> CR 0.58 -> 0.59;
B1 -> LR 0.075 -> 0.089; B1 -> ER 0.015 -> 0.020; raw B1 -> LR 0.058 -> 0.063, raw B1 -> ER 0.016 -> 0.022.
**The B verdict is unchanged: MIXED: authors decide.**
