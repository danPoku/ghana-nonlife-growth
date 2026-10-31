"""Step 2: map parsed blocks to variables, canonicalise insurer names, write long data with provenance.

Mapping is by (report, line-of-header) in the bundled text files. Every mapped
block is checked against src/expected_blocks.json (years, row count, first row)
so a changed input or parser fails loudly instead of silently mis-mapping.
"""
import json, re, sys, pandas as pd
from config import INTERIM, ROOT
from nic_parser import num
from names import canon   # shared with step 09
B={ (b['report'],b['line']):b for b in json.load(open(INTERIM/'blocks.json'))}
MAP={
 'gwp':[(2019,2400,'GHS'),(2020,3383,'GHS_m'),(2022,2366,'GHS_m'),(2024,2316,'GHS_m')],
 'pat':[(2019,2481,'GHS'),(2020,3457,'GHS_m'),(2024,2384,'GHS_m')],
 'chg_gwp_pct':[(2019,3543,'%'),(2020,4549,'%'),(2022,3354,'%')],
 'chg_nwp_pct':[(2019,3594,'%'),(2020,4597,'%'),(2022,3403,'%')],
 'net_risk_ratio':[(2019,3649,'%'),(2020,4649,'%'),(2022,3455,'%')],
 'gross_risk_ratio':[(2019,3699,'%'),(2020,4697,'%'),(2022,3502,'%')],
 'chg_cap_surplus':[(2019,3759,'%'),(2020,4752,'%'),(2022,3557,'%'),(2024,3228,'%')],
 'claims_reserve_ratio':[(2019,3815,'%'),(2020,4803,'%'),(2022,3609,'%')],
 'retention':[(2019,3868,'%'),(2020,4853,'%'),(2022,3661,'%'),(2024,3276,'%')],
 'inv_yield':[(2019,3919,'%'),(2020,4902,'%'),(2022,3706,'%'),(2024,3320,'%')],
 'roa':[(2019,3968,'%'),(2020,4949,'%'),(2022,3755,'%'),(2024,3364,'%')],
 'loss_ratio':[(2019,4029,'%'),(2020,5007,'%'),(2022,3811,'%'),(2024,3413,'%')],
 'expense_ratio':[(2019,4084,'%'),(2020,5059,'%'),(2022,3865,'%'),(2024,3461,'%')],
 'combined_ratio':[(2019,4140,'%'),(2020,5098,'%'),(2022,3918,'%'),(2024,3510,'%')],
 'tech_reserve_cover':[(2019,4198,'%'),(2020,5164,'%'),(2022,3969,'%'),(2024,3560,'%')],
 'prop_inv_assets':[(2019,4248,'%'),(2020,5212,'%'),(2022,4016,'%'),(2024,3608,'%')],
 'roe':[(2019,4299,'%'),(2020,5251,'%'),(2022,4067,'%')],
}
# ---- validate every mapped block against frozen expectations ----
EXP = json.load(open(ROOT/'src'/'expected_blocks.json'))
errs = []
for var, lst in MAP.items():
    for rep, line, unit in lst:
        k = f"{var}|{rep}|{line}"; b = B.get((rep, line))
        if b is None:
            errs.append(f"{k}: block missing"); continue
        e = EXP[k]
        if b['years'] != e['years'] or len(b['rows']) != e['n_rows'] or [b['rows'][0]['name'], b['rows'][0]['vals']] != e['first_row']:
            errs.append(f"{k}: block differs from expectation")
if errs:
    sys.exit("Validation failed:\n" + "\n".join(errs))
print(f"All {sum(len(v) for v in MAP.values())} mapped blocks validated.")

recs=[];unmapped=set();bad=[]
for var,lst in MAP.items():
    for rep,line,unit in lst:
        b=B[(rep,line)]; yrs=b['years']
        for r in b['rows']:
            if r['section']=='industry_avg':
                cid='NIC_INDUSTRY_AVG'
            elif r['section']=='insurer': cid=canon(r['name'])
            elif r['section']=='total':
                cid='TOTAL_'+re.sub(r'\W','',r['name']).upper()
            else: continue
            if cid is None: unmapped.add(r['name']); continue
            v=r['vals']
            if len(v)!=len(yrs):
                bad.append((var,rep,r['name'],v))
                if var=='gwp' and rep==2024 and len(v)==4: v=v+['N-A']  # Millennium 2024 missing in source
                else: continue
            for y,x in zip(yrs,v):
                val=num(x)
                if unit=='GHS_m' and val is not None: val=val*1e6
                recs.append(dict(insurer_id=cid,source_name=r['name'],year=y,variable=var,value=val,raw=x,
                    unit='GHS' if unit.startswith('GHS') else '%',source_report=f'NIC Annual Report {rep}',
                    table=b['title'],txt_line=line,precision='exact GHS' if unit=='GHS' else ('rounded GHS million' if unit=='GHS_m' else 'integer %')))
df=pd.DataFrame(recs)
df.to_csv(INTERIM/'nic_long_all_vintages.csv',index=False)
print(df.shape); print('unmapped',unmapped); print('bad',bad)
print(df.groupby(['variable','source_report']).size().unstack().fillna(0).astype(int))
