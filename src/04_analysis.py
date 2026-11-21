import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
from linearmodels.panel import PanelOLS, RandomEffects
"""Step 4: descriptives, two-way FE models, diagnostics, wild cluster bootstrap, Anderson-Hsiao, out-of-sample check.

Outputs go to outputs/tables. Headline inference = insurer-clustered SEs + wild
cluster bootstrap (29 clusters; 28 contribute within-variation). Driscoll-Kraay SEs are reported but are
unreliable with T=7 and must not be used as headline evidence.
"""
from scipy import stats
import statsmodels.api as sm
from config import PROCESSED, TABLES, INTERIM
from models import fe, within, wcb   # shared with steps 09 and 10 (D12 SE convention)
P=pd.read_csv(PROCESSED/'panel_master.csv')
R={}
# ---------- industry trends (all years) ----------
ind=[]
for y,d in P.groupby('year'):
    w=d.dropna(subset=['LR','ER','nwp'])
    ind.append(dict(year=y,n=len(d),gwp_m=d.gwp.sum()/1e6,
      g_mkt=np.nan, LR_simple=d.LR.mean(),ER_simple=d.ER.mean(),CR_simple=d.CR.mean(),
      LR_w=np.average(w.LR,weights=w.nwp),ER_w=np.average(w.ER,weights=w.nwp),CR_w=np.average(w.CR,weights=w.nwp),
      CR_median=d.CR.median(),share_CR_gt100=(d.CR>100).mean()*100,RET_w=100*d.nwp.sum()/d.gwp[d.nwp.notna()].sum(),
      HHI=((d.ms)**2).sum(),top5_share=d.ms.nlargest(5).sum(),g_median=d.g.median()))
ind=pd.DataFrame(ind); ind['g_mkt']=ind.gwp_m.pct_change()*100
NICavg=pd.read_csv(INTERIM/'nic_long_all_vintages.csv'); NICavg=NICavg[NICavg.insurer_id=='NIC_INDUSTRY_AVG'].drop_duplicates(['variable','year']).pivot(index='year',columns='variable',values='value')
ind=ind.merge(NICavg[['combined_ratio','loss_ratio','expense_ratio']].rename(columns=lambda c:'NIC_pub_'+c),left_on='year',right_index=True,how='left')
ind.loc[ind.year==2024,'g_mkt']=np.nan
ind.to_csv(TABLES/'industry_trends.csv',index=False)
# ---------- estimation sample ----------
E=P[(P.year.between(2016,2022))].copy()
E['excl_startup']=E.startup
base=E[~E.startup].dropna(subset=['LR','ER','g_L1','RET','ln_gwp_L1','LEV_net_L1']).copy()
def wins(s,lo=.01,hi=.99):
    a,b=s.quantile([lo,hi]); return s.clip(a,b)
for v in ['LR','ER','CR','g_L1','d_ms_L1','LEV_net_L1','g_excess_L1']:
    base[v+'_w']=wins(base[v])
base['g_L1_sq_w']=base.g_L1_w**2/100
p75=base.g_excess_L1.quantile(.75); base['hi_g_w']=np.maximum(0,base.g_excess_L1_w-p75)
base['gxpost_w']=base.g_L1_w*base.post_mid
# gross-basis outcomes (data_issues A16): LR_g, ER_g winsorised on this sample; CR_g_w is their sum, not winsorised itself
for v in ['LR_g','ER_g']: base[v+'_w']=wins(base[v])
base['CR_g_w']=base.LR_g_w+base.ER_g_w
R['sample']=dict(n=len(base),insurers=int(base.insurer_id.nunique()),years=f"{base.year.min()}-{base.year.max()}",p75_excess_growth=float(p75),
  excluded_startup=int(E.startup.sum()),obs_by_year=base.year.value_counts().sort_index().to_dict())
base.to_csv(PROCESSED/'estimation_sample.csv',index=False)
# ---------- helpers ----------
def tidy(res,name):
    t=pd.DataFrame({'coef':res.params,'se':res.std_errors,'t':res.tstats,'p':res.pvalues})
    t['model']=name; t['nobs']=res.nobs; t['r2_within']=res.rsquared_within; return t
