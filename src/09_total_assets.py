"""Step 9 (robustness): total assets as the size control, from the NIC quarterly returns workbook.

The defence specified ln(total assets) (D1), but NIC annual reports do not publish assets per insurer,
so the main models use ln(lagged GWP). The NIC quarterly returns workbook (an NIC product, source confirmed;
the figures are insurers' unaudited quarterly submissions; published by the NIC, tracked, data_issues A15, A17) has total
assets per insurer per quarter. Q4 sheets only: assets are a year-end stock. Reading rules: src/returns_io.py.

Filters (counts reported in robust_total_assets_coverage.csv):
  (a) copy-forward, REPORT-ONLY: Q4 row identical to Q3 on all shared reported money columns (ratios and
      market share excluded as they are recomputed per sheet; >= 3 shared values); (b) decides
  (b) concordance: workbook Q4 GWP vs audited annual GWP in panel_master. 2015-2019 (exact GHS):
      |diff| <= 5%. 2020+ (panel rounded to GHS m): |diff| <= max(5%, GHS 0.5m). Fail -> assets missing
  (c) non-positive assets -> missing
  (d) jump, REPORT-ONLY: assets > 3x or < 1/3 of the previous year
Models reuse models.fe (D12) on estimation_sample.csv without re-winsorising.
"""
import sys
import numpy as np, pandas as pd
from config import PROCESSED, TABLES
from models import fe, twdm, wcb
from returns_io import map_id, sheet_quarter, header_row, data_rows, open_workbook   # shared with step 12

YEARS = range(2015, 2023)          # years with audited panel GWP for the concordance check
HDR_GWP = ('gross written premium', 'gross premium', 'gross premiums')

def read_sheet(ws, year):
    """Rows below the LAST header row (earlier ones are INDEX lookup blocks), stopping at a total row."""
    rows = list(ws.iter_rows(values_only=True))
    h, hn, nc = header_row(rows)
    ta = hn.index('total assets'); gw = next(i for i, c in enumerate(hn) if c in HDR_GWP)
    out = []
    for r, nm in data_rows(rows, h, nc):
        num = lambda v: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else np.nan
        vals = {hn[i]: num(r[i]) for i in range(len(hn)) if hn[i] and i != nc and i < len(r)}
        out.append(dict(source_name=nm, insurer_id=map_id(nm, year), year=year,
                        total_assets_raw=num(r[ta]), wb_gwp=num(r[gw]), vals=vals))
    return out

wb = open_workbook()
sheets = {}
for s in wb.sheetnames:
    qy = sheet_quarter(s)
    if qy and qy[0] in (3, 4) and qy[1] in YEARS: sheets[qy] = s
missing = [(q, y) for y in YEARS for q in (3, 4) if (q, y) not in sheets]
if missing: sys.exit(f"Missing Q3/Q4 sheets for {missing}")
Q4 = pd.DataFrame([r for y in YEARS for r in read_sheet(wb[sheets[(4, y)]], y)])
Q3 = pd.DataFrame([r for y in YEARS for r in read_sheet(wb[sheets[(3, y)]], y)])

bad = Q4[Q4.insurer_id.isna() & Q4.total_assets_raw.notna()]
if len(bad): sys.exit("STOP: unmapped insurer names with total assets:\n" + bad[['year', 'source_name']].to_string(index=False))
n_excluded = int((Q4.insurer_id == 'EXCLUDED').sum())
Q4 = Q4[Q4.insurer_id.notna() & (Q4.insurer_id != 'EXCLUDED')]
dup = Q4[Q4.duplicated(['insurer_id', 'year'], keep=False)]
if len(dup): sys.exit("STOP: several workbook rows map to one insurer-year:\n" + dup[['year', 'insurer_id', 'source_name']].to_string(index=False))

# (a) copy-forward (report-only): Q4 identical to Q3 on every reported money column both rows have.
# Derived columns (ratios, market share) are excluded: they are recomputed per sheet (market share against
# that quarter's total; ratios sometimes in different units), so a copied return still differs there.
# At least 3 shared values are required, so an empty row is never flagged.
derived = lambda k: 'ratio' in k or 'market share' in k
q3 = {(r.insurer_id, r.year): r.vals for r in Q3[Q3.insurer_id.notna()].itertuples()}
def same_as_q3(r):
    v3 = q3.get((r.insurer_id, r.year))
    if v3 is None: return False
    common = [k for k in r.vals if not derived(k) and k in v3 and not np.isnan(r.vals[k]) and not np.isnan(v3[k])]
    return len(common) >= 3 and all(r.vals[k] == v3[k] for k in common)
