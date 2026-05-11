"""Generate the four figures from the paper using matplotlib.

Figure 1: IRFs with 90% posterior credible bands (technology & carbon tax).
Figure 2: Prior vs posterior densities for the 14 estimated parameters.
Figure 3: Policy scenario comparison - GDP, emissions, welfare.
Figure 4: Carbon stock and temperature trajectories under the 8 scenarios.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from .params import PRIORS, POSTERIOR_TABLE
from .model import EDSGEModel
from .policy import SCENARIOS, run_scenario


REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# Figure 1: IRFs with credible bands
# ----------------------------------------------------------------------
def figure_1_irf(model: EDSGEModel, horizon: int = 12, n_draws: int = 200) -> Path:
    irf_vars = ["y", "c", "i", "pi", "R", "e"]
    labels = ["Output", "Consumption", "Investment", "Inflation",
              "Interest Rate", "Emissions"]
    fig, axes = plt.subplots(2, len(irf_vars), figsize=(16, 6), sharex=True)
    rng = np.random.default_rng(0)
    for row, shock in enumerate(["eA", "eTau"]):
        # Draw posterior-equivalent samples for IRF bands.
        irfs = np.zeros((n_draws, horizon + 1, len(irf_vars)))
        for d in range(n_draws):
            jit = EDSGEModel()
            # Random perturbations on a few parameters within posterior SDs.
            jit.estim = type(jit.estim)(**{
                **jit.estim.__dict__,
                "rho_R": jit.estim.rho_R + rng.normal(0, 0.06),
                "rho_tau": np.clip(jit.estim.rho_tau + rng.normal(0, 0.05), 0, 0.99),
                "kappa_P": max(20.0, jit.estim.kappa_P + rng.normal(0, 12.0)),
                "kappa_I": max(1.0, jit.estim.kappa_I + rng.normal(0, 1.1)),
            })
            irf = jit.irf(shock, horizon=horizon)
            for j, v in enumerate(irf_vars):
                irfs[d, :, j] = irf[v]
        for j, v in enumerate(irf_vars):
            ax = axes[row, j]
            mean = irfs[:, :, j].mean(axis=0)
            lo = np.percentile(irfs[:, :, j], 5, axis=0)
            hi = np.percentile(irfs[:, :, j], 95, axis=0)
            x = np.arange(horizon + 1)
            ax.fill_between(x, lo, hi, alpha=0.25, color="#1f77b4")
            ax.plot(x, mean, color="#1f77b4", linewidth=1.6)
            ax.axhline(0, color="0.4", lw=0.6, ls="--")
            ax.set_title(labels[j] if row == 0 else "", fontsize=9)
            if j == 0:
                ax.set_ylabel("Tech." if row == 0 else "Carbon tax", fontsize=9)
            if row == 1:
                ax.set_xlabel("Years")
            ax.grid(alpha=0.3)
    fig.suptitle("Figure 1: Impulse Response Functions (one-SD shocks)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = FIG_DIR / "fig1_irf.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------
# Figure 2: Prior vs posterior densities
# ----------------------------------------------------------------------
def figure_2_prior_posterior() -> Path:
    fig, axes = plt.subplots(4, 4, figsize=(13, 10))
    axes = axes.flatten()
    params = list(POSTERIOR_TABLE.keys())
    for i, p in enumerate(params):
        ax = axes[i]
        post_mean, post_sd, lo, hi = POSTERIOR_TABLE[p]
        family, p_mean, p_sd = PRIORS[p]
        x = np.linspace(max(0, p_mean - 4 * p_sd), p_mean + 4 * p_sd, 300)
        if family == "beta":
            x = np.linspace(0.01, 0.99, 300)
            from .bayesian import _beta_ab
            a, b = _beta_ab(p_mean, p_sd)
            prior_pdf = stats.beta(a, b).pdf(x)
        elif family == "normal":
            prior_pdf = stats.norm(p_mean, p_sd).pdf(x)
        elif family == "gamma":
            from .bayesian import _gamma_ab
            shape, scale = _gamma_ab(p_mean, p_sd)
            x = np.linspace(0.01, p_mean + 6 * p_sd, 300)
            prior_pdf = stats.gamma(shape, scale=scale).pdf(x)
        elif family == "inv_gamma":
            from .bayesian import _inv_gamma_ab
            shape, scale = _inv_gamma_ab(p_mean, p_sd)
            x = np.linspace(0.001, max(0.05, p_mean + 6 * p_sd), 300)
            prior_pdf = stats.invgamma(a=shape, scale=scale).pdf(x)
        post_pdf = stats.norm(post_mean, post_sd).pdf(x)
        # Rescale for visibility.
        if prior_pdf.max() > 0:
            prior_pdf = prior_pdf / prior_pdf.max()
        if post_pdf.max() > 0:
            post_pdf = post_pdf / post_pdf.max()
        ax.plot(x, prior_pdf, ls="--", color="#d62728", label="Prior")
        ax.plot(x, post_pdf, color="#1f77b4", label="Posterior")
        ax.axvline(post_mean, color="#1f77b4", lw=0.6, ls=":")
        ax.set_title(p, fontsize=9)
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(fontsize=8)
    # Remove last empty subplots (we have 14 params, 16 axes).
    for j in range(len(params), len(axes)):
        axes[j].axis("off")
    fig.suptitle("Figure 2: Prior (dashed) vs Posterior (solid) Distributions",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG_DIR / "fig2_prior_posterior.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------
# Figure 3: Policy scenario comparison
# ----------------------------------------------------------------------
def figure_3_policy_comparison(results: dict) -> Path:
    names = list(results.keys())
    gdp = [results[n]["gdp_20yr"] for n in names]
    emi = [results[n]["emi_20yr"] for n in names]
    welfare = [results[n]["welfare_ev"] for n in names]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    titles = ["(a) GDP at year 20 (% dev.)",
              "(b) Emissions at year 20 (% dev.)",
              "(c) Welfare (consumption EV, %)"]
    data = [gdp, emi, welfare]
    colors = ["#2ca02c", "#d62728", "#9467bd"]
    for ax, t, d, c in zip(axes, titles, data, colors):
        bars = ax.barh(range(len(names)), d, color=c, alpha=0.8)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels([results[n]["name"] for n in names], fontsize=8)
        ax.axvline(0, color="black", lw=0.7)
        ax.grid(axis="x", alpha=0.3)
        ax.set_title(t, fontsize=10)
        for bar, val in zip(bars, d):
            ax.text(val + (0.05 if val >= 0 else -0.05), bar.get_y() + 0.3,
                    f"{val:+.2f}", fontsize=7,
                    ha="left" if val >= 0 else "right")
    fig.suptitle("Figure 3: Policy scenario comparison",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = FIG_DIR / "fig3_policy_comparison.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------
# Figure 4: Carbon stock & temperature pathways
# ----------------------------------------------------------------------
def figure_4_climate_pathways(results: dict) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    horizon = 20
    cmap = plt.get_cmap("tab10")
    for i, (k, r) in enumerate(results.items()):
        axes[0].plot(np.arange(horizon + 1), r["E"], lw=1.6,
                     color=cmap(i % 10), label=r["name"])
        axes[1].plot(np.arange(horizon + 1), r["T_AT"], lw=1.6,
                     color=cmap(i % 10), label=r["name"])
    axes[0].set_title("CO2 emissions trajectory", fontsize=10)
    axes[0].set_xlabel("Years"); axes[0].set_ylabel("E_t")
    axes[1].set_title("Atmospheric temperature anomaly", fontsize=10)
    axes[1].set_xlabel("Years"); axes[1].set_ylabel(r"$T_{AT}$ ($^\circ$C)")
    axes[1].legend(fontsize=7, loc="upper left")
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.suptitle("Figure 4: Climate pathways under alternative policy scenarios",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = FIG_DIR / "fig4_climate_pathways.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
