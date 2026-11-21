"""Step 12: returns-based component panel (Tier 2) from the NIC quarterly returns workbook.

Source: the NIC quarterly returns workbook (an NIC product, source confirmed; the figures are insurers' unaudited
quarterly submissions). data_issues A15, A17-A19. Insurer-level outputs -> data/processed/confidential/ (git-ignored,
decision A2); aggregate tables -> outputs/tables/. Skips (exit 0) if the workbook is absent: the public pipeline then
reproduces the v1 (Tier 1) results only. Runs after step 02 and before step 03 (decision A4); Tier 1 comes from
src/tier1.py, the reading rules from src/returns_io.py (shared with step 09).

Reading. Every sheet 'Qq YYYY' (Q1 2013 - Q1 2026); last header row; rows down to the total row. Every header must
map to a variable (HMAP4 for 2013-2023, IFRS 4; HMAP17 for 2024+, IFRS 17) or be on the IGNORE list; any other header
STOPS the step. Unmapped insurer names STOP the step, except the HOLD_OUT rows listed below. Ratio columns: unit per
sheet and column (median of |values| < 3 -> fraction, x 100). Sheets are year-to-date (YTD); flows also get quarterly
increments (Qq - Qq-1 of the same insurer-year; Q1 = YTD).

Derived, IFRS 4 years 2013-2023 (percent; codebook):
  NEP     = net earned premium column (2021+); else implied NEP = claims / (workbook claims ratio / 100);
            not recoverable if claims <= 0 or the claims ratio is missing or <= 0
  LR_c = claims / NEP; ER_c = (management + commission) / NEP; CR_c = LR_c + ER_c
  ER_gross = (management + commission) / GWP; ER_netric = (management + commission - RIC) / NEP (missing if RIC blank:
  blank RIC is MISSING, never zero); COMM_r = commission / NEP; MGT_r = management / NEP; RET_c = NWP / GWP;
  ln_assets = ln(total assets) if > 0; TP_r = technical provisions / NEP (2021+); motor_share = motor GWP / GWP (2021+)
  Before 2021, LR_c equals the workbook's own claims ratio BY CONSTRUCTION (NEP is implied from it).
IFRS 17 (2024+): extracted into i17_* columns only, never mixed with 2013-2023.

Gaps (A18): Q2 2022 expense-ratio column is a copy of the claims ratio (detected: >= 90% of rows equal), so it is
ignored; ER_c is always recomputed from components. Q1/Q3 2017 claims are under 'claim expenses' and are used.
Cells: Excel error codes ('#REF!' etc.) -> missing; numbers stored as text -> parsed; any other text STOPS the step.
Copy-forward (Qq identical to Qq-1 on every shared money column, >= 3 values) is flagged; at Q4 the concordance check
decides which rows are stale. Rows with no figures (only derived columns such as market share, or nothing) -> missing.

Annual panel = Q4 rows. Concordance with Tier 1, 2015-2023: pass if |Q4 GWP - audited GWP| <= max(5%, GHS 0.5m).
Fill rule (2d): where Q4 fails or is missing, the annual columns gwp_a, RET_a, LR_a, ER_a, CR_a come from Tier 1 and
are flagged 'filled from annual'; components and assets stay missing.
"""
import sys
import numpy as np, pandas as pd
from config import QUARTERLY_FILE, CONFIDENTIAL, TABLES, MERGERS
from returns_io import map_id, norm, sheet_quarter, header_row, data_rows
import tier1
if not QUARTERLY_FILE.exists():
    print("NIC quarterly returns workbook not found; skipping step 12 (v2 returns panel). "
          "The public pipeline reproduces v1 (Tier 1) results only."); sys.exit(0)
import openpyxl

# ---------------------------------------------------------------- header maps (decision A3)
HMAP4 = {'gwp': ['gross written premium', 'gross premium', 'gross premiums'],
         'nwp': ['net written premium', 'net premiums written', 'net written premiums'],
         'nep': ['net earned premiums'],
         'claims': ['incurred claims', 'claims expense', 'claim expenses', 'net claims incurred'],
         'gross_claims': ['gross claims incurred'],
         'mgmt': ['management expense', 'management expenses'],
         'comm': ['commission expense', 'gross commissions expense', 'commsission expenses'],
         'ric': ['commission income', 'reinsurance commission income'],
         'tp': ['technical provision'],
         'total_assets': ['total assets'],
         'motor_gwp': ['motor'],
         'LR_wb': ['claims ratio', 'claims ratio %'],
         'ER_wb': ['expense ratio', 'expense ratio %', 'expense'],
         'CR_wb': ['combined ratio %']}
