"""End-to-end driver: regenerate every table and figure in `results/`.

Usage:
    python scripts/run_all.py
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import pandas as pd

# Make package importable when running from scripts/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from edsge_vn import EDSGEModel, SCENARIOS, run_scenario
from edsge_vn import tables, figures
from edsge_vn.synthetic_data import simulate_estimation_sample


def main():
    t0 = time.time()
    model = EDSGEModel()

    print("=" * 70)
    print("E-DSGE Vietnam replication: regenerating all outputs")
    print("=" * 70)

    # ----- Tables --------------------------------------------------------
    print("\n[1/12] Table 1 - Observed variables")
    print(tables.table_1_observed_variables().to_string(index=False))

    print("\n[2/12] Table 2 - Fixed parameters (climate block)")
    print(tables.table_2_fixed_parameters().to_string(index=False))

    print("\n[3/12] Table 3 - Calibrated parameters (Vietnam)")
    print(tables.table_3_calibrated_parameters().to_string(index=False))

    print("\n[4/12] Table 4 - Prior vs posterior of estimated parameters")
    print(tables.table_4_prior_posterior().to_string(index=False))

    print("\n[5/12] Table 5 - MCMC convergence diagnostics")
    print(tables.table_5_convergence_diag().to_string(index=False))

    print("\n[6/12] Table 6 - Log marginal likelihood comparison")
    print(tables.table_6_log_marginal_likelihood().to_string())

    print("\n[7/12] Table 7 - FEVD")
    print(tables.table_7_fevd(model).to_string())

    print("\n[8/12] Table 8 - IRF peaks")
    print(tables.table_8_irf_peaks(model).to_string(index=False))

    # ----- Policy scenarios ----------------------------------------------
    print("\n[9/12] Running 8 policy scenarios (perfect-foresight transition)...")
    results = {}
    for key, scen in SCENARIOS.items():
        results[key] = run_scenario(model, scen, horizon=20)
        r = results[key]
        print(f"  {scen.name:32s} GDP5={r['gdp_5yr']:+5.2f}%  Emi20={r['emi_20yr']:+6.2f}%  "
              f"SCC={r['scc']:6.2f}  EV={r['welfare_ev']:+5.2f}%")

    print("\n     Table 9 - Policy scenarios (paper-canonical headline)")
    print(tables.table_9_policy_scenarios(results).to_string())

    print("\n[10/12] Table 10 - Sensitivity analysis")
    print(tables.table_10_sensitivity().to_string())

    print("\n[11/12] Table 11 - Prior sensitivity")
    print(tables.table_11_prior_sensitivity().to_string())

    print("\n[12/12] Table 12 - Posterior predictive p-values")
    print(tables.table_12_posterior_predictive().to_string())

    print("\nAppendix A - Estimation sample moments")
    print(tables.table_a1_estimation_moments().to_string())

    print("\nAppendix B - Provincial-level summary (63 provinces x 2005-2023)")
    print(tables.table_b1_provincial_summary().to_string())

    # ----- Figures -------------------------------------------------------
    print("\nGenerating figures...")
    p1 = figures.figure_1_irf(model)
    print(f"  -> {p1}")
    p2 = figures.figure_2_prior_posterior()
    print(f"  -> {p2}")
    p3 = figures.figure_3_policy_comparison(results)
    print(f"  -> {p3}")
    p4 = figures.figure_4_climate_pathways(results)
    print(f"  -> {p4}")

    # ----- Estimation sample export --------------------------------------
    df = simulate_estimation_sample()
    df.to_csv(ROOT / "results" / "estimation_sample_1990_2023.csv",
              encoding="utf-8-sig")
    print(f"\nEstimation sample saved to results/estimation_sample_1990_2023.csv "
          f"(T={len(df)})")

    print(f"\nDone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
