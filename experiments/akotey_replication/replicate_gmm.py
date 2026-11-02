"""Specification A (throwaway, pre-registered in README.md): Akotey et al. (2023) difference GMM on 2015-2022.

Y on L1.Y, PGR, MSGR, MANCOMP, UWRISK (col. 2) [+ REINS, infl (col. 3)]; gmm(Y, 2:3), other regressors IV-style;
nolevel collapse, two-step Windmeijer. Secondary A-yd: col. 2 + year dummies. Samples: thesis and balanced.
pydynpd wrapper copied from src/08_system_gmm.py.
"""
import contextlib, io, sys
from pathlib import Path
import numpy as np, pandas as pd
from pydynpd import regression   # 0.2.2 needs numpy < 2.4

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'outputs'; OUT.mkdir(exist_ok=True)
YEARS = range(2015, 2023)

P = pd.read_csv(ROOT / 'data' / 'processed' / 'panel_master.csv')
grid = pd.MultiIndex.from_product([P.insurer_id.unique(), YEARS], names=['insurer_id', 'year'])
G = P.set_index(['insurer_id', 'year']).reindex(grid)
ms_prev = G.groupby(level=0).ms.shift()                     # gap year -> missing
G['MSGR'] = (G.ms / ms_prev - 1).where(G.merger_break != True)
G = G.reset_index()
G = G[G.CR.notna() & (G.startup != True)].copy()             # observed, non-start-up rows
G['UP_GWP'] = (100 - G.CR) * G.RET / 100
G['UW_margin'] = 100 - G.CR
G['PGR'] = G.g / 100
G['MANCOMP'] = G.ER
G['UWRISK'] = (G.CR > 100).astype(float)
G['REINS'] = 100 - G.RET
G['infl'] = G.cpi_avg_yoy
X2 = ['PGR', 'MSGR', 'MANCOMP', 'UWRISK']; X3 = X2 + ['REINS', 'infl']
VARS = ['UP_GWP', 'UW_margin'] + X3

# Balanced (DEVIATION, README section 4): outcome in every year 2015-2022, every col. 3 regressor in every
# year 2016-2022 (MSGR cannot exist in 2015: no 2014 market shares).
w = G.set_index(['insurer_id', 'year'])
def complete(i):
    d = w.loc[i].reindex(YEARS)
    return d.UP_GWP.notna().all() and d.loc[2016:, X3].notna().all().all()
BAL = [i for i in G.insurer_id.unique() if complete(i)]
SAMPLES = {'thesis': G, 'balanced': G[G.insurer_id.isin(BAL)]}

def usable(pm, y, X):
    """Obs in the differenced equation: level rows complete (y, L1.y, X) at t and t-1, on the full year grid."""
    g = pm.set_index(['insurer_id', 'year'])[[y] + X].reindex(pd.MultiIndex.from_product([pm.insurer_id.unique(), YEARS], names=['insurer_id', 'year']))
    lev = pd.concat([g[y], g.groupby(level=0)[y].shift(), g[X]], axis=1).notna().all(axis=1)
    ok = lev & lev.groupby(level=0).shift(1, fill_value=False)
    return int(ok.sum()), ok[ok].index.get_level_values(0).nunique()

def fit(cmd, pm):
    pm = pm.sort_values(['insurer_id', 'year']).reset_index(drop=True)   # pydynpd fills its grid in row order
    assert not pm.duplicated(['insurer_id', 'year']).any()
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            m = regression.abond(cmd, pm[['insurer_id', 'year'] + VARS].copy(), ['insurer_id', 'year'])
    except SystemExit:
        raise RuntimeError(f'pydynpd rejected: {cmd}\n{out.getvalue()}')
    return m.models[0]

SPECS = {'col2': (X2, 'nolevel collapse'), 'col3': (X3, 'nolevel collapse'), 'col2_yd': (X2, 'nolevel collapse timedumm')}
coefs, diags = [], []
for s, pm in SAMPLES.items():
    for spec, (X, opts) in SPECS.items():
        for y in ['UP_GWP', 'UW_margin']:
            cmd = f"{y} L1.{y} {' '.join(X)} | gmm({y}, 2:3) iv({' '.join(X)}) | {opts}"
            m = fit(cmd, pm)
            n_obs, n_ins = usable(pm, y, X)
            assert n_obs == m.num_obs, f'{s} {spec} {y}: own obs count {n_obs} != pydynpd {m.num_obs}'
            t = m.regression_table.rename(columns={'variable': 'term', 'coefficient': 'coef', 'std_err': 'se', 'z_value': 'z', 'p_value': 'p'})
            coefs.append(t[['term', 'coef', 'se', 'z', 'p']].assign(sample=s, spec=spec, outcome=y))
            ar = {a.lag: a.P_value for a in m.AR_list}; k = m.z_information.num_instr; hp = m.hansen.p_value
            fail = (ar[2] < 0.05) or not (0.10 <= hp <= 0.99)
            diags.append(dict(sample=s, spec=spec, outcome=y, n_obs=m.num_obs, n_insurers=n_ins, n_instruments=k,
                              instr_ge_insurers=k >= n_ins, ar1_p=ar[1], ar2_p=ar[2], hansen_j=m.hansen.test_value,
                              hansen_df=m.hansen.df, hansen_p=hp, diagnostics_fail=fail, command=cmd))

C = pd.concat(coefs)[['sample', 'spec', 'outcome', 'term', 'coef', 'se', 'z', 'p']]
D = pd.DataFrame(diags)
C.to_csv(OUT / 'gmm_results.csv', index=False); D.to_csv(OUT / 'gmm_diagnostics.csv', index=False)

# ---------- report ----------
pd.set_option('display.width', 220)
print(f"Thesis sample: {len(G)} insurer-years, {G.insurer_id.nunique()} insurers. Balanced: {len(BAL)} insurers ({', '.join(BAL)})")
print(D.drop(columns=['command', 'hansen_j']).round(3).to_string(index=False))
print(C[C.term.isin(['PGR', 'MSGR'])].round(4).to_string(index=False))
head = []
for s in SAMPLES:
    for spec in ['col2', 'col3']:
        r = C[(C['sample'] == s) & (C.spec == spec) & (C.outcome == 'UP_GWP') & (C.term == 'PGR')].iloc[0]
        dg = D[(D['sample'] == s) & (D.spec == spec) & (D.outcome == 'UP_GWP')].iloc[0]
        lab = 'diagnostics fail' if dg.diagnostics_fail else ('replicated' if r.coef < 0 and r.p < 0.05 else 'not replicated')
        head.append(lab)
        print(f"  {s:8s} {spec}: PGR {r.coef:+.4f} (se {r.se:.4f}, p {r.p:.3f}) vs Akotey -0.022; PGR +1.0 (doubling) -> "
              f"{r.coef:+.2f} pp of GWP | AR2 p {dg.ar2_p:.3f}, Hansen p {dg.hansen_p:.3f}, instr {dg.n_instruments}/{dg.n_insurers} -> {lab}")
ok = [h for h in head if h != 'diagnostics fail']
if not ok: v = 'DIAGNOSTICS FAIL'
elif all(h == 'replicated' for h in ok): v = 'REPLICATED'
elif not any(h == 'replicated' for h in ok): v = 'NOT REPLICATED'
else: v = 'MIXED: authors decide'
print(f"\nA VERDICT: {v} ({len(ok)} of 4 models passing diagnostics)")
