"""Step 5: the thesis figures (PNG, 200 dpi) in outputs/figures, numbered as in the thesis.

Figure 1 combined ratio, component-based vs published    Figure 5 growth quartiles
Figure 2 loss / expense decomposition                    Figure 6 coefficients across specifications
Figure 3 nominal vs real market growth                   Figure 7 year-specific MID slopes
Figure 4 seasonality of premium                          Figure 8 leave-one-insurer-out (drawn by step 10)

Built from aggregate tables only. Notes on sample, sources and inference are in the thesis captions, not in the
images. The v1 figures are frozen in outputs/figures/v1/ (not redrawn).
Palette: the thesis blue/orange pair plus purple, validated together (lightness, chroma, CVD separation dE >= 18.6,
contrast >= 3:1); identity is also carried by line style / marker and direct labels, not colour alone.
"""
import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from config import TABLES, FIGURES, PROCESSED
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
BLUE, ORANGE, PURPLE, INK, MUTED = '#2e75b6', '#c55a11', '#7a4fa0', '#333333', '#666666'

def finish(f, title, path):
    f.suptitle(title, x=.01, ha='left', fontsize=10)
    f.tight_layout(); f.savefig(path, dpi=200); plt.close(f)   # tight_layout leaves room for the suptitle itself

S = pd.read_csv(TABLES/'industry_trends_v2.csv')

# Figure 1: component-based vs published combined ratio, NWP-weighted, with the 2019-20 gap annotated
f, ax = plt.subplots(figsize=(8.2, 4.4))
ax.axvspan(2022.5, 2023.5, color='#f0f0f0'); ax.text(2023, 86, '2023: published\nis IFRS 17', ha='center', fontsize=7, color=MUTED)
ax.plot(S.year, S.CR_component, 'o-', color=BLUE, lw=2, ms=6, label='Component-based (returns, NEP + RIC basis; primary)')
ax.plot(S.year, S.CR_published, 's--', color=ORANGE, lw=2, ms=6, label='Published (NIC annual reports)')
ax.axhline(100, color=INK, lw=.8)
for yr in (2019, 2020):
    r = S[S.year == yr].iloc[0]
    ax.annotate('', xy=(yr, r.CR_published + 1), xytext=(yr, r.CR_component - 1), arrowprops=dict(arrowstyle='<->', color=INK, lw=.9))
    ax.text(yr + .08, (r.CR_component + r.CR_published) / 2, f'{r.CR_component - r.CR_published:+.0f} pp', fontsize=8, color=INK, va='center')
ax.text(2020.7, 151, '2019: Q4 returns differ from audited figures\n2020: published ER omits commission',
        ha='center', va='center', fontsize=7.5, color=INK)
r16 = S[S.year == 2016].iloc[0]   # direct labels where the two lines are well apart
ax.text(2016.12, r16.CR_component + 3.5, 'component', ha='left', color=INK, fontsize=8)
ax.text(2016.12, r16.CR_published - 7, 'published', ha='left', color=INK, fontsize=8)
ax.set_xticks(S.year); ax.set_ylim(80, 160); ax.set_ylabel('Combined ratio, NWP-weighted (%)')
ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8, loc='lower left')
finish(f, 'Figure 1. Non-life combined ratio 2015-2023: component-based vs published', FIGURES/'Figure_1_combined_ratio.png')

# Figure 2: component-based decomposition, NWP-weighted
f, ax = plt.subplots(figsize=(8, 4.2)); x = S.year
ax.bar(x, S.LR_component, .8, color=BLUE, label='Loss ratio'); ax.bar(x, S.ER_component, .8, bottom=S.LR_component, color=ORANGE, label='Expense ratio')
for xi, a, b in zip(x, S.LR_component, S.ER_component): ax.text(xi, a + b + 2, f'{a + b:.0f}', ha='center', fontsize=8, color=INK)
ax.axhline(100, color=INK, lw=.8); ax.set_xticks(x); ax.set_ylim(0, 160); ax.set_ylabel('% of NEP + RIC (NWP-weighted)')
ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8, ncol=2, loc='upper right')
finish(f, 'Figure 2. Decomposition of the aggregate combined ratio (component-based): expenses dominate',
       FIGURES/'Figure_2_loss_expense_decomposition.png')