HMAP17 = {'i17_revenue': ['insurance service revenue', 'insurance revenue'],
          'i17_service_expenses': ['total insurance service expenses', 'insurance services expenses'],
          'i17_result_gross': ['insurance results', 'insurance service result from insurance contracts issued'],
          'i17_service_result': ['insurance service results', 'insurance service result'],
          'i17_incurred_claims': ['total incurred claims'],
          'i17_nonattrib_exp': ['non-attributable expenses'],
          'i17_acq_cf': ['acquisition cashflow'],
          'i17_attrib_exp': ['total attributable expenses'],
          'i17_total_assets': ['total assets'],
          'i17_motor_comp': ['motor comprehensive'], 'i17_motor_tp': ['motor third party'],
          'i17_motor_tpft': ['motor third party, fire & theft'], 'i17_motor_other': ['motor - others', 'motor others'],
          'i17_LR_wb': ['claims ratio'], 'i17_ER_wb': ['expense ratio'],
          'i17_attrib_ER_wb': ['attributable expense ratio'], 'i17_nonattrib_ER_wb': ['non-attributable expense ratio'],
          'i17_tech_margin_wb': ['technical results margin']}
IGNORE = {  # class premiums other than motor, balance-sheet and income items not used, market share
    'fire, theft & property', 'fire, theft and property (private)', 'fire, theft and property (commercial)',
    'marine & aviation', 'marine cargo', 'marine hull', 'aviation', 'engineering', 'engineering others',
    'engineering- others', 'engineering-all risk', 'bonds', 'bonds/financial guarantee', 'bonds/financial guarantees',
    'personal accident, health & medical', 'liability', 'others', 'accident- public liability',
    'accident- professional indemnity', 'accident- travel', "workman compensation/ employer's liability",
    'workmen compensation/ employers liability', 'accident- personal', 'accident- others', 'agric -others',
    'agric others', 'agric area index', 'agric weather index', 'agriculture area index', 'agriculture weather index',
    'agric poultry & livestock', 'microinsurance', 'non-life microinsurance', 'motor - others',
    'investment', 'investments', 'investment income', 'total investment income', 'net investment income',
    'inv. assets', 'total investments', 'cash balance', 'cash balances', 'cash and cash equivalents', 'receivables',
    'total receivables', 'ppes', 'total property, plant & equipment', 'intangibles', 'other assets', 'payables',
    'total liabilities', 'insurance contract assets', 'insurance contract liabilities', 'reinsurance contract assets',
    'reinsurance contract liabilities', 'market share', 'market share (%)', 'profit after tax', 'profit before tax',
    'profit for the year', 'other income', 'total other income', 'total other income/ expense',
    'total other income and expenses', 'underwriting profit', 'underwriting income',
    'total insurance finance income/ expense', 'total insurance finance income or expenses',
    'share of insurance service results'}
RATIOS = ['LR_wb', 'ER_wb', 'CR_wb', 'i17_LR_wb', 'i17_ER_wb', 'i17_attrib_ER_wb', 'i17_nonattrib_ER_wb', 'i17_tech_margin_wb']
FLOWS4 = ['gwp', 'nwp', 'nep', 'claims', 'gross_claims', 'mgmt', 'comm', 'ric', 'motor_gwp']
FLOWS17 = ['i17_revenue', 'i17_service_expenses', 'i17_result_gross', 'i17_service_result', 'i17_incurred_claims',
           'i17_nonattrib_exp', 'i17_acq_cf', 'i17_attrib_exp', 'i17_motor_comp', 'i17_motor_tp', 'i17_motor_tpft',
           'i17_motor_other']
STOCKS = ['tp', 'total_assets', 'i17_total_assets']
MONEY = FLOWS4 + FLOWS17 + STOCKS                                   # 'figures' = any of these present
# Rows held out pending a mapping decision (reported, never silently mapped)
HOLD_OUT = {('regency insurance ghana limited', 2016, 1):
            'Regency listed separately from NEM in Q1 2016; step 09 alias covers Regency only to 2015'}

lookup = {}
for era, hm in (('ifrs4', HMAP4), ('ifrs17', HMAP17)):
    for var, hs in hm.items():
        for h in hs: lookup[(era, h)] = var

