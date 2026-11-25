"""Step 5: figures for the thesis (PNG, 200 dpi) in outputs/figures."""
import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from config import TABLES, FIGURES, PROCESSED
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
I=pd.read_csv(TABLES/'industry_trends.csv'); T=pd.read_csv(TABLES/'regressions.csv'); G=pd.read_csv(TABLES/'growth_quartiles.csv')
# F1
f,ax=plt.subplots(figsize=(8,4.2))
ax.axvspan(2022.5,2024.5,color='#eee'); ax.text(2023.5,84,'IFRS 17\n(not comparable)',ha='center',fontsize=8,color='#555')
ax.plot(I.year,I.NIC_pub_combined_ratio,'o-',color='#1f4e79',label='NIC published "industry average"')
ax.plot(I.year,I.CR_w,'s--',color='#c55a11',label='NWP-weighted aggregate (this study)')
ax.plot(I.year,I.CR_median,'^:',color='#548235',label='Median insurer')
ax.axhline(100,color='k',lw=.8); ax.set_ylim(80,160); ax.set_ylabel('Combined ratio (%)'); ax.set_xticks(I.year)
ax.set_title('Figure 1. Non-life combined ratio, 2015–2024: three aggregation methods',loc='left',fontsize=10)
ax.legend(frameon=False,fontsize=8,loc='upper center'); f.text(.01,.01,'Source: NIC Annual Reports 2019, 2020, 2022, 2024; authors\' computation.',fontsize=7)
f.tight_layout(rect=(0,.03,1,1)); f.savefig(FIGURES/'F1_combined_ratio_methods.png',dpi=200)
# F2 decomposition
f,ax=plt.subplots(figsize=(8,4.2)); x=I.year
ax.bar(x,I.LR_w,color='#2e75b6',label='Loss ratio (NWP-weighted)'); ax.bar(x,I.ER_w,bottom=I.LR_w,color='#f4b183',label='Expense ratio (NWP-weighted)')
ax.axhline(100,color='k',lw=.8); ax.axhline(40,color='#2e75b6',lw=.6,ls=':'); 
for xi,a,b in zip(x,I.LR_w,I.ER_w): ax.text(xi,a+b+2,f'{a+b:.0f}',ha='center',fontsize=8)
ax.set_xticks(x); ax.set_ylabel('% of net earned premium (approx.)'); ax.legend(frameon=False,fontsize=8,loc='upper right')
ax.set_title('Figure 2. Decomposition of the aggregate combined ratio: expenses dominate',loc='left',fontsize=10)
f.text(.01,.01,'Note: 2023–24 under IFRS 17. Weights = GWP × retention (NWP). Source: NIC Annual Reports; authors\' computation.',fontsize=7)
f.tight_layout(rect=(0,.03,1,1)); f.savefig(FIGURES/'F2_LR_ER_decomposition.png',dpi=200)
# F3 growth quartiles
f,ax=plt.subplots(figsize=(7,4)); 
xx=np.arange(4); ax.bar(xx-.2,G.LR,.4,label='Loss ratio',color='#2e75b6'); ax.bar(xx+.2,G.ER,.4,label='Expense ratio',color='#f4b183')
for i,(c,s) in enumerate(zip(G.CR,G.share_CR_gt100)): ax.text(i,max(G.ER)+6,f'CR {c:.0f}%\n{s:.0f}% loss-making',ha='center',fontsize=8)
ax.set_xticks(xx); ax.set_xticklabels([f"{q}\n(median {g:+.0f} pp)" for q,g in zip(G.gq,G.g_excess_L1)],fontsize=8); ax.set_ylim(0,115)
ax.set_ylabel('Ratio in year t (%)'); ax.legend(frameon=False,fontsize=8,ncol=2,loc='lower right',bbox_to_anchor=(1,1.0))
ax.set_title('Figure 3. Underwriting ratios by quartile of prior-year excess premium growth',loc='left',fontsize=10)
f.text(.01,.01,'Estimation sample 2016–2022, start-up years excluded, winsorised 1/99. Excess growth = insurer growth − year median.',fontsize=7)
f.tight_layout(rect=(0,.03,1,1)); f.savefig(FIGURES/'F3_growth_quartiles.png',dpi=200)
# F4 coefficient plot
rows=[]
for y,lab in [('LR_w','Loss ratio'),('ER_w','Expense ratio'),('CR_w','Combined ratio')]:
    for m,ml in [('M0_growth_only','Growth only'),('M1_linear','Baseline (M1)'),('M1_linear_from2017','From 2017'),('M1_laggedRET','Lagged retention')]:
        r=T[(T.model==f'{y}|{m}|cluster')&(T.term=='g_L1_w')]
        if len(r): r=r.iloc[0]; rows.append((lab,ml,r.coef*10,r.se*10))
    r=T[(T.model==f'{y[:2]}_raw_incl_startups|M1_linear|cluster')&(T.term=='g_L1')].iloc[0]; rows.append((lab,'Raw, incl. start-ups',r.coef*10,r.se*10))
