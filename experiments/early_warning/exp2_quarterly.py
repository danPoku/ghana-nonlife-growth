"""Experiment 2 (exploratory, pre-registered in README.md): quarterly nowcast of the red zone.

Does year-to-date CR at Q2 (Q3 for reference) from the NIC quarterly returns workbook
predict full-year CR > 110? Primary target: audited panel CR (2015-2022). Secondary: workbook Q4 CR
(2013-2023, and 2024-2025 separately as IFRS 17). Header, alias and exclusion rules copied from
src/09_total_assets.py; insurer names via names.canon. The workbook is opened (SHA-256 checked) via src/returns_io.py.
"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import rankdata
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from names import canon

from returns_io import open_workbook   # config.QUARTERLY_FILE, checked against data/raw/CHECKSUMS
OUT = Path(__file__).resolve().parent / 'outputs'
YEARS = range(2013, 2026); B, SEED = 1999, 1

# ---------- reading (rules from src/09_total_assets.py) ----------
HDR_NAME = ('company', 'non-life insurer', 'non life insurers')
HDR_GWP = ('gross written premium', 'gross premium', 'gross premiums', 'insurance service revenue', 'insurance revenue')
ALIASES = [(r'^gn insurance', 'BEDROCK', None), (r'^equity assurance', 'SUNU', None), (r'^regency insurance', 'REGENCYNEM', 2015)]
EXCLUDE = [r'^nem insurance', r'^industrial\s*(&|and)\s*general']
norm = lambda v: re.sub(r'\s+', ' ', str(v)).strip().lower() if v is not None else ''
num = lambda v: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else np.nan

def map_id(name, year):
    n = norm(name).replace('*', '')
    if any(re.search(p, n) for p in EXCLUDE): return 'EXCLUDED'
    for p, cid, last in ALIASES:
        if re.search(p, n) and (last is None or year <= last): return cid
    return canon(str(name))

def col(hn, *names):
    return next((i for i, c in enumerate(hn) if c in names), None)

def read_sheet(ws, q, year):
    rows = list(ws.iter_rows(values_only=True))
    h = [i for i, r in enumerate(rows) if any(norm(c) in HDR_NAME for c in r)][-1]
    hn = [norm(c) for c in rows[h]]
    nc = col(hn, *HDR_NAME); gw = col(hn, *HDR_GWP)
    cl, ex, cr = col(hn, 'claims ratio', 'claims ratio %'), col(hn, 'expense ratio', 'expense ratio %'), col(hn, 'combined ratio', 'combined ratio %')
    assert cl is not None and ex is not None, f"no claims/expense ratio column in {ws.title}"
    derived = lambda k: 'ratio' in k or 'market share' in k
    out = []
    for r in rows[h + 1:]:
        nm = r[nc] if nc < len(r) else None
        if nm is None or not str(nm).strip(): continue
        if re.match(r'^\s*(total|industry|grand)', str(nm), re.I): break
        g = lambda i: num(r[i]) if i is not None and i < len(r) else np.nan
        money = {hn[i]: num(r[i]) for i in range(len(hn)) if hn[i] and i != nc and i < len(r) and not derived(hn[i])}
        out.append(dict(sheet=ws.title, q=q, year=year, source_name=str(nm).strip(), insurer_id=map_id(nm, year),
                        gwp=g(gw), claims_ratio=g(cl), expense_ratio=g(ex), combined_ratio_sheet=g(cr), money=money))
    return out

wb = open_workbook()
rows = []
for s in wb.sheetnames:
    m = re.match(r'^\s*q\s*([234])\s*,?\s*(\d{4})\s*$', s, re.I)
    if m and int(m.group(2)) in YEARS: rows += read_sheet(wb[s], int(m.group(1)), int(m.group(2)))
Q = pd.DataFrame(rows)
missing = [(q, y) for y in YEARS for q in (2, 3, 4) if not ((Q.q == q) & (Q.year == y)).any()]
if missing: sys.exit(f"Missing sheets: {missing}")
bad = Q[Q.insurer_id.isna() & (Q.claims_ratio.notna() | Q.gwp.notna())]
if len(bad): sys.exit("STOP: unmapped insurer names:\n" + bad[['sheet', 'source_name']].drop_duplicates().to_string(index=False))
n_excl = int((Q.insurer_id == 'EXCLUDED').sum())
Q = Q[Q.insurer_id.notna() & (Q.insurer_id != 'EXCLUDED')]
dup = Q[Q.duplicated(['insurer_id', 'year', 'q'], keep=False)]
if len(dup): sys.exit("STOP: several rows per insurer-year-quarter:\n" + dup[['sheet', 'insurer_id', 'source_name']].to_string(index=False))

# ---------- units: per sheet, claims-ratio median < 3 -> fractions ----------
units = []
for s, d in Q.groupby('sheet', sort=False):
    med_c, med_e = d.claims_ratio.median(), d.expense_ratio.median()
    frac = med_c < 3
    both = d.dropna(subset=['claims_ratio', 'expense_ratio'])
    units.append(dict(sheet=s, q=d.q.iat[0], year=d.year.iat[0], n=len(d), median_claims_ratio_raw=med_c,
                      median_expense_ratio_raw=med_e, unit='fraction (x100)' if frac else 'percent',
                      expense_ratio_agrees=bool((med_e < 3) == frac),
                      share_expense_equals_claims=float((both.claims_ratio == both.expense_ratio).mean())))
U = pd.DataFrame(units).sort_values(['year', 'q'])
# DEVIATION from the pre-registration (found while running): in a sheet whose expense-ratio column copies the
# claims-ratio column (Q2 2022: 25 of 25 rows), YTD CR would be 2 x claims ratio. Such sheets (>= 90% of rows
# equal) get their ratios set to missing; nothing is recomputed from amounts.
U['ratios_invalid'] = U.share_expense_equals_claims >= 0.9
U.to_csv(OUT / 'exp2_units.csv', index=False)
Q.loc[Q.sheet.isin(U[U.ratios_invalid].sheet), ['claims_ratio', 'expense_ratio']] = np.nan
assert U.expense_ratio_agrees.all(), "claims and expense ratio units disagree within a sheet:\n" + U[~U.expense_ratio_agrees].to_string()
fx = Q.sheet.map(U.set_index('sheet').unit.str.startswith('fraction'))
for c in ['claims_ratio', 'expense_ratio', 'combined_ratio_sheet']:
    Q[c] = np.where(fx, Q[c] * 100, Q[c])
Q['cr_ytd'] = Q.claims_ratio + Q.expense_ratio

# ---------- wide: one row per insurer-year ----------
W = Q.pivot_table(index=['insurer_id', 'year'], columns='q', values=['cr_ytd', 'gwp', 'combined_ratio_sheet'], aggfunc='first')
W.columns = [f'{a}_q{b}' for a, b in W.columns]; W = W.reset_index()
mq = {(r.insurer_id, r.year, r.q): r.money for r in Q.itertuples()}
def copy_fwd(i, y):                       # Q4 identical to Q3 on >= 3 shared money values (report-only)
    a, b = mq.get((i, y, 4)), mq.get((i, y, 3))
    if a is None or b is None: return False
    k = [c for c in a if c in b and not np.isnan(a[c]) and not np.isnan(b[c])]
    return len(k) >= 3 and all(a[c] == b[c] for c in k)
W['flag_copy_forward_q4'] = [copy_fwd(i, y) for i, y in zip(W.insurer_id, W.year)]

P = pd.read_csv(ROOT / 'data' / 'processed' / 'panel_master.csv')[['insurer_id', 'year', 'gwp', 'CR', 'CR_L1', 'startup']]
W = W.merge(P.rename(columns={'gwp': 'panel_gwp', 'CR': 'audited_CR', 'CR_L1': 'audited_CR_L1'}), on=['insurer_id', 'year'], how='left')
chk = W.year.between(2015, 2023)
diff = (W.gwp_q4 - W.panel_gwp).abs()
tol = np.where(W.year <= 2019, 0.05 * W.panel_gwp, np.maximum(0.05 * W.panel_gwp, 0.5e6))
W['concordance'] = np.where(~chk, 'not checked', np.where(diff <= tol, 'pass', 'fail'))   # NaN GWP fails
W['startup'] = W.startup.fillna(False).astype(bool)
W.to_csv(OUT / 'exp2_insurer_years.csv', index=False)

# ---------- helpers ----------
def auc(y, s):
    y, s = np.asarray(y), np.asarray(s, float); r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def boot(d, ycol, fn):
    rng = np.random.default_rng(SEED); ids = d.insurer_id.unique(); ix = {i: np.flatnonzero(d.insurer_id.values == i) for i in ids}
    out, skipped = [], 0
    while len(out) < B:
        s = d.iloc[np.concatenate([ix[i] for i in rng.choice(ids, len(ids))])]
        if s[ycol].nunique() < 2: skipped += 1; continue
        out.append(fn(s))
    return np.array(out), skipped
def flags(y, f):
    y, f = np.asarray(y), np.asarray(f, bool)
    return dict(share_flagged=f.mean(), hit_rate=(y[f].mean() if f.any() else np.nan), share_caught=f[y == 1].mean())

def evaluate(d, target, label):
    res = []
    base = lambda d: dict(analysis=label, n=len(d), n_red=int(d[target].sum()), n_insurers=d.insurer_id.nunique(),
                          years=f"{d.year.min()}-{d.year.max()}", n_copy_forward_q4=int(d.flag_copy_forward_q4.sum()))
    for sc in ['cr_ytd_q2', 'cr_ytd_q3']:
        e = d.dropna(subset=[sc])
        bs, sk = boot(e, target, lambda s: auc(s[target], s[sc]))
        res.append(dict(base(e), score=sc, auc=auc(e[target], e[sc]), ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5),
                        boot_skipped=sk, cutoff=110, **flags(e[target], e[sc] > 110)))
    pairs = [('cr_ytd_q2', 'audited_CR_L1'), ('cr_ytd_q3', 'cr_ytd_q2')]
    for a, b in pairs:
        e = d.dropna(subset=[a, b])
        if len(e) == 0 or e[target].nunique() < 2: continue
        f = lambda s: [auc(s[target], s[a]), auc(s[target], s[b])]
        bs, sk = boot(e, target, lambda s: (lambda x: x + [x[0] - x[1]])(f(s)))
        A = f(e); lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        if b == 'audited_CR_L1':
            res.append(dict(base(e), score=b + ' (paired rows)', auc=A[1], ci_lo=lo[1], ci_hi=hi[1], boot_skipped=sk,
                            cutoff=110, **flags(e[target], e[b] > 110)))
            res.append(dict(base(e), score=a + ' (paired rows)', auc=A[0], ci_lo=lo[0], ci_hi=hi[0], boot_skipped=sk))
        res.append(dict(base(e), score=f'DIFF {a} - {b}', auc=A[0] - A[1], ci_lo=lo[2], ci_hi=hi[2], boot_skipped=sk))
    return res

keep = (W.concordance != 'fail') & ~W.startup
# primary: audited CR(t) > 110, 2015-2022, Q2 and Q4 present, concordance passed
A = W[keep & W.year.between(2015, 2022) & W.audited_CR.notna() & W.cr_ytd_q2.notna() & W.gwp_q4.notna()].copy()
A['red'] = (A.audited_CR > 110).astype(int)
# secondary: workbook Q4 CR > 110, Q2 and Q4 present
S = W[keep & W.cr_ytd_q4.notna() & W.cr_ytd_q2.notna()].copy()
S['red'] = (S.cr_ytd_q4 > 110).astype(int)
res = evaluate(A, 'red', 'PRIMARY: audited CR > 110 (2015-2022)')
res += evaluate(S[S.year <= 2023], 'red', 'secondary: workbook Q4 CR > 110 (2013-2023)')
res += evaluate(S[S.year >= 2024], 'red', 'secondary: workbook Q4 CR > 110 (2024-2025, IFRS 17)')
R = pd.DataFrame(res); R.to_csv(OUT / 'exp2_results.csv', index=False)

# ---------- report ----------
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30)
print(f"Workbook rows mapped: {len(Q)} (Q2-Q4, 2013-2025; {n_excl} excluded NEM / Industrial & General rows)")
print("\nUnits by sheet (fraction if median claims ratio < 3):")
print(U.round(3).to_string(index=False))
ytd = (W.gwp_q2 / W.gwp_q4).groupby(W.year).median()
print("\nYTD check, median Q2 GWP / Q4 GWP by year:", ytd.round(3).to_dict())
print("Sheets with ratios set to missing (expense ratio copies claims ratio):", list(U[U.ratios_invalid].sheet))
for q in (2, 3, 4):
    a, b = f'combined_ratio_sheet_q{q}', f'cr_ytd_q{q}'
    xc = W.dropna(subset=[a, b]) if a in W else W.iloc[:0]
    print(f"Cross-check vs a sheet's own combined ratio (Q{q}): " +
          (f"{len(xc)} rows, max |diff| {(xc[a] - xc[b]).abs().max():.3f}" if len(xc) else "no Q2-Q4 sheet has one"))
print("\nConcordance (Q4 GWP vs audited GWP):", W.groupby('concordance').size().to_dict(),
      f"| start-ups excluded: {int(W.startup.sum())} | Q4 copy-forward flagged: {int(W.flag_copy_forward_q4.sum())}")
cmp_ = A.dropna(subset=['cr_ytd_q4'])
print(f"Primary rows: workbook Q4 CR vs audited CR, median |diff| {(cmp_.cr_ytd_q4 - cmp_.audited_CR).abs().median():.2f} pp, "
      f"red-zone agreement {((cmp_.cr_ytd_q4 > 110) == (cmp_.audited_CR > 110)).mean():.3f} (n {len(cmp_)})")
print(); print(R.round(3).to_string(index=False))
p = R[(R.analysis.str.startswith('PRIMARY')) & (R.score == 'cr_ytd_q2')].iloc[0]
d = R[(R.analysis.str.startswith('PRIMARY')) & (R.score == 'DIFF cr_ytd_q2 - audited_CR_L1')].iloc[0]
v = 'STRONG' if p.auc >= 0.80 else 'NOT STRONG'
print(f"\nVERDICT (primary target): {v}. Q2 YTD CR AUC {p.auc:.3f} [{p.ci_lo:.3f}, {p.ci_hi:.3f}], n {p.n} ({p.n_red} red). "
      f"Q2 minus audited CR(t-1): {d.auc:+.3f}, paired 95% CI [{d.ci_lo:+.3f}, {d.ci_hi:+.3f}]"
      f"{' -- CI INCLUDES 0' if d.ci_lo <= 0 <= d.ci_hi else ''} (n {d.n}).")
