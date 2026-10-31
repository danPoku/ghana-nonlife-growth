"""Step 8 (robustness): System GMM (Blundell-Bond) with pydynpd, mirroring R/twfe_and_system_gmm.R Step 2.

Runs after 07_validate.py so the 26 validation checks stay independent of it. Results are NOT pinned.
Spec: Y_it on Y_i,t-1, g_i,t-1, RET_it, ln_gwp_i,t-1, LEV_net_i,t-1; GMM-style lags 2-3 of Y and g,
IV-style RET, L1.ln_gwp, L1.LEV_net; year dummies; collapsed instruments; two-step, Windmeijer SEs.
Variants: lags 2-4, and one-step. Sample: 2015-2022, start-ups dropped, pooled 1/99 winsorising.
"""
import contextlib, io, json
import numpy as np, pandas as pd
from pydynpd import regression   # 0.2.2 needs numpy < 2.4 (np.in1d, float() of 1x1 arrays): see requirements.txt
from config import PROCESSED, TABLES, WINSOR

P = pd.read_csv(PROCESSED / 'panel_master.csv')
pm = P[P.year.between(2015, 2022) & ~P.startup.astype(bool)].copy()
for v in ['LR', 'ER', 'CR', 'g', 'LEV_net']:
    a, b = pm[v].quantile(list(WINSOR)); pm[v] = pm[v].clip(a, b)
pm['ln_gwp'] = np.log(pm.gwp)
# pydynpd fills its insurer x year grid in row order without sorting, so the order must be fixed here
pm = pm.sort_values(['insurer_id', 'year']).reset_index(drop=True)
assert not pm.duplicated(['insurer_id', 'year']).any(), 'duplicate insurer-years'
VARS = ['LR', 'ER', 'CR', 'g', 'RET', 'ln_gwp', 'LEV_net']
N_INS = pm.insurer_id.nunique()

VARIANTS = {'baseline': ('2:3', 'timedumm collapse'),
            'lags2_4': ('2:4', 'timedumm collapse'),
            'onestep': ('2:3', 'timedumm collapse onestep')}

def usable(y):
    """Insurers / obs entering the differenced equation, with lags taken on the full year grid (gaps -> NaN)."""
    g = pm.set_index(['insurer_id', 'year'])[VARS].reindex(pd.MultiIndex.from_product([pm.insurer_id.unique(), range(2015, 2023)], names=['insurer_id', 'year']))
    L = lambda s, k=1: g.groupby(level=0)[s].shift(k)
    lev = pd.concat([g[y], L(y), L('g'), g.RET, L('ln_gwp'), L('LEV_net')], axis=1).notna().all(axis=1)
    ok = lev & lev.groupby(level=0).shift(1, fill_value=False)
    ok = ok[ok.index.get_level_values('year') >= 2017]   # first differenced period given lag-1 regressors
    return int(ok.sum()), ok[ok].index.get_level_values(0).nunique()

def fit(cmd):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            m = regression.abond(cmd, pm[['insurer_id', 'year'] + VARS].copy(), ['insurer_id', 'year'])
    except SystemExit:   # pydynpd calls exit() (code 0) on a bad command; make that a real failure
        raise RuntimeError(f'pydynpd rejected: {cmd}\n{out.getvalue()}')
    return m.models[0]

coefs, diags = [], []
for var, (lags, opts) in VARIANTS.items():
    for y in ['LR', 'ER', 'CR']:
        cmd = f'{y} L1.{y} L1.g RET L1.ln_gwp L1.LEV_net | gmm({y}, {lags}) gmm(g, {lags}) iv(RET L1.ln_gwp L1.LEV_net) | {opts}'
        m = fit(cmd)
        t = m.regression_table.rename(columns={'variable': 'term', 'coefficient': 'coef', 'std_err': 'se', 'z_value': 'z', 'p_value': 'p'})
        coefs.append(t[['term', 'coef', 'se', 'z', 'p']].assign(variant=var, outcome=y))
        n_obs, n_ins = usable(y)
        assert n_obs == m.num_obs, f'{var} {y}: own obs count {n_obs} != pydynpd {m.num_obs} (lag/gap handling differs)'
        ar = {a.lag: a.P_value for a in m.AR_list}
        k = m.z_information.num_instr
        diags.append(dict(variant=var, outcome=y, n_obs=m.num_obs, n_insurers=n_ins, n_insurers_panel=m.N,
                          n_instruments=k, ar1_p=ar[1], ar2_p=ar[2], hansen_j=m.hansen.test_value,
                          hansen_df=m.hansen.df, hansen_p=m.hansen.p_value,
                          instr_lt_insurers=k < n_ins, ar1_rejects=ar[1] < 0.05, ar2_ok=ar[2] >= 0.10,
                          hansen_ok=0.10 < m.hansen.p_value < 0.99, command=cmd))

C = pd.concat(coefs)[['variant', 'outcome', 'term', 'coef', 'se', 'z', 'p']]
D = pd.DataFrame(diags)
C.to_csv(TABLES / 'system_gmm.csv', index=False)
D.to_csv(TABLES / 'system_gmm_diagnostics.csv', index=False)

# ---------- console report ----------
pd.set_option('display.width', 160)
print(f'Sample: {len(pm)} insurer-years, {N_INS} insurers, 2015-2022, start-ups excluded')
print('\nDiagnostics:')
print(D.drop(columns=['command', 'hansen_j', 'n_insurers_panel']).round(3).to_string(index=False))
for _, r in D.iterrows():
    if not r.instr_lt_insurers:
        print(f'FLAG {r.variant} {r.outcome}: {r.n_instruments} instruments >= {r.n_insurers} insurers')
print('\nLagged growth (L1.g), pp of ratio per pp of growth:')
FE = pd.read_csv(TABLES / 'regressions.csv')
AH = json.load(open(TABLES / 'results_summary.json'))['anderson_hsiao']
g = C[C.term == 'L1.g'].set_index(['outcome', 'variant'])
for y in ['LR', 'ER', 'CR']:
    fe = FE[(FE.model == f'{y}_w|M1_linear|cluster') & (FE.term == 'g_L1_w')].iloc[0]
    print(f'  {y}: TWFE {fe.coef:+.4f} (se {fe.se:.4f}, p {fe.p:.3f}) | AH {AH[y]["g"]:+.4f} (se {AH[y]["g_se"]:.4f}, p {AH[y]["g_p"]:.3f})')
    for var in VARIANTS:
        r = g.loc[(y, var)]
        print(f'      GMM {var:8s} {r.coef:+.4f} (se {r.se:.4f}, p {r.p:.3f}); +10pp growth -> {10 * r.coef:+.2f} pp')
print('\nSaved: system_gmm.csv, system_gmm_diagnostics.csv')
