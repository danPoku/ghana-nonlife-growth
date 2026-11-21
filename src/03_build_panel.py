"""Step 3: choose a preferred vintage per insurer-year-variable and build the analysis panel.

Vintage rule: GWP and PAT for 2015-2019 come from the 2019 report (exact GHS);
everything else from the latest report containing it. Overlapping vintages
were found to agree exactly (see 07_validate.py), so the rule affects
precision only, not values.

Gross-basis ratios (LR_g, ER_g, CR_g; docs/data_issues.md A16). NIC's LR and ER are on a net basis
(denominator: net earned premium, NEP, plus reinsurance commission income, RIC, for LR in all reports and
for ER from the 2020 report), so an insurer that cedes much of its book has a small denominator and a high
ER. To express claims and expenses relative to GROSS premium:
    LR_g = LR x RET/100,  ER_g = ER x RET/100,  CR_g = LR_g + ER_g   (RET = NWP/GWP, %)
Approximation: it assumes NEP ~ NWP and gross earned premium ~ GWP, and it ignores RIC in NIC's denominator.
Because that denominator is NEP + RIC, ER x RET/100 = (expenses / gross earned premium) x NEP/(NEP+RIC),
so the gross-basis figures are UNDERSTATED by the factor NEP/(NEP+RIC): the direction is certain, the size
is unknown because RIC is not published per insurer. (The 2019 report's ER wording omits RIC, but its
values equal those carried in later reports, so the same factor is assumed throughout.)
CR_g is NOT an underwriting-profitability measure: it omits the net cost of reinsurance (ceded premium less
recoveries and commission). The net CR remains the profitability measure; ER_g measures operating
efficiency only.
2023-24 (IFRS 17): ER is already over gross Insurance Revenue, so ER x RET/100 would deflate it twice; LR_g,
ER_g and CR_g are left missing for those years (they are not estimated). The industry gross series in step
04 handles 2023-24 separately.
"""
import pandas as pd, numpy as np, json, re
from config import INTERIM, PROCESSED, RAW_MACRO, WDI_CPI_FILE, MERGERS, QUARTERLY_FILE, CONFIDENTIAL, TABLES
import tier1   # vintage rule, Tier 1 table and CR rule, shared with step 12 (A4)

df, ins = tier1.preferred_long()
ins.drop(columns=['pref']).to_csv(INTERIM/'nic_long_preferred.csv', index=False)
L = df
NAMES={'ACTIVA':'Activa International','ALLIANZ':'Allianz Insurance','BEDROCK':'Bedrock Insurance','BEST':'Best Assurance',
'CORONATION':'Coronation Insurance (formerly WAPIC)','DONEWELL':'Donewell Insurance','ENTERPRISE':'Enterprise Insurance',
'GUA':'Ghana Union Assurance','GLICO_GEN':'Glico General','HERITAGE':'Heritage (Energy) Insurance','HOLLARD':'Hollard Insurance',
'IMPERIAL':'Imperial General','LOYALTY':'Loyalty Insurance','MILLENNIUM':'Millennium Insurance','MULTI':'Multi Insurance',
'NSIA':'NSIA Ghana','PHOENIX':'Phoenix Insurance','PRIME':'Prime Insurance','PRIORITY':'Priority Insurance','PROVIDENT':'Provident Insurance',
'QUALITY':'Quality Insurance','REGENCYNEM':'RegencyNem Insurance','SAHAM_SANLAM':'Saham / Sanlam / SanlamAllianz','SERENE':'Serene Insurance',
'SIC':'SIC Insurance','STAR':'Star Assurance','SUNU':'SUNU Assurances','UNIQUE':'Unique Insurance','VANGUARD':'Vanguard Assurance'}
P=tier1.panel(ins)
P['insurer_name']=P.insurer_id.map(NAMES)
P=P.sort_values(['insurer_id','year']).reset_index(drop=True)
# market totals (insurers only, GOGIP excluded)
tot=P.groupby('year').gwp.sum().rename('mkt_gwp')
P=P.merge(tot,on='year',how='left')
P['ms']=100*P.gwp/P.mkt_gwp
# lag helper requiring consecutive year
prev=P[['insurer_id','year','gwp','ms','RET','LEV_net']].copy(); prev['year']+=1
P=P.merge(prev.add_suffix('_prev').rename(columns={'insurer_id_prev':'insurer_id','year_prev':'year'}),on=['insurer_id','year'],how='left')
P['g_calc']=100*(P.gwp/P.gwp_prev-1)
# primary growth rule
P['g']=np.where(P.year<=2019,P.g_calc,np.where(P.year<=2022,P.chg_gwp_pct.fillna(P.g_calc),P.g_calc))
P.loc[(P.year<=2019)&P.g.isna(),'g']=P.chg_gwp_pct   # 2015 from NIC table (no 2014 GWP)
P['g_source']=np.select([(P.year==2015)&P.chg_gwp_pct.notna(),(P.year<=2019)&P.g_calc.notna(),(P.year.between(2020,2022))&P.chg_gwp_pct.notna(),P.g_calc.notna()],
   ['NIC change table','computed exact GHS','NIC change table','computed rounded GHS m'],default='missing')