# ---------------------------------------------------------------- read every quarterly sheet
wb = openpyxl.load_workbook(QUARTERLY_FILE, data_only=True, read_only=True)
recs, unmatched, unmapped, held, nonnum, dupvar, cells = [], {}, [], [], {}, [], []   # cells: non-numeric cells handled
for s in wb.sheetnames:
    qy = sheet_quarter(s)
    if not qy: continue
    q, y = qy; era = 'ifrs4' if y <= 2023 else 'ifrs17'
    rows = list(wb[s].iter_rows(values_only=True))
    h, hn, nc = header_row(rows)
    cols = {}
    for i, c in enumerate(hn):
        if not c or i == nc: continue
        v = lookup.get((era, c))
        if v is None:
            if c not in IGNORE: unmatched.setdefault(c, []).append(s)
            continue
        if v in cols.values(): dupvar.append((s, v, c))
        cols[i] = v
    for r, nm in data_rows(rows, h, nc):
        cid = map_id(nm, y)
        if cid is None:
            why = HOLD_OUT.get((norm(nm).replace('*', ''), y, q))
            (held if why else unmapped).append((s, nm, why)); continue
        rec = dict(sheet=s, year=y, quarter=q, era=era, source_name=nm, insurer_id=cid)
        for i, v in cols.items():
            x = r[i] if i < len(r) else None
            if isinstance(x, (int, float)) and not isinstance(x, bool): rec[v] = float(x); continue
            rec[v] = np.nan
            t = str(x).strip() if x is not None else ''
            if t in ('', '-'): continue
            if t.startswith('#'): cells.append((s, nm, v, t, 'Excel error -> missing')); continue
            try: rec[v] = float(t.replace(',', '')); cells.append((s, nm, v, t, 'number stored as text -> parsed'))
            except ValueError: nonnum.setdefault(v, []).append((s, nm, x))
        recs.append(rec)
stop = []
if unmatched: stop.append('Unmatched headers:\n' + '\n'.join(f'  {c!r}: {v}' for c, v in unmatched.items()))
if dupvar: stop.append('Two headers map to one variable in a sheet:\n' + '\n'.join(map(str, dupvar)))
if unmapped: stop.append('Unmapped insurer names:\n' + '\n'.join(f'  {s}: {n!r}' for s, n, _ in unmapped))
if nonnum: stop.append('Non-numeric values in mapped columns:\n' + '\n'.join(f'  {v}: {x[:5]}' for v, x in nonnum.items()))
if stop: sys.exit('STOP (step 12):\n' + '\n'.join(stop))

Q = pd.DataFrame(recs)
for v in set(HMAP4) | set(HMAP17):
    if v not in Q: Q[v] = np.nan
dup = Q[Q.insurer_id != 'EXCLUDED'].duplicated(['insurer_id', 'year', 'quarter'], keep=False)
if dup.any(): sys.exit('STOP (step 12): several rows per insurer-quarter:\n' + Q[dup.reindex(Q.index, fill_value=False)][['sheet', 'insurer_id', 'source_name']].to_string())

# ---------------------------------------------------------------- units (per sheet and ratio column)
units = []
for (s, v), d in Q.melt(id_vars=['sheet'], value_vars=RATIOS).dropna().groupby(['sheet', 'variable']):
    med = float(d.value.abs().median()); frac = med < 3
    units.append(dict(sheet=s, column=v, n=len(d), median_abs=med, unit='fraction (x100)' if frac else 'percent'))
    if frac: Q.loc[Q.sheet == s, v] = Q.loc[Q.sheet == s, v] * 100
U = pd.DataFrame(units)
# Q2 2022-type defect: expense ratio identical to claims ratio in >= 90% of a sheet's rows -> ignore that column
er_bad = []
for s, d in Q[Q.era == 'ifrs4'].groupby('sheet'):
    both = d[['LR_wb', 'ER_wb']].dropna()
    if len(both) and (both.LR_wb == both.ER_wb).mean() >= 0.9:
        er_bad.append((s, len(both), int((both.LR_wb == both.ER_wb).sum()))); Q.loc[Q.sheet == s, 'ER_wb'] = np.nan
Q['er_wb_defective_sheet'] = Q.sheet.isin([s for s, _, _ in er_bad])

# ---------------------------------------------------------------- figures, copy-forward, increments
Q['has_figures'] = Q[MONEY].notna().any(axis=1)
Q = Q.sort_values(['insurer_id', 'year', 'quarter']).reset_index(drop=True)
prevq = Q.groupby(['insurer_id', 'year']).shift()                  # previous row of the same insurer-year
consec = Q.quarter.sub(Q.groupby(['insurer_id', 'year']).quarter.shift()).eq(1)
def copy_fwd(i):
    if not consec.iat[i]: return False
    a, b = Q.loc[i, MONEY], prevq.loc[i, MONEY]
    m = a.notna() & b.notna()
    return bool(m.sum() >= 3 and (a[m] == b[m]).all())
