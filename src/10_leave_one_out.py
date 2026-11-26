"""Step 10 (robustness): leave-one-insurer-out re-estimation of M1, v1 and v2.

Question an examiner will ask: does the headline depend on any single insurer? For each insurer in the
estimation sample, drop it and re-estimate M1 for LR_w, ER_w and CR_w with models.fe (D12 convention),
recording growth (g_L1_w) and size (v1: ln_gwp_L1; v2: ln_assets_L1).

WINSORISING: the existing _w values in the estimation sample are used unchanged. Bounds are NOT recomputed
after dropping an insurer, so each run changes only the sample, not the variable definitions.
v1: estimation_sample.csv, checked against regressions.csv -> robust_leave_one_out*.csv
(the v1 figure is frozen in outputs/figures/v1/).
v2: data/processed/estimation_sample_v2.csv, checked against main_models_v2.csv
-> robust_leave_one_out*_v2.csv (aggregate) and thesis Figure 8 (Figure_8_leave_one_out.png).
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import PROCESSED, TABLES, FIGURES
from models import fe

Ys = ['LR_w', 'ER_w', 'CR_w']
OUTCOME_LABEL = {'LR_w': 'Loss ratio', 'ER_w': 'Expense ratio', 'CR_w': 'Combined ratio'}
# Figure 8 labels: the display names used in the tables (insurer_name in panel_master.csv, step 03), except
# SAHAM_SANLAM, shown as "SanlamAllianz" to match the thesis text (the tables print "Saham / Sanlam / SanlamAllianz").
DISPLAY = pd.read_csv(PROCESSED / 'panel_master.csv').drop_duplicates('insurer_id').set_index('insurer_id').insurer_name.to_dict()
DISPLAY['SAHAM_SANLAM'] = 'SanlamAllianz'

def loo(E, X, terms, ref_coef):
    full = {}
    for y in Ys:
        r = fe(E.dropna(subset=[y] + X), y, X); full[y] = r
        for t in terms:
            c, s = ref_coef(y, t)
            assert abs(r.params[t] - c) < 1e-10 and abs(r.std_errors[t] - s) < 1e-10, f'full-sample {y} {t} differs from step 04'
    rows = []
    for y in Ys:
        d0 = E.dropna(subset=[y] + X)
        for ins in sorted(d0.insurer_id.unique()):
            r = fe(d0[d0.insurer_id != ins], y, X)
            row = dict(outcome=y, dropped=ins, n=int(r.nobs))
            for t in terms: row.update({f'{t}_coef': r.params[t], f'{t}_se': r.std_errors[t], f'{t}_p': r.pvalues[t]})
            rows.append(row)
    L = pd.DataFrame(rows); summ = []
    for y in Ys:
        d = L[L.outcome == y]
        for t in terms:
            b0 = full[y].params[t]; dev = (d[f'{t}_coef'] - b0).abs()
            summ.append(dict(outcome=y, term=t, full_coef=b0, full_p=full[y].pvalues[t], min_coef=d[f'{t}_coef'].min(),
                             max_coef=d[f'{t}_coef'].max(), runs=len(d), runs_p_lt_05=int((d[f'{t}_p'] < 0.05).sum()),
                             most_influential=d.loc[dev.idxmax(), 'dropped'], max_abs_shift=dev.max()))
    return L, pd.DataFrame(summ), full

def figure(L, full, title, path):
    """Thesis Figure 8: g_L1_w with 95% CI per dropped insurer, one panel per outcome, same insurer order in every panel.
    The full-sample estimate is the dashed line, with its value in the panel title (no floating label)."""
    ink, accent = '#333333', '#2e75b6'
    f, axs = plt.subplots(1, 3, figsize=(10.5, 7.5), sharey=True)
    order = sorted(L.dropped.unique(), key=lambda i: DISPLAY[i].lower()); ypos = {ins: i for i, ins in enumerate(order)}
    for ax, y in zip(axs, Ys):
        d = L[L.outcome == y]; yy = d.dropped.map(ypos); b0 = full[y].params['g_L1_w']
        ax.errorbar(d.g_L1_w_coef, yy, xerr=1.96 * d.g_L1_w_se, fmt='o', ms=4, color=accent, ecolor=accent, elinewidth=1, capsize=0)
        ax.axvline(b0, color=accent, lw=1, ls='--'); ax.axvline(0, color=ink, lw=.8)
        ax.set_title(f"{OUTCOME_LABEL[y]}\nfull sample {b0:+.3f} (dashed)", loc='left', fontsize=9.5)
        ax.tick_params(labelsize=7); ax.grid(axis='x', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
        for s in ('top', 'right'): ax.spines[s].set_visible(False)
    axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels([DISPLAY[i] for i in order]); axs[0].set_ylabel('Insurer dropped', fontsize=8)
    axs[0].set_ylim(len(order) - .5, -.5)
    f.supxlabel('Coefficient on lagged premium growth: pp change in the ratio per 1 pp of growth (95% CI)', fontsize=8)
    f.suptitle(title, x=.01, ha='left', fontsize=10)
    f.tight_layout(); f.savefig(path, dpi=200); plt.close(f)

pd.set_option('display.width', 200)
# ---------- v1 (public, Tier 1 only) ----------
E = pd.read_csv(PROCESSED / 'estimation_sample.csv')
T4 = pd.read_csv(TABLES / 'regressions.csv')
ref1 = lambda y, t: tuple(T4[(T4.model == f'{y}|M1_linear|cluster') & (T4.term == t)].iloc[0][['coef', 'se']])
L, S, full = loo(E, ['g_L1_w', 'RET', 'ln_gwp_L1', 'LEV_net_L1_w'], ['g_L1_w', 'ln_gwp_L1'], ref1)
L.to_csv(TABLES / 'robust_leave_one_out.csv', index=False); S.to_csv(TABLES / 'robust_leave_one_out_summary.csv', index=False)
print('v1:'); print(S.round(4).to_string(index=False))
# ---------- v2 (thesis) ----------
E2p, MV = PROCESSED / 'estimation_sample_v2.csv', TABLES / 'main_models_v2.csv'
E2 = pd.read_csv(E2p); M = pd.read_csv(MV)
ref2 = lambda y, t: tuple(M[(M.block == 'main') & (M.model == 'M1') & (M.outcome == y) & (M.term == t)].iloc[0][['coef', 'se']])
L2, S2, full2 = loo(E2, ['g_L1_w', 'RET', 'ln_assets_L1', 'LEV_net_L1_w'], ['g_L1_w', 'ln_assets_L1'], ref2)
L2.to_csv(TABLES / 'robust_leave_one_out_v2.csv', index=False); S2.to_csv(TABLES / 'robust_leave_one_out_summary_v2.csv', index=False)
figure(L2, full2, 'Figure 8. Leave-one-insurer-out: effect of lagged premium growth (M1, two-way FE)',
       FIGURES / 'Figure_8_leave_one_out.png')
print('v2:'); print(S2.round(4).to_string(index=False))
print('Saved: robust_leave_one_out*.csv, Figure_8_leave_one_out.png')