P['g_flag_nic_disagree']=(P.g_calc-P.chg_gwp_pct).abs()>5
# merger rule (D13): growth across a merger is not organic -> missing. Applied before g_excess so the merger
# year does not move the year median; g_excess, g_real, g_real_dec and the _L1 lags follow from g.
mrg=pd.DataFrame(MERGERS)
P['merger_break']=pd.MultiIndex.from_frame(P[['insurer_id','year']]).isin(pd.MultiIndex.from_frame(mrg[['insurer_id','year']]))
assert P.merger_break.sum()==len(mrg), 'a MERGERS entry matches no insurer-year in the panel'
P.loc[P.merger_break,'g']=np.nan
mg=P.groupby('year').apply(lambda d: 100*(d.gwp.sum()/d.gwp_prev[d.gwp_prev.notna()].sum()-1) if d.gwp_prev.notna().any() else np.nan,include_groups=False).rename('g_mkt_matched')
P=P.merge(mg,on='year',how='left')
P['g_excess']=P.g-P.groupby('year').g.transform('median')
P['d_ms']=P.ms-P.ms_prev
P=tier1.add_cr(P)
# v2 (3a): 2015-16 printed-ER error (A6, A16, A19): ER_t1 := CR_nic - LR on the 2015-16 cr_nic_mismatch rows; CR_t1 = LR + ER_t1.
# Uses NIC data only, so it is public. ER and CR keep the published values (v1). Corroboration by the returns is in panel_v2.
fix1516=P.year.isin([2015,2016])&P.cr_nic_mismatch
P['ER_t1']=np.where(fix1516,P.CR_nic-P.LR,P.ER); P['CR_t1']=P.LR+P.ER_t1
P['er_t1_flag']=np.where(fix1516,'ER corrected: ER := CR_nic - LR (2015-16 printed-ER error)','')
P['nwp']=P.gwp*P.RET/100
# gross-basis ratios (see docstring; data_issues A16): understated by NEP/(NEP+RIC); missing under IFRS 17
ifrs4=P.year<=2022
P['LR_g']=np.where(ifrs4,P.LR*P.RET/100,np.nan)
P['ER_g']=np.where(ifrs4,P.ER*P.RET/100,np.nan)
P['CR_g']=P.LR_g+P.ER_g
P['ln_gwp']=np.log(P.gwp)
P['equity_proxy']=np.where(P.LEV_gross>0,P.gwp/(P.LEV_gross/100),np.nan)
first=P[P.gwp.notna()].groupby('insurer_id').year.min().rename('first_year')
P=P.merge(first,on='insurer_id',how='left')
P['entrant']=P.first_year>2015
P['firm_age_in_panel']=P.year-P.first_year
P['startup']=P.entrant&(P.firm_age_in_panel<=1)
P['post_mid']=(P.year>=2020).astype(int); P['covid']=(P.year==2020).astype(int)
P['ifrs17']=(P.year>=2023).astype(int)
P['gwp_basis']=np.where(P.year==2024,'Insurance Revenue (IFRS 17)','Gross Written Premium')
P.loc[P.year==2024,['g','g_excess','d_ms']]=np.nan  # IR vs GWP not comparable
P.loc[P.year==2024,'g_source']='not computed: 2024 is Insurance Revenue'
P['last_year']=P.groupby('insurer_id').year.transform('max')
# December y/y CPI inflation (kept for comparison; see docs/data_issues.md A14)
dec_bul='GSS Dec bulletins (levels-derived, corroborated)'
infl={2015:(17.7,'GSS CPI Statistical Bulletin Dec 2015 (rel. 13 Jan 2016), verified'),2016:(15.4,dec_bul),2017:(11.8,dec_bul),2018:(9.4,dec_bul),
2019:(7.9,'NIC 2019 Annual Report'),2020:(10.4,'NIC 2020 Annual Report'),2021:(12.6,'GSS CPI Statistical Bulletin Dec 2021 (rel. 12 Jan 2022), verified'),2022:(54.1,'NIC 2022 Annual Report'),
2023:(23.2,'NIC 2024 Annual Report'),2024:(23.8,'NIC 2024 Annual Report')}
P['cpi_dec_yoy']=P.year.map(lambda y:infl[y][0]); P['cpi_dec_source']=P.year.map(lambda y:infl[y][1])
# Annual-average CPI inflation from the offline WDI snapshot (premium is a flow, so the average is the deflator)
wdi={int(r['date']):r['value'] for r in json.loads(WDI_CPI_FILE.read_text(encoding='utf-8'))[1] if r['value'] is not None}
retrieved=re.search(r'\*\*Retrieved:\*\* (\d{4}-\d{2}-\d{2})',(RAW_MACRO/'README.md').read_text(encoding='utf-8')).group(1)
P['cpi_avg_yoy']=P.year.map(wdi)
P['cpi_avg_source']=np.where(P.cpi_avg_yoy.notna(),f'World Bank WDI FP.CPI.TOTL.ZG (orig. GSS), retrieved {retrieved}','')
P['g_real']=100*((1+P.g/100)/(1+P.cpi_avg_yoy/100)-1)
P['g_real_dec']=100*((1+P.g/100)/(1+P.cpi_dec_yoy/100)-1)
P.loc[P.merger_break,['g','g_excess','g_real','g_real_dec','d_ms']]=np.nan  # merger rule (D13), explicit
P.loc[P.merger_break,'g_source']='not computed: merger year'
# lags for regression
lag=P[['insurer_id','year','g','g_excess','d_ms','RET','LEV_net','ln_gwp','LR','ER','CR']].copy(); lag['year']+=1
P=P.merge(lag.add_suffix('_L1').rename(columns={'insurer_id_L1':'insurer_id','year_L1':'year'}),on=['insurer_id','year'],how='left')
cols=['insurer_id','insurer_name','year','gwp_basis','gwp','mkt_gwp','ms','g','g_source','g_calc','chg_gwp_pct','g_flag_nic_disagree','g_mkt_matched','g_excess','g_real','g_real_dec','d_ms',
'LR','ER','CR','CR_nic','cr_nic_mismatch','ER_t1','CR_t1','er_t1_flag','RET','nwp','LR_g','ER_g','CR_g','LEV_net','LEV_gross','equity_proxy','ln_gwp','claims_reserve_ratio','tech_reserve_cover','inv_yield','roa','roe','pat','chg_nwp_pct','chg_cap_surplus','prop_inv_assets',
'first_year','last_year','entrant','firm_age_in_panel','startup','post_mid','covid','ifrs17','merger_break','cpi_dec_yoy','cpi_dec_source','cpi_avg_yoy','cpi_avg_source',
'g_L1','g_excess_L1','d_ms_L1','RET_L1','LEV_net_L1','ln_gwp_L1','LR_L1','ER_L1','CR_L1']
P=P[cols]; P.to_csv(PROCESSED/'panel_master.csv',index=False)
print(P.shape, P.insurer_id.nunique()); print(P.groupby('year').agg(n=('insurer_id','size'),lr=('LR','count'),g=('g','count'),gL1=('g_L1','count')).T)
chk=P.groupby('year').gwp.sum()/1e6
nict=L[(L.variable=='gwp')&(L.insurer_id=='TOTAL_TOTALS')].drop_duplicates('year').set_index('year').value/1e6
print(pd.DataFrame({'sum_insurers':chk.round(1),'NIC_Totals':nict}))
print('startup rows',P.startup.sum(),'cr mismatches',P.cr_nic_mismatch.sum(), P[P.cr_nic_mismatch].year.value_counts().to_dict())