Q['flag_copy_forward'] = [copy_fwd(i) for i in range(len(Q))]
for v in FLOWS4 + FLOWS17:
    inc = Q[v] - prevq[v]
    Q[v + '_inc'] = np.where(Q.quarter == 1, Q[v], np.where(consec, inc, np.nan))

# ---------------------------------------------------------------- derived ratios (YTD basis; IFRS 4 only)
i4 = Q.era == 'ifrs4'
pos = lambda s: s.where(s > 0)
impl = Q.claims / (Q.LR_wb / 100)
ok_impl = (Q.claims > 0) & (Q.LR_wb > 0)
Q['NEP'] = np.where(i4 & Q.nep.notna(), Q.nep, np.where(i4 & ok_impl, impl, np.nan))
Q['nep_source'] = np.select([~i4, Q.nep.notna(), ok_impl], ['IFRS 17 (not derived)', 'column', 'implied from claims ratio'],
                            default='not recoverable')
NEP, exp = pos(Q.NEP), Q.mgmt + Q.comm
Q['LR_c'] = 100 * Q.claims / NEP
Q['ER_c'] = 100 * exp / NEP
Q['CR_c'] = Q.LR_c + Q.ER_c
Q['ER_gross'] = 100 * exp / pos(Q.gwp)
Q['ER_netric'] = 100 * (exp - Q.ric) / NEP                          # NaN where RIC is blank (never zero-filled)
Q['COMM_r'] = 100 * Q.comm / NEP
Q['MGT_r'] = 100 * Q.mgmt / NEP
Q['RET_c'] = 100 * Q.nwp / pos(Q.gwp)
Q['ln_assets'] = np.log(pos(Q.total_assets))
Q['TP_r'] = 100 * Q.tp / NEP
Q['motor_share'] = 100 * Q.motor_gwp / pos(Q.gwp)
Q['i17_motor_gwp'] = Q[['i17_motor_comp', 'i17_motor_tp', 'i17_motor_tpft', 'i17_motor_other']].sum(axis=1, min_count=1)
Q['i17_CR_wb'] = Q.i17_LR_wb + Q.i17_ER_wb
mrg = {(m['insurer_id'], m['year']) for m in MERGERS}
Q['merger_year'] = [(i, y) in mrg for i, y in zip(Q.insurer_id, Q.year)]
CONFIDENTIAL.mkdir(parents=True, exist_ok=True)
EXC = Q[Q.insurer_id == 'EXCLUDED'].copy()
Q = Q[Q.insurer_id != 'EXCLUDED'].copy()
Q.to_csv(CONFIDENTIAL / 'returns_quarterly.csv', index=False)
U.to_csv(TABLES / 'returns_units.csv', index=False)

# ---------------------------------------------------------------- Tier 1 and the annual panel (Q4)
_, ins = tier1.preferred_long()
T = tier1.add_cr(tier1.panel(ins))[['insurer_id', 'year', 'gwp', 'LR', 'ER', 'CR', 'CR_nic', 'RET', 'cr_nic_mismatch']]
T = T[T.year <= 2023].add_suffix('_t1').rename(columns={'insurer_id_t1': 'insurer_id', 'year_t1': 'year'})
Q4 = Q[(Q.quarter == 4) & (Q.year <= 2025)]
A = Q4.merge(T, on=['insurer_id', 'year'], how='outer')
A['in_tier1'] = A.gwp_t1.notna() | A.LR_t1.notna()
A['has_q4_row'] = A.sheet.notna()
A['has_figures'] = A.has_figures.fillna(False).astype(bool)
diff = (A.gwp - A.gwp_t1).abs()
A['gwp_rel_diff'] = diff / A.gwp_t1
A['concordance'] = np.select(
    [A.year <= 2014, A.year >= 2024, ~A.has_q4_row, ~A.has_figures, A.gwp_t1.isna(),
     diff <= np.maximum(0.05 * A.gwp_t1, 0.5e6)],
    ['not checked: no audited GWP (2013-14)', 'not checked: IFRS 17', 'no Q4 row', 'Q4 row without figures',
     'not checked: no audited GWP', 'pass'], default='fail')