C=pd.DataFrame(rows,columns=['y','spec','b','se'])
f,ax=plt.subplots(figsize=(8,4.6)); yt=[];yl=[];k=0
cols={'Loss ratio':'#2e75b6','Expense ratio':'#c55a11','Combined ratio':'#404040'}
for y in ['Loss ratio','Expense ratio','Combined ratio']:
    for _,r in C[C.y==y].iterrows():
        ax.errorbar(r.b,k,xerr=1.96*r.se,fmt='o',color=cols[y],capsize=3); yt.append(k); yl.append(f'{y}: {r.spec}'); k+=1
    k+=.7
ax.axvline(0,color='k',lw=.8); ax.set_yticks(yt); ax.set_yticklabels(yl,fontsize=8); ax.invert_yaxis()
ax.set_xlabel('Change in ratio (pp) for +10 pp prior-year premium growth, 95% CI (insurer-clustered)')
ax.set_title('Figure 4. Effect of lagged premium growth on underwriting ratios (two-way FE)',loc='left',fontsize=10)
f.tight_layout(); f.savefig(FIGURES/'F4_coefficients.png',dpi=200)
# F5 nominal vs real growth
f,ax=plt.subplots(figsize=(8,3.8)); s=I[I.year.between(2016,2023)]
P=pd.read_csv(PROCESSED/'panel_master.csv'); cpi=P.drop_duplicates('year').set_index('year').cpi_avg_yoy
real=100*((1+s.g_mkt/100)/(1+s.year.map(cpi)/100)-1)
ax.bar(s.year-.2,s.g_mkt,.4,label='Nominal GWP growth',color='#1f4e79'); ax.bar(s.year+.2,real,.4,label='Real (annual-avg CPI-deflated)',color='#a9d18e')
ax.axhline(0,color='k',lw=.8); ax.set_xticks(s.year); ax.set_ylabel('%'); ax.legend(frameon=False,fontsize=8)
ax.set_title('Figure 5. Non-life market GWP growth (excl. GOGIP): nominal vs real',loc='left',fontsize=10)
f.text(.01,.01,f"Deflator: annual-average CPI inflation, World Bank WDI FP.CPI.TOTL.ZG (orig. GSS), retrieved {P.cpi_avg_source.str.extract(r'retrieved (\d{4})')[0].dropna().iloc[0]}.",fontsize=7)
f.tight_layout(rect=(0,.04,1,1)); f.savefig(FIGURES/'F5_nominal_real_growth.png',dpi=200)


# ---------- v2 figures (methodology revision, Part 3), from aggregate v2 tables ----------
# Palette: the thesis blue/orange pair, validated (lightness, chroma, CVD separation dE 22, contrast >= 3:1); identity is
# also carried by line style / marker and direct labels, not colour alone.
BLUE, ORANGE, INK, MUTED = '#2e75b6', '#c55a11', '#333333', '#666666'
GQ2, IT2 = TABLES/'growth_quartiles_v2.csv', TABLES/'industry_trends_v2.csv'
# F3 (v2): growth quartiles; legend outside the plotting area so it cannot overlap the CR annotations
G2=pd.read_csv(GQ2); xx=np.arange(len(G2)); top=max(G2.LR.max(),G2.ER.max())
f,ax=plt.subplots(figsize=(7.2,4.4))
ax.bar(xx-.21,G2.LR,.4,label='Loss ratio',color=BLUE); ax.bar(xx+.21,G2.ER,.4,label='Expense ratio',color=ORANGE)
for i,(c,s) in enumerate(zip(G2.CR,G2.share_CR_gt100)):
    ax.text(i,top+5,f'CR {c:.0f}%\n{s:.0f}% loss-making',ha='center',va='bottom',fontsize=8,color=INK)
ax.set_xticks(xx); ax.set_xticklabels([f"{q}\n(median {g:+.0f} pp)" for q,g in zip(G2.gq,G2.g_excess_L1)],fontsize=8)
ax.set_ylim(0,top+30); ax.set_ylabel('Ratio in year t (% of NEP + RIC)'); ax.grid(axis='y',color='#e5e5e5',lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=8,ncol=2,loc='lower right',bbox_to_anchor=(1,1.0))
f.suptitle('Figure 3 (v2). Underwriting ratios by quartile of prior-year excess premium growth',x=.01,ha='left',fontsize=10)
f.text(.01,.01,'The pattern compares insurers: it reflects between-insurer differences (faster-growing insurers have lower average ratios;\n'
       'Mundlak decomposition, D18), not the effect of an insurer\'s own growth, which is nil within insurers (two-way FE).\n'
       'v2 sample 2016-2022 (171 insurer-years), start-ups excluded; component-based ratios, LR and ER winsorised 1/99, CR = LR + ER;\n'
       'excess growth = insurer growth minus the year median. Source: NIC quarterly returns (insurers\' unaudited submissions); NIC Annual Reports.',fontsize=7,color=MUTED)