# Figure 3: market growth, nominal vs real (audited NIC market totals)
Iv = pd.read_csv(TABLES/'industry_trends.csv'); s = Iv[Iv.year.between(2016, 2023)]
Pm = pd.read_csv(PROCESSED/'panel_master.csv'); cpi5 = Pm.drop_duplicates('year').set_index('year').cpi_avg_yoy
real = 100*((1+s.g_mkt/100)/(1+s.year.map(cpi5)/100)-1)
f, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(s.year-.21, s.g_mkt, .4, label='Nominal GWP growth', color=BLUE); ax.bar(s.year+.21, real, .4, label='Real (annual-average CPI-deflated)', color=ORANGE)
ax.axhline(0, color=INK, lw=.8); ax.set_xticks(s.year); ax.set_ylabel('%'); ax.legend(frameon=False, fontsize=8)
ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
finish(f, 'Figure 3. Non-life market GWP growth (excl. GOGIP): nominal vs real', FIGURES/'Figure_3_nominal_real_growth.png')

# Figure 4: seasonality of written premium (industry cumulative share by quarter)
Z = pd.read_csv(TABLES/'seasonality.csv'); I8 = Z[(Z.section == 'industry_cumulative_share') & (Z.statistic == 'premium')].copy()
I8['quarter'] = I8.quarter.astype(int); I8['year'] = I8.year.astype(int)
f, ax = plt.subplots(figsize=(7, 4.2))
for yr, d in I8[I8.year.between(2013, 2023)].groupby('year'): ax.plot(d.quarter, d.value, color='#c9c9c9', lw=1, zorder=1)
m = I8[I8.year.between(2015, 2023)].groupby('quarter').value.mean()
ax.plot(m.index, m.values, 'o-', color=BLUE, lw=2, ms=6, zorder=3, label='IFRS 4 average 2015-2023 (GWP)')
for q, v in m.items():
    if q < 4: ax.text(q - .06, v + .035, f'{v:.2f}', ha='right', fontsize=8, color=INK)
for yr, d in I8[I8.year >= 2024].groupby('year'):
    ax.plot(d.quarter, d.value, 's--', color=ORANGE, lw=1.4, ms=5, zorder=2, label='IFRS 17, 2024-25 (Insurance Revenue)' if yr == 2024 else None)
ax.plot([], [], color='#c9c9c9', lw=1, label='Single years 2013-2023 (GWP)')
e8 = Z[(Z.section == 'earning') & (Z.statistic == 'share_of_year_premium_earned_in_same_year')].value.iloc[0]
ax.text(3.95, .12, f"Share of a year's premium earned in the same year: {e8:.2f}\n(mid-quarter writing, 12-month policies)", ha='right', fontsize=7.5, color=INK)
ax.set_xticks([1, 2, 3, 4]); ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4']); ax.set_ylim(0, 1.05); ax.set_xlim(.6, 4.15)   # room for the Q1 label
ax.set_ylabel('Cumulative share of full-year premium'); ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc='upper left')
finish(f, 'Figure 4. Seasonality of non-life premium: cumulative share written by quarter', FIGURES/'Figure_4_seasonality.png')

# Figure 5: growth quartiles; legend outside the plotting area so it cannot overlap the CR annotations
G2 = pd.read_csv(TABLES/'growth_quartiles_v2.csv'); xx = np.arange(len(G2)); top = max(G2.LR.max(), G2.ER.max())
f, ax = plt.subplots(figsize=(7.2, 4.4))
ax.bar(xx-.21, G2.LR, .4, label='Loss ratio', color=BLUE); ax.bar(xx+.21, G2.ER, .4, label='Expense ratio', color=ORANGE)
for i, (c, sh) in enumerate(zip(G2.CR, G2.share_CR_gt100)):
    ax.text(i, top+5, f'CR {c:.0f}%\n{sh:.0f}% loss-making', ha='center', va='bottom', fontsize=8, color=INK)
ax.set_xticks(xx); ax.set_xticklabels([f"{q}\n(median {g:+.0f} pp)" for q, g in zip(G2.gq, G2.g_excess_L1)], fontsize=8)
ax.set_ylim(0, top+30); ax.set_ylabel('Ratio in year t (% of NEP + RIC)'); ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, ncol=2, loc='lower right', bbox_to_anchor=(1, 1.0))
finish(f, 'Figure 5. Underwriting ratios by quartile of prior-year excess premium growth', FIGURES/'Figure_5_growth_quartiles.png')

