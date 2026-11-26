"""Experiment 1 (exploratory, pre-specified analysis plan in README.md): annual early warning of the red zone.

Red zone: CR(t) > 110 (sensitivity: CR > 100 in t and t-1). Indicators at t-1 from panel_master.csv,
training t = 2016-2020, test t = 2021-2022. Methods: (a) binary rule CR(t-1) > 110, (b) single-indicator
Youden thresholds, (c) L2 logistic composite of the top-4 training indicators. Verdict vs README section 2.
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'outputs'; OUT.mkdir(exist_ok=True)
IND = ['CR', 'ER', 'LR', 'inv_yield', 'roa', 'ln_gwp', 'g']
TRAIN, TEST = range(2016, 2021), range(2021, 2023)
B, B_STAB, SEED = 1999, 999, 1

# ---------- data: lags on the full insurer x year grid ----------
P = pd.read_csv(ROOT / 'data' / 'processed' / 'panel_master.csv')
grid = pd.MultiIndex.from_product([P.insurer_id.unique(), range(P.year.min(), P.year.max() + 1)], names=['insurer_id', 'year'])
G = P.set_index(['insurer_id', 'year']).reindex(grid)
for v in IND + ['startup']:
    G[v + '_lag'] = G.groupby(level=0)[v].shift()
G = G.reset_index()
obs = G.CR.notna() | G.gwp.notna()                   # rows that exist in the panel
for v in ['CR', 'ER', 'LR', 'g', 'ln_gwp']:          # panel's own lags must agree on those rows
    assert np.allclose(G.loc[obs, v + '_L1'], G.loc[obs, v + '_lag'], equal_nan=True), f"lag of {v} differs from panel {v}_L1"
D = G[G.year.between(2016, 2022) & G.CR.notna() & (G.startup != True) & (G.startup_lag != True)].copy()
D['red'] = (D.CR > 110).astype(int)
D['red_sens'] = ((D.CR > 100) & (D.CR_lag > 100)).astype(int).where(D.CR_lag.notna())
X = [v + '_lag' for v in IND]

# ---------- helpers ----------
def auc(y, s):
    y, s = np.asarray(y), np.asarray(s, float); r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def youden(y, s):
    """Cut-off c maximising TPR - FPR for the flag s > c (midpoints of sorted unique values).
    Ties broken towards the higher cut-off (fewer flags)."""
    y, s = np.asarray(y), np.asarray(s, float)
    u = np.unique(s); cuts = np.r_[u[0] - 1, (u[:-1] + u[1:]) / 2]
    F = s[None, :] > cuts[:, None]
    J = (F & (y == 1)).sum(1) / y.sum() - (F & (y == 0)).sum(1) / (y == 0).sum()
    return cuts[len(J) - 1 - int(np.argmax(J[::-1]))]
def flags(y, f):
    y, f = np.asarray(y), np.asarray(f, bool)
    return dict(share_flagged=f.mean(), hit_rate=(y[f].mean() if f.any() else np.nan), share_caught=f[y == 1].mean())
def boot(d, ycol, fn, B=B, seed=SEED):
    """Insurer-cluster bootstrap of fn(resampled df); redraws resamples with only one class."""
    rng = np.random.default_rng(seed); ids = d.insurer_id.unique(); ix = {i: np.flatnonzero(d.insurer_id.values == i) for i in ids}
    out, skipped = [], 0
    while len(out) < B:
        s = d.iloc[np.concatenate([ix[i] for i in rng.choice(ids, len(ids))])]
        if s[ycol].nunique() < 2: skipped += 1; continue
        out.append(fn(s))
    return np.array(out), skipped
def ci(a): return np.nanpercentile(a, [2.5, 97.5], axis=0)
def logit_l2(Z, y, lam=1.0):
    """Logistic regression, penalty (lam/2)*||slopes||^2 (sklearn C = 1 equivalent), intercept free."""
    Z1 = np.c_[np.ones(len(Z)), Z]
    def f(b):
        eta = Z1 @ b; return np.sum(np.logaddexp(0, eta) - y * eta) + lam / 2 * b[1:] @ b[1:]
    def gr(b):
        p = 1 / (1 + np.exp(-(Z1 @ b))); g = Z1.T @ (p - y); g[1:] += lam * b[1:]; return g
    r = minimize(f, np.zeros(Z1.shape[1]), jac=gr, method='BFGS'); assert r.success, r.message
    return r.x

def run(target):
    tr, te = D[D.year.isin(TRAIN) & D[target].notna()], D[D.year.isin(TEST) & D[target].notna()]
    thr, res = [], []
    # (b) single indicators: direction and Youden cut-off on training rows
    sign = {}
    for v in X:
        d = tr.dropna(subset=[v]); a = auc(d[target], d[v]); sign[v] = 1 if a >= 0.5 else -1
        c = youden(d[target].values, sign[v] * d[v].values)
        thr.append(dict(target=target, kind='single', indicator=v, direction='high = risk' if sign[v] > 0 else 'low = risk',
                        train_n=len(d), train_red=int(d[target].sum()), train_auc_adj=max(a, 1 - a), cutoff=sign[v] * c))
    T = pd.DataFrame(thr).sort_values('train_auc_adj', ascending=False)
    # (c) composite: top 4 by training AUC, never all three of CR, LR, ER
    comp = []
    for v in T.indicator:
        if len(comp) == 4: break
        if v in ('CR_lag', 'LR_lag', 'ER_lag') and sum(c in ('CR_lag', 'LR_lag', 'ER_lag') for c in comp) == 2: continue
        comp.append(v)
    trc = tr.dropna(subset=comp)
    lo, hi = trc[comp].quantile(0.01), trc[comp].quantile(0.99)
    mu, sd = trc[comp].clip(lo, hi, axis=1).mean(), trc[comp].clip(lo, hi, axis=1).std()
    Zf = lambda d: ((d[comp].clip(lo, hi, axis=1) - mu) / sd).values
    beta = logit_l2(Zf(trc), trc[target].values)
    score = lambda d: np.c_[np.ones(len(d)), Zf(d)] @ beta
    c_comp = youden(trc[target].values, score(trc))
    thr.append(dict(target=target, kind='composite', indicator='intercept', coef=beta[0], train_n=len(trc),
                    train_red=int(trc[target].sum()), cutoff=1 / (1 + np.exp(-c_comp))))
    for v, b, l, h in zip(comp, beta[1:], lo, hi):
        thr.append(dict(target=target, kind='composite', indicator=v, coef=b, winsor_lo=l, winsor_hi=h, train_mean=mu[v], train_sd=sd[v]))
    # ---------- test: primary comparison sample ----------
    S = te.dropna(subset=list(dict.fromkeys(['CR_lag'] + comp))).copy()
    S['s_comp'] = score(S)
    y = S[target].values
    base = dict(target=target, sample='primary (complete on CR_lag + composite inputs)', n=len(S), n_red=int(y.sum()), n_insurers=S.insurer_id.nunique())
    def scores(s): return [auc(s[target], s.CR_lag), auc(s[target], s.s_comp)]
    def paired(s): a = scores(s); return a + [a[1] - a[0]]
    bs, skip = boot(S, target, paired)
    (l1, l2, l3), (h1, h2, h3) = ci(bs)
    a_cr, a_comp = scores(S)
    res.append(dict(base, method='continuous CR(t-1)', auc=a_cr, ci_lo=l1, ci_hi=h1, boot_skipped=skip,
                    cutoff=T.set_index('indicator').cutoff['CR_lag'], **flags(y, S.CR_lag > T.set_index('indicator').cutoff['CR_lag'])))
    res.append(dict(base, method='composite: ' + '+'.join(comp), auc=a_comp, ci_lo=l2, ci_hi=h2, boot_skipped=skip,
                    cutoff=1 / (1 + np.exp(-c_comp)), **flags(y, S.s_comp > c_comp)))
    res.append(dict(base, method='DIFF composite - continuous CR(t-1)', auc=a_comp - a_cr, ci_lo=l3, ci_hi=h3, boot_skipped=skip))
    f = (S.CR_lag > 110).values; fl = flags(y, f)
    res.append(dict(base, method='binary rule CR(t-1) > 110', auc=(fl['share_caught'] + 1 - f[y == 0].mean()) / 2, cutoff=110, **fl))
    # ---------- test: each single indicator on its own rows ----------
    for r in T.itertuples():
        d = te.dropna(subset=[r.indicator]); sg = sign[r.indicator]
        bs, skip = boot(d, target, lambda s: auc(s[target], sg * s[r.indicator]))
        lo_, hi_ = ci(bs)
        res.append(dict(target=target, sample='own rows', n=len(d), n_red=int(d[target].sum()), n_insurers=d.insurer_id.nunique(),
                        method='single: ' + r.indicator, auc=auc(d[target], sg * d[r.indicator]), ci_lo=lo_, ci_hi=hi_,
                        boot_skipped=skip, cutoff=r.cutoff, **flags(d[target], sg * d[r.indicator] > sg * r.cutoff)))
    # ---------- stability: expanding windows 2016..E ----------
    stab = []
    for E in range(2017, 2023):
        W = D[D.year.between(2016, E) & D[target].notna()]
        for v in X:
            d = W.dropna(subset=[v]); a = auc(d[target], d[v]); sg = 1 if a >= 0.5 else -1
            c = sg * youden(d[target].values, sg * d[v].values)
            bs, skip = boot(d, target, lambda s: sg * youden(s[target].values, sg * s[v].values), B=B_STAB)
            lo_, hi_ = ci(bs)
            stab.append(dict(target=target, window_end=E, indicator=v, n=len(d), n_red=int(d[target].sum()),
                             direction='high = risk' if sg > 0 else 'low = risk', cutoff=c, ci_lo=lo_, ci_hi=hi_, boot_skipped=skip))
    St = pd.DataFrame(stab)
    ref = St[St.window_end == 2020].set_index('indicator').cutoff
    St['dev_from_2016_2020'] = St.cutoff - St.indicator.map(ref)
    crit = sorted({'CR_lag'} | {c for c in comp if c in ('CR_lag', 'LR_lag', 'ER_lag')})
    St['in_stability_criterion'] = St.indicator.isin(crit)
    stable = bool((St[St.in_stability_criterion].dev_from_2016_2020.abs() <= 10).all())
    return pd.DataFrame(res), pd.DataFrame(thr), St, dict(comp=comp, a_cr=a_cr, a_comp=a_comp, diff_ci=(l3, h3), stable=stable,
                                                          crit=crit, all_aucs=[x for x in pd.DataFrame(res).query("~method.str.startswith('DIFF') and ~method.str.startswith('binary')").auc])

R, Th, St, V = zip(*[run(t) for t in ('red', 'red_sens')])
pd.concat(R).to_csv(OUT / 'exp1_results.csv', index=False)
pd.concat(Th).to_csv(OUT / 'exp1_thresholds.csv', index=False)
pd.concat(St).to_csv(OUT / 'exp1_stability.csv', index=False)

pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30)
print(f"Rows: {len(D)} insurer-years 2016-2022 (train {D.year.isin(TRAIN).sum()}, test {D.year.isin(TEST).sum()}); "
      f"red share train {D[D.year.isin(TRAIN)].red.mean():.3f}, test {D[D.year.isin(TEST)].red.mean():.3f}")
for t, r, th, st, v in zip(('red', 'red_sens'), R, Th, St, V):
    print(f"\n===== target {t} =====")
    print(th.round(4).to_string(index=False))
    print(r.drop(columns=['target']).round(3).to_string(index=False))
    print(st[st.in_stability_criterion].drop(columns=['target']).round(2).to_string(index=False))
    if t != 'red': continue
    gain = v['a_comp'] - v['a_cr']
    if gain >= 0.05 and v['stable']: verdict = 'STRONG'
    elif v['a_cr'] >= 0.70 and gain < 0.05: verdict = 'MODERATE'
    elif all(a < 0.70 for a in v['all_aucs']): verdict = 'WEAK'
    else: verdict = 'MIXED: authors decide'
    lo, hi = v['diff_ci']
    print(f"\nVERDICT (primary target): {verdict}. Composite AUC {v['a_comp']:.3f} vs continuous CR(t-1) {v['a_cr']:.3f}: "
          f"difference {gain:+.3f}, paired 95% CI [{lo:+.3f}, {hi:+.3f}]{' -- CI INCLUDES 0' if lo <= 0 <= hi else ''}. "
          f"Thresholds stable ({', '.join(v['crit'])} within +/-10 pp): {v['stable']}.")
