"""Parse five-year insurer tables from NIC Annual Report text extractions.

A table block is anchored on a header line ("Year: 2015 2016 ..." or
"COMPANY 2015 2016 ..."). Rows are read until the block ends. Titles are
attached heuristically but are NOT used for mapping: mapping to variables is
by (report, line) in 02_build_long.py and is validated against frozen
expectations in expected_blocks.json.
"""
import re, json, pandas as pd
VAL = re.compile(r'^(-?[\d,]+(\.\d+)?|\(-?[\d,]+(\.\d+)?\)|N-A|N-S|N/A|NA|NS|-|N-A\*|N-S\*)$')
def is_val(t): return bool(VAL.match(t))
def toks_vals(line):
    # merge broken thousands like "31,536, 467"
    line = re.sub(r'(\d),\s+(\d{3})\b', r'\1,\2', line)
    line = re.sub(r'\(\s*(-?[\d,.]+)\s*\)', r'(\1)', line)
    line = line.replace('N-Av','N-A')
    toks = line.split()
    vals=[]
    while toks and is_val(toks[-1]):
        vals.insert(0,toks.pop())
    return toks, vals
def num(v):
    if v in ('N-A','N-S','N/A','NA','NS','-','N-A*','N-S*'): return None
    neg = v.startswith('(')
    x=float(v.strip('()').replace(',',''))
    return -x if neg else x
def parse_blocks(path, report):
    L=[l.rstrip() for l in open(path,encoding='utf-8',errors='ignore')]
    out=[]
    for i,l in enumerate(L):
        m=re.match(r'^\s*(Year:|COMPANY)\s+((?:\d{4}\s*)+)$', l.strip())
        if not m: continue
        years=[int(y) for y in m.group(2).split()]
        n=len(years); rows=[]; j=i+1; section='insurer'; flags=[]
        while j<len(L) and j<i+60:
            s=L[j].strip()
            if s.startswith('Industry Average'):
                _,v=toks_vals(s.replace('Industry Average:','IA'))
                rows.append(dict(section='industry_avg',no=None,name='Industry Average',vals=v)); j+=1; continue
            if s.startswith('Reinsurers'): section='reinsurer'; j+=1; continue
            if re.match(r'^(Totals?|TOTALS|GOGIP|Grand Total)\b',s):
                t,v=toks_vals(s); rows.append(dict(section='total',no=None,name=' '.join(t),vals=v)); j+=1; continue
            mm=re.match(r'^(\d{1,2})\s+(.*)$',s)
            body = mm.group(2) if mm else s
            t,v=toks_vals(body)
            if t and not v and j+1<len(L):   # name wraps onto next line
                t2,v2=toks_vals(L[j+1].strip())
                if v2 and len(t2)<=3:
                    t=t+t2; v=v2; j+=1
            if t and v and re.match(r'^[A-Za-z]',t[0]):
                rows.append(dict(section=section,no=int(mm.group(1)) if mm else None,name=' '.join(t),vals=v)); j+=1; continue
            if rows and not s: j+=1; continue
            if rows: break
            j+=1
        end=j
        # find title: after (within 4 lines) else before (within 40)
        title=None
        for k in range(end,min(end+4,len(L))):
            if re.match(r'^\s*(TABLE|Table)\s*:?\s*\d+',L[k]): title=L[k].strip(); break
        if not title:
            for k in range(i,max(i-40,0),-1):
                if re.match(r'^\s*(TABLE|Table)\s*:?\s*\d+',L[k]): title=L[k].strip(); break
        out.append(dict(report=report,line=i+1,years=years,title=title,rows=rows))
    return out