Q4['flag_copy_forward'] = [same_as_q3(r) for r in Q4.itertuples()]
# (b) concordance with audited annual GWP
P = pd.read_csv(PROCESSED / 'panel_master.csv')[['insurer_id', 'year', 'gwp']].rename(columns={'gwp': 'panel_gwp'})
Q4 = Q4.merge(P, on=['insurer_id', 'year'], how='left')
diff = (Q4.wb_gwp - Q4.panel_gwp).abs()
tol = np.where(Q4.year <= 2019, 0.05 * Q4.panel_gwp, np.maximum(0.05 * Q4.panel_gwp, 0.5e6))
Q4['gwp_rel_diff'] = diff / Q4.panel_gwp
Q4['flag_concordance_fail'] = ~(diff <= tol)          # NaN workbook or panel GWP also fails
# (c) non-positive assets; (d) jumps (report-only), on positive raw assets in consecutive years
Q4['flag_nonpositive'] = Q4.total_assets_raw <= 0
Q4 = Q4.sort_values(['insurer_id', 'year'])
pos = Q4.total_assets_raw.where(Q4.total_assets_raw > 0)
prev = pos.groupby(Q4.insurer_id).shift(); consec = Q4.year.diff().eq(1) & Q4.insurer_id.eq(Q4.insurer_id.shift())
ratio = (pos / prev).where(consec)
Q4['flag_jump'] = (ratio > 3) | (ratio < 1 / 3)
Q4['total_assets'] = Q4.total_assets_raw.where(~Q4.flag_concordance_fail & ~Q4.flag_nonpositive & Q4.total_assets_raw.notna())
cols = ['insurer_id', 'year', 'source_name', 'total_assets', 'total_assets_raw', 'wb_gwp', 'panel_gwp', 'gwp_rel_diff',
        'flag_copy_forward', 'flag_concordance_fail', 'flag_nonpositive', 'flag_jump']
Q4[cols].to_csv(PROCESSED / 'total_assets_q4.csv', index=False)

# coverage by year
ids = lambda d: ';'.join(sorted(d.insurer_id))
cov = []
for y, d in Q4.groupby('year'):
    has = d[d.total_assets_raw.notna()]; cf = d[d.flag_copy_forward]
    cov.append(dict(year=y, insurers_in_q4_sheet=len(d), with_total_assets=len(has),
                    concordance_pass=int((~has.flag_concordance_fail).sum()), concordance_fail=int(has.flag_concordance_fail.sum()),
                    nonpositive=int(has.flag_nonpositive.sum()), final_with_assets=int(d.total_assets.notna().sum()),
                    copy_forward=len(cf), copy_forward_kept=ids(cf[~cf.flag_concordance_fail]), copy_forward_dropped=ids(cf[cf.flag_concordance_fail]),
                    concordance_failed_ids=ids(has[has.flag_concordance_fail]), jump_flagged=ids(d[d.flag_jump])))
cov = pd.DataFrame(cov)
cov.to_csv(TABLES / 'robust_total_assets_coverage.csv', index=False)

# ---------- models ----------
E = pd.read_csv(PROCESSED / 'estimation_sample.csv')
A = Q4[['insurer_id', 'year', 'total_assets']].dropna().assign(year=lambda d: d.year + 1)   # end of t-1
E = E.merge(A.assign(ln_assets_L1=np.log(A.total_assets))[['insurer_id', 'year', 'ln_assets_L1']], on=['insurer_id', 'year'], how='left')
S = E[E.ln_assets_L1.notna()].copy()     # existing _w columns, not re-winsorised
base = ['g_L1_w', 'RET', 'LEV_net_L1_w']
specs = {'A_lngwp_same_sample': base + ['ln_gwp_L1'], 'B_lnassets': base + ['ln_assets_L1'], 'C_both': base + ['ln_gwp_L1', 'ln_assets_L1']}
rows = []
for y in ['LR_w', 'ER_w', 'CR_w']:
    for s, X in specs.items():
        d = S.dropna(subset=[y] + X); r = fe(d, y, X)
        boot = {}
        if s != 'C_both':
            for v in ['g_L1_w', X[-1]]: boot[v] = wcb(d, y, X, var=v, B=999)[1]
        for t in X:
            rows.append(dict(model=s, outcome=y, term=t, coef=r.params[t], se=r.std_errors[t], p=r.pvalues[t],
                             wcb_p=boot.get(t, np.nan), n=int(r.nobs), n_insurers=d.insurer_id.nunique()))
d = S.dropna(subset=['ln_assets_L1', 'ln_gwp_L1'])
dm = lambda v: d[v] - d.groupby('insurer_id')[v].transform('mean')
corr_within = float(np.corrcoef(dm('ln_assets_L1'), dm('ln_gwp_L1'))[0, 1])
rows.append(dict(model='within_insurer_corr', outcome='', term='ln_assets_L1~ln_gwp_L1', coef=corr_within,
                 n=len(d), n_insurers=d.insurer_id.nunique()))
R = pd.DataFrame(rows)
R.to_csv(TABLES / 'robust_total_assets.csv', index=False)

pd.set_option('display.width', 200)
print(f"Workbook: {len(Q4)} mapped Q4 insurer-years 2015-2022 ({n_excluded} excluded rows: NEM / Industrial & General)")
print(cov.drop(columns=['concordance_failed_ids']).to_string(index=False))
print(f"\nSubsample with ln_assets_L1: {len(S)} of {len(E)} rows, {S.insurer_id.nunique()} insurers. Within-insurer corr(ln_assets_L1, ln_gwp_L1) = {corr_within:.3f}")
show = R[R.term.isin(['g_L1_w', 'ln_gwp_L1', 'ln_assets_L1'])]
print(show.round(4).to_string(index=False))
print("Saved: robust_total_assets.csv, robust_total_assets_coverage.csv (insurer-level detail in data/processed/total_assets_q4.csv)")
