"""Shared model helpers: two-way FE with insurer-clustered SEs (D12 convention) and the wild cluster bootstrap.

Used by step 04 (main models), step 09 (total-assets robustness) and step 10 (leave-one-insurer-out),
so every model shares one implementation.
"""
from types import SimpleNamespace
import numpy as np, pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

def fe(df,y,X,cov='clustered',time=True):
    d=df.set_index(['insurer_id','year'])
    m=PanelOLS(d[y],d[X],entity_effects=True,time_effects=time,drop_absorbed=True)
    if cov=='clustered':
        # SE convention (D12): count year effects but not insurer effects, which are nested in the insurer
        # clusters (as Stata xtreg/reghdfe; Cameron & Miller 2015). linearmodels ignores count_effects=False
        # when time_effects=True, so year effects enter as explicit dummies. Coefficients are identical;
        # r2_within is kept from the two-way fit so it still excludes the year effects.
        yrs=sorted(d.index.get_level_values(1).unique())[1:] if time else []
        D=pd.DataFrame({f'_yr{t}':(d.index.get_level_values(1)==t).astype(float) for t in yrs},index=d.index)
        r=PanelOLS(d[y],pd.concat([d[X],D],axis=1),entity_effects=True,drop_absorbed=True).fit(
            cov_type='clustered',cluster_entity=True,count_effects=False)
        X=[c for c in r.params.index if not c.startswith('_yr')]
        return SimpleNamespace(params=r.params[X],std_errors=r.std_errors[X],tstats=r.tstats[X],pvalues=r.pvalues[X],
                               nobs=r.nobs,rsquared_within=m.fit().rsquared_within)
    if cov=='dk': return m.fit(cov_type='kernel',kernel='bartlett',bandwidth=2)
    return m.fit()

def twdm(df,v):
    x=df[v]-df.groupby('insurer_id')[v].transform('mean')-df.groupby('year')[v].transform('mean')+df[v].mean(); return x

def wcb(df,y,X,var='g_L1_w',B=1999,seed=1):
    rng=np.random.default_rng(seed); d=df.dropna(subset=[y]+X).copy()
    cols=[y]+X; D=d[['insurer_id','year']+cols].copy()
    for c in cols: D[c]=twdm(D,c)
    full=sm.OLS(D[y],D[X]).fit(cov_type='cluster',cov_kwds={'groups':D.insurer_id}); t0=full.tvalues[var]
    Xr=[x for x in X if x!=var]; rest=sm.OLS(D[y],D[Xr]).fit(); fit=rest.fittedvalues; u=rest.resid
    cl=D.insurer_id.values; uc=np.unique(cl); ts=[]
    for b in range(B):
        w=dict(zip(uc,rng.choice([-1,1],len(uc)))); ys=fit+u*np.array([w[c] for c in cl])
        r=sm.OLS(ys,D[X]).fit(cov_type='cluster',cov_kwds={'groups':cl}); ts.append(r.tvalues[var])
    return float(t0), float(np.mean(np.abs(ts)>=abs(t0)))