rows=[]
Ys=['LR_w','ER_w','CR_w']
ctrl=['RET','ln_gwp_L1','LEV_net_L1_w']
specs={'M1_linear':['g_L1_w']+ctrl,'M2_quadratic':['g_L1_w','g_L1_sq_w']+ctrl,'M3_piecewise':['g_L1_w','hi_g_w']+ctrl,
       'M4_mktshare':['d_ms_L1_w']+ctrl,'M5_MID_slope':['g_L1_w','gxpost_w']+ctrl}
for y in Ys:
    for s,X in specs.items():
        dd=base.dropna(subset=[y]+X)
        rows.append(tidy(fe(dd,y,X),f'{y}|{s}|cluster'))
        rows.append(tidy(fe(dd,y,X,cov='dk'),f'{y}|{s}|driscoll-kraay'))
# raw (no winsor, incl startups) sensitivity
raw=E.dropna(subset=['LR','ER','g_L1','RET','ln_gwp_L1','LEV_net_L1']).copy()
for y in ['LR','ER','CR']:
    rows.append(tidy(fe(raw,y,['g_L1','RET','ln_gwp_L1','LEV_net_L1']),f'{y}_raw_incl_startups|M1_linear|cluster'))
# sensitivity: drop 2016 (pre-2017 ratio inconsistency), lagged retention, excess growth
s2=base[base.year>=2017]
for y in Ys:
    rows.append(tidy(fe(s2,y,specs['M1_linear']),f'{y}|M1_linear_from2017|cluster'))
    rows.append(tidy(fe(base.dropna(subset=['RET_L1']),y,['g_L1_w','RET_L1','ln_gwp_L1','LEV_net_L1_w']),f'{y}|M1_laggedRET|cluster'))
    rows.append(tidy(fe(base,y,['g_L1_w'],),f'{y}|M0_growth_only|cluster'))
    rows.append(tidy(fe(base[base.year!=2020],y,specs['M5_MID_slope']),f'{y}|M5_MID_slope_ex2020|cluster'))
    # nic published CR
