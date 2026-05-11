# Replication procedure

This document records exactly how to regenerate every table and figure in
the paper from the source data shipped in `data/`.

## Environment

```bash
python --version  # 3.10 or newer
pip install -r requirements.txt
```

## Step 1: regenerate every table and figure

```bash
python scripts/run_all.py
```

Output:

```
results/
├── estimation_sample_1990_2023.csv           # Appendix A synthesised series
├── tables/
│   ├── table_01_observed_variables.csv
│   ├── table_02_fixed_parameters.csv
│   ├── table_03_calibrated_parameters.csv
│   ├── table_04_prior_posterior.csv
│   ├── table_05_convergence.csv
│   ├── table_06_log_marginal_likelihood.csv
│   ├── table_07_fevd.csv
│   ├── table_08_irf_peaks.csv
│   ├── table_09_policy_scenarios.csv
│   ├── table_10_sensitivity.csv
│   ├── table_11_prior_sensitivity.csv
│   ├── table_12_posterior_predictive.csv
│   ├── table_A1_estimation_moments.csv
│   └── table_B1_provincial_summary.csv
└── figures/
    ├── fig1_irf.png
    ├── fig2_prior_posterior.png
    ├── fig3_policy_comparison.png
    └── fig4_climate_pathways.png
```

## Step 2: Bayesian estimation demo

```bash
python scripts/run_bayesian_demo.py
```

This runs 4 x 4 000 RWMH chains on a synthetic dataset calibrated to the
Appendix A moments. To replicate the paper's full estimation, edit
`scripts/run_bayesian_demo.py` and set `N_DRAWS = 500_000`. Expected
runtime on a modern desktop is several hours.

## Step 3: data inspection

```bash
python scripts/inspect_data.py
```

Prints the contents of both source workbooks for verification.

## Step 4: regression tests

```bash
python -m pytest tests/ -v
```

The suite covers climate primitives, model stability, data loaders and
policy scenarios.

## Mapping paper -> code

| Paper element | Module / function |
| --- | --- |
| Eq. (1)-(5) household FOCs | `model.EDSGEModel.steady_state` |
| Eq. (6)-(7) Cobb-Douglas + damage | `model.EDSGEModel.steady_state` + `climate.output_multiplier` |
| Eq. (8) DICE damage | `climate.damage` |
| Eq. (9)-(10) Rotemberg pricing | `model.EDSGEModel.linear_state_space` (Phillips slope) |
| Eq. (11) emissions | `policy.simulate_emissions` |
| Eq. (12)-(13) abatement | `climate.abatement_share` / `climate.optimal_abatement` |
| Eq. (14) carbon cycle | `climate.CarbonCycle` |
| Eq. (15) temperature | `climate.TemperatureModule` |
| Eq. (16) SCC | `policy.social_cost_of_carbon` |
| Section 4 calibration | `params.FIXED`, `params.CALIBRATED`, `params.POSTERIOR_TABLE` |
| Section 5 Bayesian | `bayesian.KalmanLogLik`, `bayesian.run_rwmh`, diagnostics |
| Section 6 policy | `policy.run_scenario`, `policy.SCENARIOS` |
| Section 8 Ramsey | `policy.ramsey_optimal` |
| Appendix A | `synthetic_data.simulate_estimation_sample` |
| Appendix B | `data_io.provincial_climate_summary` |
| Appendix C | `scripts/run_all.py` |

## Reporting issues

Open an issue on GitHub describing the platform (OS, Python version),
the command you ran, and the full traceback.
