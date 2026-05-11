"""Demonstrate the full Bayesian estimation pipeline on simulated data.

We run a short RWMH chain (4 chains x 10 000 draws by default) on a state-
space model identified to a subset of the 14 estimated parameters. The aim
is illustrative: the same code can scale to the paper's 4 x 500 000 by
adjusting `N_DRAWS`.

Usage:
    python scripts/run_bayesian_demo.py
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from edsge_vn import EDSGEModel
from edsge_vn.bayesian import (
    KalmanLogLik, run_rwmh, log_prior, sample_prior,
    gelman_rubin, geweke_diag, effective_sample_size,
)
from edsge_vn.synthetic_data import simulate_estimation_sample


N_CHAINS = 4
N_DRAWS = 4000  # set to 500_000 to mirror the paper exactly


def build_loglik(observed: np.ndarray):
    """Return a closure mapping a parameter dict to log-likelihood."""

    def loglik(theta):
        model = EDSGEModel()
        # Overwrite the posterior dataclass.
        model.estim = type(model.estim)(**{**model.estim.__dict__, **{
            k: v for k, v in theta.items() if hasattr(model.estim, k)
        }})
        ss = model.linear_state_space()
        F = ss["Pi"]
        names = ss["names"]
        sigmas = ss["sigmas"]
        Qmat = ss["Q"]
        # State innovation covariance.
        Sigma_eps = np.diag(sigmas ** 2)
        Q_state = Qmat @ Sigma_eps @ Qmat.T + 1e-10 * np.eye(F.shape[0])
        # Measurement: H selects observable rows.
        H_idx = [names.index(n) for n in ["y", "c", "i", "pi", "R", "e"]]
        H = np.zeros((len(H_idx), F.shape[0]))
        for r, idx in enumerate(H_idx):
            H[r, idx] = 1.0
        R_meas = np.diag([5e-4] * len(H_idx))
        try:
            kf = KalmanLogLik(F=F, H=H, Q=Q_state, R=R_meas)
            return kf(observed)
        except Exception:
            return -np.inf

    return loglik


def main():
    print("Building observed sample (Table A1 calibrated synthetic series)...")
    df = simulate_estimation_sample()
    observed = df.values

    print(f"Sample T={len(df)} years, columns={list(df.columns)}")

    loglik = build_loglik(observed)
    estimated_names = ["rho_R", "phi_pi", "phi_y", "kappa_P", "kappa_I",
                       "rho_A", "rho_G", "rho_tau", "rho_E",
                       "sigma_A", "sigma_R", "sigma_G", "sigma_tau", "sigma_E"]

    def log_post(theta):
        lp = log_prior(theta)
        if not np.isfinite(lp):
            return -np.inf
        ll = loglik(theta)
        if not np.isfinite(ll):
            return -np.inf
        return lp + ll

    # Scale proposal SDs to ~1/3 of posterior SD; tuned to give ~25% acceptance.
    proposal_sd = {
        "rho_R":   0.012, "phi_pi": 0.045, "phi_y":   0.020,
        "kappa_P": 2.20,  "kappa_I": 0.18,
        "rho_A":   0.012, "rho_G":   0.018, "rho_tau": 0.012, "rho_E": 0.018,
        "sigma_A": 0.0004, "sigma_R": 0.0003, "sigma_G": 0.0007,
        "sigma_tau": 0.0007, "sigma_E": 0.0008,
    }

    chains = []
    accept_rates = []
    for ch in range(N_CHAINS):
        rng = np.random.default_rng(100 + ch)
        # Initialize at posterior mean perturbed by ~prior SD.
        from edsge_vn.params import POSTERIOR_TABLE
        init = {p: POSTERIOR_TABLE[p][0] + rng.normal(0, POSTERIOR_TABLE[p][1])
                for p in estimated_names}
        # Project to feasible support.
        for k, v in list(init.items()):
            if k.startswith("rho_"):
                init[k] = float(np.clip(v, 0.05, 0.97))
            elif k.startswith("sigma_") or k.startswith("kappa_"):
                init[k] = float(max(v, 0.001))
        print(f"\nChain {ch + 1}/{N_CHAINS}: running {N_DRAWS} draws...")
        t0 = time.time()
        out = run_rwmh(log_post, init, N_DRAWS, proposal_sd,
                       burn_in=0.3, seed=ch, verbose=False)
        print(f"  acceptance {out['acceptance_rate']:.3f}  "
              f"elapsed {time.time() - t0:.1f}s")
        chains.append(out["chain"])
        accept_rates.append(out["acceptance_rate"])

    # Diagnostics across chains.
    Rhat = gelman_rubin(chains)
    z_g, p_g = geweke_diag(np.vstack(chains))
    ess = effective_sample_size(np.vstack(chains))
    diag = pd.DataFrame({
        "Rhat": np.round(Rhat, 3),
        "Geweke z": np.round(z_g, 3),
        "Geweke p": np.round(p_g, 3),
        "ESS": np.round(ess, 0),
    }, index=estimated_names)
    print("\nConvergence summary (demo chains):")
    print(diag.to_string())
    out_dir = ROOT / "results"
    diag.to_csv(out_dir / "bayesian_demo_diagnostics.csv", encoding="utf-8-sig")

    # Posterior means.
    stacked = np.vstack(chains)
    post_mean = pd.Series(stacked.mean(axis=0), index=estimated_names, name="post_mean")
    post_sd = pd.Series(stacked.std(axis=0, ddof=1), index=estimated_names, name="post_sd")
    pd.concat([post_mean, post_sd], axis=1).round(4).to_csv(
        out_dir / "bayesian_demo_posterior.csv", encoding="utf-8-sig")
    print(f"\nMean acceptance: {np.mean(accept_rates):.3f}")
    print("Posterior saved to results/bayesian_demo_posterior.csv")


if __name__ == "__main__":
    main()