passed = A.concordance.eq('pass')
COMP = ['NEP', 'LR_c', 'ER_c', 'CR_c', 'ER_gross', 'ER_netric', 'COMM_r', 'MGT_r', 'RET_c', 'ln_assets', 'TP_r',
        'motor_share', 'total_assets']
chk = A.year.between(2015, 2023)
A.loc[chk & ~passed, COMP] = np.nan                                  # failing / missing Q4: components stay missing
# annual columns: returns where concordance passes and the ratio exists; otherwise Tier 1, flagged
comp_ok = passed & A[['LR_c', 'ER_c', 'RET_c']].notna().all(axis=1)
fill = chk & A.in_tier1 & ~comp_ok
A['annual_source'] = np.select([chk & comp_ok, fill & passed, fill, A.year <= 2014, A.year >= 2024],
                               ['returns (concordance pass)', 'filled from annual (components incomplete)',
                                'filled from annual', 'returns (not checked: 2013-14)', 'IFRS 17 (i17_ columns only)'],
                               default='returns only (not in Tier 1)')
for a, c, t in [('gwp_a', 'gwp', 'gwp_t1'), ('RET_a', 'RET_c', 'RET_t1'), ('LR_a', 'LR_c', 'LR_t1'), ('ER_a', 'ER_c', 'ER_t1')]:
    A[a] = np.where(fill, A[t], np.where(A.year >= 2024, np.nan, A[c]))
A['CR_a'] = A.LR_a + A.ER_a

# ---------------------------------------------------------------- non-submission (2f): quarters without figures
fig = Q[Q.has_figures].groupby(['insurer_id', 'year']).quarter.nunique().rename('n_quarters_with_figures')
uni = pd.concat([Q[Q.has_figures][['insurer_id', 'year']], T[['insurer_id', 'year']]]).drop_duplicates()
uni = uni[uni.year <= 2025].merge(fig, on=['insurer_id', 'year'], how='left').fillna({'n_quarters_with_figures': 0})
uni['n_quarters_no_figures'] = 4 - uni.n_quarters_with_figures.astype(int)
A = A.merge(uni[['insurer_id', 'year', 'n_quarters_no_figures']], on=['insurer_id', 'year'], how='left')
NS = uni.groupby('year').n_quarters_no_figures.value_counts().unstack(fill_value=0).reindex(columns=range(5), fill_value=0)
NS.columns = [f'insurer_years_{k}_quarters_missing' for k in NS.columns]
NS.insert(0, 'insurer_years', uni.groupby('year').size())
NS.reset_index().to_csv(TABLES / 'returns_nonsubmission.csv', index=False)

keep = ['insurer_id', 'year', 'source_name', 'in_tier1', 'has_q4_row', 'has_figures', 'flag_copy_forward', 'merger_year',
        'concordance', 'gwp_rel_diff', 'annual_source', 'n_quarters_no_figures', 'gwp', 'gwp_t1', 'gwp_a', 'nwp', 'NEP',
        'nep_source', 'claims', 'gross_claims', 'mgmt', 'comm', 'ric', 'tp', 'total_assets', 'motor_gwp',
        'LR_c', 'ER_c', 'CR_c', 'ER_gross', 'ER_netric', 'COMM_r', 'MGT_r', 'RET_c', 'ln_assets', 'TP_r', 'motor_share',
        'LR_a', 'ER_a', 'CR_a', 'RET_a', 'LR_wb', 'ER_wb', 'CR_wb', 'LR_t1', 'ER_t1', 'CR_t1', 'CR_nic_t1', 'RET_t1',
        'cr_nic_mismatch_t1'] + [c for c in Q.columns if c.startswith('i17_') and not c.endswith('_inc')]
A = A[keep].sort_values(['insurer_id', 'year']).reset_index(drop=True)
A.to_csv(CONFIDENTIAL / 'returns_panel.csv', index=False)

