"""Step 7: validation checks. Exits non-zero if any check fails.

Data checks confirm the extraction is faithful to NIC's own figures. Result
checks pin the headline numbers from the first validated run, so any change
to code or data that moves them is noticed and must be explained.
"""
import sys, json
import numpy as np, pandas as pd
from config import ROOT, INTERIM, PROCESSED, TABLES, MERGERS, QUARTERLY_FILE, CONFIDENTIAL
from models import fe, wcb

fails, notes = [], []
def check(cond, msg):
    (notes if cond else fails).append(("PASS " if cond else "FAIL ") + msg)

L = pd.read_csv(INTERIM / 'nic_long_all_vintages.csv')
P = pd.read_csv(PROCESSED / 'panel_master.csv')
E = pd.read_csv(PROCESSED / 'estimation_sample.csv')
T = pd.read_csv(TABLES / 'regressions.csv')

# 1. Cross-vintage agreement: each overlapping insurer-year must be identical across reports
ins = L[~L.insurer_id.str.startswith(('TOTAL', 'NIC'))]
core = ['gwp', 'loss_ratio', 'expense_ratio', 'combined_ratio', 'retention', 'chg_gwp_pct', 'net_risk_ratio']
for v in core:
    d = ins[ins.variable == v].dropna(subset=['value'])
    spread = d.groupby(['insurer_id', 'year']).value.agg(['max', 'min', 'count'])
    spread = spread[spread['count'] >= 2]
    tol = 1.01e6 if v == 'gwp' else 1.01      # GWP after 2019 is published in rounded GHS millions
    n_rev = int(((spread['max'] - spread['min']) > tol).sum())
    check(n_rev == 0, f"vintage agreement {v}: {len(spread)} overlaps, {n_rev} revisions")

# 2. Market totals reconcile to NIC published totals
tot = L[(L.variable == 'gwp') & (L.insurer_id == 'TOTAL_TOTALS')].drop_duplicates('year').set_index('year').value
s = P.groupby('year').gwp.sum()
for y in range(2016, 2020):
    check(abs(s[y] - tot[y]) < 1, f"GWP total {y} reconciles to the cedi ({s[y]:,.0f})")
gap15 = tot[2015] - s[2015]
check(abs(gap15 - 3_287_646) < 1, f"2015 unitemised gap is the documented GHS {gap15:,.0f} (survivorship)")
for y in range(2020, 2025):
    check(abs(s[y] - tot[y]) <= 3e6, f"GWP total {y} within rounding of NIC total")

# 3. Panel structure
check(P.insurer_id.nunique() == 29, f"29 insurer entities (found {P.insurer_id.nunique()})")
check(len(P) == 263, f"263 insurer-years in master panel (found {len(P)})")
check(len(E) == 176, f"176 observations in estimation sample (found {len(E)})")  # 177 before merger rule (D13)
check(int(P.startup.sum()) == 10, f"10 start-up insurer-years flagged (found {int(P.startup.sum())})")
mm = P[P.cr_nic_mismatch].year.value_counts().to_dict()
check(set(mm) <= {2015, 2016, 2021}, f"CR != LR+ER only in documented years {mm}")
mrg = P.set_index(['insurer_id', 'year']).reindex([(m['insurer_id'], m['year']) for m in MERGERS])
check(mrg.g.isna().all() and len(mrg) == len(MERGERS),
      f"g missing in every merger year ({', '.join(f'{i} {y}' for i, y in mrg.index)})")

# 4. Headline results pinned from the first validated run. Two independent sets: "v1 (public, Tier 1 only)" here,
#    checked on every run; "v2 (thesis, requires NIC workbook)" in section 9, checked only when the workbook is present.
V1 = 'v1 (public, Tier 1 only)'
def coef(model, term):
    r = T[(T.model == model) & (T.term == term)]
    return float(r.coef.iloc[0]), float(r.se.iloc[0])
