"""Step 10 (robustness): leave-one-insurer-out re-estimation of M1.

Question an examiner will ask: does the headline depend on any single insurer? For each insurer in the
estimation sample, drop it and re-estimate M1 for LR_w, ER_w and CR_w with models.fe (D12 convention),
recording growth (g_L1_w) and size (ln_gwp_L1, the study's positive result).

WINSORISING: the existing _w values in estimation_sample.csv are used unchanged. Bounds are NOT recomputed
after dropping an insurer, so each run changes only the sample, not the variable definitions.
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import PROCESSED, TABLES, FIGURES
from models import fe

E = pd.read_csv(PROCESSED / 'estimation_sample.csv')
X = ['g_L1_w', 'RET', 'ln_gwp_L1', 'LEV_net_L1_w']
TERMS = ['g_L1_w', 'ln_gwp_L1']
Ys = ['LR_w', 'ER_w', 'CR_w']

# full sample must reproduce step 04 (same helper, same data)
T4 = pd.read_csv(TABLES / 'regressions.csv')
full = {}
for y in Ys:
    r = fe(E.dropna(subset=[y] + X), y, X); full[y] = r
    for t in TERMS:
        ref = T4[(T4.model == f'{y}|M1_linear|cluster') & (T4.term == t)].iloc[0]
        assert abs(r.params[t] - ref.coef) < 1e-10 and abs(r.std_errors[t] - ref.se) < 1e-10, f'full-sample {y} {t} differs from step 04'

rows = []
for y in Ys:
    d0 = E.dropna(subset=[y] + X)
    for ins in sorted(d0.insurer_id.unique()):
        r = fe(d0[d0.insurer_id != ins], y, X)
        row = dict(outcome=y, dropped=ins, n=int(r.nobs))
        for t in TERMS: row.update({f'{t}_coef': r.params[t], f'{t}_se': r.std_errors[t], f'{t}_p': r.pvalues[t]})
        rows.append(row)
L = pd.DataFrame(rows)
L.to_csv(TABLES / 'robust_leave_one_out.csv', index=False)

summ = []
for y in Ys:
    d = L[L.outcome == y]
    for t in TERMS:
        b0 = full[y].params[t]; dev = (d[f'{t}_coef'] - b0).abs()
        summ.append(dict(outcome=y, term=t, full_coef=b0, full_p=full[y].pvalues[t], min_coef=d[f'{t}_coef'].min(),
                         max_coef=d[f'{t}_coef'].max(), runs=len(d), runs_p_lt_05=int((d[f'{t}_p'] < 0.05).sum()),
                         most_influential=d.loc[dev.idxmax(), 'dropped'], max_abs_shift=dev.max()))
S = pd.DataFrame(summ)
S.to_csv(TABLES / 'robust_leave_one_out_summary.csv', index=False)

# F6: g_L1_w with 95% CI per dropped insurer, one panel per outcome, same insurer order in every panel
ink, accent = '#333333', '#1f4e79'
f, axs = plt.subplots(1, 3, figsize=(10, 7.5), sharey=True)
order = sorted(L.dropped.unique())
ypos = {ins: i for i, ins in enumerate(order)}
for ax, y in zip(axs, Ys):
    d = L[L.outcome == y]; yy = d.dropped.map(ypos)
    ax.errorbar(d.g_L1_w_coef, yy, xerr=1.96 * d.g_L1_w_se, fmt='o', ms=4, color=accent, ecolor=accent, elinewidth=1, capsize=0)
    b0 = full[y].params['g_L1_w']
    ax.axvline(b0, color=accent, lw=1, ls='--'); ax.axvline(0, color=ink, lw=.8)
    ax.text(b0, -1.2, f' full sample {b0:+.3f}', color=ink, fontsize=7, va='center')
    ax.set_title(y.replace('_w', ''), loc='left', fontsize=10)
    ax.set_xlabel('Coefficient on lagged growth (pp per pp), 95% CI', fontsize=8)
    ax.tick_params(labelsize=7); ax.grid(axis='x', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels(order); axs[0].set_ylabel('Insurer dropped', fontsize=8)
axs[0].set_ylim(len(order) - .5, -1.8)
f.suptitle('Figure 6. Leave-one-insurer-out: effect of lagged premium growth (M1, two-way FE)', x=.01, ha='left', fontsize=10)
f.text(.01, .01, 'Each row re-estimates M1 without that insurer; winsorised values unchanged; insurer-clustered SEs (D12).', fontsize=7)
f.tight_layout(rect=(0, .02, 1, .97)); f.savefig(FIGURES / 'F6_leave_one_out.png', dpi=200)

pd.set_option('display.width', 200)
print(S.round(4).to_string(index=False))
print('Saved: robust_leave_one_out.csv, robust_leave_one_out_summary.csv, F6_leave_one_out.png')
