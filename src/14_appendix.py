"""Step 14 (v2, Part 5): assemble the thesis appendix tables, outputs/tables/appendix_*.csv.

Built from the AGGREGATE outputs of steps 04 (models_v2), 08, 10, 12, 13 and the two experiments; no insurer-level
value is read or written. Every file carries a `note` column with one line on sample and inference. Runs last, so it
checks its own output (non-empty, noted) instead of step 07. Skips if the v2 tables are absent (public pipeline = v1).
"""
import sys
import numpy as np, pandas as pd
from config import TABLES, ROOT

need = ['main_models_v2.csv', 'rq3_tests_v2.csv', 'diagnostics_v2.csv', 'cre_mundlak_v2.csv', 'system_gmm_v2.csv',
        'system_gmm_diagnostics_v2.csv', 'anderson_hsiao_v2.csv', 'robust_leave_one_out_summary_v2.csv', 'threshold_v2.csv',
        'seasonality.csv', 'returns_concordance.csv', 'driscoll_kraay_v2.csv']
miss = [f for f in need if not (TABLES / f).exists()]
if miss:
    print(f'Step 14 skipped: v2 tables absent ({", ".join(miss)}); the public pipeline reproduces v1 only.'); sys.exit(0)
rd = lambda f: pd.read_csv(TABLES / f)
EW, AK = ROOT / 'experiments' / 'early_warning' / 'outputs', ROOT / 'experiments' / 'akotey_replication' / 'outputs'
M = rd('main_models_v2.csv')
COLS = ['model', 'outcome', 'variant', 'term', 'coef', 'se', 'p_cluster', 'p_wcb', 'ci95_lo', 'ci95_hi', 'mde_2_8se', 'n', 'insurers', 'note']
SAMPLE = ('v2 sample 2016-2022, start-up years excluded (171 insurer-years, 28 insurers unless n says otherwise); '
          'two-way FE; insurer-clustered SEs (D12); wild cluster bootstrap p (Rademacher, 1,999 reps, exact within-transformation, D14); '
          'MDE = 2.8 x SE; 95% CI = coef +/- 1.96 SE')
out = {}

# 1. FE models: M0-M6 and the RQ3 interaction models, plus the RQ3 Wald tests
fe_ = M[M.block.isin(['main', 'rq3'])][COLS].rename(columns={'note': 'model_note'}).assign(row_type='coefficient')
tt = rd('rq3_tests_v2.csv').rename(columns={'test': 'term', 'F': 'coef', 'p': 'p_cluster'}).assign(
    row_type='Wald test (cluster-robust, F(q, G-1); coef = F)', variant='component (primary)')
out['appendix_fe_models.csv'] = (pd.concat([fe_, tt[['model', 'outcome', 'variant', 'term', 'coef', 'p_cluster', 'q', 'df2', 'n', 'row_type']]],
                                           ignore_index=True), SAMPLE + '. RQ3 tests: Wooldridge (2021), Sections 5.2 and 7.')

# 2. Diagnostics per outcome (M1, v2)
dg, cre = rd('diagnostics_v2.csv'), rd('cre_mundlak_v2.csv').drop_duplicates('outcome').set_index('outcome')
rows = []
for _, r in dg.iterrows():
    c = cre.loc[r.outcome]
    rows += [dict(outcome=r.outcome, test='Hausman (classical, FE vs RE with year dummies)', statistic=r.hausman_chi2, df=r.hausman_df, p=r.hausman_p),
             dict(outcome=r.outcome, test='Mundlak variable-addition (all regressor means = 0; robust)', statistic=c.va_test_F, df=f'{int(c.va_test_q)}, {int(c.va_test_df2)}', p=c.va_test_p),
             dict(outcome=r.outcome, test='Wooldridge serial correlation (FD residuals)', statistic=r.wooldridge_F, df='1, G-1', p=r.wooldridge_p),
             dict(outcome=r.outcome, test='Modified Wald groupwise heteroskedasticity', statistic=r.modwald_chi2, df='', p=r.modwald_p),
             dict(outcome=r.outcome, test='Pesaran CD cross-sectional dependence', statistic=r.pesaran_CD, df='', p=r.pesaran_p)]
