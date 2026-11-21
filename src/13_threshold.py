"""Step 13 (v2, 3f): Hansen (1999) panel threshold test on lagged premium growth, validated by simulation first.

Model (two-way FE): y_it = a_i + l_t + X_it b + c1 q_it 1(q_it <= gamma) + c2 q_it 1(q_it > gamma) + e_it, q = g_L1_w,
X = RET, ln_assets_L1, LEV_net_L1_w (the M1 controls), y = CR_w (also LR_w, ER_w on real data).

Estimation: insurer and year effects are partialled out exactly by least squares (Frisch-Waugh-Lovell; as in
models.within, D14), then gamma is chosen by minimising the sum of squared residuals S1(gamma) over a grid of the
observed values of q between its 15th and 85th percentiles. Test of no threshold (c1 = c2): F1 = (S0 - S1) / s2,
s2 = S1 / (N - rank(dummies) - k - 1). Confidence set for gamma: grid points with LR(gamma) = (S1(gamma) - S1) / s2
<= -2 ln(1 - sqrt(0.95)) = 7.35 (Hansen 2000), reported as [min, max].

Bootstrap (DEPARTURE from Hansen 1999, decision A7, recorded in D20): Hansen resamples each individual's vector of
residuals, which requires a balanced panel and a one-way model. This panel is unbalanced (1-7 years per insurer) and
the model is two-way, so the null distribution of F1 is obtained by a wild bootstrap under the null (linear model):
y* = fitted + e * w_i with one Rademacher sign w_i per insurer, insurer and year effects re-absorbed in every sample,
regressors and grid held fixed, 999 replications.

Validation FIRST (authors' instruction): 200 simulated panels per design, on the real estimation-sample structure
(same insurers, years, unbalanced pattern, X and q), y generated from the M1 fit with normal errors of the M1
residual s.d.: (a) no threshold -> rejection rate at 5% = size; (b) threshold at the 60th percentile of q, slope
above it larger by delta = 0.25 and 0.5 pp per pp -> rejection rate = power. Real-data estimation runs only once
RUN_REAL_DATA is set to True after the authors have reviewed the simulation results.
"""
import sys
import numpy as np, pandas as pd
from config import CONFIDENTIAL, TABLES, QUARTERLY_FILE
from models import dummies, absorb, fe

RUN_REAL_DATA = True           # approved by the authors after reviewing the simulation results (Part 3, 21 Nov 2026)
B_BOOT, N_SIM, SEED = 999, 200, 20261121
C95 = -2 * np.log(1 - np.sqrt(0.95))
ES = CONFIDENTIAL / 'estimation_sample_v2.csv'
if not (QUARTERLY_FILE.exists() and ES.exists()):
    print('Step 13 skipped: v2 estimation sample absent (NIC quarterly returns workbook not available).'); sys.exit(0)

class Threshold:
    """Pre-computes everything that depends only on (X, q, grid), so each outcome vector costs a few matrix products."""
    def __init__(self, d, Xo, q, lo=.15, hi=.85):
        self.d = d.reset_index(drop=True); self.Z = dummies(self.d)
        self.Xl = absorb(self.Z, self.d[Xo + [q]].to_numpy(float))            # linear model regressors (within)
        qv = self.d[q].to_numpy(float); a, b = np.quantile(qv, [lo, hi])
        grid = np.unique(qv[(qv >= a) & (qv <= b)])
        A = absorb(self.Z, qv[:, None] * (qv[:, None] <= grid[None, :]))       # q * 1(q <= gamma), within
        A = A - self.Xl @ np.linalg.lstsq(self.Xl, A, rcond=None)[0]           # ... net of the linear regressors
        aa = (A ** 2).sum(axis=0); ok = aa > 1e-8 * aa.max()
        self.A, self.aa, self.grid = A[:, ok], aa[ok], grid[ok]
        self.df = len(self.d) - np.linalg.matrix_rank(self.Z) - self.Xl.shape[1] - 1
        _, self.cl = np.unique(self.d.insurer_id.values, return_inverse=True); self.G = self.cl.max() + 1
    def resid_lin(self, Yw):
        return Yw - self.Xl @ np.linalg.lstsq(self.Xl, Yw, rcond=None)[0]
    def stat(self, Y):
        """Y: N x R outcomes (any scale; effects absorbed here). Returns F1, gamma_hat index, S1(grid) for each column."""
        E = self.resid_lin(absorb(self.Z, Y)); S0 = (E ** 2).sum(axis=0)
        drop = (self.A.T @ E) ** 2 / self.aa[:, None]                         # S0 - S1(gamma), grid x R
        k = drop.argmax(axis=0); S1 = S0 - drop[k, np.arange(Y.shape[1])]
        return (S0 - S1) / (S1 / self.df), k, S0[None, :] - drop
    def test(self, y, B=B_BOOT, seed=SEED):
        y = np.asarray(y, float)
        F, k, S1g = self.stat(y[:, None]); F, k, S1g = F[0], k[0], S1g[:, 0]
        yw = absorb(self.Z, y); e = self.resid_lin(yw); fit = yw - e             # null (linear) model, within scale
        rng = np.random.default_rng(seed); W = rng.choice([-1.0, 1.0], size=(self.G, B))
        Fb, _, _ = self.stat(fit[:, None] + e[:, None] * W[self.cl, :])         # effects re-absorbed inside stat
        s2 = S1g[k] / self.df; LR = (S1g - S1g[k]) / s2; inset = self.grid[LR <= C95]
        return dict(F1=float(F), p_boot=float(np.mean(Fb >= F)), gamma_hat=float(self.grid[k]),
                    ci_lo=float(inset.min()), ci_hi=float(inset.max()), grid_n=len(self.grid))

