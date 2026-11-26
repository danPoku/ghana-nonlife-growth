# Data notice

The code in this repository is released under the MIT License (`LICENSE`). The data are covered by this notice instead.

## Source publications (not relicensed)

These files are included so that the results can be reproduced. Neither the MIT License nor CC BY 4.0 applies to
them; cite the publisher when you use them.

| Path | Publication | Publisher |
|---|---|---|
| `data/raw/nic_text/` | Text extracted from the NIC annual reports (Annual Report on the Insurance Industry, 2019, 2020, 2022 and 2024 editions); the reports themselves remain the NIC's publications | National Insurance Commission (NIC), Ghana |
| `data/raw/quarterly/` | Market Report, Quarter 2 2026, Non-Life (insurer-level quarterly returns); source, URL and retrieval date in `data/raw/quarterly/SOURCE.md` | National Insurance Commission (NIC), Ghana |
| `data/raw/macro/` | World Development Indicators, FP.CPI.TOTL.ZG (Ghana), originally from the Ghana Statistical Service | World Bank (WDI data are licensed by the World Bank under CC BY 4.0) |

The figures in the NIC quarterly returns workbook are insurers' unaudited quarterly submissions, compiled and
published by the NIC.

## Derived data and outputs (CC BY 4.0)

The tables and figures derived from these sources by the authors are released under the Creative Commons Attribution
4.0 International licence (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/):

- `data/processed/` (insurer-year panels, estimation samples, returns panels)
- `outputs/tables/` and `outputs/figures/`
- `experiments/*/outputs/`

Attribution: Sarfo, B. K., & Poku, D. G. (2026), with the National Insurance Commission as the source of the
underlying data. See `CITATION.cff`.

## Not included

The supplementary facultative-reinsurance analysis (pipeline step 6) uses a reinsurer's production report that
contains client names. It is confidential and is not in this repository; the step skips when the file is absent.
