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
ax.set_ylabel('Ratio in year t (%)'); ax.legend(frameon=False,fontsize=8,loc='upper left')
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


# ---------- v2 figures (methodology revision, Part 3). Built from aggregate v2 tables; skipped if they are absent ----------
# Palette: the thesis blue/orange pair, validated (lightness, chroma, CVD separation dE 22, contrast >= 3:1); identity is
# also carried by line style / marker and direct labels, not colour alone.
BLUE, ORANGE, INK, MUTED = '#2e75b6', '#c55a11', '#333333', '#666666'
GQ2, IT2 = TABLES/'growth_quartiles_v2.csv', TABLES/'industry_trends_v2.csv'
if GQ2.exists() and IT2.exists():
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
    f.text(.01,.01,'v2 estimation sample 2016-2022 (171 insurer-years), start-up years excluded; component-based ratios, LR and ER\n'
           'winsorised 1/99, CR = LR + ER. Excess growth = insurer growth (single exact-GWP measure) minus the year median.\n'
           'Source: NIC quarterly returns (insurers\' unaudited submissions); NIC Annual Reports; authors\' computation.',fontsize=7,color=MUTED)
    f.tight_layout(rect=(0,.10,1,.95)); f.savefig(FIGURES/'F3_growth_quartiles_v2.png',dpi=200)
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
else:
    print('v2 figures skipped (v2 tables absent: NIC quarterly returns workbook not available).')
