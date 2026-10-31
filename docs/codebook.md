# Codebook: data/processed/panel_master.csv

One row per insurer-year. 29 insurers, 2015-2024, unbalanced (263 rows). Missing = not reported (never zero).

Sources: NIC Annual Reports 2019, 2020, 2022, 2024 (insurer tables). Provenance for every value: data/interim/nic_long_all_vintages.csv (report, table, line).

`estimation_sample.csv` = 2016-2022, start-ups excluded, complete cases; `_w` suffix = winsorised 1st/99th; `g_L1_sq_w` = g_L1_w^2/100; `hi_g_w` = max(0, excess growth - 75th pct); `gxpost_w` = g_L1_w x post_mid.

| Variable | Non-missing | Description |
|---|---|---|
| `insurer_id` | 263 | Canonical insurer ID (stable across renames) |
| `insurer_name` | 263 | Display name incl. former names |
| `year` | 263 | Financial year |
| `gwp_basis` | 263 | GWP (2015-2023) or Insurance Revenue IFRS 17 (2024) |
| `gwp` | 262 | Gross written premium, GHS (exact to 2019; rounded GHS m from 2020) |
| `mkt_gwp` | 263 | Sum of insurer GWP in year (GOGIP pool excluded), GHS |
| `ms` | 262 | Market share of mkt_gwp, % |
| `g` | 231 | PRIMARY premium growth, % (see g_source) |
| `g_source` | 263 | Origin of g: computed from exact GWP / NIC change table / computed from rounded GWP / not computed: 2024 is Insurance Revenue / not computed: merger year (D13) |
| `g_calc` | 232 | Growth computed from gwp (consecutive years only), % |
| `chg_gwp_pct` | 205 | NIC published change in GWP, % |
| `g_flag_nic_disagree` | 263 | g_calc and NIC % differ by > 5 pp |
| `g_mkt_matched` | 239 | Market growth over insurers present in both years, % |
| `g_excess` | 231 | g minus year median g, pp |
| `g_real` | 231 | g deflated by annual-average CPI inflation (`cpi_avg_yoy`), % |
| `g_real_dec` | 231 | g deflated by December CPI inflation (`cpi_dec_yoy`), %; for comparison |
| `d_ms` | 207 | Change in market share, pp |
| `LR` | 262 | Loss (claims) ratio, % (NIC: net claims incurred / NEP incl. reinsurance commission) |
| `ER` | 261 | Expense ratio, % (NIC: management + commission expense / NEP [+ reins. income]) |
| `CR` | 261 | Combined ratio constructed as LR + ER, % |
| `CR_nic` | 262 | Combined ratio as printed by NIC, % |
| `cr_nic_mismatch` | 263 | |CR - CR_nic| > 1 |
| `RET` | 262 | Retention ratio NWP/GWP, % |
| `nwp` | 261 | Net written premium = gwp x RET/100, GHS (approx.; weights) |
| `LEV_net` | 210 | Net insurance risk ratio NWP/equity, % |
| `LEV_gross` | 211 | Gross insurance risk ratio GWP/equity, % |
| `equity_proxy` | 210 | gwp / (LEV_gross/100), GHS (approx.) |
| `ln_gwp` | 262 | Natural log of gwp |
| `claims_reserve_ratio` | 211 | (Outstanding claims + IBNR) / NEP, % |
| `tech_reserve_cover` | 262 | Technical reserve cover, % |
| `inv_yield` | 262 | Investment yield, % |
| `roa` | 262 | Return on assets, % |
| `roe` | 208 | Return on equity, % |
| `pat` | 262 | Profit after tax, GHS |
| `chg_nwp_pct` | 207 | NIC change in NWP, % |
| `chg_cap_surplus` | 259 | NIC change in capital & surplus, % |
| `prop_inv_assets` | 262 | Proportion of investment assets, % |
| `first_year` | 263 | First year with GWP in panel |
| `last_year` | 263 | Last year in panel |
| `entrant` | 263 | Entered after 2015 |
| `firm_age_in_panel` | 263 | year - first_year |
| `startup` | 263 | Entrant in first two years (excluded from main sample) |
| `post_mid` | 263 | 1 if year >= 2020 (Motor Insurance Database) |
| `covid` | 263 | 1 if 2020 |
| `ifrs17` | 263 | 1 if year >= 2023 |
| `merger_break` | 263 | First year of a combined entity, from `MERGERS` in src/config.py: RegencyNem 2016 (NEM absorbed), SanlamAllianz 2024 (Allianz absorbed). Growth columns are missing in these rows (D13) |
| `cpi_dec_yoy` | 263 | December y/y CPI inflation, % |
| `cpi_dec_source` | 263 | Source of the December CPI value (verify where marked) |
| `cpi_avg_yoy` | 263 | Annual-average CPI inflation, % (World Bank WDI FP.CPI.TOTL.ZG snapshot, orig. GSS) |
| `cpi_avg_source` | 263 | Source and retrieval date of `cpi_avg_yoy` |
| `g_L1` | 227 | g lagged one year (consecutive years only) |
| `g_excess_L1` | 227 | g_excess lagged one year (consecutive years only) |
| `d_ms_L1` | 203 | d_ms lagged one year (consecutive years only) |
| `RET_L1` | 233 | RET lagged one year (consecutive years only) |
| `LEV_net_L1` | 207 | LEV_net lagged one year (consecutive years only) |
| `ln_gwp_L1` | 233 | ln_gwp lagged one year (consecutive years only) |
| `LR_L1` | 233 | LR lagged one year (consecutive years only) |
| `ER_L1` | 232 | ER lagged one year (consecutive years only) |
| `CR_L1` | 232 | CR lagged one year (consecutive years only) |

Robustness variable (step 09 only; not in panel_master.csv or estimation_sample.csv):

| Variable | Non-missing | Description |
|---|---|---|
| `ln_assets_L1` | 172 of 176 estimation rows | ln(total assets at 31 Dec of t-1), from the Q4 sheets of the confidential NIC quarterly returns workbook (A15), kept only where the workbook's Q4 GWP passes the concordance check against audited annual GWP. Insurer-level values are in the git-ignored `data/processed/confidential/total_assets_q4.csv` |