# SE pins updated 31 Oct 2026 for the clustered-SE convention change (D12): the small-sample correction now
# counts year effects but not insurer effects (nested in the insurer clusters), as in Stata xtreg/reghdfe.
# Every clustered SE fell by sqrt((N-k-G-(T-1))/(N-k-(T-1))): sqrt(138/167) = 0.909 for these M1 models.
# Previous pins: SE 0.0571, 0.0447, 0.0960, 5.657. Coefficients are unchanged.
# Updated for merger rule (RegencyNem 2016); see docs (D13). N 177 -> 176, winsor bounds from the 176-row
# sample, SEs on the D12 convention. Previous pins: coef 0.0225 / 0.0303 / 0.0461 / -11.644,
# SE 0.0519 / 0.0406 / 0.0873 / 5.1425.
pins = {('LR_w|M1_linear|cluster', 'g_L1_w'): (0.0261, 0.0523),
        ('ER_w|M1_linear|cluster', 'g_L1_w'): (0.0324, 0.0411),
        ('CR_w|M1_linear|cluster', 'g_L1_w'): (0.0547, 0.0881),
        ('ER_w|M1_linear|cluster', 'ln_gwp_L1'): (-11.427, 5.1405)}
for (m, t), (b0, se0) in pins.items():
    b, se = coef(m, t)
    check(abs(b - b0) < 1e-3 * max(1, abs(b0)) and abs(se - se0) < 1e-3 * max(1, se0),
          f"{V1} pinned result {m} {t}: coef {b:.4f} (expected {b0}), se {se:.4f} (expected {se0})")
# The shared helper used by step 10 (leave-one-out) reproduces the pins on the full estimation sample.
# (07 runs before 10, so it refits with models.fe directly; step 10 also asserts its full sample equals 04.)
X1 = ['g_L1_w', 'RET', 'ln_gwp_L1', 'LEV_net_L1_w']
fits = {y: fe(E.dropna(subset=[y] + X1), y, X1) for y in ('LR_w', 'ER_w', 'CR_w')}
ok = all(abs(fits[m.split('|')[0]].params[t] - b0) < 1e-3 * max(1, abs(b0)) and
         abs(fits[m.split('|')[0]].std_errors[t] - se0) < 1e-3 * max(1, se0) for (m, t), (b0, se0) in pins.items())
check(ok, f"{V1}: models.fe (step 10 helper) reproduces all four pinned results on the full estimation sample")
# D14: the wild cluster bootstrap's original t must be the two-way FE t (exact within-transformation), every M1 term
dt = max(abs(wcb(E, y, X1, var=v, B=0)[0] - fits[y].tstats[v]) for y in fits for v in X1)
check(dt < 1e-8, f"models.wcb original t equals models.fe t for all {len(fits) * len(X1)} M1 terms (max |diff| {dt:.1e})")
# 5. Deflator: annual-average CPI inflation from the WDI snapshot (descriptive g_real only)
cpi = P.drop_duplicates('year').set_index('year').cpi_avg_yoy
miss = [y for y in range(2015, 2024) if pd.isna(cpi.get(y))]
check(not miss, f"cpi_avg_yoy present for every year 2015-2023 (missing: {miss})")
n_blank = int(P.cpi_avg_source.fillna('').str.strip().eq('').sum())
check(n_blank == 0, f"every row has a cpi_avg_source ({n_blank} blank)")
g_real = 100 * ((1 + P.g / 100) / (1 + P.cpi_avg_yoy / 100) - 1)
same_na = (g_real.isna() == P.g_real.isna()).all()
max_dev = float((g_real - P.g_real).abs().max())
check(same_na and max_dev <= 1e-9, f"g_real = g deflated by cpi_avg_yoy (max deviation {max_dev:.1e})")