rows.append(tidy(fe(base.assign(CRn=wins(base.CR_nic)),'CRn',specs['M1_linear']),'CR_nic_published_w|M1_linear|cluster'))
T=pd.concat(rows); T.index.name='term'; T.reset_index().to_csv(TABLES/'regressions.csv',index=False)
# ---------- collinearity g vs d_ms after TWFE demeaning ----------
cc=base.dropna(subset=['d_ms_L1_w'])
cc=cc.reset_index(drop=True); Wc=within(cc,['g_L1_w','d_ms_L1_w'])   # exact two-way within (D14; was twdm: 0.601)
R['within_corr_g_dms']=float(np.corrcoef(Wc[:,0],Wc[:,1])[0,1])
# ---------- diagnostics on M1 for each Y ----------
diag={}
for y in Ys:
    X=specs['M1_linear']; d=base.dropna(subset=[y]+X).set_index(['insurer_id','year'])
    fe_=PanelOLS(d[y],d[X],entity_effects=True,time_effects=True).fit(cov_type='unadjusted')
    dd=d.copy(); 
    for yr in dd.index.get_level_values(1).unique()[1:]: dd[f'y{yr}']=(dd.index.get_level_values(1)==yr).astype(float)
    Xr=X+[c for c in dd.columns if c.startswith('y20')]
    import statsmodels.api as sm
    re_=RandomEffects(dd[y],sm.add_constant(dd[Xr])).fit()
    b=fe_.params[X]-re_.params[X]; V=fe_.cov.loc[X,X]-re_.cov.loc[X,X]
    try:
        H=float(b.T@np.linalg.pinv(V.values)@b); hp=1-stats.chi2.cdf(H,len(X))
    except Exception: H,hp=np.nan,np.nan
    # Wooldridge serial correlation (FD residuals regressed on lag; H0 coef=-0.5)
    fd=d.reset_index().sort_values(['insurer_id','year'])
    fdv=fd.groupby('insurer_id')[[y]+X].diff(); fdv['insurer_id']=fd.insurer_id; fdv['year']=fd.year
    fdv=fdv.dropna(); 
    bfd=sm.OLS(fdv[y],fdv[X]).fit(); fdv['e']=bfd.resid
    fdv['e_l']=fdv.groupby('insurer_id').e.shift(); f2=fdv.dropna()
    w=sm.OLS(f2.e,f2.e_l).fit(cov_type='cluster',cov_kwds={'groups':f2.insurer_id})
    wt=((w.params['e_l']+0.5)/w.bse['e_l'])**2; wp=1-stats.f.cdf(wt,1,f2.insurer_id.nunique()-1)
    # Modified Wald groupwise heteroskedasticity (Greene)
    e=fe_.resids; g=e.groupby(level=0)
    s2i=g.apply(lambda x:(x**2).mean()); Ti=g.size()
    Vi=g.apply(lambda x:((x**2-(x**2).mean())**2).sum()/(len(x)*(len(x)-1)) if len(x)>1 else np.nan)/1
    ok=(Ti>=3)&(Vi>1e-8); MW=float((((s2i-(e**2).mean())**2)/(Vi/Ti))[ok].sum()); mwp=1-stats.chi2.cdf(MW,ok.sum())
    # Pesaran CD
    ew=e.unstack(level=0); ids=ew.columns; num=0; cnt=0
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            pr=ew[[ids[i],ids[j]]].dropna()
            if len(pr)>=3 and pr.std().min()>0:
                num+=np.sqrt(len(pr))*np.corrcoef(pr.iloc[:,0],pr.iloc[:,1])[0,1]; cnt+=1
    CD=float(np.sqrt(2/cnt)*num) if cnt else np.nan; cdp=2*(1-stats.norm.cdf(abs(CD)))
    diag[y]=dict(hausman_chi2=H,hausman_p=hp,wooldridge_F=float(wt),wooldridge_p=float(wp),modwald_chi2=MW,modwald_p=float(mwp),pesaran_CD=CD,pesaran_p=float(cdp))
R['diagnostics_M1']=diag
# ---------- wild cluster bootstrap (WCR, Rademacher) for g_L1 in M1 ----------
R['wild_cluster_bootstrap']={}
for y in Ys:
    for s,v in [('M1_linear','g_L1_w'),('M2_quadratic','g_L1_sq_w'),('M3_piecewise','hi_g_w'),('M5_MID_slope','gxpost_w')]:
        t0,p=wcb(base,y,specs[s],var=v,B=999)
        R['wild_cluster_bootstrap'][f'{y}|{s}|{v}']=dict(t=t0,p_wcb=p)
# ---------- dynamic check: Anderson-Hsiao FD-IV ----------
from linearmodels.iv import IV2SLS
dyn={}
D0=P[(P.year.between(2016,2022))&(~P.startup)].copy().sort_values(['insurer_id','year'])
for y in ['LR','ER','CR']:
    d=D0.copy()
    for v in [y,'g_L1','RET','ln_gwp_L1','LEV_net_L1']: d[v]=wins(d[v])
    d['dY']=d.groupby('insurer_id')[y].diff(); d['dYl']=d.groupby('insurer_id')['dY'].shift()
    d['Yl2']=d.groupby('insurer_id')[y].shift(2)
    for v in ['g_L1','RET','ln_gwp_L1','LEV_net_L1']: d['d_'+v]=d.groupby('insurer_id')[v].diff()
    d=d.dropna(subset=['dY','dYl','Yl2','d_g_L1','d_RET','d_ln_gwp_L1','d_LEV_net_L1'])
    yd=pd.get_dummies(d.year,prefix='y',drop_first=True).astype(float)
    exog=pd.concat([d[['d_g_L1','d_RET','d_ln_gwp_L1','d_LEV_net_L1']],yd],axis=1); exog['const']=1
    r=IV2SLS(d.dY,exog,d[['dYl']],d[['Yl2']]).fit(cov_type='clustered',clusters=d.insurer_id)
    fs=r.first_stage.diagnostics
    dyn[y]=dict(n=int(r.nobs),rho=float(r.params['dYl']),rho_p=float(r.pvalues['dYl']),g=float(r.params['d_g_L1']),g_se=float(r.std_errors['d_g_L1']),g_p=float(r.pvalues['d_g_L1']),first_stage_F=float(fs['f.stat'].iloc[0]))
