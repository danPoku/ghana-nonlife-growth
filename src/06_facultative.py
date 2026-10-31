"""Step 6 (supplementary): clean and profile the facultative reinsurance production report.

One reinsurer's facultative inward book, Jun 2020 - Dec 2024. No claims fields,
so it cannot enter the main models. Contains client names: do NOT publish.
"""
import pandas as pd, numpy as np, re, json, sys
from config import PRODUCTION_FILE, RAW_PROD, PROCESSED, TABLES
if not PRODUCTION_FILE.exists():
    print("Production file not found; skipping step 6."); sys.exit(0)
df=pd.read_excel(PRODUCTION_FILE)
df.columns=[c.strip() for c in df.columns]
n0=len(df)
df=df[df['Offer Date'].notna()].copy()
for c in ['Fac. Sum Insured','FAC. Premium','Brokerage','NIC Levy','Amount Due','Commission','Amount Paid','Outstanding Balance']:
    df[c]=pd.to_numeric(df[c],errors='coerce')
df['offer_date']=pd.to_datetime(df['Offer Date'].str[4:],format='%b %d %Y',errors='coerce')
per=df.Period.str.extract(r'^\w{3} (\w{3} \d{2} \d{4}) - \w{3} (\w{3} \d{2} \d{4})')
df['cover_start']=pd.to_datetime(per[0],format='%b %d %Y',errors='coerce'); df['cover_end']=pd.to_datetime(per[1],format='%b %d %Y',errors='coerce')
df['year']=df.offer_date.dt.year
df['currency_clean']=df.Currency.replace({'Le':'SLE','D':'UNKNOWN','0':'UNKNOWN','NIC Levy':'UNKNOWN'})
def grp(b):
    b=str(b).lower()
    if 'motor' in b: return 'Motor'
    if any(k in b for k in ['fire','burglary','property','assets all risks','business interruption','loss profit','landlord','householder','money','cash in transit','theft']): return 'Fire, Theft & Property'
    if any(k in b for k in ['contractor','erection','machinery','plant','boiler','engineering','electronic','cyber']): return 'Engineering'
    if any(k in b for k in ['marine','goods in transit','hull','cargo','aviation','aircraft']): return 'Marine & Aviation'
    if any(k in b for k in ['liability','indemnity','workmen','lawmakers','directors','employer']): return 'Liability'
    if any(k in b for k in ['bond','guarantee','fidelity','bankers blanket','credit']): return 'Bonds / Financial Loss'
    if any(k in b for k in ['accident','medical','health','travel']): return 'PA, Health & Medical'
    return 'Other'
df['class_group']=df['Business Name'].map(grp)
df['auto_fac_facility']=df['Business Name'].str.contains('Automobile Fac Facility',case=False,na=False)
# Foreign cedant names come from the confidential file, so they live beside it (git-ignored), not in code
FOREIGN_FILE=RAW_PROD/'foreign_cedants.txt'
if not FOREIGN_FILE.exists():
    sys.exit(f"Missing {FOREIGN_FILE}: one foreign cedant name per line (kept with the confidential production file).")
foreign=[s.strip() for s in FOREIGN_FILE.read_text(encoding='utf-8').splitlines() if s.strip()]
df['cedant_type']=np.select([df.Reinsured.isin(foreign),df.Reinsured.str.contains('Reinsurance',na=False)],['Foreign / non-Ghana non-life','Reinsurer (retrocession)'],default='Ghana non-life insurer')
df['premium_rate_pct']=100*df['FAC. Premium']/df['Fac. Sum Insured'].replace(0,np.nan)
df['flag_amount_due_basis']=np.where((df['Amount Due']-df['FAC. Premium']).abs()<0.01,'gross',np.where(df['Amount Due']<df['FAC. Premium'],'net','other'))
df['flag_partial_year']=df.year==2020
df['flag_no_premium']=df['FAC. Premium'].fillna(0)<=0
out=df[['Policy No','offer_date','year','cover_start','cover_end','Insured','Business Name','class_group','auto_fac_facility','Reinsured','cedant_type','currency_clean',
 'Fac. Sum Insured','FAC. Premium','premium_rate_pct','Brokerage','NIC Levy','Commission','Amount Due','Amount Paid','Outstanding Balance','Payment Status','flag_amount_due_basis','flag_partial_year','flag_no_premium']]
out.columns=['policy_no','offer_date','offer_year','cover_start','cover_end','insured','business_name','class_group','auto_fac_facility','cedant','cedant_type','currency',
 'fac_sum_insured','fac_premium','premium_rate_pct','brokerage','nic_levy','ceding_commission_pct','amount_due','amount_paid','outstanding_balance','payment_status','flag_amount_due_basis','flag_partial_year_2020','flag_no_premium']
out.to_csv(PROCESSED/'fac_production_clean.csv',index=False)
S={}
S['rows_raw']=n0; S['rows_clean']=len(out); S['date_range']=[str(out.offer_date.min().date()),str(out.offer_date.max().date())]
S['by_year']=out.groupby('offer_year').size().to_dict()
S['currency']=out.currency.value_counts().to_dict()
cg=out.groupby('class_group').agg(n=('policy_no','size'),comm_median=('ceding_commission_pct','median'),usd_prem=('fac_premium',lambda s:s[out.loc[s.index,'currency']=='USD'].sum()),ghs_prem=('fac_premium',lambda s:s[out.loc[s.index,'currency']=='GHS'].sum())).sort_values('n',ascending=False)
cg['share_n_pct']=100*cg.n/cg.n.sum(); S['class']=cg.round(1).reset_index().to_dict('records')
yc=pd.crosstab(out.offer_year,out.class_group,normalize='index').mul(100).round(1); yc.to_csv(TABLES/'fac_class_mix_by_year.csv')
S['motor_share_by_year']=yc['Motor'].to_dict()
ced=out.groupby('cedant').size().sort_values(ascending=False); S['n_cedants']=int(ced.size); S['top5_cedant_share_pct']=float(100*ced.head(5).sum()/ced.sum()); S['top_cedant']=ced.index[0]; S['top_cedant_share_pct']=float(100*ced.iloc[0]/ced.sum())
S['cedant_type']=out.cedant_type.value_counts().to_dict()
pay=pd.crosstab(out.offer_year,out.payment_status,normalize='index').mul(100).round(1); pay.to_csv(TABLES/'fac_payment_by_year.csv'); S['payment_status_by_year']=pay.to_dict()
S['amount_due_basis']=out.flag_amount_due_basis.value_counts().to_dict()
comm=out.groupby(['offer_year','class_group']).ceding_commission_pct.median().unstack().round(1); comm.to_csv(TABLES/'fac_commission_by_year_class.csv')
S['commission_overall']=out.ceding_commission_pct.describe().round(2).to_dict()
cy=out.groupby(['cedant','offer_year']).agg(n=('policy_no','size'),usd_prem=('fac_premium',lambda s:s[out.loc[s.index,'currency']=='USD'].sum()),ghs_prem=('fac_premium',lambda s:s[out.loc[s.index,'currency']=='GHS'].sum()),motor_share=('class_group',lambda s:(s=='Motor').mean()*100)).reset_index()
cy.to_csv(PROCESSED/'fac_cedant_year_summary.csv',index=False)
json.dump(S,open(TABLES/'fac_summary.json','w'),indent=1,default=str)
print(f"Facultative: {S['rows_clean']} placements, {S['n_cedants']} cedants")