# 6. Gross-basis ratios (data_issues A16): LR_g = LR x RET/100 etc., IFRS 4 years only; CR_g_w is a sum
g4 = P[(P.year <= 2022) & P[['LR', 'ER', 'RET']].notna().all(axis=1)]
have = {'LR_g', 'ER_g', 'CR_g'} <= set(P.columns)
ok = have and g4[['LR_g', 'ER_g', 'CR_g']].notna().all().all() and \
     np.allclose(g4.LR_g, g4.LR * g4.RET / 100, rtol=0, atol=1e-9) and np.allclose(g4.ER_g, g4.ER * g4.RET / 100, rtol=0, atol=1e-9) and \
     np.allclose(g4.CR_g, g4.LR_g + g4.ER_g, rtol=0, atol=1e-9)
check(ok, f"LR_g, ER_g, CR_g present and equal to LR, ER x RET/100 and their sum for all {len(g4)} 2015-2022 rows with LR, ER, RET")
n17 = int(P.loc[P.year >= 2023, ['LR_g', 'ER_g', 'CR_g']].notna().any(axis=1).sum()) if have else -1
check(n17 == 0, f"gross-basis ratios missing for 2023-24 (IFRS 17 ER is already gross; {n17} rows filled)")
# exact test needs exact floats: pandas' default CSV parser can be off by 1 ulp, so re-read with round_trip
Eg = pd.read_csv(PROCESSED / 'estimation_sample.csv', float_precision='round_trip')
n_bad = int((Eg.CR_g_w != Eg.LR_g_w + Eg.ER_g_w).sum()) if {'LR_g_w', 'ER_g_w', 'CR_g_w'} <= set(Eg.columns) else -1
check(n_bad == 0, f"CR_g_w == LR_g_w + ER_g_w exactly in the estimation sample ({n_bad} rows differ)")
# Mismatch counts pinned from the first run of step 11 (11 runs after 07, so count from the same panel flag).
# 2015: 21 of 23 comparable rows, 2016: 20 of 23. An earlier off-pipeline check found 19 and 18 of 21 (A16).
check(mm.get(2015) == 21 and mm.get(2016) == 20, f"CR_nic mismatches: 2015 = {mm.get(2015)} (expected 21), 2016 = {mm.get(2016)} (expected 20)")

