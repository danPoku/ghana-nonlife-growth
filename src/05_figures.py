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
P=pd.read_csv(PROCESSED/'panel_master.csv'); cpi=P.drop_duplicates('year').set_index('year').cpi_dec_yoy
real=100*((1+s.g_mkt/100)/(1+s.year.map(cpi)/100)-1)
ax.bar(s.year-.2,s.g_mkt,.4,label='Nominal GWP growth',color='#1f4e79'); ax.bar(s.year+.2,real,.4,label='Real (Dec CPI-deflated)',color='#a9d18e')
ax.axhline(0,color='k',lw=.8); ax.set_xticks(s.year); ax.set_ylabel('%'); ax.legend(frameon=False,fontsize=8)
ax.set_title('Figure 5. Non-life market GWP growth (excl. GOGIP): nominal vs real',loc='left',fontsize=10)
f.text(.01,.01,'CPI 2016–18, 2021 from GSS pending verification; 2019, 2020, 2022, 2023 as stated in NIC reports.',fontsize=7)
f.tight_layout(rect=(0,.04,1,1)); f.savefig(FIGURES/'F5_nominal_real_growth.png',dpi=200)