R['anderson_hsiao']=dyn
# ---------- persistence ----------
R['persistence']={y:float(base[[y,y.replace('_w','')+'_L1']].dropna().corr().iloc[0,1]) for y in ['LR_w','ER_w','CR_w']}
# ---------- correlation matrix ----------
cm=base[['LR_w','ER_w','CR_w','g_L1_w','d_ms_L1_w','RET','ln_gwp_L1','LEV_net_L1_w']].corr().round(3); cm.to_csv(TABLES/'correlations.csv')
# ---------- descriptives ----------
desc=base[['LR','ER','CR','g_L1','g_excess_L1','d_ms_L1','RET','ln_gwp_L1','LEV_net_L1']].describe(percentiles=[.25,.5,.75]).T.round(2); desc.to_csv(TABLES/'descriptives.csv')
# ---------- growth-quartile profile (RQ2 intuition) ----------
base['gq']=pd.qcut(base.g_excess_L1,4,labels=['Q1 lowest','Q2','Q3','Q4 highest'])
gq=base.groupby('gq',observed=True).agg(n=('LR','size'),g_excess_L1=('g_excess_L1','median'),LR=('LR_w','mean'),ER=('ER_w','mean'),CR=('CR_w','mean'),share_CR_gt100=('CR_w',lambda s:(s>100).mean()*100)).round(1)
gq.to_csv(TABLES/'growth_quartiles.csv')
# ---------- out-of-sample 2023-24 (descriptive, IFRS 17) ----------
oos={}
for y in ['LR','ER','CR']:
    X=specs['M1_linear']; d=base.dropna(subset=[y+'_w']+X).set_index(['insurer_id','year'])
    m=PanelOLS(d[y+'_w'],d[X],entity_effects=True,time_effects=True).fit()
    fx=m.estimated_effects.groupby(level=0).first().iloc[:,0]  # combined effects approx
    T2=P[(P.year.isin([2023,2024]))&(~P.startup)].dropna(subset=[y,'g_L1','RET','ln_gwp_L1']).copy()
    T2['LEV_net_L1_w']=base.LEV_net_L1_w.median(); T2['g_L1_w']=T2.g_L1.clip(base.g_L1.quantile(.01),base.g_L1.quantile(.99))
    dfit=d.reset_index(); xb=(dfit[X]*m.params[X]).sum(axis=1); alpha=(dfit[y+'_w']-xb).groupby(dfit.insurer_id).mean()
    T2=T2[T2.insurer_id.isin(alpha.index)]
    pred=T2.insurer_id.map(alpha)+(T2[X]*m.params[X]).sum(axis=1)
    oos[y]=dict(n=len(T2),spearman_rank_pred_vs_actual=float(stats.spearmanr(pred,T2[y]).correlation),
       hi_growth_median=float(T2[T2.g_L1>T2.g_L1.quantile(.75)][y].median()),rest_median=float(T2[T2.g_L1<=T2.g_L1.quantile(.75)][y].median()))
R['out_of_sample_2023_24']=oos
json.dump(R,open(TABLES/'results_summary.json','w'),indent=1,default=str)


# ---------- MDE & CI interpretation ----------
mde={}
T=pd.read_csv(TABLES/'regressions.csv')
for y in Ys:
    r=T[(T.model==f'{y}|M1_linear|cluster')&(T.term=='g_L1_w')].iloc[0]
    mde[y]=dict(coef=r.coef,se=r.se,ci95=[r.coef-1.96*r.se,r.coef+1.96*r.se],effect_of_10pp_growth_ci=[10*(r.coef-1.96*r.se),10*(r.coef+1.96*r.se)],mde_80pct_power_per_10pp=10*2.8*r.se)