# ---------------------------------------------------------------- concordance (2c)
C = A[A.year.between(2015, 2023) & A.in_tier1]
crow = []
for y, d in list(C.groupby('year')) + [('2015-2023', C)]:
    p = d[d.concordance == 'pass']
    r = dict(year=y, tier1_insurer_years=len(d), q4_rows=int(d.has_q4_row.sum()),
             q4_without_figures=int((d.concordance == 'Q4 row without figures').sum()), no_q4_row=int((d.concordance == 'no Q4 row').sum()),
             concordance_pass=len(p), concordance_fail=int((d.concordance == 'fail').sum()),
             copy_forward_q4=int(d.flag_copy_forward.fillna(False).astype(bool).sum()),
             copy_forward_q4_pass=int(p.flag_copy_forward.fillna(False).astype(bool).sum()),
             filled_from_annual=int(d.annual_source.str.startswith('filled').sum()))
    for c, t in [('LR_c', 'LR_t1'), ('ER_c', 'ER_t1'), ('CR_c', 'CR_nic_t1'), ('CR_c', 'CR_t1')]:
        e = (p[c] - p[t]).abs().dropna()
        r.update({f'{c}_vs_{t}_n': len(e), f'{c}_vs_{t}_within_1pp': (e <= 1).mean() if len(e) else np.nan,
                  f'{c}_vs_{t}_within_5pp': (e <= 5).mean() if len(e) else np.nan, f'{c}_vs_{t}_median_abs': e.median()})
    crow.append(r)
CC = pd.DataFrame(crow); CC.to_csv(TABLES / 'returns_concordance.csv', index=False)
P5 = C[C.concordance == 'pass'].copy()
det = []
for c, t in [('LR_c', 'LR_t1'), ('ER_c', 'ER_t1'), ('CR_c', 'CR_nic_t1')]:
    d = P5[(P5[c] - P5[t]).abs() > 5]
    det += [dict(insurer_id=r.insurer_id, year=r.year, comparison=f'{c} vs {t}', returns=r[c], tier1=r[t],
                 diff=r[c] - r[t], nep_source=r.nep_source, flag_copy_forward=r.flag_copy_forward) for _, r in d.iterrows()]
DET = pd.DataFrame(det); DET.to_csv(CONFIDENTIAL / 'returns_concordance_detail.csv', index=False)
# 2015-16 cr_nic_mismatch rows: does the returns ER match CR_nic - LR (the typo hypothesis) or the printed ER?
MM = C[C.year.isin([2015, 2016]) & C.cr_nic_mismatch_t1.fillna(False).astype(bool)].copy()
MM['ER_implied_by_CRnic'] = MM.CR_nic_t1 - MM.LR_t1
MM['abs_diff_vs_CRnic_minus_LR'] = (MM.ER_c - MM.ER_implied_by_CRnic).abs()
MM['abs_diff_vs_printed_ER'] = (MM.ER_c - MM.ER_t1).abs()
MM['abs_diff_LR_c_vs_LR'] = (MM.LR_c - MM.LR_t1).abs()
MM[['insurer_id', 'year', 'concordance', 'nep_source', 'LR_t1', 'ER_t1', 'CR_nic_t1', 'ER_implied_by_CRnic', 'LR_c', 'ER_c',
    'abs_diff_LR_c_vs_LR', 'abs_diff_vs_CRnic_minus_LR', 'abs_diff_vs_printed_ER']].to_csv(CONFIDENTIAL / 'returns_mismatch_2015_16.csv', index=False)
mp = MM[MM.concordance == 'pass'].dropna(subset=['ER_c'])
mm_sum = dict(mismatch_rows=len(MM), concordance_pass=int((MM.concordance == 'pass').sum()), with_ER_c=len(mp),
              ER_c_within_1pp_of_CRnic_minus_LR=int((mp.abs_diff_vs_CRnic_minus_LR <= 1).sum()),
              ER_c_within_5pp_of_CRnic_minus_LR=int((mp.abs_diff_vs_CRnic_minus_LR <= 5).sum()),
              ER_c_within_1pp_of_printed_ER=int((mp.abs_diff_vs_printed_ER <= 1).sum()),
              ER_c_within_5pp_of_printed_ER=int((mp.abs_diff_vs_printed_ER <= 5).sum()),
              closer_to_CRnic_minus_LR=int((mp.abs_diff_vs_CRnic_minus_LR < mp.abs_diff_vs_printed_ER).sum()),
              LR_c_within_1pp_of_LR=int((mp.abs_diff_LR_c_vs_LR <= 1).sum()))
pd.DataFrame([mm_sum]).to_csv(TABLES / 'returns_mismatch_2015_16_summary.csv', index=False)

# ---------------------------------------------------------------- NEP validation (2021-23: column vs implied)
nv = []
for lab, d in [('Q4', Q[(Q.quarter == 4)]), ('all quarters', Q)]:
    d = d[d.year.between(2021, 2023) & (d.nep > 0) & (d.claims > 0) & (d.LR_wb > 0)]
    for den, x in [('NEP', d.nep), ('NEP + RIC', d.nep + d.ric)]:
        r = (d.claims / (d.LR_wb / 100)) / x; r = r.dropna()
        nv.append(dict(quarters=lab, implied_over=den, n=len(r), p10=r.quantile(.1), p25=r.quantile(.25), median=r.median(),
                       p75=r.quantile(.75), p90=r.quantile(.9), within_1pct=((r - 1).abs() <= .01).mean(),
                       within_5pct=((r - 1).abs() <= .05).mean()))