dk = rd('driscoll_kraay_v2.csv').assign(test='Driscoll-Kraay SE (Bartlett, bandwidth 2): INDICATIVE ONLY',
                                       row_note='allows for cross-sectional dependence (Pesaran CD significant for ER) but needs large T; T = 7 (D8, D22)')
out['appendix_diagnostics.csv'] = (pd.concat([pd.DataFrame(rows).assign(n=int(dg.n.iloc[0])), dk], ignore_index=True),
                                   'M1 (v2) on the v2 sample (171 insurer-years); the Mundlak test replaces the classical Hausman test as the reported FE-vs-RE test; '
                                   'Driscoll-Kraay rows (term, coef, se, p) are an indicative check only.')

# 3. GMM and Anderson-Hsiao (v2)
gm = rd('system_gmm_v2.csv').merge(rd('system_gmm_diagnostics_v2.csv').drop(columns=['command']), on=['variant', 'outcome'])
gm = gm.assign(estimator='System GMM (pydynpd; collapsed instruments, year dummies; two-step Windmeijer, onestep robust)')
ah = rd('anderson_hsiao_v2.csv').rename(columns={'n': 'n_obs', 'insurers': 'n_insurers'}).assign(estimator='Anderson-Hsiao FD-IV', variant='baseline')
out['appendix_gmm.csv'] = (pd.concat([gm[['estimator', 'variant', 'outcome', 'term', 'coef', 'se', 'p', 'n_obs', 'n_insurers', 'n_instruments',
                                           'ar1_p', 'ar2_p', 'hansen_df', 'hansen_p']], ah], ignore_index=True),
                           'v2 panel 2015-2022, start-ups excluded; component-based outcomes, single growth measure, ln(total assets) as size; '
                           'pooled 1/99 winsorising; System GMM lags 2-3 (variant lags 2-4); Anderson-Hsiao: dY(t-1) instrumented by Y(t-2), clustered SEs.')

# 4. Akotey replication, parts A and B (pre-registered, v1 data)
A = pd.read_csv(AK / 'gmm_results.csv').merge(pd.read_csv(AK / 'gmm_diagnostics.csv').drop(columns=['command']), on=['sample', 'spec', 'outcome'])
Bb = pd.read_csv(AK / 'bridge_results.csv').rename(columns={'p': 'p_cluster', 'wcb_p': 'p_wcb', 'n': 'n_obs', 'version': 'sample', 'model': 'spec'})
out['appendix_replication.csv'] = (pd.concat([A.assign(part='A: difference GMM'), Bb.assign(part='B: timing bridge (two-way FE)')], ignore_index=True),
                                   'Pre-registered (experiments/akotey_replication/README.md); v1 audited data (panel_master), 2015-2022, start-ups excluded; '
                                   'A: Arellano-Bond difference GMM, two-step Windmeijer; B: models.fe + wild cluster bootstrap (after D14 and its addendum).')

# 5. Early warning (Experiments 1-3)
e1 = pd.read_csv(EW / 'exp1_results.csv').assign(section='Exp 1: annual (v1 data; pre-registered 00a2c89)')
e2 = pd.read_csv(EW / 'exp2_results.csv').rename(columns={'score': 'method', 'analysis': 'target'}).assign(section='Exp 2: quarterly nowcast (pre-registered 00a2c89)')
e3 = pd.read_csv(EW / 'exp3_results.csv')
e3['section'] = e3.item.map({'4a': 'v2 additions: annual, CR(t-1) vs growth (pre-registered 3eef056)', '4a (Exp 1 v1 data)': 'v2 additions: annual, CR(t-1) vs growth (pre-registered 3eef056)',
                             '4b': 'v2 additions: quarterly indicators', '4c': 'v2 additions: incremental test (decision rule)', '4d': 'v2 additions: non-submission (exploratory)'})
