"""Tier 1 = audited NIC annual reports (data/raw/nic_text via steps 01-02).

Shared by step 03 (analysis panel) and step 12 (returns panel: concordance and fill rule), so both read the same
audited figures. Moved unchanged from step 03 (v2 refactor, decision A4); step 03's output is byte-identical.

Vintage rule: GWP and PAT for 2015-2019 come from the 2019 report (exact GHS); everything else from the latest
report containing it. Overlapping vintages agree exactly (07_validate.py), so the rule affects precision only.
"""
import pandas as pd
from config import INTERIM

RENAME = {'loss_ratio': 'LR', 'expense_ratio': 'ER', 'combined_ratio': 'CR_nic', 'retention': 'RET',
          'net_risk_ratio': 'LEV_net', 'gross_risk_ratio': 'LEV_gross'}

def preferred_long():
    """(all-vintage long table, preferred-vintage long table incl. the 'pref' sort key)."""
    df = pd.read_csv(INTERIM / 'nic_long_all_vintages.csv')
    ins = df[~df.insurer_id.str.startswith(('TOTAL', 'NIC'))].copy()
    ins['vint'] = ins.source_report.str[-4:].astype(int)
    ins['pref'] = -ins.vint
    m = (ins.variable.isin(['gwp', 'pat'])) & (ins.year <= 2019) & (ins.vint == 2019)
    ins.loc[m, 'pref'] = -9999
    ins = ins.sort_values('pref').drop_duplicates(['insurer_id', 'year', 'variable'])
    return df, ins

def panel(ins):
    """Insurer x year table 2015-2024 with analysis names; rows with neither GWP nor LR dropped."""
    W = ins.pivot_table(index=['insurer_id', 'year'], columns='variable', values='value', aggfunc='first').reset_index()
    P = W.rename(columns=RENAME).copy()
    P = P[P.year.between(2015, 2024)]
    return P[P.gwp.notna() | P.LR.notna()]

def add_cr(P):
    """CR constructed as LR + ER (D5); flag where NIC's printed CR differs by more than 1 point (A6, A16)."""
    P['CR'] = P.LR + P.ER
    P['cr_nic_mismatch'] = (P.CR - P.CR_nic).abs() > 1
    return P
