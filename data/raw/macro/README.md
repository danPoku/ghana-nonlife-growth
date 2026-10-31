# Macro data snapshot

- **Indicator:** `FP.CPI.TOTL.ZG`: Inflation, consumer prices (annual %)
- **Country:** Ghana (GH)
- **URL:** https://api.worldbank.org/v2/country/GH/indicator/FP.CPI.TOTL.ZG?format=json&date=2015:2024&per_page=100
- **Retrieved:** 2026-10-31 (WDI last updated 2026-10-08)
- **File:** `wdi_FP.CPI.TOTL.ZG_GH.json` (raw API response, unchanged)
- **Original source:** Ghana Statistical Service (GSS), compiled by the World Bank
- **Used for:** deflating premium growth (`g_real`, Figure 5) by annual-average CPI inflation
- **Refresh:** `python src/00_fetch_macro.py`, then rerun the pipeline. Values may be revised between WDI releases.

| Year | Inflation, annual average (%) |
|---|---|
| 2015 | 17.1499695007877 |
| 2016 | 17.4546347070867 |
| 2017 | 12.3719215507048 |
| 2018 | 7.80876516610703 |
| 2019 | 7.14364003330856 |
| 2020 | 9.88728956269944 |
| 2021 | 9.97108867504439 |
| 2022 | 31.2558951049016 |
| 2023 | 38.1069656296501 |
| 2024 | 22.8483281157842 |