# =====================================================================================================================
# v2 analysis panel (Part 3a) -> data/processed/confidential/panel_v2.csv. Built only when the returns panel (step 12)
# exists: it holds values derived from the NIC quarterly returns workbook (an NIC product; insurers' unaudited quarterly
# submissions), which stay out of git (decision A2). panel_master.csv above stays Tier 1 only, so v1 is reproducible.
# =====================================================================================================================
RP=CONFIDENTIAL/'returns_panel.csv'
if not (QUARTERLY_FILE.exists() and RP.exists()):
    print('v2 panel not built: NIC quarterly returns workbook or returns panel absent (public pipeline = v1 only).')
else:
    R=pd.read_csv(RP)
    R=R[['insurer_id','year','concordance','annual_source','gwp','LR_a','ER_a','CR_a','LR_c','ER_c','ER_gross','ER_netric',
         'COMM_r','MGT_r','ln_assets','TP_r','motor_share']].rename(columns={
        'gwp':'gwp_ret','annual_source':'c_source','LR_c':'LR_ret','ER_c':'ER_ret','LR_a':'LR_c','ER_a':'ER_c','CR_a':'CR_c'})
    V=P.merge(R,on=['insurer_id','year'],how='left')
    V['concordance']=V.concordance.fillna('no Q4 row')
    # Primary outcomes (authors' decision after Part 2): component-based on the NEP + RIC basis = returns where Q4 passes
    # concordance, Tier 1 published where it fails or is missing (5 rows, 'filled from annual'); CR_c = LR_c + ER_c.
    # 2015-16 Tier 1 correction: corroborated if the returns ER (pure, NEP + RIC basis) is within 5 pp of CR_nic - LR
    V['er1516_corroborated']=np.where(fix1516.values,(V.ER_ret-(V.CR_nic-V.LR)).abs()<=5,np.nan)
    V['er_t1_flag']=np.where(V.er1516_corroborated==1,'ER corrected (returns-corroborated)',
                     np.where(V.er1516_corroborated==0,'ER corrected (not returns-corroborated)',''))
    # 2020 published ER excludes commission (A20): replace with the returns ER (management + commission, NEP + RIC basis)
    # where Q4 passes concordance; LOYALTY 2020 fails and keeps the published value. Built on ER_t1.
    rep20=(V.year==2020)&(V.concordance=='pass')&V.ER_ret.notna()
    V['ER_corr2020']=np.where(rep20,V.ER_ret,V.ER_t1); V['CR_corr2020']=V.LR+V.ER_corr2020
    V['flag_er_corr2020']=np.where(rep20,'2020 ER corrected: published figure excludes commission (returns-corroborated)','')
    # Single growth measure (3a, decision A5): exact GWP in every year where available. Audited exact GHS to 2019;
    # returns GWP 2020-22 where Q4 passes concordance; 2015 from NIC's %-change table (no 2014 GWP, flagged); 2020-22
    # rows whose GWP (t or t-1) is not exact fall back to NIC's %-change table (flagged); 2023 as v1 (rounded GHS m).
    # Merger rule (D13) and consecutive-year rule unchanged. v1 growth kept as g_v1.
    V['g_v1']=V.g; V['g_excess_v1']=V.g_excess
    V['gwp_exact']=np.where(V.year<=2019,V.gwp,np.where(V.year.between(2020,2022)&(V.concordance=='pass'),V.gwp_ret,np.nan))
    pe=V[['insurer_id','year','gwp_exact']].assign(year=V.year+1).rename(columns={'gwp_exact':'gwp_exact_prev'})
    V=V.merge(pe,on=['insurer_id','year'],how='left')
    ge=100*(V.gwp_exact/V.gwp_exact_prev-1)
    y=V.year
    V['g']=np.select([y==2015,y.between(2016,2019),y.between(2020,2022)&ge.notna(),y.between(2020,2022)&V.chg_gwp_pct.notna(),
                      y.between(2020,2023)],[V.chg_gwp_pct,ge,ge,V.chg_gwp_pct,V.g_calc],default=np.nan)
    V['g_source']=np.select([y==2015,y.between(2016,2019)&ge.notna(),y.between(2020,2022)&ge.notna(),
                             y.between(2020,2022)&V.chg_gwp_pct.notna(),y.between(2020,2023)&V.g_calc.notna()],
                            ['NIC change table (2015: no 2014 GWP)','computed exact GHS (audited)',
                             'computed exact GHS (returns 2020-22, concordance pass)','NIC change table (fallback: GWP not exact in t or t-1)',
                             'computed rounded GHS m (as v1)'],default='missing')
    V.loc[V.merger_break|(V.year==2024),'g']=np.nan
    V.loc[V.merger_break,'g_source']='not computed: merger year'; V.loc[V.year==2024,'g_source']='not computed: 2024 is Insurance Revenue'
    V.loc[V.g.isna()&~V.g_source.str.startswith('not computed'),'g_source']='missing'
    V['g_excess']=V.g-V.groupby('year').g.transform('median')
    # cross-check of the exact 2020-22 growth against NIC's %-change table (aggregate, public)
    x=V[V.g_source.str.startswith('computed exact GHS (returns')]; dd=(x.g-x.chg_gwp_pct).dropna()
    xc=[dict(year=yr,n_exact_returns=int((x.year==yr).sum()),n_with_nic_table=int(d.notna().sum()),median_abs_diff_pp=d.abs().median(),
             within_1pp=(d.abs()<=1).mean(),within_5pp=(d.abs()<=5).mean(),
             n_fallback_nic_table=int(((V.year==yr)&V.g_source.str.startswith('NIC change table (fallback')).sum()))
        for yr,d in [(yr,(x.g-x.chg_gwp_pct)[x.year==yr]) for yr in (2020,2021,2022)]]
    pd.DataFrame(xc).to_csv(TABLES/'growth_v2_crosscheck.csv',index=False)
    # lags on the insurer x year grid (a gap year gives a missing lag)
    def lagged(D,cols,k):
        s=D[['insurer_id','year']+cols].copy(); s['year']+=k
        return D.merge(s.rename(columns={c:f'{c}_L{k}' for c in cols}),on=['insurer_id','year'],how='left')
    V=V.drop(columns=['g_L1','g_excess_L1']).rename(columns={})
    V=lagged(V,['g','g_excess','ln_assets','TP_r','claims_reserve_ratio','LR_c','ER_c','CR_c','g_v1','g_excess_v1'],1)
    V=lagged(V,['g'],2)
    V['g_L2']=np.where(V.year==2016,np.nan,V.g_L2)       # 2014 growth not available (decision A5)
    V['motor_share_2021']=V.insurer_id.map(V[V.year==2021].set_index('insurer_id').motor_share)
    V.to_csv(CONFIDENTIAL/'panel_v2.csv',index=False)
    print(f"v2 panel: {len(V)} rows -> data/processed/confidential/panel_v2.csv; 2015-16 ER corrections {int(fix1516.sum())} "
          f"(corroborated {int((V.er1516_corroborated==1).sum())}); 2020 ER corrections {int(rep20.sum())}")
    print('g_source (v2), 2015-2023:', V[V.year.between(2015,2023)].g_source.value_counts().to_dict())
    print(pd.DataFrame(xc).round(3).to_string(index=False))