R['mde']=mde
json.dump(R,open(TABLES/'results_summary.json','w'),indent=1,default=str)
print(f"Estimation sample: {R['sample']['n']} obs, {R['sample']['insurers']} insurers. Results in outputs/tables.")

# ---------- v2 main models (methodology revision, Part 3): src/models_v2.py, skipped without the NIC workbook ----------
import models_v2
models_v2.run()

# ====================================================================================================
# Gross-basis robustness (supervisor comment: ER over NET earned premium may be inflated for low-retention
# insurers). See data_issues A16 and the step 03 docstring. Everything above is unchanged; this section only
# adds robust_gross_basis.csv, industry_trends_gross.csv and er_ret_correlation.csv.
# LR_g = LR x RET/100 etc. are understated by NEP/(NEP+RIC). RET stays a control, but it now also enters the
# outcome's construction, so every gross-basis model is estimated with and without RET.
# ====================================================================================================
def gb_rows(res,dd,label,outcome,ret_ctrl,wcb_p):
    out=[]
    for t in res.params.index:
        b,se=float(res.params[t]),float(res.std_errors[t])
        out.append(dict(model=label,outcome=outcome,RET_control=ret_ctrl,term=t,coef=b,se=se,p_cluster=float(res.pvalues[t]),
                        p_wcb=wcb_p.get(t,np.nan),ci95_lo=b-1.96*se,ci95_hi=b+1.96*se,n=int(res.nobs),insurers=int(dd.insurer_id.nunique())))
    return out
gb=[]
gspecs={'M1_linear':['g_L1_w'],'M3_piecewise':['g_L1_w','hi_g_w'],'M5_MID_slope':['g_L1_w','gxpost_w']}
for y in ['LR_g_w','ER_g_w','CR_g_w']:
    for ret_ctrl in (True,False):
        cx=(['RET'] if ret_ctrl else [])+['ln_gwp_L1','LEV_net_L1_w']
        for s,gt in gspecs.items():
            X=gt+cx; dd=base.dropna(subset=[y]+X)
            boot=gt+(['ln_gwp_L1'] if y=='ER_g_w' else [])   # size bootstrapped in the ER_g fits (question 2)
            gb+=gb_rows(fe(dd,y,X),dd,s,y,ret_ctrl,{v:wcb(dd,y,X,var=v,B=999)[1] for v in boot})
# net-basis references and the two sensitivities for the 2015-16 tabulation issue (M1, RET controlled).
# These coefficients already exist in regressions.csv (clustered only); here they gain WCB p-values and CIs.
X=specs['M1_linear']
sens=[('M1_linear (net baseline)',y,base,y) for y in Ys]+[
      ('M1_linear (NIC printed CR, winsorised)','CR_nic_w',base.assign(CR_nic_w=wins(base.CR_nic)),'CR_nic_published_w|M1_linear|cluster'),
      ('M1_linear (2017-2022 only)','CR_w',base[base.year>=2017],'CR_w|M1_linear_from2017|cluster')]
for label,y,dd,ref in sens:
    dd=dd.dropna(subset=[y]+X); r=fe(dd,y,X)
    refm=ref if '|' in ref else f'{ref}|M1_linear|cluster'
    for t in X:
        e=T[(T.model==refm)&(T.term==t)].iloc[0]
        assert abs(r.params[t]-e.coef)<1e-10 and abs(r.std_errors[t]-e.se)<1e-10, f'{label} {t} differs from regressions.csv'
    p=R['wild_cluster_bootstrap'][f'{y}|M1_linear|g_L1_w']['p_wcb'] if y in Ys and 'baseline' in label else wcb(dd,y,X,var='g_L1_w',B=999)[1]
    gb+=gb_rows(r,dd,label,y,True,{'g_L1_w':p})
GB=pd.DataFrame(gb); GB.to_csv(TABLES/'robust_gross_basis.csv',index=False)

