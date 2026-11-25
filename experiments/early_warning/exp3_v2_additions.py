"""Experiment 3 (exploratory): v2 additions 4a-4e, pre-registered in README.md section 5 (commit 3eef056, pushed
before this script was written). Implements section 5 as written; anything that had to change is in section 6.

Data: data/processed/panel_v2.csv, returns_quarterly.csv, returns_panel.csv (pipeline steps 12 and 03;
the NIC quarterly returns workbook is an NIC product and its figures are insurers' unaudited quarterly submissions) and
data/processed/panel_master.csv. Helpers (AUC, Youden, flags, insurer bootstrap, L2 logit) are copied unchanged from
exp1_annual.py so the estimators are identical.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / 'data' / 'processed'
OUT = Path(__file__).resolve().parent / 'outputs'
TRAIN, TEST = range(2016, 2021), range(2021, 2023)
B, SEED = 1999, 1

# ---------- helpers copied from exp1_annual.py ----------
def auc(y, s):
    y, s = np.asarray(y), np.asarray(s, float); r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def youden(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    u = np.unique(s); cuts = np.r_[u[0] - 1, (u[:-1] + u[1:]) / 2]
    F = s[None, :] > cuts[:, None]
    J = (F & (y == 1)).sum(1) / y.sum() - (F & (y == 0)).sum(1) / (y == 0).sum()
    return cuts[len(J) - 1 - int(np.argmax(J[::-1]))]
def flags(y, f):
    y, f = np.asarray(y), np.asarray(f, bool)
    return dict(share_flagged=f.mean(), hit_rate=(y[f].mean() if f.any() else np.nan), share_caught=f[y == 1].mean())
def boot(d, ycol, fn, B=B, seed=SEED):
    rng = np.random.default_rng(seed); ids = d.insurer_id.unique(); ix = {i: np.flatnonzero(d.insurer_id.values == i) for i in ids}
    out, skipped = [], 0
    while len(out) < B:
        s = d.iloc[np.concatenate([ix[i] for i in rng.choice(ids, len(ids))])]
        if s[ycol].nunique() < 2: skipped += 1; continue
        out.append(fn(s))
    return np.array(out), skipped
def ci(a): return np.nanpercentile(a, [2.5, 97.5], axis=0)
def logit_l2(Z, y, lam=1.0):
    Z1 = np.c_[np.ones(len(Z)), Z]
    def f(b):
        eta = Z1 @ b; return np.sum(np.logaddexp(0, eta) - y * eta) + lam / 2 * b[1:] @ b[1:]
    def gr(b):
        p = 1 / (1 + np.exp(-(Z1 @ b))); g = Z1.T @ (p - y); g[1:] += lam * b[1:]; return g
    r = minimize(f, np.zeros(Z1.shape[1]), jac=gr, method='BFGS'); assert r.success, r.message
    return r.x

# ---------- data on the full insurer x year grid (a gap year gives a missing lag) ----------
V = pd.read_csv(PROC / 'panel_v2.csv'); Qr = pd.read_csv(PROC / 'returns_quarterly.csv'); Rp = pd.read_csv(PROC / 'returns_panel.csv')
V = V.merge(Rp[['insurer_id', 'year', 'n_quarters_no_figures']], on=['insurer_id', 'year'], how='left')
q2 = Qr[Qr.quarter == 2].merge(Qr[Qr.quarter == 1][['insurer_id', 'year', 'gwp']].rename(columns={'gwp': 'gwp_q1'}),
                               on=['insurer_id', 'year'], how='left')
# 4b quality checks (i)-(iv) on each Q2 return
q2['q2_ok'] = q2.has_figures & ~q2.flag_copy_forward & q2.NEP_RIC.notna() & q2[['claims', 'mgmt', 'comm']].notna().all(axis=1) \
              & q2.CR_c.notna() & (q2.gwp > 0) & ~(q2.gwp < q2.gwp_q1)
V = V.merge(q2[['insurer_id', 'year', 'CR_c', 'gwp', 'q2_ok']].rename(columns={'CR_c': 'q2cr', 'gwp': 'q2gwp'}),
            on=['insurer_id', 'year'], how='left')
grid = pd.MultiIndex.from_product([V.insurer_id.unique(), range(V.year.min(), V.year.max() + 1)], names=['insurer_id', 'year'])
G = V.set_index(['insurer_id', 'year']).reindex(grid)
for v in ['CR_corr2020', 'CR_t1', 'CR', 'g', 'g_v1', 'startup', 'merger_break', 'concordance', 'n_quarters_no_figures',
          'q2cr', 'q2gwp', 'q2_ok']:
    G[v + '_lag'] = G.groupby(level=0)[v].shift()
G = G.reset_index()
D = G[G.year.between(2016, 2022) & G.CR_corr2020.notna() & (G.startup != True) & (G.startup_lag != True)].copy()
D['red'] = (D.CR_corr2020 > 110).astype(int)            # primary target (both v2 corrections)
D['red_s'] = (D.CR_t1 > 110).astype(int)               # sensitivity target (2015-16 correction only)
D['CRlag_p'] = D.CR_corr2020_lag; D['CRlag_s'] = D.CR_t1_lag
qual = (D.q2_ok == True) & (D.q2_ok_lag == True) & (D.concordance_lag == 'pass')          # checks (i)-(v)
D['dQ2CR'] = np.where(qual, D.q2cr - D.q2cr_lag, np.nan)
D['gQ2'] = np.where(qual & (D.merger_break != True) & (D.merger_break_lag != True), 100 * (D.q2gwp / D.q2gwp_lag - 1), np.nan)
D['nsub_lag'] = D.n_quarters_no_figures_lag
tr_all, te_all = D[D.year.isin(TRAIN)], D[D.year.isin(TEST)]
res = []
def row(**k): res.append(k)

for tgt, crl, lab in [('red', 'CRlag_p', 'primary (CR_corr2020)'), ('red_s', 'CRlag_s', 'sensitivity (CR_t1)')]:
    tr, te = tr_all, te_all
    # ---------- 4a: CR(t-1) vs growth(t-1), both growth measures, paired on the same test rows ----------
    sg = {}
    for gv in ['g_lag', 'g_v1_lag']:
        d = tr.dropna(subset=[gv]); sg[gv] = 1 if auc(d[tgt], d[gv]) >= 0.5 else -1
    S = te.dropna(subset=[crl, 'g_lag', 'g_v1_lag'])
    def f4a(s):
        a = auc(s[tgt], s[crl]); b2 = auc(s[tgt], sg['g_lag'] * s.g_lag); b1 = auc(s[tgt], sg['g_v1_lag'] * s.g_v1_lag)
        return [a, b2, b1, a - b2, a - b1]
    bs, sk = boot(S, tgt, f4a); lo, hi = ci(bs); pt = f4a(S)
    names = ['CR(t-1)', 'growth v2 (g_L1)', 'growth v1 (g_v1_L1)', 'DIFF CR(t-1) - growth v2', 'DIFF CR(t-1) - growth v1']
    for i, nm in enumerate(names):
        row(item='4a', target=lab, method=nm, n=len(S), n_red=int(S[tgt].sum()), n_insurers=S.insurer_id.nunique(), auc=pt[i],
            ci_lo=lo[i], ci_hi=hi[i], boot_redrawn=sk,
            direction=('high = risk' if sg.get({1: 'g_lag', 2: 'g_v1_lag'}.get(i), 1) > 0 else 'low = risk') if i in (1, 2) else '',
            readout=('growth carries less warning value than CR(t-1)' if lo[i] > 0 else 'no detectable difference') if i == 3 else '')
    # ---------- 4b: quarterly indicators ----------
    d = te.dropna(subset=['dQ2CR']); dtr = tr.dropna(subset=['dQ2CR'])
    c = youden(dtr[tgt].values, dtr.dQ2CR.values)                                   # direction fixed: higher = riskier
    bs, sk = boot(d, tgt, lambda s: auc(s[tgt], s.dQ2CR)); lo, hi = ci(bs)
    row(item='4b', target=lab, method='dQ2CR (higher = riskier, pre-specified)', n=len(d), n_red=int(d[tgt].sum()),
        n_insurers=d.insurer_id.nunique(), auc=auc(d[tgt], d.dQ2CR), ci_lo=lo, ci_hi=hi, boot_redrawn=sk, cutoff=c,
        **flags(d[tgt], d.dQ2CR > c))
    d = te.dropna(subset=['gQ2']); dtr = tr.dropna(subset=['gQ2'])
    sgq = 1 if auc(dtr[tgt], dtr.gQ2) >= 0.5 else -1; cq = sgq * youden(dtr[tgt].values, sgq * dtr.gQ2.values)
    bs, sk = boot(d, tgt, lambda s: auc(s[tgt], s.gQ2)); lo, hi = ci(bs); a = auc(d[tgt], d.gQ2)
    row(item='4b', target=lab, method='gQ2 (two-sided; AUC with higher growth = riskier)', n=len(d), n_red=int(d[tgt].sum()),
        n_insurers=d.insurer_id.nunique(), auc=a, ci_lo=lo, ci_hi=hi, boot_redrawn=sk, cutoff=cq,
        direction='flags: ' + ('high = risk' if sgq > 0 else 'low = risk') + ' (training)',
        readout='faster growth signals higher risk' if lo > .5 else 'faster growth signals lower risk' if hi < .5 else 'no detectable signal',
        **flags(d[tgt], sgq * d.gQ2 > sgq * cq))
    # ---------- 4c: incremental test on the rows meeting model B's requirements ----------
    def fit_score(cols, trd):
        lo_, hi_ = trd[cols].quantile(.01), trd[cols].quantile(.99)
        mu, sd = trd[cols].clip(lo_, hi_, axis=1).mean(), trd[cols].clip(lo_, hi_, axis=1).std()
        Zf = lambda dd: ((dd[cols].clip(lo_, hi_, axis=1) - mu) / sd).values
        b = logit_l2(Zf(trd), trd[tgt].values); return lambda dd: np.c_[np.ones(len(dd)), Zf(dd)] @ b, b
    for mlab, extra in [('B: CR(t-1) + dQ2CR', ['dQ2CR']), ('C: CR(t-1) + dQ2CR + gQ2 (secondary)', ['dQ2CR', 'gQ2'])]:
        req = [crl] + extra
        trd, ted = tr.dropna(subset=req).copy(), te.dropna(subset=req).copy()
        sA, bA = fit_score([crl], trd); sB, bB = fit_score(req, trd)
        ted['sA'], ted['sB'] = sA(ted), sB(ted)
        f4c = lambda s: [auc(s[tgt], s.sA), auc(s[tgt], s.sB), auc(s[tgt], s.sB) - auc(s[tgt], s.sA)]
        bs, sk = boot(ted, tgt, f4c); lo, hi = ci(bs); pt = f4c(ted)
        base = dict(item='4c', target=lab, n=len(ted), n_red=int(ted[tgt].sum()), n_insurers=ted.insurer_id.nunique(),
                    n_train=len(trd), boot_redrawn=sk)
        row(**base, method=f'A: CR(t-1) [on {mlab[0]} rows]', auc=pt[0], ci_lo=lo[0], ci_hi=hi[0], coefs=str(np.round(bA, 4).tolist()))
        row(**base, method=mlab, auc=pt[1], ci_lo=lo[1], ci_hi=hi[1], coefs=str(np.round(bB, 4).tolist()))
        verdict = 'ADDS INFORMATION' if (pt[2] >= 0.03 and lo[2] > 0) else 'DOES NOT ADD INFORMATION'
        row(**base, method=f'DIFF {mlab[0]} - A', auc=pt[2], ci_lo=lo[2], ci_hi=hi[2],
            readout=verdict + ('' if mlab.startswith('B') and tgt == 'red' else ' (not decisive)'))
        ted.assign(model=mlab, target=lab)[['insurer_id', 'year', 'model', 'target', tgt, crl] + extra + ['sA', 'sB']] \
            .to_csv(OUT / f"exp3_4c_scores_{tgt}_{mlab[0]}.csv", index=False)
    # ---------- 4d: non-submission in t-1 (exploratory) ----------
    d = te.dropna(subset=['nsub_lag'])
    bs, sk = boot(d, tgt, lambda s: auc(s[tgt], s.nsub_lag)); lo, hi = ci(bs)
    row(item='4d', target=lab, method='quarters without figures in t-1 (higher = riskier, pre-specified)', n=len(d),
        n_red=int(d[tgt].sum()), n_insurers=d.insurer_id.nunique(), auc=auc(d[tgt], d.nsub_lag), ci_lo=lo, ci_hi=hi,
        boot_redrawn=sk, cutoff=0.5, **flags(d[tgt], d.nsub_lag >= 1))

# ---------- 4a on the Experiment 1 (v1) data: published CR, v1 growth ----------
P = pd.read_csv(ROOT / 'data' / 'processed' / 'panel_master.csv')
g1 = pd.MultiIndex.from_product([P.insurer_id.unique(), range(P.year.min(), P.year.max() + 1)], names=['insurer_id', 'year'])
H = P.set_index(['insurer_id', 'year']).reindex(g1)
for v in ['CR', 'g', 'startup']: H[v + '_lag'] = H.groupby(level=0)[v].shift()
H = H.reset_index(); H = H[H.year.between(2016, 2022) & H.CR.notna() & (H.startup != True) & (H.startup_lag != True)].copy()
H['red'] = (H.CR > 110).astype(int)
d = H[H.year.isin(TRAIN)].dropna(subset=['g_lag']); s1 = 1 if auc(d.red, d.g_lag) >= .5 else -1
S = H[H.year.isin(TEST)].dropna(subset=['CR_lag', 'g_lag'])
f = lambda s: [auc(s.red, s.CR_lag), auc(s.red, s1 * s.g_lag), auc(s.red, s.CR_lag) - auc(s.red, s1 * s.g_lag)]
bs, sk = boot(S, 'red', f); lo, hi = ci(bs); pt = f(S)
for i, nm in enumerate(['CR(t-1)', 'growth v1', 'DIFF CR(t-1) - growth v1']):
    row(item='4a (Exp 1 v1 data)', target='Exp 1: published CR > 110', method=nm, n=len(S), n_red=int(S.red.sum()),
        n_insurers=S.insurer_id.nunique(), auc=pt[i], ci_lo=lo[i], ci_hi=hi[i], boot_redrawn=sk,
        readout=('growth carries less warning value than CR(t-1)' if lo[i] > 0 else 'no detectable difference') if i == 2 else '')
Rs = pd.DataFrame(res); Rs.to_csv(OUT / 'exp3_results.csv', index=False)

# ---------- 4e: IFRS 17 recalibration demonstration (descriptive) ----------
pub = P[['insurer_id', 'year', 'CR', 'gwp', 'startup']].copy()
wb = Rp[Rp.year.isin([2024, 2025])][['insurer_id', 'year', 'i17_CR_wb', 'i17_revenue', 'has_figures', 'flag_copy_forward']].merge(
    pub[['insurer_id', 'year', 'gwp', 'startup']], on=['insurer_id', 'year'], how='left')
tol = np.maximum(0.05 * wb.gwp, 0.5e6)
wb['ok'] = wb.has_figures.fillna(False).astype(bool) & ~wb.flag_copy_forward.fillna(False).astype(bool) & wb.i17_CR_wb.notna() \
           & ((wb.year == 2025) | ((wb.i17_revenue - wb.gwp).abs() <= tol))
cut_ifrs4 = youden(tr_all.dropna(subset=['CRlag_p']).red.values, tr_all.dropna(subset=['CRlag_p']).CRlag_p.values)
dist = []
for basis, d in [('IFRS 4 audited (corrected)', V[V.year.isin([2021, 2022])][['insurer_id', 'year', 'CR_corr2020']].rename(columns={'CR_corr2020': 'cr'})),
                 ('IFRS 17 published (NIC 2024 report)', pub[pub.year.isin([2023, 2024])][['insurer_id', 'year', 'CR']].rename(columns={'CR': 'cr'})),
                 ('IFRS 17 workbook Q4 (quality-checked)', wb[wb.ok][['insurer_id', 'year', 'i17_CR_wb']].rename(columns={'i17_CR_wb': 'cr'}))]:
    for yr, x in d.dropna(subset=['cr']).groupby('year'):
        dist.append(dict(section='distribution', basis=basis, year=yr, n=len(x), median=x.cr.median(), p75=x.cr.quantile(.75),
                         share_gt110=(x.cr > 110).mean(), share_flag_rule110=(x.cr > 110).mean(),
                         share_flag_ifrs4_youden=(x.cr > cut_ifrs4).mean(), ifrs4_youden_cutoff=cut_ifrs4))
pairs = []
for lab, a, b in [('published 2023 -> 2024', pub[pub.year == 2023][['insurer_id', 'CR']].rename(columns={'CR': 'x'}),
                   pub[pub.year == 2024][['insurer_id', 'CR', 'startup']].rename(columns={'CR': 'y'})),
                  ('workbook 2024 -> 2025', wb[(wb.year == 2024) & wb.ok][['insurer_id', 'i17_CR_wb']].rename(columns={'i17_CR_wb': 'x'}),
                   wb[(wb.year == 2025) & wb.ok][['insurer_id', 'i17_CR_wb', 'startup']].rename(columns={'i17_CR_wb': 'y'}))]:
    d = a.merge(b, on='insurer_id').dropna(subset=['x', 'y']); d = d[d.startup != True].copy(); d['red'] = (d.y > 110).astype(int)
    if d.red.nunique() < 2:
        pairs.append(dict(section='pair', basis=lab, n=len(d), n_red=int(d.red.sum()), note='one class only: AUC undefined')); continue
    bs, sk = boot(d, 'red', lambda s: [auc(s.red, s.x), youden(s.red.values, s.x.values)]); lo, hi = ci(bs)
    pairs.append(dict(section='pair', basis=lab, n=len(d), n_red=int(d.red.sum()), auc=auc(d.red, d.x), auc_ci_lo=lo[0], auc_ci_hi=hi[0],
                      youden_cutoff=youden(d.red.values, d.x.values), cutoff_ci_lo=lo[1], cutoff_ci_hi=hi[1], boot_redrawn=sk,
                      ifrs4_youden_cutoff=cut_ifrs4, **flags(d.red, d.x > 110)))
I17 = pd.concat([pd.DataFrame(dist), pd.DataFrame(pairs)], ignore_index=True); I17.to_csv(OUT / 'exp3_ifrs17.csv', index=False)

pd.set_option('display.width', 240); pd.set_option('display.max_columns', 30)
print(f"Rows: train {len(tr_all)}, test {len(te_all)} insurer-years (t = 2016-2020 / 2021-2022); "
      f"dQ2CR available: train {tr_all.dQ2CR.notna().sum()}, test {te_all.dQ2CR.notna().sum()}")
print(Rs.drop(columns=[c for c in ['coefs'] if c in Rs]).round(3).to_string(index=False))
print(I17.round(3).to_string(index=False))
v = Rs[(Rs.item == '4c') & (Rs.target.str.startswith('primary')) & Rs.method.str.startswith('DIFF B')].iloc[0]
print(f"\n4c VERDICT (pre-registered rule, primary target): {v.readout}. AUC(B) - AUC(A) = {v.auc:+.3f}, "
      f"paired 95% CI [{v.ci_lo:+.3f}, {v.ci_hi:+.3f}], n = {v.n} test rows ({v.n_red} red).")