E = pd.read_csv(ES)
Xo, q = ['RET', 'ln_assets_L1', 'LEV_net_L1_w'], 'g_L1_w'
d = E.dropna(subset=['CR_w'] + Xo + [q]).reset_index(drop=True)
T = Threshold(d, Xo, q)
# simulation design from the real M1 fit on CR_w
r = fe(d, 'CR_w', Xo + [q]); beta = r.params[Xo + [q]].to_numpy()
ew = T.resid_lin(absorb(T.Z, d.CR_w.to_numpy(float))); sigma = float(np.sqrt((ew ** 2).sum() / (T.df + 1)))
qv = d[q].to_numpy(float); g0 = float(np.quantile(qv, .60)); Xmat = d[Xo + [q]].to_numpy(float)
ins = pd.factorize(d.insurer_id)[0]; yrs = pd.factorize(d.year)[0]
rng = np.random.default_rng(SEED)
rows = []
for dgp, delta in [('no threshold (size)', 0.0), ('threshold, delta = 0.25 (power)', 0.25), ('threshold, delta = 0.5 (power)', 0.5)]:
    res = []
    for s in range(N_SIM):
        a_i = rng.normal(0, 10, ins.max() + 1); l_t = rng.normal(0, 10, yrs.max() + 1)
        y = a_i[ins] + l_t[yrs] + Xmat @ beta + delta * qv * (qv > g0) + rng.normal(0, sigma, len(d))
        res.append(T.test(y, seed=SEED + 1 + s))
    R = pd.DataFrame(res)
    row = dict(dgp=dgp, delta=delta, gamma0=g0 if delta else np.nan, n_sims=N_SIM, B=B_BOOT, n=len(d),
               insurers=int(d.insurer_id.nunique()), grid_points=int(R.grid_n.iloc[0]), sigma=sigma,
               reject_5pct=float((R.p_boot < .05).mean()), reject_10pct=float((R.p_boot < .10).mean()),
               median_p=float(R.p_boot.median()), median_gamma_hat=float(R.gamma_hat.median()))
    if delta:
        row.update(median_abs_error_gamma=float((R.gamma_hat - g0).abs().median()),
                   ci_coverage=float(((R.ci_lo <= g0) & (R.ci_hi >= g0)).mean()), median_ci_width=float((R.ci_hi - R.ci_lo).median()))
    rows.append(row)
S = pd.DataFrame(rows); S.to_csv(TABLES / 'threshold_simulation.csv', index=False)
pd.set_option('display.width', 220)
print(f"Threshold simulation: N = {len(d)}, {d.insurer_id.nunique()} insurers, grid {T.grid.size} points "
      f"(q = {q}, 15th-85th percentile), sigma = {sigma:.2f}, gamma0 (60th pct) = {g0:.2f}")
print(S.round(3).to_string(index=False))
if RUN_REAL_DATA:
    out = []
    for y in ['LR_w', 'ER_w', 'CR_w']:
        dd = E.dropna(subset=[y] + Xo + [q]).reset_index(drop=True); Ty = Threshold(dd, Xo, q); t = Ty.test(dd[y].to_numpy())
        dd['q_low'] = dd[q] * (dd[q] <= t['gamma_hat']); dd['q_high'] = dd[q] * (dd[q] > t['gamma_hat'])
        rr = fe(dd, y, Xo + ['q_low', 'q_high'])
        out.append(dict(outcome=y, **t, slope_low=rr.params.q_low, se_low=rr.std_errors.q_low, slope_high=rr.params.q_high,
                        se_high=rr.std_errors.q_high, n=len(dd), insurers=int(dd.insurer_id.nunique())))
    pd.DataFrame(out).to_csv(TABLES / 'threshold_v2.csv', index=False); print(pd.DataFrame(out).round(4).to_string(index=False))
else:
    print('Real-data threshold estimation not run (RUN_REAL_DATA = False until the authors review the simulations).')
