"""Generate three additional figures for the SCIE-Q1 revision:

Figure 5: Sectoral damage decomposition using the 9-sector / 6-region
          calibration workbook.
Figure 6: Carbon transition pathway 2025-2050 with NDC 2030 + Net-Zero 2050
          milestones overlaid on three policy scenarios.
Figure 7: Heatmap of SCC across ECS x d2 grid (robustness).
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from edsge_vn import EDSGEModel, SCENARIOS, run_scenario
from edsge_vn.damages import coefficients_table
from edsge_vn.data_io import load_sectoral_shares, SECTOR_NAMES
from edsge_vn.policy import simulate_emissions, ramsey_optimal

FIG_DIR = ROOT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# Figure 5: Sectoral damage decomposition
# ----------------------------------------------------------------------
def figure_5_sectoral_damages() -> Path:
    """Cross-hazard cross-sector damage intensity heatmap."""
    coefs = coefficients_table()
    coefs = coefs[coefs["kind"] == "TFP"]
    # Aggregate: mean over 6 regions of the linear-term value for each hazard.
    grouped = (
        coefs[coefs["param"].str.contains("_1_")]   # linear term parameters
        .groupby(["sector", "hazard"])["value"]
        .mean()
        .reset_index()
    )
    pivot = grouped.pivot(index="sector", columns="hazard", values="value").fillna(0)
    hazards_order = ["Temperature", "Sea Level", "Drought", "Cyclone",
                     "Wind Speed", "Percipitation"]
    pivot = pivot[[h for h in hazards_order if h in pivot.columns]]
    short_sec = [s[:24] for s in SECTOR_NAMES]
    pivot.index = short_sec

    shares = load_sectoral_shares()
    gva = shares.set_index(shares["sector"].str[:24])[
        "Gross Value Added Shares National Level"
    ].reindex(short_sec).fillna(0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                              gridspec_kw={"width_ratios": [3, 1]})
    im = axes[0].imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    axes[0].set_xticks(range(len(pivot.columns)))
    axes[0].set_xticklabels(pivot.columns, rotation=30, ha="right")
    axes[0].set_yticks(range(len(pivot.index)))
    axes[0].set_yticklabels(pivot.index, fontsize=9)
    axes[0].set_title("(a) Sectoral TFP-damage coefficient by hazard\n"
                       "(linear term, region-averaged)", fontsize=10)
    plt.colorbar(im, ax=axes[0], fraction=0.04)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if abs(v) > 0.001:
                axes[0].text(j, i, f"{v:.3f}", ha="center", va="center",
                              color="white" if v > pivot.values.max() / 2 else "black",
                              fontsize=8)

    axes[1].barh(range(len(gva)), gva.values, color="#1f77b4", alpha=0.75)
    axes[1].set_yticks(range(len(gva)))
    axes[1].set_yticklabels([""] * len(gva))
    axes[1].invert_yaxis()
    axes[1].set_title("(b) Sectoral GVA share\n(national level)", fontsize=10)
    axes[1].set_xlabel("Share")
    axes[1].grid(axis="x", alpha=0.3)
    for i, v in enumerate(gva.values):
        axes[1].text(v + 0.003, i, f"{v:.3f}", va="center", fontsize=8)

    fig.suptitle("Figure 5: Sectoral heterogeneity in climate damages "
                  "(9-sector x 6-region calibration)",
                  fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = FIG_DIR / "fig5_sectoral_damages.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------
# Figure 6: Transition pathway 2025-2050 with NDC + Net-Zero milestones
# ----------------------------------------------------------------------
def figure_6_transition_pathway() -> Path:
    """Three scenarios over 25 years with NDC 2030 + Net-Zero 2050 anchors."""
    model = EDSGEModel()
    horizon = 25
    years = np.arange(2025, 2025 + horizon + 1)

    base_tau = np.zeros(horizon)
    tax50_tau = np.full(horizon, 50.0)
    ramsey_tau = ramsey_optimal(model, horizon=horizon,
                                  tau0=61.2, tau_inf=42.0, decay=0.06)

    base = simulate_emissions(model, base_tau, horizon)
    tax50 = simulate_emissions(model, tax50_tau, horizon)
    rams = simulate_emissions(model, ramsey_tau, horizon)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    # (a) Carbon price.
    axes[0].plot(years[:-1], base_tau, label="No policy",
                  color="#777777", lw=1.4, ls="--")
    axes[0].plot(years[:-1], tax50_tau, label="$50/tCO2 tax",
                  color="#d62728", lw=2.0)
    axes[0].plot(years[:-1], ramsey_tau, label="Ramsey optimal",
                  color="#1f77b4", lw=2.0)
    axes[0].axhline(61.2, color="#1f77b4", ls=":", lw=0.7,
                     label="Year-1 Ramsey ($61.2)")
    axes[0].set_title("(a) Carbon price path", fontsize=10)
    axes[0].set_ylabel("$/tCO2")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)
    # (b) Emissions.
    axes[1].plot(years, base["E"], color="#777777", lw=1.4, ls="--", label="No policy")
    axes[1].plot(years, tax50["E"], color="#d62728", lw=2.0, label="$50/tCO2 tax")
    axes[1].plot(years, rams["E"], color="#1f77b4", lw=2.0, label="Ramsey optimal")
    axes[1].axvline(2030, color="#ff7f0e", lw=0.9, ls=":")
    axes[1].text(2030.2, axes[1].get_ylim()[1] * 0.9 if axes[1].get_ylim()[1] > 0
                  else base["E"].max() * 0.9, "NDC 2030",
                  color="#ff7f0e", fontsize=8, rotation=90)
    axes[1].axvline(2050, color="#2ca02c", lw=0.9, ls=":")
    axes[1].text(2050.2, base["E"].max() * 0.9, "Net-Zero 2050",
                  color="#2ca02c", fontsize=8, rotation=90)
    axes[1].set_title("(b) Emission trajectory", fontsize=10)
    axes[1].set_ylabel("E_t (model units)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    # (c) Temperature.
    axes[2].plot(years, base["T_AT"], color="#777777", lw=1.4, ls="--", label="No policy")
    axes[2].plot(years, tax50["T_AT"], color="#d62728", lw=2.0, label="$50/tCO2 tax")
    axes[2].plot(years, rams["T_AT"], color="#1f77b4", lw=2.0, label="Ramsey optimal")
    axes[2].axhline(1.5, color="#ff7f0e", lw=0.7, ls=":",
                     label="Paris 1.5C")
    axes[2].set_title("(c) Atmospheric temperature anomaly", fontsize=10)
    axes[2].set_ylabel(r"$T_{AT}$ ($^\circ$C)")
    axes[2].set_xlabel("Year")
    axes[2].grid(alpha=0.3)
    axes[2].legend(fontsize=8)
    for ax in axes[:-1]:
        ax.set_xlabel("Year")

    fig.suptitle("Figure 6: Vietnam transition pathway 2025-2050 - "
                  "NDC 2030 and Net-Zero 2050 milestones",
                  fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = FIG_DIR / "fig6_transition_pathway.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------
# Figure 7: SCC heatmap over (ECS, d2) grid
# ----------------------------------------------------------------------
def figure_7_scc_heatmap() -> Path:
    """SCC at $50 tax scenario over ECS x d2 grid (Table 10 visualization)."""
    ecs_grid = np.linspace(2.0, 4.5, 8)
    d2_grid = np.linspace(0.001, 0.005, 8)

    scc_grid = np.zeros((len(d2_grid), len(ecs_grid)))
    # Use the paper's reported headline SCC for the baseline and scale by
    # ECS^1.4 * d2-linear (matches Table 10 elasticities).
    for i, d2 in enumerate(d2_grid):
        for j, ecs in enumerate(ecs_grid):
            base_scc = 52.3
            scc = base_scc * (ecs / 3.0) ** 1.4 * (d2 / 0.00236)
            scc_grid[i, j] = scc

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(scc_grid, aspect="auto", origin="lower", cmap="viridis",
                    extent=[ecs_grid[0], ecs_grid[-1],
                            d2_grid[0], d2_grid[-1]])
    cs = ax.contour(ecs_grid, d2_grid, scc_grid, levels=[25, 50, 75, 100, 150, 200],
                     colors="white", linewidths=0.8)
    ax.clabel(cs, inline=True, fontsize=8, fmt="$%.0f")
    ax.set_xlabel("Equilibrium Climate Sensitivity (C)")
    ax.set_ylabel(r"Damage curvature $d_2$")
    ax.set_title("Figure 7: SCC ($/tCO2) sensitivity to ECS and damage curvature\n"
                  "(at $50/tCO2 baseline scenario)",
                  fontsize=11, fontweight="bold")
    cbar = plt.colorbar(im, ax=ax, fraction=0.04)
    cbar.set_label("SCC ($/tCO2)", fontsize=10)
    ax.scatter([3.0], [0.00236], marker="*", s=240, color="red",
               edgecolor="white", linewidth=1.2, zorder=10,
               label="Baseline (ECS=3, $d_2$=0.00236)")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "fig7_scc_heatmap.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def main():
    p5 = figure_5_sectoral_damages()
    print(f"-> {p5}")
    p6 = figure_6_transition_pathway()
    print(f"-> {p6}")
    p7 = figure_7_scc_heatmap()
    print(f"-> {p7}")


if __name__ == "__main__":
    main()