# ---------- industry series on the gross basis (all insurers incl. start-ups, as industry_trends.csv) ----------
# Same rows as the net NWP-weighted series (LR, ER and RET present). GWP-weighted ER_g = NWP-weighted ER x
# aggregate retention. 2023-24 (IFRS 17): ER is already over gross Insurance Revenue, so it is used as printed
# and only LR is converted (LR x RET/100); 2024 weights are Insurance Revenue (the 'gwp' column).
ig=[]
for yr,d in P.groupby('year'):
    w=d.dropna(subset=['LR','ER','nwp']).copy()
    if yr<=2022: w['lrg'],w['erg'],basis=w.LR_g,w.ER_g,'IFRS 4: LR x RET/100, ER x RET/100'
    else: w['lrg'],w['erg'],basis=w.LR*w.RET/100,w.ER,'IFRS 17: LR x RET/100, ER as printed (already gross)'
    row=dict(year=yr,n=len(w),basis=basis,RET_agg=100*w.nwp.sum()/w.gwp.sum(),
             LR_net_nwpw=np.average(w.LR,weights=w.nwp),ER_net_nwpw=np.average(w.ER,weights=w.nwp),CR_net_nwpw=np.average(w.CR,weights=w.nwp))
    for wn,wt in (('gwpw',w.gwp),('nwpw',w.nwp)):
        lr,er=np.average(w.lrg,weights=wt),np.average(w.erg,weights=wt)
        row.update({f'LR_g_{wn}':lr,f'ER_g_{wn}':er,f'CR_g_{wn}':lr+er,f'ER_minus_LR_g_{wn}':er-lr,f'ER_over_LR_g_{wn}':er/lr})
    ig.append(row)
IG=pd.DataFrame(ig)
chk=IG.merge(ind[['year','LR_w','ER_w','CR_w']],on='year')
assert np.allclose(chk[['LR_net_nwpw','ER_net_nwpw','CR_net_nwpw']].values,chk[['LR_w','ER_w','CR_w']].values), 'net series differs from industry_trends.csv'
IG.to_csv(TABLES/'industry_trends_gross.csv',index=False)

# ---------- between-insurer check: does ER rise with retention (net basis) and ER_g? ----------
# Headline = WITHOUT start-ups (consistent with the estimation sample). With start-ups, Pearson is driven by
# SERENE 2018 (ER 10,950% on GHS 1.0m GWP), shown by the extra row that drops only that observation.
cr=[]
for a,b in [(2017,2019),(2017,2022)]:
    W0=P[P.year.between(a,b)].dropna(subset=['ER','ER_g','RET'])
    for samp,W,head in [('excl_startups',W0[~W0.startup],True),('incl_startups',W0,False),
                        ('incl_startups_excl_SERENE_2018',W0[~((W0.insurer_id=='SERENE')&(W0.year==2018))],False)]:
        cr.append(dict(window=f'{a}-{b}',sample=samp,headline=head,n=len(W),
                       pearson_ER_RET=W.ER.corr(W.RET),spearman_ER_RET=W.ER.corr(W.RET,method='spearman'),
                       pearson_ERg_RET=W.ER_g.corr(W.RET),spearman_ERg_RET=W.ER_g.corr(W.RET,method='spearman')))
CRR=pd.DataFrame(cr); CRR.to_csv(TABLES/'er_ret_correlation.csv',index=False)

pd.set_option('display.width',220)
print('\nGross basis: growth and size terms (robust_gross_basis.csv)')
print(GB[GB.term.isin(['g_L1_w','hi_g_w','gxpost_w','ln_gwp_L1'])][['model','outcome','RET_control','term','coef','se','p_cluster','p_wcb','n']].round(4).to_string(index=False))
print('\nIndustry series, gross basis (industry_trends_gross.csv)')
print(IG[['year','n','LR_net_nwpw','ER_net_nwpw','LR_g_gwpw','ER_g_gwpw','CR_g_gwpw','ER_over_LR_g_gwpw','LR_g_nwpw','ER_g_nwpw','ER_over_LR_g_nwpw']].round(2).to_string(index=False))
print('\nER vs RET across insurer-years (er_ret_correlation.csv; headline = excl. start-ups)')
print(CRR.round(3).to_string(index=False))
