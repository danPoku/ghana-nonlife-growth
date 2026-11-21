"""Shared model helpers: two-way FE with insurer-clustered SEs (D12 convention) and the wild cluster bootstrap.

Used by step 04 (main models), step 09 (total-assets robustness) and step 10 (leave-one-insurer-out),
so every model shares one implementation.
"""
from types import SimpleNamespace
import numpy as np, pandas as pd
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
                               nobs=r.nobs,rsquared_within=m.fit().rsquared_within,cov=r.cov.loc[X,X],
                               n_clusters=d.index.get_level_values(0).nunique())
    if cov=='dk': return m.fit(cov_type='kernel',kernel='bartlett',bandwidth=2)
    return m.fit()

def twdm(df,v):
    """Closed-form two-way demeaning x - mean_i - mean_t + mean. Equals the two-way within transformation ONLY in a
    balanced panel (Wooldridge 2021, Section 9.1); the estimation panel is unbalanced, so use `within` for estimation.
    Kept for the descriptive within-correlation in step 04."""
    x=df[v]-df.groupby('insurer_id')[v].transform('mean')-df.groupby('year')[v].transform('mean')+df[v].mean(); return x

def dummies(df):
    """Full set of insurer dummies and year dummies (first year dropped), as a matrix."""
    return pd.concat([pd.get_dummies(df.insurer_id,dtype=float),
                      pd.get_dummies(df.year,prefix='_yr',drop_first=True,dtype=float)],axis=1).to_numpy()

def absorb(Z,M):
    """Residuals of M (vector or matrix) on Z by least squares."""
    return M-Z@np.linalg.lstsq(Z,M,rcond=None)[0]

def within(df,cols):
    """Exact two-way within transformation (Frisch-Waugh-Lovell): residuals of each column on a full set of insurer
    dummies and year dummies (first year dropped), by least squares. Valid in unbalanced panels (D14)."""
    return absorb(dummies(df),df[cols].to_numpy(float))

def wald(b,V,R,G,r=None):
    """Cluster-robust Wald test of R b = r with (b, V) from models.fe (D12 covariance). Returns (F, q, df2, p),
    F = W / q referred to F(q, G - 1), G = number of insurer clusters."""
    from scipy import stats
    R=np.atleast_2d(np.asarray(R,float)); b=np.asarray(b,float); V=np.asarray(V,float)
    dv=R@b-(np.zeros(R.shape[0]) if r is None else np.asarray(r,float))
    q=R.shape[0]; F=float(dv@np.linalg.solve(R@V@R.T,dv))/q
    return F,q,G-1,float(1-stats.f.cdf(F,q,G-1))

def wcb(df,y,X,var='g_L1_w',B=1999,seed=1,draws=0):
    """Restricted (null-imposed) wild cluster bootstrap, Rademacher weights, one sign per insurer.

    D14: y and every regressor are first partialled on insurer and year dummies by OLS (`within`), so the original
    statistic is exactly the two-way FE estimate of models.fe (the previous closed-form demeaning was exact only in a
    balanced panel; Wooldridge 2021, Section 9.1). t uses the models.fe clustered variance (D12: scale N/(N-k-(T-1)),
    no G/(G-1) factor, as linearmodels with count_effects=False and explicit year dummies), so t0 equals models.fe's t
    (asserted in 07); a constant scale does not change the p-value. Weights are drawn in the same order as before
    (one draw of G signs per replication, insurers sorted), so the change from D14 reflects the estimator only.
    D14 addendum (Part 3): every bootstrap outcome fit + u*w is re-absorbed on the insurer and year dummies before its
    t-statistic is computed, as a two-way FE re-estimation of the bootstrap sample does (sign flips are constant within
    insurer, so u*w is not orthogonal to the YEAR dummies). Bootstrap coefficients were already exact; bootstrap
    residuals, and so bootstrap t, now are too (07 checks them against models.fe re-run on bootstrap samples).
    Returns (t0, p). B=0 returns (t0, nan). draws=k also returns the first k bootstrap t, the bootstrap outcomes on the
    original scale (restricted FE fit + u*w) and the estimation rows, for that check."""
    d=df.dropna(subset=[y]+X).reset_index(drop=True)
    Z=dummies(d); W=absorb(Z,d[[y]+X].to_numpy(float)); yv,Xv=W[:,0],W[:,1:]
    N,k=Xv.shape; scale=N/(N-k-(d.year.nunique()-1))
    _,cl=np.unique(d.insurer_id.values,return_inverse=True); G=cl.max()+1
    j=X.index(var); XtXi=np.linalg.inv(Xv.T@Xv); h=Xv@XtXi[:,j]   # b_j = h'y; its cluster score is sum_g h_g'u_g
    def tstats(Y):                                                  # Y: N x R, one column per replication
        U=Y-Xv@(XtXi@(Xv.T@Y)); S=np.zeros((G,Y.shape[1])); np.add.at(S,cl,h[:,None]*U)
        return (h@Y)/np.sqrt(scale*(S**2).sum(axis=0))
    t0=float(tstats(yv[:,None])[0])
    if B==0: return t0, float('nan')
    Xr=np.delete(Xv,j,axis=1)
    fit=Xr@np.linalg.lstsq(Xr,yv,rcond=None)[0] if Xr.shape[1] else np.zeros(N); u=yv-fit
    rng=np.random.default_rng(seed); Wt=np.stack([rng.choice([-1,1],G) for _ in range(B)],axis=1)   # G x B
    ts=tstats(absorb(Z,fit[:,None]+u[:,None]*Wt[cl,:]))            # FE re-absorbed in every bootstrap sample
    p=float(np.mean(np.abs(ts)>=abs(t0)))
    if draws:
        return t0, p, ts[:draws], (d[y].to_numpy(float)-u)[:,None]+u[:,None]*Wt[cl,:draws], d
    return t0, p