i17 = pd.read_csv(EW / 'exp3_ifrs17.csv').assign(section='v2 additions: IFRS 17 recalibration (descriptive)')
i17['label'] = np.where(i17.section.eq('v2 additions: IFRS 17 recalibration (descriptive)') & i17.youden_cutoff.notna(),
                        'recalibration needed; current evidence too thin to set a value', '')
out['appendix_early_warning.csv'] = (pd.concat([e1, e2, e3, i17], ignore_index=True),
                                     'Target red zone CR(t) > 110; train t = 2016-2020, test t = 2021-2022 (IFRS 4); all intervals resample insurers '
                                     '(1,999 resamples, percentile 95% CI, paired where compared); IFRS 17 cut-offs with bootstrap ranges are descriptive only.')

# 6. Robustness
blk = lambda b, cond=None: M[(M.block == b) & (cond if cond is not None else True)]
parts = [('size measure: ln(total assets) (M1) vs ln(GWP) (M1b)', blk('main', M.model.isin(['M1', 'M1b_lngwp_size']))),
         ('growth measure: v2 single measure vs v1', pd.concat([blk('main', M.model.eq('M1') & M.term.eq('g_L1_w')),
                                                               blk('robustness', M.variant.str.startswith('v1 growth'))])),
         ('lag length: g(t-2) alone and with g(t-1)', blk('main', M.model.isin(['M6a_g_L2', 'M6b_g_L1_g_L2']))),
         ('reserving: + lagged claims reserve ratio (M1c)', blk('main', M.model.eq('M1c_reserving'))),
         ('exact-basis and gross-basis outcomes (concordance-passing rows)', blk('exact_basis')),
         ('2015-16, 2020 and 2019 outcome sensitivities', pd.concat([blk('outcome_variant'), blk('robustness', M.variant.eq('2017-2022 only'))])),
         ('reverse regression: g(t) on lagged ratios', blk('reverse')),
         ('ownership / brand change years excluded', blk('robustness', M.variant.str.startswith('excl. first year')))]
rb = [p[COLS].rename(columns={'note': 'model_note'}).assign(section=s) for s, p in parts]
lo = rd('robust_leave_one_out_summary_v2.csv').rename(columns={'full_coef': 'coef', 'full_p': 'p_cluster'}).assign(
    section='leave-one-insurer-out (M1, v2)', model='M1')
th = rd('threshold_v2.csv').rename(columns={'ci_lo': 'gamma_ci_lo', 'ci_hi': 'gamma_ci_hi', 'n': 'n'}).assign(
    section='Hansen (1999) threshold on g(t-1) (wild bootstrap under the null, D20)', model='threshold')
out['appendix_robustness.csv'] = (pd.concat(rb + [lo, th], ignore_index=True), SAMPLE + '. Leave-one-out: winsorised values unchanged. '
                                  'Threshold: grid 15th-85th percentile, 999 bootstrap reps, CI by LR inversion.')

# 7-8. Seasonality and concordance (Part 2)
out['appendix_seasonality.csv'] = (rd('seasonality.csv'), "NIC quarterly returns (an NIC product; insurers' unaudited submissions); insurers with figures in all "
                                   'four quarters, no copy-forward, not a merger year; 2024-25 on Insurance Revenue (IFRS 17).')
out['appendix_concordance.csv'] = (rd('returns_concordance.csv'), 'Q4 workbook GWP vs audited NIC GWP, 2015-2023: pass if within max(5%, GHS 0.5m); '
                                   'ratio comparisons on passing rows, NEP + RIC basis (A17-A19).')

for f, (d, note) in out.items():
    d = d.rename(columns={'note': 'row_note'}).copy(); d.insert(0, 'note', note)
    assert len(d) and d.note.str.len().gt(0).all(), f'{f}: empty or unnoted'
    d.to_csv(TABLES / f, index=False)
    print(f'{f}: {len(d)} rows')
print(f'Saved {len(out)} appendix tables (outputs/tables/appendix_*.csv).')
