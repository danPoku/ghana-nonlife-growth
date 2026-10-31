"""Step 0 (run once, by hand; NOT part of run_all.py): snapshot World Bank WDI CPI inflation for Ghana.

Saves the raw API response unchanged so the pipeline runs offline and reproducibly from the snapshot.
Usage: python src/00_fetch_macro.py   (re-running overwrites the snapshot and README with today's data)
"""
import json, sys, urllib.request
from datetime import date
from config import RAW_MACRO, WDI_CPI_FILE

INDICATOR = 'FP.CPI.TOTL.ZG'
URL = f'https://api.worldbank.org/v2/country/GH/indicator/{INDICATOR}?format=json&date=2015:2024&per_page=100'
REQUIRED = range(2015, 2024)   # 2015-2023 must be present; 2024 is only used descriptively

try:
    with urllib.request.urlopen(URL, timeout=60) as r:
        raw = r.read()
    meta, rows = json.loads(raw)
except Exception as e:
    sys.exit(f'World Bank API request failed ({e}). Nothing saved.')
vals = {int(r['date']): r['value'] for r in rows}
missing = [y for y in REQUIRED if vals.get(y) is None]
if missing:
    sys.exit(f'Missing years {missing} in WDI {INDICATOR}. Nothing saved; do not fill gaps from other sources.')
if vals.get(2024) is None:
    sys.exit('2024 is missing in WDI (2015-2023 present). Nothing saved; decide how to proceed before re-running.')

RAW_MACRO.mkdir(parents=True, exist_ok=True)
WDI_CPI_FILE.write_bytes(raw)   # unchanged API response
name = rows[0]['indicator']['value']
lines = [f'# Macro data snapshot', '',
         f'- **Indicator:** `{INDICATOR}`: {name}',
         f'- **Country:** Ghana (GH)',
         f'- **URL:** {URL}',
         f'- **Retrieved:** {date.today().isoformat()} (WDI last updated {meta.get("lastupdated")})',
         f'- **File:** `{WDI_CPI_FILE.name}` (raw API response, unchanged)',
         f'- **Original source:** Ghana Statistical Service (GSS), compiled by the World Bank',
         f'- **Used for:** deflating premium growth (`g_real`, Figure 5) by annual-average CPI inflation',
         f'- **Refresh:** `python src/00_fetch_macro.py`, then rerun the pipeline. Values may be revised between WDI releases.',
         '', '| Year | Inflation, annual average (%) |', '|---|---|']
lines += [f'| {y} | {vals[y]} |' for y in sorted(vals)]
(RAW_MACRO / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Saved {WDI_CPI_FILE} and README.md ({len(vals)} years, WDI last updated {meta.get("lastupdated")})')
