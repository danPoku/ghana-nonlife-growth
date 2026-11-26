"""Step 11 (documentation): why NIC's printed combined ratio differs from LR + ER in 2015-16 (data_issues A6, A16).

NIC defines CR = claims ratio + expense ratio in every report, yet the printed CR differs from LR + ER by more
than 1 point for most insurers in 2015 and 2016 (and for two in 2021). This step tests whether a retention
(net-vs-gross) adjustment explains the gap. Sample: insurer-years with cr_nic_mismatch == True.
  d = CR_nic - (LR + ER)
  - by year: n, median |d|, min, max
  - candidate formulas for CR_nic (r = RET/100): LR+ER; LR+ER*r; (LR+ER)*r; LR*r+ER; LR+ER/r; (LR+ER)/r,
    with R-squared (1 - SSE/SST of CR_nic) and median absolute error
  - corr(d, RET), corr(d, ER), corr(d, LR)
  - rows where the printed CR is below ER alone or LR alone (impossible under any additive definition)
Fits and correlations are reported for the 2015-16 rows (the tabulation issue) and for all mismatched rows.
Output: outputs/tables/cr_mismatch_analysis.csv (long format: section, sample, item, metric, value).
The 2015 and 2016 mismatch counts are pinned in 07_validate.py (07 runs first, so it counts from panel_master).
"""
import numpy as np, pandas as pd
from config import PROCESSED, TABLES

P = pd.read_csv(PROCESSED / 'panel_master.csv')
M = P[P.cr_nic_mismatch].copy()
assert M[['LR', 'ER', 'CR_nic']].notna().all().all(), 'mismatch row without LR, ER or CR_nic'
M['d'] = M.CR_nic - (M.LR + M.ER)
assert (M.d.abs() > 1).all() and int((((P.CR_nic - (P.LR + P.ER)).abs()) > 1).sum()) == len(M), 'flag differs from |d| > 1'

out = []
def add(section, sample, item, metric, value):
    out.append(dict(section=section, sample=sample, item=item, metric=metric, value=value))

# 1. by year (denominator: rows where LR, ER and CR_nic are all printed)
full = P.dropna(subset=['LR', 'ER', 'CR_nic']).groupby('year').size()
for y, d in M.groupby('year'):
    for k, v in dict(n_mismatched=len(d), n_comparable=int(full[y]), median_abs_d=d.d.abs().median(),
                     min_d=d.d.min(), max_d=d.d.max()).items():
        add('by_year', 'all_mismatched', str(y), k, v)

# 2-3. formula fits and correlations
samples = {'2015-2016': M[M.year.isin([2015, 2016])].dropna(subset=['RET']), 'all_mismatched': M.dropna(subset=['RET'])}
for sname, s in samples.items():
    r = s.RET / 100
    forms = {'LR+ER': s.LR + s.ER, 'LR+ER*RET/100': s.LR + s.ER * r, '(LR+ER)*RET/100': (s.LR + s.ER) * r,
             'LR*RET/100+ER': s.LR * r + s.ER, 'LR+ER/(RET/100)': s.LR + s.ER / r, '(LR+ER)/(RET/100)': (s.LR + s.ER) / r}
    sst = ((s.CR_nic - s.CR_nic.mean()) ** 2).sum()
    for f, v in forms.items():
        e = s.CR_nic - v
        add('formula_fit', sname, f, 'n', len(s))
        add('formula_fit', sname, f, 'r_squared', 1 - (e ** 2).sum() / sst)
        add('formula_fit', sname, f, 'median_abs_error', e.abs().median())
    for v in ['RET', 'ER', 'LR']:
        add('correlation', sname, f'corr(d,{v})', 'pearson', s.d.corr(s[v]))

# 4. internally impossible rows: printed CR below one of its own components
imp = M[(M.CR_nic < M.ER) | (M.CR_nic < M.LR)].sort_values(['year', 'insurer_id'])
for _, row in imp.iterrows():
    for k in ['LR', 'ER', 'CR_nic', 'RET', 'd']:
        add('impossible_rows', 'all_mismatched', f'{row.insurer_id} {int(row.year)}', k, row[k])

O = pd.DataFrame(out)
O.to_csv(TABLES / 'cr_mismatch_analysis.csv', index=False)

# printed summary
pd.set_option('display.width', 200)
by = O[O.section == 'by_year'].pivot(index='item', columns='metric', values='value')
print('Mismatched insurer-years, d = CR_nic - (LR + ER):')
print(by[['n_mismatched', 'n_comparable', 'median_abs_d', 'min_d', 'max_d']].to_string())
ff = O[(O.section == 'formula_fit') & (O.metric != 'n')].pivot_table(index='item', columns=['sample', 'metric'], values='value')
print('\nCandidate formulas for the printed CR:'); print(ff.round(3).to_string())
best = ff[('2015-2016', 'r_squared')].max()
print(f"Best R-squared (2015-16): {best:.3f} -> {'no formula fits' if best < 0 else 'a formula fits'}")
print('\nCorrelations of d:'); print(O[O.section == 'correlation'].pivot(index='item', columns='sample', values='value').round(3).to_string())
print('\nPrinted CR below ER or LR alone:'); print(imp[['insurer_id', 'year', 'LR', 'ER', 'CR_nic', 'RET']].to_string(index=False))
print('Saved: cr_mismatch_analysis.csv')