NV = pd.DataFrame(nv); NV.to_csv(TABLES / 'returns_nep_validation.csv', index=False)

# ---------------------------------------------------------------- seasonality (2e)
# Sample per insurer-year: figures in all 4 quarters, positive Q4 GWP (IFRS 17: Insurance Revenue), not a merger year,
# no copy-forward quarter. IFRS 4 years use GWP and net claims; 2024-25 use Insurance Revenue and IFRS 17 incurred claims.
S = Q[Q.year <= 2025].copy()
S['prem'] = np.where(S.era == 'ifrs4', S.gwp, S.i17_revenue)
S['clm'] = np.where(S.era == 'ifrs4', S.claims, S.i17_incurred_claims)
g = S.groupby(['insurer_id', 'year'])
S['n_q'] = g.prem.transform(lambda x: x.notna().sum()); S['any_cf'] = g.flag_copy_forward.transform('any')
q4p = S[S.quarter == 4].set_index(['insurer_id', 'year']).prem
S['prem_q4'] = [q4p.get((i, y), np.nan) for i, y in zip(S.insurer_id, S.year)]
S = S[(S.n_q == 4) & (S.prem_q4 > 0) & ~S.merger_year & ~S.any_cf]
S['share'] = S.prem / S.prem_q4
seas = []
add = lambda sec, yr, q, stat, val, basis='', note='': seas.append(dict(section=sec, year=yr, quarter=q, statistic=stat,
                                                                          value=val, basis=basis, note=note))
for yr, d in S.groupby('year'):
    basis = 'GWP; net claims (IFRS 4)' if yr <= 2023 else 'Insurance Revenue; incurred claims (IFRS 17)'
    tot = d[d.quarter == 4].prem.sum()
    cl = d.dropna(subset=['clm']); cl = cl[cl.groupby('insurer_id').quarter.transform('size') == 4]
    tcl = cl[cl.quarter == 4].clm.sum()
    for q in (1, 2, 3, 4):
        add('industry_cumulative_share', yr, q, 'premium', d[d.quarter == q].prem.sum() / tot, basis)
        add('industry_cumulative_share', yr, q, 'claims', cl[cl.quarter == q].clm.sum() / tcl if tcl else np.nan, basis)
    add('industry_cumulative_share', yr, '', 'n_insurers', d.insurer_id.nunique(), basis)
I = S[S.year.between(2015, 2023)]
for q in (1, 2):
    v = I[I.quarter == q].share
    for p in (10, 25, 50, 75, 90):
        add('insurer_cumulative_share_2015_2023', '2015-2023', q, f'p{p}', v.quantile(p / 100), 'GWP')
    add('insurer_cumulative_share_2015_2023', '2015-2023', q, 'n', len(v), 'GWP')
q1 = S[S.quarter == 1].set_index(['insurer_id', 'year']).share
pairs = [(q1[(i, y)], q1[(i, y - 1)]) for i, y in q1.index if 2016 <= y <= 2023 and (i, y - 1) in q1.index]
pr = pd.DataFrame(pairs, columns=['t', 't_1'])
add('q1_share_persistence', '2016-2023 vs t-1', 1, 'pearson', pr.t.corr(pr.t_1), 'GWP')
add('q1_share_persistence', '2016-2023 vs t-1', 1, 'spearman', pr.t.corr(pr.t_1, method='spearman'), 'GWP')
add('q1_share_persistence', '2016-2023 vs t-1', 1, 'n_pairs', len(pr), 'GWP')
ind = pd.DataFrame([r for r in seas if r['section'] == 'industry_cumulative_share' and r['statistic'] == 'premium'
                    and isinstance(r['year'], (int, np.integer)) and 2015 <= r['year'] <= 2023])
cum = ind.pivot(index='year', columns='quarter', values='value')
inc = cum.diff(axis=1); inc[1] = cum[1]; s_q = inc.mean()
f_q = {1: 7 / 8, 2: 5 / 8, 3: 3 / 8, 4: 1 / 8}
for q in (1, 2, 3, 4):
    add('earning', '2015-2023 avg', q, 'incremental_premium_share', s_q[q], 'GWP')
    add('earning', '2015-2023 avg', q, 'earned_in_year_factor', f_q[q], 'GWP', 'mid-quarter writing, 12-month policies')
