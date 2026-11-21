"""v2 main models (Part 3 of the methodology revision), run at the end of step 04.

Data: data/processed/confidential/panel_v2.csv (step 03), which holds values derived from the NIC quarterly returns
workbook (an NIC product; insurers' unaudited quarterly submissions), so the insurer-level estimation sample is written
to data/processed/confidential/ and only aggregate results go to outputs/tables/. Skips if the panel is absent.

Design (authors' decisions after the Part 2 review):
- Sample: 2016-2022, start-up years excluded, complete on the M1 variables (outcome, g_L1, RET, ln_assets_L1, LEV_net_L1).
- PRIMARY outcomes: component-based ratios on the NEP + RIC basis, LR_c and ER_c (returns where Q4 passes concordance,
  Tier 1 where it fails or is missing), winsorised 1/99 on the sample; CR_w = LR_w + ER_w (additive, checked in 07).
- Growth: single measure g (exact GWP; step 03). Size: ln_assets_L1 (primary), ln_gwp_L1 in M1b.
- Every model: models.fe (two-way FE, D12 clustered SEs), models.wcb (exact within-transformation, D14, B = 1999) for
  every reported term, 95% CI and minimum detectable effect 2.8 x SE.
- Outcome variants for M1 (sensitivities): Tier 1 published (2015-16 ER corrected), Tier 1 corrected 2020 (A20),
  primary excluding 2020 outcomes, primary excluding 2019 outcomes; plus Tier 1 published without the 10 uncorroborated
  2015-16 rows.
- Exact-basis parallel table (M1) on concordance-passing rows only, with a sensitivity excluding 2019.
- RQ3: g_L1 x year dummies 2020, 2021, 2022 (Wooldridge 2021, Section 5.2), joint and equality Wald tests (cluster-
  robust, F(q, G-1)); pre-trend: g_L1 x 2017..2022, test 2017 = 2018 = 2019 = 0 (Section 7); exploratory triple
  interaction with demeaned 2021 motor share.
- Two-way Mundlak (correlated random effects; Wooldridge 2021, Theorem 3.1 and Section 9.1 for unbalanced panels):
  pooled OLS on the M1 regressors, their insurer means, year dummies and the insurer means of the year dummies;
  within coefficients asserted equal to models.fe; robust variable-addition test that the regressor means are zero.
- Reverse regression: g_t on CR_c(t-1), and on LR_c(t-1) and ER_c(t-1), with the M1 controls.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import CONFIDENTIAL, TABLES, QUARTERLY_FILE
from models import fe, wcb, wald

B_WCB = 1999
def wins(s, lo=.01, hi=.99):
    a, b = s.quantile([lo, hi]); return s.clip(a, b)

def fit_rows(d, y, X, block, model, outcome, variant, note='', boot=True):
    d = d.dropna(subset=[y] + X)
    r = fe(d, y, X); out = []
    for t in X:
        b, se = float(r.params[t]), float(r.std_errors[t])
        out.append(dict(block=block, model=model, outcome=outcome, variant=variant, term=t, coef=b, se=se,
                        p_cluster=float(r.pvalues[t]), p_wcb=wcb(d, y, X, var=t, B=B_WCB)[1] if boot else np.nan,
                        ci95_lo=b - 1.96 * se, ci95_hi=b + 1.96 * se, mde_2_8se=2.8 * se, n=int(r.nobs),
                        insurers=int(d.insurer_id.nunique()), note=note))
    return out, r, d

def add_outcomes(D, lr, er):
    D = D.copy(); D['LR_w'] = wins(D[lr]); D['ER_w'] = wins(D[er]); D['CR_w'] = D.LR_w + D.ER_w; return D

def mundlak(D, y, X, fe_params=None):
    """Two-way Mundlak (Wooldridge 2021, Theorem 3.1; Section 9.1 for unbalanced panels): pooled OLS of y on X, insurer
    means of X, year dummies and insurer means of the year dummies; insurer-clustered SEs. Returns one dict per term
    (within, mean coefficient, between-type sum with SE and p) and the variable-addition test that all X means are 0."""
    from scipy import stats
    d = D.dropna(subset=[y] + X).reset_index(drop=True)
    yd = pd.get_dummies(d.year, prefix='yr', drop_first=True, dtype=float)
    Z = pd.concat([d[X], d.groupby('insurer_id')[X].transform('mean').add_prefix('mean_'), yd,
                   yd.groupby(d.insurer_id).transform('mean').add_prefix('mean_')], axis=1)
    res = sm.OLS(d[y], sm.add_constant(Z)).fit(cov_type='cluster', cov_kwds={'groups': d.insurer_id})
    diff = float(np.max(np.abs(res.params[X].values - fe_params[X].values))) if fe_params is not None else np.nan
    if fe_params is not None: assert diff < 1e-8, f'Mundlak within coefficients differ from models.fe ({diff})'
    G = d.insurer_id.nunique(); cv = res.cov_params(); mx = ['mean_' + c for c in X]
    F, q, df2, p = wald(res.params[mx].values, cv.loc[mx, mx].values, np.eye(len(mx)), G)
    out = []
    for t in X:
        w, bm = res.params[t], res.params['mean_' + t]
        se = float(np.sqrt(cv.loc[t, t] + cv.loc['mean_' + t, 'mean_' + t] + 2 * cv.loc[t, 'mean_' + t]))
        out.append(dict(outcome=y, term=t, within=w, within_se=res.bse[t], mean_coef=bm, mean_se=res.bse['mean_' + t],
                        mean_p=res.pvalues['mean_' + t], between_sum=w + bm, between_sum_se=se,
                        between_sum_p=float(2 * (1 - stats.norm.cdf(abs((w + bm) / se)))), n=len(d), insurers=G,
                        max_abs_diff_within_vs_fe=diff, va_test_F=F, va_test_q=q, va_test_df2=df2, va_test_p=p))
    return out

def diagnostics(B, y, X):
    """M1 diagnostics as in step 04 (v1), on the v2 sample: classical Hausman (FE vs RE with year dummies), Wooldridge
    serial correlation (FD residuals on their lag, H0 coefficient -0.5), modified Wald groupwise heteroskedasticity
    (Greene), Pesaran CD cross-sectional dependence."""
    from scipy import stats
    from linearmodels.panel import PanelOLS, RandomEffects
    d = B.dropna(subset=[y] + X).set_index(['insurer_id', 'year'])
    fe_ = PanelOLS(d[y], d[X], entity_effects=True, time_effects=True).fit(cov_type='unadjusted')
    dd = d.copy()
    for yr in dd.index.get_level_values(1).unique()[1:]: dd[f'y{yr}'] = (dd.index.get_level_values(1) == yr).astype(float)
    Xr = X + [c for c in dd.columns if c.startswith('y20')]
    re_ = RandomEffects(dd[y], sm.add_constant(dd[Xr])).fit()
    b = fe_.params[X] - re_.params[X]; Vd = fe_.cov.loc[X, X] - re_.cov.loc[X, X]
    H = float(b.T @ np.linalg.pinv(Vd.values) @ b); hp = 1 - stats.chi2.cdf(H, len(X))
    fd = d.reset_index().sort_values(['insurer_id', 'year'])
    fdv = fd.groupby('insurer_id')[[y] + X].diff(); fdv['insurer_id'] = fd.insurer_id; fdv['year'] = fd.year; fdv = fdv.dropna()
    fdv['e'] = sm.OLS(fdv[y], fdv[X]).fit().resid; fdv['e_l'] = fdv.groupby('insurer_id').e.shift(); f2 = fdv.dropna()
    w = sm.OLS(f2.e, f2.e_l).fit(cov_type='cluster', cov_kwds={'groups': f2.insurer_id})
    wt = ((w.params['e_l'] + 0.5) / w.bse['e_l']) ** 2; wp = 1 - stats.f.cdf(wt, 1, f2.insurer_id.nunique() - 1)
    e = fe_.resids; g = e.groupby(level=0); s2i = g.apply(lambda x: (x ** 2).mean()); Ti = g.size()
    Vi = g.apply(lambda x: ((x ** 2 - (x ** 2).mean()) ** 2).sum() / (len(x) * (len(x) - 1)) if len(x) > 1 else np.nan)
    ok = (Ti >= 3) & (Vi > 1e-8); MW = float((((s2i - (e ** 2).mean()) ** 2) / (Vi / Ti))[ok].sum()); mwp = 1 - stats.chi2.cdf(MW, ok.sum())
    ew = e.unstack(level=0); ids = ew.columns; num = 0; cnt = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            pr = ew[[ids[i], ids[j]]].dropna()
            if len(pr) >= 3 and pr.std().min() > 0: num += np.sqrt(len(pr)) * np.corrcoef(pr.iloc[:, 0], pr.iloc[:, 1])[0, 1]; cnt += 1
    CD = float(np.sqrt(2 / cnt) * num) if cnt else np.nan
    return dict(n=int(fe_.nobs), hausman_chi2=H, hausman_df=len(X), hausman_p=float(hp), wooldridge_F=float(wt), wooldridge_p=float(wp),
                modwald_chi2=MW, modwald_p=float(mwp), pesaran_CD=CD, pesaran_p=float(2 * (1 - stats.norm.cdf(abs(CD)))))

def anderson_hsiao(E):
    """Anderson-Hsiao FD-IV (as step 04, v1) on v2 data: dY on dY(t-1) instrumented by Y(t-2), differenced M1
    regressors (g_L1, RET, ln_assets_L1, LEV_net_L1), year dummies; insurer-clustered SEs; LR_c, ER_c, CR_c."""
    from linearmodels.iv import IV2SLS
    out = []
    X0 = ['g_L1', 'RET', 'ln_assets_L1', 'LEV_net_L1']
    for y in ['LR_c', 'ER_c', 'CR_c']:
        d = E.sort_values(['insurer_id', 'year']).copy()
        for v in [y] + X0: d[v] = wins(d[v])
        d['dY'] = d.groupby('insurer_id')[y].diff(); d['dYl'] = d.groupby('insurer_id')['dY'].shift()
        d['Yl2'] = d.groupby('insurer_id')[y].shift(2)
        for v in X0: d['d_' + v] = d.groupby('insurer_id')[v].diff()
        d = d.dropna(subset=['dY', 'dYl', 'Yl2'] + ['d_' + v for v in X0])
        yd = pd.get_dummies(d.year, prefix='y', drop_first=True).astype(float)
        exog = pd.concat([d[['d_' + v for v in X0]], yd], axis=1); exog['const'] = 1
        r = IV2SLS(d.dY, exog, d[['dYl']], d[['Yl2']]).fit(cov_type='clustered', clusters=d.insurer_id)
        out.append(dict(outcome=y, term='d_g_L1', coef=float(r.params['d_g_L1']), se=float(r.std_errors['d_g_L1']),
                        p=float(r.pvalues['d_g_L1']), rho=float(r.params['dYl']), rho_p=float(r.pvalues['dYl']), n=int(r.nobs),
                        insurers=int(d.insurer_id.nunique()), first_stage_F=float(r.first_stage.diagnostics['f.stat'].iloc[0])))
    return pd.DataFrame(out)

def run():
    PV = CONFIDENTIAL / 'panel_v2.csv'
    if not (QUARTERLY_FILE.exists() and PV.exists()):
        print('v2 models skipped: NIC quarterly returns workbook or panel_v2 absent (public pipeline = v1 results only).')
        return
    V = pd.read_csv(PV)
    E = V[V.year.between(2016, 2022) & ~V.startup].copy()
    base = E.dropna(subset=['LR_c', 'ER_c', 'g_L1', 'RET', 'ln_assets_L1', 'LEV_net_L1']).copy()
    for v in ['g_L1', 'g_L2', 'd_ms_L1', 'LEV_net_L1', 'g_excess_L1', 'claims_reserve_ratio_L1']: base[v + '_w'] = wins(base[v])
    base['g_L1_sq_w'] = base.g_L1_w ** 2 / 100
    p75 = base.g_excess_L1.quantile(.75); base['hi_g_w'] = np.maximum(0, base.g_excess_L1_w - p75)
    B = add_outcomes(base, 'LR_c', 'ER_c')
    B.to_csv(CONFIDENTIAL / 'estimation_sample_v2.csv', index=False)
    ctrl = ['RET', 'ln_assets_L1', 'LEV_net_L1_w']
    specs = {'M0_growth_only': ['g_L1_w'], 'M1': ['g_L1_w'] + ctrl,
             'M1b_lngwp_size': ['g_L1_w', 'RET', 'ln_gwp_L1', 'LEV_net_L1_w'],
             'M1c_reserving': ['g_L1_w'] + ctrl + ['claims_reserve_ratio_L1_w'],
             'M2_quadratic': ['g_L1_w', 'g_L1_sq_w'] + ctrl, 'M3_piecewise': ['g_L1_w', 'hi_g_w'] + ctrl,
             'M4_mktshare': ['d_ms_L1_w'] + ctrl, 'M6a_g_L2': ['g_L2_w'] + ctrl, 'M6b_g_L1_g_L2': ['g_L1_w', 'g_L2_w'] + ctrl}
    rows, fits = [], {}
    for y in ['LR_w', 'ER_w', 'CR_w']:
        for m, X in specs.items():
            o, r, _ = fit_rows(B, y, X, 'main', m, y, 'component (primary)',
                               'M6: 2017-2022 (g_L2 missing for 2016)' if 'g_L2_w' in X else '')
            rows += o; fits[(y, m)] = r
    # ---------- outcome variants for M1 (5 + uncorroborated) ----------
    var_sets = [('component (primary)', B),
                ('Tier 1 published (2015-16 ER corrected)', add_outcomes(base, 'LR', 'ER_t1')),
                ('Tier 1 corrected 2020', add_outcomes(base, 'LR', 'ER_corr2020')),
                ('component, excl. 2020 outcomes', B[B.year != 2020]),
                ('component, excl. 2019 outcomes', B[B.year != 2019]),
                ('Tier 1 published, excl. uncorroborated 2015-16 rows',
                 add_outcomes(base[base.er1516_corroborated.fillna(1) != 0], 'LR', 'ER_t1'))]
    for lab, D in var_sets:
        for y in ['LR_w', 'ER_w', 'CR_w']:
            rows += fit_rows(D, y, specs['M1'], 'outcome_variant', 'M1', y, lab,
                             'excl. rows keep the primary winsorising bounds' if 'excl. 20' in lab else '')[0]
    # ---------- exact-basis parallel table (M1), concordance-passing rows only ----------
    Bx = base[base.c_source == 'returns (concordance pass)'].copy()
    for lab, D0 in [('concordance pass', Bx), ('concordance pass, excl. 2019', Bx[Bx.year != 2019])]:
        D = add_outcomes(D0, 'LR_c', 'ER_c')
        for o in ['ER_gross', 'ER_netric', 'COMM_r', 'MGT_r']: D[o + '_w'] = wins(D[o])
        names = {'LR_w': 'LR_c (exact)', 'ER_w': 'ER_c (exact)', 'CR_w': 'CR_c (exact)', 'ER_gross_w': 'ER_gross',
                 'ER_netric_w': 'ER_netric (true NEP)', 'COMM_r_w': 'COMM_r', 'MGT_r_w': 'MGT_r'}
        for y, name in names.items():
            rows += fit_rows(D, y, specs['M1'], 'exact_basis', 'M1', name, lab)[0]
    # ---------- RQ3: year-specific growth slopes ----------
    tests = []
    D = B.copy()
    for yr in range(2017, 2023): D[f'gx{yr}'] = D.g_L1_w * (D.year == yr)
    D['post'] = (D.year >= 2020).astype(float)
    m21 = D.drop_duplicates('insurer_id').set_index('insurer_id').motor_share_2021
    D['motor_dm'] = D.insurer_id.map(m21 - m21.mean())
    D['g_post'] = D.g_L1_w * D.post; D['g_motor'] = D.g_L1_w * D.motor_dm
    D['g_post_motor'] = D.g_post * D.motor_dm; D['post_motor'] = D.post * D.motor_dm
    rq3 = {'RQ3_year_slopes': specs['M1'] + ['gx2020', 'gx2021', 'gx2022'],
           'RQ3_pretrend': specs['M1'] + [f'gx{yr}' for yr in range(2017, 2023)],
           'RQ3_motor_exploratory': specs['M1'] + ['g_post', 'g_motor', 'g_post_motor', 'post_motor']}
    for y in ['LR_w', 'ER_w', 'CR_w']:
        for m, X in rq3.items():
            o, r, d = fit_rows(D, y, X, 'rq3', m, y, 'component (primary)',
                               'base years 2016-2019' if m == 'RQ3_year_slopes' else 'base year 2016' if m == 'RQ3_pretrend'
                               else 'insurers with a 2021 motor share; motor share demeaned across insurers')
            rows += o; b, Vc, G = r.params, r.cov, r.n_clusters
            if m == 'RQ3_year_slopes':
                ix = [X.index(c) for c in ['gx2020', 'gx2021', 'gx2022']]
                for name, R in [('2020 = 2021 = 2022 = 0 (joint)', np.eye(len(X))[ix]),
                                ('2020 = 2021 = 2022 (equality)', np.eye(len(X))[[ix[0], ix[1]]] - np.eye(len(X))[[ix[1], ix[2]]])]:
                    F, q, df2, p = wald(b.values, Vc.values, R, G)
                    tests.append(dict(model=m, outcome=y, test=name, F=F, q=q, df2=df2, p=p, n=int(r.nobs)))
            if m == 'RQ3_pretrend':
                ix = [X.index(c) for c in ['gx2017', 'gx2018', 'gx2019']]
                F, q, df2, p = wald(b.values, Vc.values, np.eye(len(X))[ix], G)
                tests.append(dict(model=m, outcome=y, test='pre-trend: 2017 = 2018 = 2019 = 0 (relative to 2016)', F=F, q=q,
                                  df2=df2, p=p, n=int(r.nobs)))
    pd.DataFrame(tests).to_csv(TABLES / 'rq3_tests_v2.csv', index=False)
    # ---------- two-way Mundlak (CRE) ----------
    cre = []
    X = specs['M1']
    for y in ['LR_w', 'ER_w', 'CR_w']:
        d = B.dropna(subset=[y] + X).reset_index(drop=True)
        yd = pd.get_dummies(d.year, prefix='yr', drop_first=True, dtype=float)
        Z = pd.concat([d[X], d.groupby('insurer_id')[X].transform('mean').add_prefix('mean_'), yd,
                       yd.groupby(d.insurer_id).transform('mean').add_prefix('mean_')], axis=1)
        res = sm.OLS(d[y], sm.add_constant(Z)).fit(cov_type='cluster', cov_kwds={'groups': d.insurer_id})
        rf = fits[(y, 'M1')]; diff = float(np.max(np.abs(res.params[X].values - rf.params[X].values)))
        assert diff < 1e-8, f'Mundlak within coefficients differ from models.fe ({diff})'
        G = d.insurer_id.nunique(); cv = res.cov_params()
        mx = ['mean_' + c for c in X]
        F, q, df2, p = wald(res.params[mx].values, cv.loc[mx, mx].values, np.eye(len(mx)), G)
        for t in X:
            w, bm = res.params[t], res.params['mean_' + t]
            vs = cv.loc[t, t] + cv.loc['mean_' + t, 'mean_' + t] + 2 * cv.loc[t, 'mean_' + t]
            cre.append(dict(outcome=y, term=t, within=w, within_se=res.bse[t], mean_coef=bm, mean_se=res.bse['mean_' + t],
                            mean_p=res.pvalues['mean_' + t], between_sum=w + bm, between_sum_se=np.sqrt(vs),
                            between_sum_p=2 * (1 - __import__('scipy').stats.norm.cdf(abs((w + bm) / np.sqrt(vs)))),
                            n=len(d), insurers=G, max_abs_diff_within_vs_fe=diff,
                            va_test_F=F, va_test_q=q, va_test_df2=df2, va_test_p=p))
    pd.DataFrame(cre).to_csv(TABLES / 'cre_mundlak_v2.csv', index=False)
    # ---------- reverse regression ----------
    Rv = E.dropna(subset=['g', 'CR_c_L1', 'RET', 'ln_assets_L1', 'LEV_net_L1']).copy()
    for v in ['g', 'CR_c_L1', 'LR_c_L1', 'ER_c_L1', 'LEV_net_L1']: Rv[v + '_w'] = wins(Rv[v])
    for m, X in {'REV1_CR': ['CR_c_L1_w', 'RET', 'ln_assets_L1', 'LEV_net_L1_w'],
                 'REV2_LR_ER': ['LR_c_L1_w', 'ER_c_L1_w', 'RET', 'ln_assets_L1', 'LEV_net_L1_w']}.items():
        rows += fit_rows(Rv, 'g_w', X, 'reverse', m, 'g_w (growth in t)', 'component (primary)',
                         'outcome g(t) and lagged ratios winsorised on this sample')[0]
    # ---------- ownership / brand-change sensitivity (M1, primary outcomes) ----------
    from config import RENAMES
    rob = []
    for lab, pairs in [('excl. first year under new name (Q4 returns names)', {(r['insurer_id'], r['year']) for r in RENAMES}),
                       ('excl. first year under new name, Coronation 2020 (NIC report name)',
                        {(r['insurer_id'], r.get('alt_year', r['year'])) for r in RENAMES})]:
        keep = ~pd.Series([(i, y) in pairs for i, y in zip(B.insurer_id, B.year)], index=B.index)
        for y in ['LR_w', 'ER_w', 'CR_w']:
            o = fit_rows(B[keep], y, specs['M1'], 'robustness', 'M1', y, lab,
                         f'{int((~keep).sum())} insurer-years dropped (SUNU, BEDROCK, CORONATION, SAHAM_SANLAM); primary winsorising bounds kept')[0]
            rows += o; rob += [dict(section='ownership change', **r) for r in o]
    # ---------- growth measure (v1 vs v2) and 2017-2022 only, on the primary outcomes (Part 5 robustness) ----------
    Bg = B.copy(); Bg['g_v1_L1_w'] = wins(Bg.g_v1_L1)
    for y in ['LR_w', 'ER_w', 'CR_w']:
        rows += fit_rows(Bg, y, ['g_v1_L1_w'] + ctrl, 'robustness', 'M1', y, 'v1 growth measure (g_v1_L1)',
                         'winsorised 1/99 on the v2 sample')[0]
        rows += fit_rows(B[B.year >= 2017], y, specs['M1'], 'robustness', 'M1', y, '2017-2022 only',
                         '2016 outcomes dropped (2015-16 tabulation issue); primary winsorising bounds kept')[0]
    M = pd.DataFrame(rows); M.to_csv(TABLES / 'main_models_v2.csv', index=False)
    # ---------- diagnostics on M1 (v2) and Anderson-Hsiao (v2) ----------
    pd.DataFrame([dict(outcome=y, **diagnostics(B, y, specs['M1'])) for y in ['LR_w', 'ER_w', 'CR_w']]).to_csv(
        TABLES / 'diagnostics_v2.csv', index=False)
    anderson_hsiao(E).to_csv(TABLES / 'anderson_hsiao_v2.csv', index=False)
    # ---------- v1 -> v2 bridge: change one element at a time (M1) ----------
    def m1(D0, lr, er, gcol, size, additive):
        D = D0.dropna(subset=[lr, er, gcol, 'RET', size, 'LEV_net_L1']).copy()
        D['g_L1_w'] = wins(D[gcol]); D['LEV_net_L1_w'] = wins(D.LEV_net_L1)
        D['LR_w'] = wins(D[lr]); D['ER_w'] = wins(D[er]); D['CR_w'] = D.LR_w + D.ER_w if additive else wins(D[lr] + D[er])
        return D, ['g_L1_w', 'RET', size, 'LEV_net_L1_w']
    steps = [('A v1 (published LR, ER; v1 growth; ln GWP; CR winsorised separately)', ('LR', 'ER', 'g_v1_L1', 'ln_gwp_L1', False)),
             ('B + additive winsorising (CR_w = LR_w + ER_w)', ('LR', 'ER', 'g_v1_L1', 'ln_gwp_L1', True)),
             ('C + 2015-16 ER corrected (Tier 1)', ('LR', 'ER_t1', 'g_v1_L1', 'ln_gwp_L1', True)),
             ('D + single growth measure', ('LR', 'ER_t1', 'g_L1', 'ln_gwp_L1', True)),
             ('E + ln(assets) as size (sample with assets)', ('LR', 'ER_t1', 'g_L1', 'ln_assets_L1', True)),
             ('F + component-based outcomes = v2 primary', ('LR_c', 'ER_c', 'g_L1', 'ln_assets_L1', True))]
    br, brm = [], []
    for lab, (lr, er, gc, size, add) in steps:
        D, X = m1(E, lr, er, gc, size, add)
        for y in ['LR_w', 'ER_w', 'CR_w']:
            r = fe(D, y, X)
            for t in ['g_L1_w', size]:
                br.append(dict(step=lab, outcome=y, term='growth' if t == 'g_L1_w' else f'size ({size})', coef=r.params[t],
                               se=r.std_errors[t], p_cluster=r.pvalues[t], p_wcb=wcb(D, y, X, var=t, B=B_WCB)[1],
                               mde_2_8se=2.8 * r.std_errors[t], n=int(r.nobs), insurers=int(D.insurer_id.nunique())))
            if lab[0] in 'AF':
                brm += [dict(step=lab, **c) for c in mundlak(D, y, X, r.params)]
    BR = pd.DataFrame(br)
    a = BR[(BR.step.str.startswith('A')) & (BR.outcome == 'CR_w') & (BR.term == 'growth')].coef.iloc[0]
    assert abs(a - 0.054668) < 1e-4, f'bridge step A does not reproduce the v1 M1 CR growth coefficient ({a})'
    f_ = BR[(BR.step.str.startswith('F')) & (BR.outcome == 'CR_w') & (BR.term == 'growth')].coef.iloc[0]
    assert abs(f_ - fits[('CR_w', 'M1')].params['g_L1_w']) < 1e-10, 'bridge step F differs from the v2 primary M1'
    BR.to_csv(TABLES / 'v1_v2_bridge.csv', index=False); pd.DataFrame(brm).to_csv(TABLES / 'v1_v2_bridge_mundlak.csv', index=False)
    # ---------- growth quartiles on v2 data (Figure 3) ----------
    Bq = B.copy(); Bq['gq'] = pd.qcut(Bq.g_excess_L1, 4, labels=['Q1 lowest', 'Q2', 'Q3', 'Q4 highest'])
    Bq.groupby('gq', observed=True).agg(n=('LR_w', 'size'), g_excess_L1=('g_excess_L1', 'median'), LR=('LR_w', 'mean'),
        ER=('ER_w', 'mean'), CR=('CR_w', 'mean'), share_CR_gt100=('CR_w', lambda s: (s > 100).mean() * 100)).round(1) \
        .to_csv(TABLES / 'growth_quartiles_v2.csv')
    # ---------- exits: insurers that stopped reporting (descriptive) ----------
    EXITS = {'ALLIANZ': 'last reported 2023; merged into SanlamAllianz in 2024 (D13)',
             'HERITAGE': 'last reported 2019; no 2016 row (Q4 2016 return has no figures; not in the NIC 2016 tables)',
             'MULTI': 'last reported 2019 (first reported 2017)', 'REGENCYNEM': 'last reported 2020'}
    W = V[V.year.between(2015, 2023)].copy()
    rk = lambda c: W.groupby('year')[c].rank(pct=True)
    W['g_pct'] = rk('g'); W['CR_c_pct'] = rk('CR_c'); W['g_v1_pct'] = rk('g_v1'); W['CR_pct'] = rk('CR')
    med = W.groupby('year')[['g', 'CR_c', 'g_v1', 'CR']].median().add_suffix('_year_median')
    ex = []
    for i, note in EXITS.items():
        d = W[(W.insurer_id == i) & (W.LR.notna() | W.LR_c.notna())].sort_values('year').tail(2)
        for _, r in d.iterrows(): ex.append(dict(insurer_id=i, status=note, **r[['year', 'g', 'g_v1', 'LR_c', 'ER_c', 'CR_c', 'LR', 'ER',
                                                  'CR', 'ms', 'c_source', 'g_pct', 'CR_c_pct', 'g_v1_pct', 'CR_pct']].to_dict()))
    EX = pd.DataFrame(ex).merge(med, left_on='year', right_index=True)
    EX.to_csv(CONFIDENTIAL / 'exits.csv', index=False)                      # component basis: workbook-derived (A2)
    EX[['insurer_id', 'status', 'year', 'g_v1', 'LR', 'ER', 'CR', 'ms', 'g_v1_pct', 'CR_pct', 'g_v1_year_median', 'CR_year_median']] \
        .assign(note='Tier 1 published values (public); component-based version in data/processed/confidential/exits.csv') \
        .to_csv(TABLES / 'exits.csv', index=False)
    # ---------- RQ1 descriptive series (all insurers, NWP-weighted) ----------
    ind = []
    for yr, d in V[V.year.between(2015, 2023)].groupby('year'):
        r = dict(year=yr)
        for lab, (lr, er) in {'component': ('LR_c', 'ER_c'), 'published': ('LR', 'ER'), 'tier1_corr': ('LR', 'ER_corr2020')}.items():
            w = d.dropna(subset=[lr, er, 'nwp'])
            r.update({f'n_{lab}': len(w), f'LR_{lab}': np.average(w[lr], weights=w.nwp), f'ER_{lab}': np.average(w[er], weights=w.nwp)})
            r[f'CR_{lab}'] = r[f'LR_{lab}'] + r[f'ER_{lab}']
        r['note'] = ('2019-2020: published and component-based ER differ by 13-18 pp: Q4 2019 returns differ from the audited '
                     'figures (A18); the published 2020 ER excludes commission (A20); management/(NEP+RIC) falls sharply from '
                     'Q1 2021, when the returns template changed (A20)') if yr in (2019, 2020, 2021) else ''
        ind.append(r)
    pd.DataFrame(ind).to_csv(TABLES / 'industry_trends_v2.csv', index=False)
    # ---------- printed summary ----------
    pd.set_option('display.width', 220)
    print(f"\nv2 estimation sample: {len(B)} insurer-years, {B.insurer_id.nunique()} insurers, {B.year.min()}-{B.year.max()} "
          f"(c_source: {B.c_source.value_counts().to_dict()})")
    show = M[M.term.isin(['g_L1_w', 'ln_assets_L1', 'ln_gwp_L1', 'g_L1_sq_w', 'hi_g_w', 'd_ms_L1_w', 'g_L2_w'])]
    print(show[show.block == 'main'][['model', 'outcome', 'term', 'coef', 'se', 'p_cluster', 'p_wcb', 'n']].round(4).to_string(index=False))
    v = M[(M.block == 'outcome_variant') & (M.term == 'g_L1_w')].pivot(index='variant', columns='outcome', values='coef')
    print('\nM1 growth coefficient by outcome variant:'); print(v.round(4).to_string())
    print('\nRQ3 tests:'); print(pd.DataFrame(tests).round(4).to_string(index=False))
    print('\nMundlak (size and growth):'); print(pd.DataFrame(cre)[lambda d: d.term.isin(['ln_assets_L1', 'g_L1_w'])].round(4).to_string(index=False))
    print('\nReverse:'); print(M[M.block == 'reverse'][['model', 'term', 'coef', 'se', 'p_cluster', 'p_wcb', 'n']].round(4).to_string(index=False))
    print('\nOwnership-change sensitivity (M1 growth):'); print(pd.DataFrame(rob)[lambda d: d.term == 'g_L1_w'][['variant', 'outcome', 'coef', 'se', 'p_wcb', 'n']].round(4).to_string(index=False))
    print('\nv1 -> v2 bridge:'); print(BR.round(4).to_string(index=False))
    print('\nExits:'); print(EX.round(2).to_string(index=False))
    print('Saved: main_models_v2.csv, rq3_tests_v2.csv, cre_mundlak_v2.csv, industry_trends_v2.csv, v1_v2_bridge*.csv, '
          'growth_quartiles_v2.csv, exits.csv, diagnostics_v2.csv, anderson_hsiao_v2.csv (outputs/tables); estimation_sample_v2.csv, exits.csv (confidential)')