# Figure 6: effect of +10 pp lagged growth across specifications and outcome variants
M = pd.read_csv(TABLES/'main_models_v2.csv')
specs = [('main', 'M0_growth_only', 'component (primary)', 'Growth only (M0)'), ('main', 'M1', 'component (primary)', 'M1 (primary)'),
         ('main', 'M1b_lngwp_size', 'component (primary)', 'M1b: ln(GWP) as size'), ('main', 'M1c_reserving', 'component (primary)', 'M1c: + reserving'),
         ('outcome_variant', 'M1', 'Tier 1 published (2015-16 ER corrected)', 'Tier 1 published'),
         ('outcome_variant', 'M1', 'Tier 1 corrected 2020', 'Tier 1 corrected 2020'),
         ('outcome_variant', 'M1', 'component, excl. 2020 outcomes', 'Excl. 2020 outcomes'),
         ('outcome_variant', 'M1', 'component, excl. 2019 outcomes', 'Excl. 2019 outcomes'),
         ('robustness', 'M1', 'v1 growth measure (g_v1_L1)', 'NIC-table growth measure')]
cols = {'LR_w': (BLUE, 'o', 'Loss ratio'), 'ER_w': (ORANGE, 's', 'Expense ratio'), 'CR_w': (PURPLE, '^', 'Combined ratio')}
f, ax = plt.subplots(figsize=(8, 6)); yt, yl, k = [], [], 0
for y, (c, mk, lab) in cols.items():
    for blk, mod, var, sl in specs:
        gt = 'g_v1_L1_w' if 'v1 growth' in var else 'g_L1_w'
        r = M[(M.block == blk) & (M.model == mod) & (M.variant == var) & (M.outcome == y) & (M.term == gt)]
        if not len(r): continue
        r = r.iloc[0]; ax.errorbar(10 * r.coef, k, xerr=1.96 * 10 * r.se, fmt=mk, ms=5, color=c, capsize=2, lw=1.2)
        yt.append(k); yl.append(f'{lab}: {sl}'); k += 1
    k += .8
ax.axvline(0, color=INK, lw=.8); ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=7.5); ax.invert_yaxis()
ax.set_xlabel('Change in the ratio (pp) for +10 pp prior-year premium growth, 95% CI (insurer-clustered)', fontsize=8)
ax.grid(axis='x', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
finish(f, 'Figure 6. Effect of lagged premium growth on underwriting ratios (two-way FE)', FIGURES/'Figure_6_coefficients.png')

# Figure 7: year-specific growth slopes (RQ3 pre-trend model: g_L1 x year, base 2016) with joint tests
Tt = pd.read_csv(TABLES/'rq3_tests_v2.csv')
f, axs = plt.subplots(1, 3, figsize=(10, 3.9)); yrs = list(range(2017, 2023))
for ax, (y, (c, mk, lab)) in zip(axs, cols.items()):
    d = M[(M.block == 'rq3') & (M.model == 'RQ3_pretrend') & (M.outcome == y) & M.term.isin([f'gx{t}' for t in yrs])].set_index('term')
    b = [d.loc[f'gx{t}', 'coef'] for t in yrs]; e = [1.96 * d.loc[f'gx{t}', 'se'] for t in yrs]
    ax.axvspan(2019.5, 2022.5, color='#f0f0f0'); ax.axhline(0, color=INK, lw=.8)
    ax.errorbar(yrs, b, yerr=e, fmt=mk, color=c, ms=5, capsize=2, lw=1.2); ax.set_xticks(yrs); ax.tick_params(labelsize=7)
    pt = Tt[(Tt.outcome == y) & Tt.test.str.startswith('pre-trend')].p.iloc[0]
    jt = Tt[(Tt.outcome == y) & Tt.test.str.contains('joint')].p.iloc[0]; eq = Tt[(Tt.outcome == y) & Tt.test.str.contains('equality')].p.iloc[0]
    ax.set_title(f'{lab}\npre-trend 2017-19 = 0: p = {pt:.2f}\n2020-22 = 0: p = {jt:.2f}; equal: p = {eq:.2f}', loc='left', fontsize=8)
    ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
axs[0].set_ylabel('Extra slope on lagged growth vs 2016\n(pp of ratio per pp of growth), 95% CI', fontsize=8)
finish(f, 'Figure 7. Year-specific effect of lagged premium growth relative to 2016 (RQ3; shaded: MID period 2020-22)',
       FIGURES/'Figure_7_mid_year_slopes.png')
print('Saved: Figure_1 to Figure_7 (outputs/figures); Figure_8 is drawn by step 10')