e1 = float(sum(s_q[q] * f_q[q] for q in f_q))
add('earning', '2015-2023 avg', '', 'share_of_year_premium_earned_in_same_year', e1, 'GWP')
add('earning', '2015-2023 avg', '', 'share_earned_in_following_year', 1 - e1, 'GWP')
SE = pd.DataFrame(seas); SE.to_csv(TABLES / 'seasonality.csv', index=False)

# ---------------------------------------------------------------- survivorship (2g)
# Insurers in any Q4 sheet 2013-2018 but absent from Tier 1 (the step 09 EXCLUDE list)
tot4 = pd.concat([Q, EXC])[lambda d: d.quarter == 4].groupby('year').gwp.sum()
SV = EXC[(EXC.quarter == 4) & EXC.year.between(2013, 2018)].copy()
SV['market_share_pct'] = 100 * SV.gwp / SV.year.map(tot4)
SV[['source_name', 'year', 'has_figures', 'gwp', 'market_share_pct', 'LR_wb', 'ER_wb', 'CR_wb']].to_csv(
    CONFIDENTIAL / 'returns_survivorship.csv', index=False)
last_q = EXC.groupby('source_name').apply(lambda d: d[d.has_figures].sheet.iloc[-1] if d.has_figures.any() else 'none',
                                          include_groups=False)
SVS = SV.groupby('year').agg(insurers=('source_name', 'nunique'), with_figures=('has_figures', 'sum'),
                             combined_market_share_pct=('market_share_pct', 'sum')).reset_index()
# small cells: a 'combined' share over 1-2 insurers is an insurer-level workbook value (A2) -> suppressed here
SVS['combined_market_share_pct'] = SVS.combined_market_share_pct.where(SVS.insurers >= 3)
SVS['note'] = np.where(SVS.insurers >= 3, '', 'share suppressed (< 3 insurers); detail in data/processed/confidential/')
SVS.to_csv(TABLES / 'returns_survivorship_summary.csv', index=False)

# ---------------------------------------------------------------- printed summary
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 40)
print(f"Read {Q.sheet.nunique()} quarterly sheets, {len(Q)} insurer-quarter rows ({len(EXC)} excluded-insurer rows: "
      f"{sorted(EXC.source_name.unique())}).")
print('Held out (not mapped, pending decision):', [(s, n) for s, n, _ in held])
print('Non-numeric cells handled (Excel errors -> missing; numbers stored as text -> parsed):', cells)
print('Units: sheets/columns in fractions ->', U[U.unit.str.startswith('fraction')].groupby('column').sheet.apply(list).to_dict())
print('Expense-ratio column ignored (copy of claims ratio):', er_bad)
q3_2018 = pd.concat([Q, EXC])[lambda d: (d.year == 2018) & (d.quarter == 3)]
print(f"Q3 2018: {len(q3_2018)} rows; not in the panel: {EXC[(EXC.year == 2018) & (EXC.quarter == 3)][['source_name', 'has_figures']].values.tolist()}")
print('YTD check, median Q2 / Q4 GWP by year:', Q[Q.era == 'ifrs4'].pivot_table(index=['insurer_id', 'year'], columns='quarter', values='gwp')
      .pipe(lambda w: (w[2] / w[4]).groupby(level=1).median()).round(2).to_dict())
print('\nNEP validation 2021-23 (implied NEP / actual):'); print(NV.round(3).to_string(index=False))
print('\nConcordance with Tier 1:'); print(CC.round(3).to_string(index=False))
print('\n2015-16 cr_nic_mismatch rows:', mm_sum)
print('\nNon-submission (quarters without figures):'); print(NS.to_string())
print('\nSurvivorship (Q4 2013-2018, not in Tier 1):'); print(SVS.round(2).to_string(index=False)); print('last quarter with figures:', last_q.to_dict())
sv = SE[SE.section != 'industry_cumulative_share']
print('\nSeasonality:'); print(SE[(SE.section == 'industry_cumulative_share') & (SE.statistic == 'premium')].pivot(index='year', columns='quarter', values='value').round(3).to_string())
print(sv[['section', 'year', 'quarter', 'statistic', 'value']].round(3).to_string(index=False))
print('Saved (aggregate): returns_units, returns_concordance, returns_mismatch_2015_16_summary, returns_nep_validation, '
      'returns_nonsubmission, returns_survivorship_summary, seasonality (outputs/tables). Insurer-level: data/processed/confidential/')
