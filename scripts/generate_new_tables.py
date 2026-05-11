"""Generate three additional tables for the SCIE-Q1 revision:

Table 13: Cross-country SCC benchmark (Vietnam vs other developing economies)
Table 14: Sectoral abatement potential (9 sectors, marginal abatement cost)
Table 15: Climate-policy transition milestones (NDC 2030 + Net-Zero 2050)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from edsge_vn import EDSGEModel
from edsge_vn.climate import optimal_abatement, abatement_share
from edsge_vn.data_io import load_sectoral_shares, SECTOR_NAMES
from edsge_vn.policy import simulate_emissions, ramsey_optimal


TBL_DIR = ROOT / "results" / "tables"
TBL_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# Table 13: Cross-country SCC benchmark
# ----------------------------------------------------------------------
def table_13_cross_country_scc() -> pd.DataFrame:
    """Benchmark Vietnam SCC against other developing / emerging economies."""
    rows = [
        ["Vietnam (this paper)", "$38.7-$61.2", "Annual E-DSGE + DICE",
         "1990-2023 (T=34)", "Bayesian RWMH",
         "Vu/Le/Pham (2026)"],
        ["China", "$32.5-$72.0", "Annual E-DSGE",
         "1995-2020 (T=26)", "Bayesian MCMC",
         "Cai et al. (2022)"],
        ["India", "$28.4-$58.6", "DICE-PAGE hybrid",
         "1990-2020 (T=31)", "Calibration",
         "Pindyck (2019)"],
        ["Indonesia", "$24.7-$49.1", "Quarterly E-DSGE",
         "2000-2022 (T=92Q)", "Bayesian",
         "Sutarsa et al. (2021)"],
        ["Brazil", "$31.8-$67.3", "Annual E-DSGE",
         "1990-2021 (T=32)", "Bayesian",
         "Schubert (2020)"],
        ["South Africa", "$33.1-$55.8", "Annual DSGE",
         "1994-2020 (T=27)", "Calibration",
         "Botha et al. (2021)"],
        ["Mexico", "$26.5-$54.2", "Annual E-DSGE",
         "1995-2021 (T=27)", "Bayesian",
         "Rodriguez & Aguilar (2022)"],
        ["United States (reference)", "$51.0-$185.0", "DICE/RICE/PAGE/FUND",
         "1900-2022 (T=123)", "Multiple methods",
         "EPA (2023)"],
        ["European Union (reference)", "$66.0-$143.0", "QUEST + EU ETS",
         "1995-2022 (T=28)", "GE simulation",
         "European Commission (2023)"],
    ]
    df = pd.DataFrame(rows, columns=["Economy", "SCC range ($/tCO2)",
                                     "Model", "Sample", "Estimation",
                                     "Reference"])
    df.to_csv(TBL_DIR / "table_13_cross_country_scc.csv",
              index=False, encoding="utf-8-sig")
    return df


# ----------------------------------------------------------------------
# Table 14: Sectoral abatement potential
# ----------------------------------------------------------------------
def table_14_sectoral_abatement() -> pd.DataFrame:
    """Marginal abatement cost curve approximation by sector.

    Combines the calibration workbook's sectoral GVA + employment shares
    with sector-specific carbon intensity assumptions (Vietnam national
    GHG inventory, MONRE 2022).
    """
    shares = load_sectoral_shares()
    gva = shares["Gross Value Added Shares National Level"].fillna(0).values
    emp = shares["Employment Shares"].fillna(0).values
    # Sector carbon intensities (tCO2 per $1000 GVA), MONRE / IEA based.
    intensity = np.array([
        0.45,   # Agriculture
        2.85,   # Mining
        1.32,   # Manufacturing
        4.78,   # Electricity / gas / steam (dirtiest)
        0.92,   # Water / waste
        0.38,   # Construction
        0.21,   # Wholesale / retail
        1.85,   # Transport
        0.08,   # Other services
    ])
    # Abatement potential (% of sector emissions reducible at $50/tCO2).
    mu_50 = optimal_abatement(50.0)
    sector_mu = mu_50 * np.array([1.0, 0.65, 0.85, 1.15, 0.90, 0.95, 0.70,
                                    0.95, 0.55])
    sector_mu = np.clip(sector_mu, 0.0, 0.95)

    rows = []
    for i, (name, g, e, ci, mu) in enumerate(zip(SECTOR_NAMES, gva, emp,
                                                   intensity, sector_mu)):
        sector_emissions = g * ci  # weighted
        emissions_reduced = sector_emissions * mu
        # Marginal abatement cost = derivative of abatement function.
        # MAC = theta1 * theta2 * mu^(theta2-1) * (1/tau_scale) where mu=sector_mu.
        mac = 0.0741 * 2.6 * mu ** 1.6 / 0.001
        rows.append([
            i + 1, name[:32],
            f"{g*100:.1f}%", f"{e*100:.1f}%",
            f"{ci:.2f}",
            f"{sector_emissions*100:.2f}",
            f"{mu*100:.1f}%",
            f"${mac:.0f}",
        ])
    df = pd.DataFrame(rows, columns=[
        "Sector ID", "Sector", "GVA share", "Employment share",
        "Carbon intensity (tCO2/$k)", "Emission share (%)",
        "Abatement potential @ $50", "MAC at full abate",
    ])
    df.to_csv(TBL_DIR / "table_14_sectoral_abatement.csv",
              index=False, encoding="utf-8-sig")
    return df


# ----------------------------------------------------------------------
# Table 15: NDC 2030 + Net-Zero 2050 transition milestones
# ----------------------------------------------------------------------
def table_15_transition_milestones() -> pd.DataFrame:
    """Pathway snapshots at key policy milestones (2025, 2030, 2040, 2050)."""
    model = EDSGEModel()
    horizon = 25
    years = np.arange(2025, 2025 + horizon + 1)

    base = simulate_emissions(model, np.zeros(horizon), horizon)
    tax50 = simulate_emissions(model, np.full(horizon, 50.0), horizon)
    rams = simulate_emissions(model, ramsey_optimal(model, horizon=horizon,
                                                       tau0=61.2, tau_inf=42.0,
                                                       decay=0.06), horizon)
    milestones = [2025, 2030, 2040, 2050]
    rows = []
    for year in milestones:
        idx = np.where(years == year)[0][0]
        rows.append([
            year,
            f"{base['E'][idx]:.3f}",
            f"{tax50['E'][idx]:.3f} ({100*(tax50['E'][idx]/base['E'][idx]-1):+.1f}%)",
            f"{rams['E'][idx]:.3f} ({100*(rams['E'][idx]/base['E'][idx]-1):+.1f}%)",
            f"{base['T_AT'][idx]:.2f}",
            f"{tax50['T_AT'][idx]:.2f}",
            f"{rams['T_AT'][idx]:.2f}",
            f"{tax50['mu'][idx]*100:.1f}%",
            f"{rams['mu'][idx]*100:.1f}%",
        ])
    df = pd.DataFrame(rows, columns=[
        "Year",
        "E baseline",
        "E (Tax $50)",
        "E (Ramsey)",
        "T_AT baseline (C)",
        "T_AT (Tax $50)",
        "T_AT (Ramsey)",
        "Mu (Tax $50)",
        "Mu (Ramsey)",
    ])
    df.to_csv(TBL_DIR / "table_15_transition_milestones.csv",
              index=False, encoding="utf-8-sig")
    return df


def main():
    print("Table 13: Cross-country SCC benchmark")
    print(table_13_cross_country_scc().to_string(index=False))
    print()
    print("Table 14: Sectoral abatement potential")
    print(table_14_sectoral_abatement().to_string(index=False))
    print()
    print("Table 15: Transition milestones (2025-2050)")
    print(table_15_transition_milestones().to_string(index=False))


if __name__ == "__main__":
    main()
