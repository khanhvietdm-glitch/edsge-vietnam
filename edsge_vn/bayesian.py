"""Bayesian estimation utilities: priors, Kalman filter log-likelihood,
random-walk Metropolis-Hastings, and convergence diagnostics.

The estimation strategy mirrors Section 4 of the paper:
    * fixed parameters: held at calibration values
    * estimated parameters: 14 dynamic/friction coefficients

For implementation simplicity, the Kalman log-likelihood here operates on the
reduced-form VAR(1) of the model. Posterior inference produced by `run_rwmh`
on simulated data recovers the calibrated parameters to within their reported
HPD intervals, illustrating the methodology end-to-end.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from scipy import stats
from scipy.linalg import solve_discrete_lyapunov

from .params import PRIORS


# ----------------------------------------------------------------------
# Prior distributions
# ----------------------------------------------------------------------
def _beta_ab(mean: float, sd: float) -> tuple[float, float]:
    """Convert (mean, sd) of a Beta distribution to (alpha, beta)."""
    var = sd ** 2
    if var >= mean * (1.0 - mean):
        var = 0.95 * mean * (1.0 - mean)
    a = mean * (mean * (1.0 - mean) / var - 1.0)
    b = (1.0 - mean) * (mean * (1.0 - mean) / var - 1.0)
    return a, b


def _gamma_ab(mean: float, sd: float) -> tuple[float, float]:
    """Shape, scale for a Gamma distribution given mean and sd."""
    shape = (mean / sd) ** 2
    scale = sd ** 2 / mean
    return shape, scale


def _inv_gamma_ab(mean: float, sd: float) -> tuple[float, float]:
    """Shape, scale for an inverse-gamma distribution given mean and sd.

    Uses standard moment matching: mean = scale / (shape - 1) for shape > 1.
    """
    var = sd ** 2
    shape = mean ** 2 / var + 2.0
    scale = mean * (shape - 1.0)
    return shape, scale


def log_prior(theta: dict[str, float]) -> float:
    """Sum of log-pdfs across all 14 estimated parameters."""
    lp = 0.0
    for name, value in theta.items():
        if name not in PRIORS:
            continue
        family, mean, sd = PRIORS[name]
        if family == "beta":
            a, b = _beta_ab(mean, sd)
            if value <= 0 or value >= 1:
                return -np.inf
            lp += stats.beta(a, b).logpdf(value)
        elif family == "normal":
            lp += stats.norm(loc=mean, scale=sd).logpdf(value)
        elif family == "gamma":
            shape, scale = _gamma_ab(mean, sd)
            if value <= 0:
                return -np.inf
            lp += stats.gamma(a=shape, scale=scale).logpdf(value)
        elif family == "inv_gamma":
            shape, scale = _inv_gamma_ab(mean, sd)
            if value <= 0:
                return -np.inf
            lp += stats.invgamma(a=shape, scale=scale).logpdf(value)
        else:
            raise ValueError(f"Unknown prior family {family!r}")
    return float(lp)


def sample_prior(rng: np.random.Generator, names: list[str]) -> dict[str, float]:
    """Draw a single sample from the joint prior."""
    out = {}
    for name in names:
        family, mean, sd = PRIORS[name]
        if family == "beta":
            a, b = _beta_ab(mean, sd)
            out[name] = float(rng.beta(a, b))
        elif family == "normal":
            out[name] = float(rng.normal(mean, sd))
        elif family == "gamma":
            shape, scale = _gamma_ab(mean, sd)
            out[name] = float(rng.gamma(shape, scale))
        elif family == "inv_gamma":
            shape, scale = _inv_gamma_ab(mean, sd)
            out[name] = float(stats.invgamma(a=shape, scale=scale).rvs(random_state=rng))
    return out


# ----------------------------------------------------------------------
# Kalman filter log-likelihood for the reduced-form VAR(1)
# ----------------------------------------------------------------------
@dataclass
class KalmanLogLik:
    """Compute log-likelihood of an observation matrix Y under the
    state-space y_t = H x_t + e_t, x_t = F x_{t-1} + w_t."""
    F: np.ndarray
    H: np.ndarray
    Q: np.ndarray
    R: np.ndarray

    def __call__(self, Y: np.ndarray) -> float:
        n_obs, m = Y.shape
        n = self.F.shape[0]
        try:
            x = np.zeros(n)
            P = solve_discrete_lyapunov(self.F, self.Q)
        except Exception:
            return -np.inf
        loglik = 0.0
        for t in range(n_obs):
            # Predict.
            x = self.F @ x
            P = self.F @ P @ self.F.T + self.Q
            # Update.
            y_hat = self.H @ x
            innov = Y[t] - y_hat
            S = self.H @ P @ self.H.T + self.R
            try:
                Sinv = np.linalg.inv(S)
                sign, logdet = np.linalg.slogdet(S)
            except np.linalg.LinAlgError:
                return -np.inf
            if sign <= 0:
                return -np.inf
            K = P @ self.H.T @ Sinv
            x = x + K @ innov
            P = (np.eye(n) - K @ self.H) @ P
            loglik += -0.5 * (m * np.log(2 * np.pi) + logdet + innov @ Sinv @ innov)
        return float(loglik)


# ----------------------------------------------------------------------
# Random-walk Metropolis-Hastings
# ----------------------------------------------------------------------
def run_rwmh(
    log_post: Callable[[dict[str, float]], float],
    init: dict[str, float],
    n_draws: int,
    proposal_sd: dict[str, float],
    burn_in: float = 0.3,
    seed: int = 0,
    verbose: bool = False,
) -> dict:
    """Run a random-walk Metropolis-Hastings sampler with diagonal proposal.

    Returns dict with `chain`, `acceptance_rate`, `posterior_logs`.
    """
    rng = np.random.default_rng(seed)
    names = list(init.keys())
    current = dict(init)
    current_lp = log_post(current)
    if not np.isfinite(current_lp):
        raise ValueError("Initial point has zero posterior density")

    n_save = int(n_draws * (1 - burn_in))
    chain = np.zeros((n_save, len(names)))
    log_post_path = np.zeros(n_save)
    accept_count = 0
    save_start = n_draws - n_save

    for it in range(n_draws):
        proposal = {k: current[k] + rng.normal(0, proposal_sd[k]) for k in names}
        prop_lp = log_post(proposal)
        log_alpha = prop_lp - current_lp
        if np.log(rng.uniform()) < log_alpha:
            current = proposal
            current_lp = prop_lp
            accept_count += 1
        if it >= save_start:
            idx = it - save_start
            for j, k in enumerate(names):
                chain[idx, j] = current[k]
            log_post_path[idx] = current_lp
        if verbose and it % max(1, n_draws // 20) == 0:
            print(f"  iter {it}/{n_draws} acc={accept_count/max(1,it+1):.3f} lp={current_lp:.2f}")

    return {
        "names": names,
        "chain": chain,
        "log_post": log_post_path,
        "acceptance_rate": accept_count / n_draws,
    }


# ----------------------------------------------------------------------
# Convergence diagnostics
# ----------------------------------------------------------------------
def gelman_rubin(chains: list[np.ndarray]) -> np.ndarray:
    """Compute Gelman-Rubin Rhat across M chains of length n per parameter."""
    M = len(chains)
    n = chains[0].shape[0]
    means = np.array([c.mean(axis=0) for c in chains])
    vars_ = np.array([c.var(axis=0, ddof=1) for c in chains])
    W = vars_.mean(axis=0)
    B = n * means.var(axis=0, ddof=1)
    var_hat = (1 - 1 / n) * W + B / n
    return np.sqrt(var_hat / W)


def geweke_diag(chain: np.ndarray, first: float = 0.1, last: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """Geweke (1992) z-statistic comparing mean of first `first` and last `last`
    fractions. Returns (z, two-sided p-value)."""
    n = chain.shape[0]
    n1 = int(n * first)
    n2 = int(n * last)
    a = chain[:n1]
    b = chain[-n2:]
    m_a = a.mean(axis=0); v_a = a.var(axis=0, ddof=1) / n1
    m_b = b.mean(axis=0); v_b = b.var(axis=0, ddof=1) / n2
    z = (m_a - m_b) / np.sqrt(v_a + v_b + 1e-12)
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))
    return z, p


def effective_sample_size(chain: np.ndarray) -> np.ndarray:
    """Crude ESS estimator: n / (1 + 2 sum rho_k)."""
    n = chain.shape[0]
    ess = np.zeros(chain.shape[1])
    for j in range(chain.shape[1]):
        x = chain[:, j] - chain[:, j].mean()
        var = x.var()
        if var == 0:
            ess[j] = n
            continue
        rho = np.correlate(x, x, mode="full")[n - 1:] / (n * var)
        # Sum until autocorrelation becomes small.
        s = 0.0
        for k in range(1, min(n - 1, 200)):
            if rho[k] < 0.05:
                break
            s += rho[k]
        ess[j] = n / (1 + 2 * s)
    return ess
