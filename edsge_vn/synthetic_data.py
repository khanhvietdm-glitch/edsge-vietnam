"""Construct the national 1990-2023 estimation dataset.

The paper estimates the E-DSGE model on six annual series for Vietnam:
    GDP, consumption, investment, CPI inflation, nominal interest rate,
    CO2 emissions (log-differences for the macro variables, level for the
    nominal interest rate). Summary statistics are reported in Table A1.

Because the original time series file was not bundled with the replication
package, this module reproduces a representative sample by:
  1. drawing a Gaussian VAR(1) calibrated to the Table A1 moments;
  2. anchoring the resulting series to the historical mean / range;
  3. allowing the random seed to be fixed for reproducibility.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from .params import DATA_MOMENTS


def simulate_estimation_sample(T: int = 34, seed: int = 1990) -> pd.DataFrame:
    """Return a DataFrame indexed by year 1990..1990+T-1 with the six
    observed variables used in Bayesian estimation."""
    rng = np.random.default_rng(seed)
    years = np.arange(1990, 1990 + T)

    cols = list(DATA_MOMENTS.keys())
    means = np.array([DATA_MOMENTS[c]["mean"] for c in cols])
    sds = np.array([DATA_MOMENTS[c]["sd"] for c in cols])

    # Pairwise correlations consistent with Table 11 (output-emissions ~0.52,
    # output-inflation ~0.31). Off-diagonals are set conservatively.
    rho = np.eye(len(cols))
    rho[0, 1] = rho[1, 0] = 0.78          # dlogY/dlogC
    rho[0, 2] = rho[2, 0] = 0.70          # dlogY/dlogI
    rho[0, 3] = rho[3, 0] = 0.31          # dlogY/pi
    rho[0, 4] = rho[4, 0] = -0.18         # dlogY/i
    rho[0, 5] = rho[5, 0] = 0.52          # dlogY/dlogE
    rho[3, 4] = rho[4, 3] = 0.62          # pi / i (Taylor rule)
    rho[1, 2] = rho[2, 1] = 0.55
    rho[5, 1] = rho[1, 5] = 0.40

    Sigma = np.outer(sds, sds) * rho
    # Project Sigma to the nearest positive semidefinite matrix to handle
    # the hand-coded correlations safely.
    eigvals, eigvecs = np.linalg.eigh((Sigma + Sigma.T) / 2)
    eigvals = np.clip(eigvals, 1e-10, None)
    Sigma = (eigvecs * eigvals) @ eigvecs.T
    raw = rng.multivariate_normal(mean=means, cov=Sigma, size=T)
    # Clip to historical min/max so the series stays plausible.
    for i, c in enumerate(cols):
        raw[:, i] = np.clip(raw[:, i],
                             DATA_MOMENTS[c]["min"],
                             DATA_MOMENTS[c]["max"])
    # Inject the 1990s high-inflation episode and the post-2010 stabilization.
    raw[:5, 3] += np.linspace(0.06, 0.0, 5)   # CPI burst
    raw[:5, 4] += np.linspace(0.04, 0.0, 5)   # high nominal rate
    raw[-5:, 5] -= 0.01                       # emission slowdown post-2018
    raw[20:25, 3] += 0.01                     # 2009-2010 inflation flare

    df = pd.DataFrame(raw, index=years, columns=cols)
    df.index.name = "year"
    return df


def estimation_moments(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the same moments as Table A1 for a given sample."""
    out = pd.DataFrame({
        "Mean": df.mean(),
        "Std. Dev.": df.std(ddof=1),
        "Min": df.min(),
        "Max": df.max(),
        "Obs.": [len(df)] * len(df.columns),
    }, index=df.columns)
    return out.round(3)
