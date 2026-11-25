# Codebook: data/processed/panel_master.csv

One row per insurer-year. 29 insurers, 2015-2024, unbalanced (263 rows). Missing = not reported (never zero).

Sources: NIC Annual Reports 2019, 2020, 2022, 2024 (insurer tables). Provenance for every value: data/interim/nic_long_all_vintages.csv (report, table, line).

`estimation_sample.csv` = 2016-2022, start-ups excluded, complete cases; `_w` suffix = winsorised 1st/99th; `g_L1_sq_w` = g_L1_w^2/100; `hi_g_w` = max(0, excess growth - 75th pct); `gxpost_w` = g_L1_w x post_mid; `LR_g_w`, `ER_g_w` = gross-basis ratios winsorised 1st/99th on the estimation sample, `CR_g_w` = LR_g_w + ER_g_w (sum of the winsorised parts, not winsorised itself).

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
| `LR` | 262 | Loss (claims) ratio, %, NET basis. NIC: net claims incurred / (net earned premium + reinsurance commission income), all IFRS 4 reports; 2023-24 (IFRS 17): incurred claims / Net Insurance Revenue incl. reinsurance commission income (data_issues A16) |
| `ER` | 261 | Expense ratio, %. NIC: (management + commission expense) / net earned premium (2019 report wording) or / (net earned premium + reinsurance income) (2020 and 2022 reports); overlapping years identical across reports. 2023-24 (IFRS 17): (attributable + non-attributable expenses) / Insurance Revenue, i.e. GROSS of reinsurance (A16) |
| `CR` | 261 | Combined ratio constructed as LR + ER, % (D5). Net profitability measure. 2023-24 mixes a net LR with a gross ER (A16) |
| `CR_nic` | 262 | Combined ratio as printed by NIC, % (defined by NIC as LR + ER in every report; differs in 2015-16, see A6, A16 and step 11) |
| `cr_nic_mismatch` | 263 | |CR - CR_nic| > 1 |
| `ER_t1` | 261 | Tier 1 ER with the 2015-16 correction (v2, 3a): CR_nic - LR on the 2015-16 `cr_nic_mismatch` rows (41), published ER elsewhere (A16, A19). NIC data only |
| `CR_t1` | 261 | LR + ER_t1 |
| `er_t1_flag` | 263 | "ER corrected: ER := CR_nic - LR (2015-16 printed-ER error)" on the 41 corrected rows, else blank |
| `RET` | 262 | Retention ratio NWP/GWP, % |
| `nwp` | 261 | Net written premium = gwp x RET/100, GHS (approx.; weights) |
| `LR_g` | 211 | Gross-basis loss ratio = LR x RET/100, %: claims relative to gross earned premium, approx. Assumes NEP ~ NWP and gross earned premium ~ GWP and ignores reinsurance commission income (RIC) in NIC's denominator, so it is UNDERSTATED by the factor NEP/(NEP+RIC) (direction certain, size unknown). 2015-2022 only; missing for 2023-24 (IFRS 17) (A16) |
| `ER_g` | 210 | Gross-basis expense ratio = ER x RET/100, %: expenses relative to gross earned premium, approx.; same approximation and understatement as `LR_g`. An operating-efficiency measure only. 2015-2022 only (A16) |
| `CR_g` | 210 | LR_g + ER_g, %. NOT an underwriting-profitability measure: it omits the net cost of reinsurance. Net `CR` remains the profitability measure. 2015-2022 only (A16) |
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
| `ln_assets_L1` | 172 of 176 estimation rows | ln(total assets at 31 Dec of t-1), from the Q4 sheets of the NIC quarterly returns workbook (published by the NIC; insurers' unaudited submissions; A15, A17), kept only where the workbook's Q4 GWP passes the concordance check against audited annual GWP. Insurer-level values are in `data/processed/total_assets_q4.csv` |

## Returns panel (Tier 2, step 12): data/processed/returns_panel.csv

Source: the NIC quarterly returns workbook (published by the NIC; the figures are insurers' unaudited quarterly submissions; data_issues A15, A17-A20; `data/raw/quarterly/SOURCE.md`). Aggregate tables: `outputs/tables/returns_*.csv`, `seasonality.csv`.
339 rows. Ratios in percent. `returns_quarterly.csv` holds every quarter (Q1 2013 - Q1 2026) with the same variables on a year-to-date basis, plus `quarter`, `sheet`, `era` (ifrs4 / ifrs17), `er_wb_defective_sheet` and quarterly increments `<flow>_inc` (Qq - Qq-1 of the same insurer-year; Q1 = year-to-date).

| Variable | Non-missing | Definition |
|---|---|---|
| `insurer_id, year` | 339 | Canonical ID (src/names.py, aliases in src/returns_io.py) and financial year; one row per insurer-year with a Q4 row (2013-2025) or a Tier 1 row (2015-2023) |
| `in_tier1, has_q4_row, has_figures` | 339 | In the audited panel; has a Q4 workbook row; that row has at least one money figure (derived columns such as market share do not count) |
| `flag_copy_forward` | 338 | Q4 identical to Q3 on every shared money column (>= 3 values); concordance decides whether it is stale |
| `merger_year` | 338 | First year of a combined entity (MERGERS in src/config.py, D13) |
| `concordance` | 339 | pass if |Q4 GWP - audited GWP| <= max(5%, GHS 0.5m) (2015-2023); else fail / no Q4 row / Q4 row without figures / not checked (2013-14: no audited GWP; 2024+: IFRS 17) |
| `gwp_rel_diff` | 237 | |Q4 GWP - audited GWP| / audited GWP |
| `annual_source` | 339 | returns (concordance pass) / filled from annual (Q4 failed or missing: annual columns from Tier 1, components missing) / filled from annual (components incomplete: NEP + RIC or a component not recoverable) / returns (not checked: 2013-14) / IFRS 17 (i17_ columns only) / returns only (not in Tier 1) |
| `n_quarters_no_figures` | 338 | Quarters of the year (0-4) without figures, over insurer-years with figures in any quarter or in Tier 1 |
| `gwp, nwp, claims, gross_claims, mgmt, comm, ric, tp, total_assets, motor_gwp` | 282 | Workbook Q4 (year-to-date = annual) amounts, GHS: gross written premium, net written premium, net claims incurred, gross claims incurred (Q4 2019+), management expenses, commission expense, reinsurance commission income (RIC; blank = missing, never zero), technical provisions (2021+), total assets, motor gross premium (2021-23). Header variants: data_issues A17 |
| `NEP_RIC, nep_source` | 271 | PRIMARY denominator = net earned premium + RIC (NIC basis, A17): before 2021 implied = claims / (LR_wb / 100) as-is; from 2021 the NEP column + RIC. Not recoverable if claims <= 0 or LR_wb missing (before 2021) or NEP or RIC blank (2021+) |
| `NEP_true` | 262 | SECONDARY: true net earned premium = NEP_RIC - RIC before 2021 (missing where RIC blank), the NEP column from 2021 |
| `LR_c` | 271 | 100 x claims / NEP_RIC. Before 2021 it equals LR_wb by construction |
| `ER_c` | 271 | 100 x (mgmt + comm) / NEP_RIC |
| `CR_c` | 271 | LR_c + ER_c (checked exactly in 07) |
| `COMM_r, MGT_r, TP_r` | 271 | 100 x comm / NEP_RIC; 100 x mgmt / NEP_RIC; 100 x tp / NEP_RIC (2021+) |
| `LR_tn, ER_tn, CR_tn` | 262 | SECONDARY: the same ratios over NEP_true |
| `ER_netric` | 257 | 100 x (mgmt + comm - ric) / NEP_true; missing where RIC is blank |
| `ER_gross` | 278 | 100 x (mgmt + comm) / gwp |
| `RET_c` | 278 | 100 x nwp / gwp |
| `ln_assets` | 278 | ln(total_assets) if > 0 |
| `motor_share` | 78 | 100 x motor_gwp / gwp (2021-23; 2024+ in i17_motor_gwp) |
| `gwp_a, RET_a, LR_a, ER_a, CR_a` | 283 | Annual columns (fill rule 2d): returns values where concordance passes and the ratios exist, else Tier 1 published values; CR_a = LR_a + ER_a (checked exactly in 07) |
| `LR_wb, ER_wb, CR_wb` | 281 | Workbook's own printed ratios, percent after unit detection (claims ratio over NEP + RIC; ER = (mgmt + comm) / (NEP + RIC) except 2020, management only, A17). ER_wb ignored in Q2 2022 (copy of the claims ratio). CR_wb only in Q1 2020 |
| `gwp_t1, LR_t1, ER_t1, CR_t1, CR_nic_t1, RET_t1, cr_nic_mismatch_t1` | 238 | Tier 1 (audited NIC annual reports, src/tier1.py) values for the same insurer-year (published ER) |
| `i17_*` | - | IFRS 17 items, 2024+ only, never mixed with 2013-2023: revenue (Insurance (Service) Revenue), service_expenses, result_gross (= revenue - service expenses), service_result (after reinsurance), incurred_claims, attrib_exp, nonattrib_exp, acq_cf, total_assets, motor classes and their sum motor_gwp, and the printed ratios LR_wb, ER_wb, attrib_ER_wb, nonattrib_ER_wb, tech_margin_wb, CR_wb = LR_wb + ER_wb |

## v2 analysis panel: data/processed/panel_v2.csv (step 03, Part 3)

263 rows: panel_master.csv plus the columns below, built from the returns panel (step 12). `estimation_sample_v2.csv` (same folder) = 2016-2022, start-ups excluded, complete on LR_c, ER_c, g_L1, RET, ln_assets_L1, LEV_net_L1 (171 rows, 28 insurers); `LR_w`, `ER_w` = LR_c, ER_c winsorised 1/99 on that sample and `CR_w` = LR_w + ER_w (additive, checked in 07).

| Variable | Non-missing | Definition |
|---|---|---|
| `(all panel_master columns)` | - | As above; ER and CR keep the published values. `g` and `g_excess` are REPLACED by the v2 single growth measure; the v1 values are kept as `g_v1`, `g_excess_v1` |
| `LR_c, ER_c, CR_c, c_source` | 238 | PRIMARY v2 outcomes: component-based ratios on the NEP + RIC basis = returns_panel LR_a, ER_a, CR_a (returns where Q4 passes concordance, Tier 1 published where it fails or is missing); c_source = returns_panel annual_source |
| `LR_ret, ER_ret` | 228 | Pure returns LR_c, ER_c (missing where Q4 fails concordance) |
| `ER_gross, ER_netric, COMM_r, MGT_r, ln_assets, TP_r, motor_share, gwp_ret` | 234 | From returns_panel (concordance-passing rows; missing where Q4 fails or is missing) |
| `er1516_corroborated` | 41 | 2015-16 corrected rows only: 1 if |ER_ret - (CR_nic - LR)| <= 5 pp (31 of 41), 0 otherwise |
| `er_t1_flag` | 41 | "ER corrected (returns-corroborated)" / "ER corrected (not returns-corroborated)" on the 41 2015-16 rows |
| `ER_corr2020, CR_corr2020, flag_er_corr2020` | 261 | Tier 1 variant (A20): ER_t1 with the 2020 published ER replaced by ER_ret where Q4 passes concordance (26 rows; LOYALTY keeps the published value); CR_corr2020 = LR + ER_corr2020; flag "2020 ER corrected: published figure excludes commission (returns-corroborated)" |
| `g, g_source` | 230 | v2 single growth measure (3a, A5): exact GWP growth; 2016-19 audited exact GHS; 2020-22 returns GWP (Q4 concordance pass in t and t-1; 2020 uses the audited 2019 base); fallback NIC %-change table (flagged); 2015 NIC %-change table; 2023 as v1 (rounded GHS m); merger years and 2024 missing |
| `gwp_exact, gwp_exact_prev` | 211 | GWP series behind g (audited to 2019, returns 2020-22 where concordance passes) |
| `g_excess` | 230 | g minus the year median (v2) |
| `g_L1, g_L2, g_excess_L1, ln_assets_L1, TP_r_L1, claims_reserve_ratio_L1, LR_c_L1, ER_c_L1, CR_c_L1, g_v1_L1, g_excess_v1_L1` | 226 | Lags on the insurer x year grid (a gap year gives a missing lag); g_L2 missing for 2016 (2014 growth not available, A5) |
| `motor_share_2021` | 250 | The insurer's 2021 motor share of GWP (returns), for the exploratory RQ3 interaction |