f.tight_layout(rect=(0,.13,1,.95)); f.savefig(FIGURES/'F3_growth_quartiles_v2.png',dpi=200)
# RQ1 (v2): component-based vs published combined ratio, NWP-weighted, with the 2019-20 gap annotated
S=pd.read_csv(IT2); f,ax=plt.subplots(figsize=(8.2,4.4))
ax.axvspan(2022.5,2023.5,color='#f0f0f0'); ax.text(2023,86,'2023: published\nis IFRS 17',ha='center',fontsize=7,color=MUTED)
ax.plot(S.year,S.CR_component,'o-',color=BLUE,lw=2,ms=6,label='Component-based (returns, NEP + RIC basis; v2 primary)')
ax.plot(S.year,S.CR_published,'s--',color=ORANGE,lw=2,ms=6,label='Published (NIC annual reports)')
ax.axhline(100,color=INK,lw=.8)
for yr in (2019,2020):
    r=S[S.year==yr].iloc[0]
    ax.annotate('',xy=(yr,r.CR_published+1),xytext=(yr,r.CR_component-1),arrowprops=dict(arrowstyle='<->',color=INK,lw=.9))
    ax.text(yr+.08,(r.CR_component+r.CR_published)/2,f'{r.CR_component-r.CR_published:+.0f} pp',fontsize=8,color=INK,va='center')
ax.text(2020.7,151,'2019: Q4 returns differ from audited figures (A18)\n2020: published ER omits commission (A20)',
        ha='center',va='center',fontsize=7.5,color=INK)
r16=S[S.year==2016].iloc[0]   # direct labels where the two lines are well apart
ax.text(2016.12,r16.CR_component+3.5,'component',ha='left',color=INK,fontsize=8)
ax.text(2016.12,r16.CR_published-7,'published',ha='left',color=INK,fontsize=8)
ax.set_xticks(S.year); ax.set_ylim(80,160); ax.set_ylabel('Combined ratio, NWP-weighted (%)'); ax.grid(axis='y',color='#e5e5e5',lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False,fontsize=8,loc='lower left')
f.suptitle('Figure 1 (v2). Non-life combined ratio 2015-2023: component-based vs published',x=.01,ha='left',fontsize=10)
f.text(.01,.01,'All insurers incl. start-ups; weights = NWP. Component-based: returns where Q4 GWP passes concordance, published values '
       'otherwise.\nSource: NIC quarterly returns (insurers\' unaudited submissions); NIC Annual Reports 2019-2024; authors\' computation.',fontsize=7,color=MUTED)
f.tight_layout(rect=(0,.07,1,.95)); f.savefig(FIGURES/'F1_v2_combined_ratio_component_vs_published.png',dpi=200)
# ---------- v2 figures, Part 5: F2, F4, F5, F7, F8 (aggregate tables only) ----------
PURPLE = '#7a4fa0'   # third categorical slot; blue/orange/purple validated together (CVD dE >= 18.6, contrast >= 3:1)
MV, SEAS = TABLES/'main_models_v2.csv', TABLES/'seasonality.csv'
def finish(f, title, note, path, bottom=.08):
    f.suptitle(title, x=.01, ha='left', fontsize=10); f.text(.01, .01, note, fontsize=7, color=MUTED)
    f.tight_layout(rect=(0, bottom, 1, .95)); f.savefig(path, dpi=200); plt.close(f)
# F2 (v2): component-based decomposition, NWP-weighted
S = pd.read_csv(IT2); f, ax = plt.subplots(figsize=(8, 4.2)); x = S.year
ax.bar(x, S.LR_component, .8, color=BLUE, label='Loss ratio'); ax.bar(x, S.ER_component, .8, bottom=S.LR_component, color=ORANGE, label='Expense ratio')
for xi, a, b in zip(x, S.LR_component, S.ER_component): ax.text(xi, a + b + 2, f'{a + b:.0f}', ha='center', fontsize=8, color=INK)
ax.axhline(100, color=INK, lw=.8); ax.set_xticks(x); ax.set_ylim(0, 160); ax.set_ylabel('% of NEP + RIC (NWP-weighted)')
ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=8, ncol=2, loc='upper right')
finish(f, 'Figure 2 (v2). Decomposition of the aggregate combined ratio (component-based): expenses dominate',
       'Component-based ratios on the NEP + RIC basis (returns where Q4 passes concordance; published otherwise); all insurers; weights = NWP. 2023 from the\n'
       "IFRS 4 returns. Source: NIC quarterly returns (insurers' unaudited submissions); NIC Annual Reports; authors' computation.",
       FIGURES/'F2_LR_ER_decomposition_v2.png')
