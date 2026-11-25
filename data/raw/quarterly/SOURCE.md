# NIC quarterly returns workbook: source

| | |
|---|---|
| Title | Market Report, Quarter 2 2026, Non-Life (insurer-level quarterly returns, Q1 2013 to Q2 2026) |
| File | `MARKET_REPORT_QUARTER_2_2026_NON_LIFE_bf1c110d5c.xlsx` |
| Publisher | National Insurance Commission (NIC), Ghana |
| URL | https://api.nic.gov.gh/api/documents/MARKET_REPORT_QUARTER_2_2026_NON_LIFE_bf1c110d5c.xlsx |
| Retrieved | 21 November 2026, 12:23 UTC |
| SHA-256 | `4cd98367b9722133cbc9d21aafa3a190c2a9cb405c352b97e89eecd9c7ae0177` (also in `data/raw/CHECKSUMS`, verified by the pipeline before reading) |

Figures are insurers' unaudited quarterly submissions, compiled and published by the NIC.

The download link on the NIC website carries access-token and version parameters; they are omitted above.

## Edition used

The analysis was built on the previous edition (Market Report 2025, Quarter 1 2026, Non-Life; SHA-256
`68e13bbf4b0673d12415908fc4c7a6f59713d47d951b102c3747aafcb30fb341`), which is not in the repository. Before switching
(25 Nov 2026) the two editions were compared cell by cell for every sheet from Q1 2013 to Q1 2026:

- Q1 2013 to Q4 2025 (52 sheets): identical in every cell.
- Q1 2026: the earlier edition had an unlabelled column (blank header) holding private + commercial fire premium for
  20 of 25 insurers; the Q2 2026 edition drops it. With columns aligned by header, every named column, every insurer
  name and every value is identical. The pipeline skips blank-header columns, so it never read this column.
- Q2 2026: new in this edition; not read (`QUARTERLY_LAST` in `src/config.py` caps the read at Q1 2026).

All outputs of the pipeline are unchanged by the switch (see `docs/data_issues.md`, A17).