# 7. Confidential outputs derived from the quarterly returns workbook (step 09) must never be committed
gi = [l.strip() for l in (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()]
check('data/processed/confidential/' in gi, "data/processed/confidential/ is listed in .gitignore")

# 8. Returns panel (step 12; NIC quarterly returns workbook: NIC product, insurers' unaudited submissions).
# Skipped, not counted, when the workbook is absent (public pipeline = v1 results only).
skips = []
RP = CONFIDENTIAL / 'returns_panel.csv'
if QUARTERLY_FILE.exists() and RP.exists():
    R = pd.read_csv(RP, float_precision='round_trip')
    pas = R[(R.concordance == 'pass') & R.year.between(2015, 2023) & ~R.nep_source.str.startswith('not recoverable', na=False)
            & R[['claims', 'mgmt', 'comm']].notna().all(axis=1)]
    filled = R[R.annual_source == 'filled from annual']     # Q4 failed or missing (not 'components incomplete')
    ok = pas[['LR_c', 'ER_c', 'CR_c']].notna().all().all() and filled[['LR_c', 'ER_c', 'ln_assets']].isna().all().all() \
         and R.loc[R.year.between(2015, 2023) & R.in_tier1, ['LR_a', 'ER_a', 'CR_a']].notna().all().all()
    check(ok, f"returns ratios present: LR_c, ER_c, CR_c for all {len(pas)} concordance-passing 2015-23 rows with "
              f"recoverable NEP; components missing in all {len(filled)} rows filled from annual; LR_a, ER_a, CR_a for every Tier 1 row")
    nb = int((R.CR_c.notna() & (R.CR_c != R.LR_c + R.ER_c)).sum() + (R.CR_a.notna() & (R.CR_a != R.LR_a + R.ER_a)).sum())
    check(nb == 0, f"CR_c == LR_c + ER_c and CR_a == LR_a + ER_a exactly in the returns panel ({nb} rows differ)")
    # Concordance counts pinned after the authors' review of Part 2 (v2; approved): 2015-2023, 238 Tier 1 insurer-years
    t = pd.read_csv(TABLES / 'returns_concordance.csv').astype({'year': str}).set_index('year').loc['2015-2023']
    got = (int(t.concordance_pass), int(t.concordance_fail), int(t.no_q4_row), int(t.copy_forward_q4))
    check(got == (234, 3, 1, 2), f"returns concordance 2015-23: pass / fail / no Q4 row / Q4 copy-forward = {got} (pinned 234, 3, 1, 2)")
    # 9. v2 models (Part 3): additive winsorising, Mundlak = FE, exact bootstrap
    E2 = pd.read_csv(CONFIDENTIAL / 'estimation_sample_v2.csv', float_precision='round_trip')
    nb2 = int((E2.CR_w != E2.LR_w + E2.ER_w).sum())
    check(nb2 == 0, f"v2 additive winsorising: CR_w == LR_w + ER_w exactly in all {len(E2)} rows ({nb2} differ)")
    cre = pd.read_csv(TABLES / 'cre_mundlak_v2.csv')
    check(cre.max_abs_diff_within_vs_fe.max() < 1e-8,
          f"two-way Mundlak within coefficients equal models.fe for LR, ER, CR (max |diff| {cre.max_abs_diff_within_vs_fe.max():.1e})")
    # v2 headline pins (approved by the authors after the Part 3 review, 21 Nov 2026).
    # v2 methodology: assets as size, single growth measure, corrected 2015-16 ER, additive winsorising.
    # (Primary outcomes are the component-based ratios on the NEP + RIC basis; M1 = g_L1_w + RET + ln_assets_L1 + LEV_net_L1_w.)
    V2 = 'v2 (thesis, requires NIC workbook)'
    MV = pd.read_csv(TABLES / 'main_models_v2.csv')
    pins2 = {('LR_w', 'g_L1_w'): (0.0201, 0.0544), ('ER_w', 'g_L1_w'): (-0.0039, 0.0453),
             ('CR_w', 'g_L1_w'): (0.0163, 0.0908), ('ER_w', 'ln_assets_L1'): (3.5081, 10.7459)}
    for (y, t), (b0, se0) in pins2.items():
        r = MV[(MV.block == 'main') & (MV.model == 'M1') & (MV.outcome == y) & (MV.term == t)].iloc[0]
        check(abs(r.coef - b0) < 1e-3 * max(1, abs(b0)) and abs(r.se - se0) < 1e-3 * max(1, se0),
              f"{V2} pinned result M1 {y} {t}: coef {r.coef:.4f} (expected {b0}), se {r.se:.4f} (expected {se0})")
    check(len(E2) == 171 and E2.insurer_id.nunique() == 28,
          f"{V2} estimation sample: {len(E2)} insurer-years, {E2.insurer_id.nunique()} insurers (pinned 171, 28)")
else:
    skips.append("SKIP returns-panel and v2-model checks (NIC quarterly returns workbook absent: v2 not reproducible, v1 only)")
# D14 addendum: bootstrap t-statistics equal models.fe re-estimated on the bootstrap samples (5 draws, M1 CR and ER size)
mx = 0.0
for y, v in [('CR_w', 'g_L1_w'), ('ER_w', 'ln_gwp_L1')]:
    _, _, ts, Ys, d = wcb(E, y, X1, var=v, B=999, draws=5)
    mx = max(mx, max(abs(fe(d.assign(**{y: Ys[:, k]}), y, X1).tstats[v] - ts[k]) for k in range(5)))
check(mx < 1e-8, f"models.wcb bootstrap t equal models.fe on bootstrap samples (5 draws x 2 terms, max |diff| {mx:.1e})")

print("\n".join(notes + fails + skips))
print(f"\n{len(notes)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
