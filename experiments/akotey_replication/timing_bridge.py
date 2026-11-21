"""Specification B (throwaway, pre-registered in README.md): timing bridge between Akotey et al. and the thesis.

Two-way FE (models.fe, D12) with insurer-clustered SEs and wild cluster bootstrap (models.wcb), outcomes
UW_margin, CR, LR, ER: B1 same-year g, B2 lagged g (thesis spec), B3 both. Controls RET, ln_gwp_L1, LEV_net_L1.
Sample: estimation_sample.csv rows with g and g_L1 present; 1/99 winsorising on this sample, raw also reported.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from models import fe, wcb

OUT = Path(__file__).resolve().parent / 'outputs'; OUT.mkdir(exist_ok=True)
E = pd.read_csv(ROOT / 'data' / 'processed' / 'estimation_sample.csv')
S = E.dropna(subset=['g', 'g_L1', 'CR', 'LR', 'ER', 'RET', 'ln_gwp_L1', 'LEV_net_L1']).copy()
for v in ['g', 'g_L1', 'CR', 'LR', 'ER', 'LEV_net_L1']:
    lo, hi = S[v].quantile([0.01, 0.99]); S[v + '_w'] = S[v].clip(lo, hi)
S['UW_margin'] = 100 - S.CR; S['UW_margin_w'] = 100 - S.CR_w

rows = []
for version in ['winsorised', 'raw']:
    sx = '_w' if version == 'winsorised' else ''
    ctrl = ['RET', 'ln_gwp_L1', 'LEV_net_L1' + sx]
    models = {'B1': ['g' + sx], 'B2': ['g_L1' + sx], 'B3': ['g' + sx, 'g_L1' + sx]}
    for y0 in ['UW_margin', 'CR', 'LR', 'ER']:
        y = y0 + sx
        for b, G in models.items():
            X = G + ctrl; r = fe(S, y, X)
            for v in G:
                rows.append(dict(version=version, outcome=y0, model=b, term=v.replace('_w', ''), coef=r.params[v],
                                 se=r.std_errors[v], p=r.pvalues[v], wcb_p=wcb(S, y, X, var=v)[1], n=int(r.nobs),
                                 n_insurers=S.insurer_id.nunique()))
R = pd.DataFrame(rows); R.to_csv(OUT / 'bridge_results.csv', index=False)

pd.set_option('display.width', 200)
print(f"B sample: {len(S)} insurer-years, {S.insurer_id.nunique()} insurers, {S.year.min()}-{S.year.max()}")
print(R.round(4).to_string(index=False))
w = R[(R.version == 'winsorised') & (R.outcome == 'CR')].set_index(['model', 'term'])
b1, b2 = w.loc[('B1', 'g')], w.loc[('B2', 'g_L1')]
print(f"\nCheck: B2 CR g_L1 {b2.coef:+.4f} vs thesis M1 +0.0547 (difference from winsorising on the B sample)")
if b1.wcb_p < 0.05 and b1.coef > 0 and b2.wcb_p >= 0.05: v = 'TIMING'
elif b1.wcb_p >= 0.05 and b2.wcb_p >= 0.05: v = 'PERIOD/POPULATION'
else: v = 'MIXED: authors decide'
print(f"B VERDICT: {v}. B1 same-year g -> CR {b1.coef:+.4f} (WCB p {b1.wcb_p:.3f}); B2 lagged g -> CR {b2.coef:+.4f} (WCB p {b2.wcb_p:.3f})")
