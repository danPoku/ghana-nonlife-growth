"""Step 7: validation checks. Exits non-zero if any check fails.

Data checks confirm the extraction is faithful to NIC's own figures. Result
checks pin the headline numbers from the first validated run, so any change
to code or data that moves them is noticed and must be explained.
"""
import sys, json
import numpy as np, pandas as pd
from config import INTERIM, PROCESSED, TABLES

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
check(len(E) == 177, f"177 observations in estimation sample (found {len(E)})")
check(int(P.startup.sum()) == 10, f"10 start-up insurer-years flagged (found {int(P.startup.sum())})")
mm = P[P.cr_nic_mismatch].year.value_counts().to_dict()
check(set(mm) <= {2015, 2016, 2021}, f"CR != LR+ER only in documented years {mm}")

# 4. Headline results pinned from the first validated run
def coef(model, term):
    r = T[(T.model == model) & (T.term == term)]
    return float(r.coef.iloc[0]), float(r.se.iloc[0])
# SE pins updated 31 Oct 2026 for the clustered-SE convention change (D12): the small-sample correction now
# counts year effects but not insurer effects (nested in the insurer clusters), as in Stata xtreg/reghdfe.
# Every clustered SE fell by sqrt((N-k-G-(T-1))/(N-k-(T-1))): sqrt(138/167) = 0.909 for these M1 models.
# Previous pins: SE 0.0571, 0.0447, 0.0960, 5.657. Coefficients are unchanged.
pins = {('LR_w|M1_linear|cluster', 'g_L1_w'): (0.0225, 0.0519),
        ('ER_w|M1_linear|cluster', 'g_L1_w'): (0.0303, 0.0406),
        ('CR_w|M1_linear|cluster', 'g_L1_w'): (0.0461, 0.0873),
        ('ER_w|M1_linear|cluster', 'ln_gwp_L1'): (-11.644, 5.1425)}
for (m, t), (b0, se0) in pins.items():
    b, se = coef(m, t)
    check(abs(b - b0) < 1e-3 * max(1, abs(b0)) and abs(se - se0) < 1e-3 * max(1, se0),
          f"pinned result {m} {t}: coef {b:.4f} (expected {b0}), se {se:.4f} (expected {se0})")

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

print("\n".join(notes + fails))
print(f"\n{len(notes)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