M = pd.read_csv(MV)
# F4 (v2): effect of +10 pp lagged growth across specifications and outcome variants
specs = [('main', 'M0_growth_only', 'component (primary)', 'Growth only (M0)'), ('main', 'M1', 'component (primary)', 'M1 (primary)'),
         ('main', 'M1b_lngwp_size', 'component (primary)', 'M1b: ln(GWP) as size'), ('main', 'M1c_reserving', 'component (primary)', 'M1c: + reserving'),
         ('outcome_variant', 'M1', 'Tier 1 published (2015-16 ER corrected)', 'Tier 1 published'),
         ('outcome_variant', 'M1', 'Tier 1 corrected 2020', 'Tier 1 corrected 2020'),
         ('outcome_variant', 'M1', 'component, excl. 2020 outcomes', 'Excl. 2020 outcomes'),
         ('outcome_variant', 'M1', 'component, excl. 2019 outcomes', 'Excl. 2019 outcomes'),
         ('robustness', 'M1', 'v1 growth measure (g_v1_L1)', 'v1 growth measure')]
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
ax.set_xlabel('Change in the ratio (pp) for +10 pp prior-year premium growth, 95% CI (insurer-clustered, D12)', fontsize=8)
ax.grid(axis='x', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
finish(f, 'Figure 4 (v2). Effect of lagged premium growth on underwriting ratios (two-way FE)',
       'v2 sample 2016-2022, start-ups excluded (171 insurer-years; excl. variants 145). Colour and marker identify the outcome (also in the labels).',
       FIGURES/'F4_coefficients_v2.png', bottom=.04)
# F7: year-specific growth slopes (RQ3 pre-trend model: g_L1 x year, base 2016) with joint tests
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
       'Two-way FE, M1 controls, g_L1 x year interactions (base 2016); tests: cluster-robust Wald, F(q, 27). Joint and equality tests from the model with\n'
       '2020-22 interactions only (base 2016-19). Wooldridge (2021), Sections 5.2 and 7. v2 sample, 171 insurer-years.',
       FIGURES/'F7_mid_year_slopes.png', bottom=.1)
# F8: seasonality of written premium (industry cumulative share by quarter)
Z = pd.read_csv(SEAS); I8 = Z[(Z.section == 'industry_cumulative_share') & (Z.statistic == 'premium')].copy()
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
ax.set_xticks([1, 2, 3, 4]); ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4']); ax.set_ylim(0, 1.05)
ax.set_ylabel('Cumulative share of full-year premium'); ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc='upper left')
finish(f, 'Figure 8. Seasonality of non-life premium: cumulative share written by quarter',
       "Insurers with figures in all four quarters, no copy-forward, not a merger year. Source: NIC quarterly returns (an NIC product; insurers'\n"
       "unaudited quarterly submissions); authors' computation.", FIGURES/'F8_seasonality.png', bottom=.08)
# F5 (v2): the market growth series is the same in v1 and v2 (audited market totals); re-rendered in the validated palette
Iv = pd.read_csv(TABLES/'industry_trends.csv'); s = Iv[Iv.year.between(2016, 2023)]
Pm = pd.read_csv(PROCESSED/'panel_master.csv'); cpi5 = Pm.drop_duplicates('year').set_index('year').cpi_avg_yoy
real = 100*((1+s.g_mkt/100)/(1+s.year.map(cpi5)/100)-1)
f, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(s.year-.21, s.g_mkt, .4, label='Nominal GWP growth', color=BLUE); ax.bar(s.year+.21, real, .4, label='Real (annual-average CPI-deflated)', color=ORANGE)
ax.axhline(0, color=INK, lw=.8); ax.set_xticks(s.year); ax.set_ylabel('%'); ax.legend(frameon=False, fontsize=8)
ax.grid(axis='y', color='#e5e5e5', lw=.6); ax.set_axisbelow(True)
finish(f, 'Figure 5 (v2). Non-life market GWP growth (excl. GOGIP): nominal vs real',
       'Audited NIC market totals (same series in v1 and v2). Deflator: annual-average CPI inflation, World Bank WDI FP.CPI.TOTL.ZG (orig. GSS).',
       FIGURES/'F5_nominal_real_growth_v2.png', bottom=.06)
