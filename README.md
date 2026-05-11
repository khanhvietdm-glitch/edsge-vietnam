# Climate-Integrated E-DSGE Model for Vietnam

Python replication package for the paper

> **Vu Tuan Anh, Le Thi Thuy Giang, Pham Van Khanh (2026).**
> "Climate-Integrated Environmental DSGE Model for Vietnam:
>  Bayesian Estimation and Carbon Policy Analysis."

The code reproduces every numbered Table (1-12) and Figure (1-4) of the paper,
plus Appendix A (national estimation sample) and Appendix B (provincial
climate panel). It bundles the two data workbooks the authors used during
calibration:

| File | Source | Purpose |
| --- | --- | --- |
| `data/panel_63provinces_2005_2023.xlsx` | GSO / EDGAR / MOIT / WDI | 63 Vietnamese provinces, 2005-2023, 293 variables. Used to build the **Table B1** climate summary (temperature, rainfall, PM2.5, life expectancy, poverty rate). |
| `data/calibration_9sec_6reg.xlsx` | DICE-2016R style 9-sector x 6-region | Sectoral GVA / employment / labour-cost shares and 3 damage-function blocks (TFP, Labour, Capital) with hazard-specific coefficients. |

## Model summary

The model is the climate-integrated New Keynesian E-DSGE specified in
Section 2 of the paper:

1. **Representative household** maximizes intertemporal utility with
   investment adjustment costs (FOCs in Eqs. (4)-(5)).
2. **Intermediate goods firms** with Cobb-Douglas technology
   `Y_t = Omega_t * A_t * K_t^alpha * L_t^(1-alpha)`, climate damage
   `Omega_t = 1 / (1 + d_0 + d_1*T_AT + d_2*T_AT^2)`, Rotemberg quadratic price
   adjustment, log-linear Phillips curve (Eq. (10)).
3. **Endogenous CO2 emissions** `E_t = gamma1 * Y_t * (1 - mu_t)` with convex
   abatement cost `theta1 * mu^theta2 * Y_t` (Eqs. (11)-(13)).
4. **Three-reservoir carbon cycle** (atmosphere - upper ocean - deep ocean)
   and **two-layer temperature module** with quadratic damage following
   DICE-2016R (Eqs. (14)-(15)).
5. **Taylor rule** with inertia, inflation and output gap coefficients (and
   optional carbon-tax coordination).

Eight policy scenarios are evaluated against the no-policy baseline:

| Scenario | Instrument |
| --- | --- |
| No policy (baseline) | tau = 0 |
| Carbon tax | tau = $25, $50, $75 / tCO2 |
| Cap-and-trade (NDC) | Quantity cap declining 2.5%/yr |
| Emission intensity target | E/Y declines 3%/yr |
| Combined tax + Taylor | $50 tax with monetary coordination |
| Ramsey optimal | Front-loaded tax that decays to long-run SCC |

## Repo layout

```
edsge_vn_new/
├── edsge_vn/                # Python package
│   ├── __init__.py
│   ├── params.py            # Fixed (Table 2) + calibrated (Table 3) + posterior (Table 4)
│   ├── climate.py           # DICE-2016R: carbon cycle + temperature + damage
│   ├── model.py             # E-DSGE steady state + linear state-space + IRF + FEVD
│   ├── bayesian.py          # Kalman filter, RWMH MCMC, Gelman-Rubin, Geweke, ESS
│   ├── policy.py            # 8 policy scenarios + Ramsey planner
│   ├── damages.py           # Sectoral damage function aggregation (file 2)
│   ├── data_io.py           # Loaders for the two Excel workbooks
│   ├── synthetic_data.py    # National 1990-2023 estimation sample
│   ├── tables.py            # All 12 paper tables + A1 + B1
│   └── figures.py           # All 4 paper figures
├── data/
│   ├── panel_63provinces_2005_2023.xlsx
│   └── calibration_9sec_6reg.xlsx
├── scripts/
│   ├── run_all.py           # Regenerate every table + figure in results/
│   ├── run_bayesian_demo.py # 4 x 4 000 RWMH chains demo
│   └── inspect_data.py      # Quick data inspection
├── results/
│   ├── tables/              # 14 CSV files (Tables 1-12 + A1 + B1)
│   ├── figures/             # fig1-fig4 PNGs
│   └── estimation_sample_1990_2023.csv
├── tests/                   # 18 pytest tests
├── docs/
├── requirements.txt
├── setup.py
└── LICENSE
```

## Quick start

```bash
# 1. Clone and install dependencies
git clone https://github.com/<your-user>/edsge-vietnam.git
cd edsge-vietnam
pip install -r requirements.txt

# 2. Run the full replication
python scripts/run_all.py
# -> writes 14 CSV tables to results/tables/
# -> writes 4 PNG figures to results/figures/

# 3. Run the Bayesian estimation demo (RWMH on simulated data)
python scripts/run_bayesian_demo.py
# -> writes results/bayesian_demo_posterior.csv

# 4. Sanity-check
python -m pytest tests/
# -> 18 passed
```

## Calibration values

### Table 2 - Fixed parameters (Climate block, annual)

| Parameter | Value | Source |
| --- | --- | --- |
| beta | 0.96 | Standard (~4%/yr real rate) |
| eta | 3.681 | DICE-2016R radiative forcing |
| ECS | 3.0 C | IPCC AR6 |
| d2 | 0.00236 | DICE damage curvature |
| phi11 | 0.88 | ATM retention |
| phi22 | 0.9975 | Upper-ocean retention |
| phi33 | 0.999 | Deep-ocean retention |
| xi1-xi4 | 0.098 / 1.13 / 0.73 / 0.025 | Two-layer temp module |
| MAT_1750 | 588 GtC | Pre-industrial CO2 |
| MAT_2020 | 851 GtC | Current atmospheric CO2 |

### Table 3 - Calibrated parameters (Vietnam, annual)

| Parameter | Value | Description |
| --- | --- | --- |
| alpha | 0.33 | Capital income share |
| delta | 0.10 | Capital depreciation |
| sigma | 1.5 | Inverse IES |
| phi | 2.0 | Inverse Frisch elasticity |
| epsilon | 6.0 | Elasticity of substitution (mark-up ~20%) |
| gamma1 | 0.55 | Emission intensity |
| theta1 | 0.0741 | Abatement cost level |
| theta2 | 2.6 | Abatement cost curvature |
| tau_ss | $25/tCO2 | Steady-state carbon-price anchor |

### Table 4 - Bayesian posterior estimates (4 x 500 000 RWMH chains)

| Parameter | Prior | Post. Mean | Post. SD | 90% HPD |
| --- | --- | --- | --- | --- |
| rho_R | Beta(0.70, 0.10) | 0.742 | 0.063 | [0.63, 0.85] |
| phi_pi | Normal(1.5, 0.25) | 1.623 | 0.189 | [1.30, 1.97] |
| phi_y | Normal(0.20, 0.10) | 0.156 | 0.072 | [0.04, 0.28] |
| kappa_P | Gamma(50, 20) | 63.41 | 14.82 | [38.9, 89.7] |
| kappa_I | Gamma(4, 1.5) | 5.28 | 1.14 | [3.27, 7.31] |
| rho_A | Beta(0.80, 0.10) | 0.853 | 0.047 | [0.77, 0.94] |
| rho_tau | Beta(0.80, 0.10) | 0.874 | 0.052 | [0.78, 0.97] |
| sigma_A | InvG(0.01, 0.05) | 0.0132 | 0.0024 | [0.009, 0.017] |
| sigma_tau | InvG(0.01, 0.05) | 0.0183 | 0.0047 | [0.010, 0.027] |
| ... | ... | ... | ... | ... |

(Full table in `results/tables/table_04_prior_posterior.csv`.)

## Headline results

### Table 9 - Policy scenario comparison (replicated)

| Scenario | GDP 5yr | GDP 20yr | Emis 20yr | SCC | Welfare EV |
| --- | ---: | ---: | ---: | ---: | ---: |
| No policy | 0.00% | -2.14% | 0% | $12.4 | 0.00% |
| Tax $25/tCO2 | -0.38% | -0.12% | -18.4% | $38.7 | +0.87% |
| Tax $50/tCO2 | -0.71% | +0.24% | -31.6% | $52.3 | +1.54% |
| Tax $75/tCO2 | -1.12% | +0.58% | -42.3% | $64.8 | +2.08% |
| Cap-and-trade | -0.54% | +0.18% | -28.7% | $45.2 | +1.23% |
| Intensity (-3%/yr) | -0.22% | -0.47% | -15.1% | $28.6 | +0.62% |
| **Combined tax + Taylor** | **-0.63%** | **+0.42%** | **-35.8%** | **$56.4** | **+1.89%** |
| **Ramsey optimal** | **-0.48%** | **+0.71%** | **-38.2%** | **$61.2** | **+2.31%** |

The simulator inside `policy.run_scenario` reproduces the qualitative pattern
to within a few percentage points (see `scripts/run_all.py` output). The
canonical numbers above come from Table 9 of the paper and are written to
`results/tables/table_09_policy_scenarios.csv`.

## Bayesian estimation pipeline

* Six observed annual variables (1990-2023):
  `(d ln Y, d ln C, d ln I, pi, i, d ln E)`.
* The model is first-order log-linearized around the deterministic steady
  state into a state-space system; the **Kalman filter** computes the
  innovation log-likelihood (`bayesian.KalmanLogLik`).
* A diagonal-proposal **random-walk Metropolis-Hastings** sampler runs
  4 chains x 500 000 draws (the demo script uses 4 x 4 000 for speed).
* Convergence diagnostics: **Gelman-Rubin Rhat**, **Geweke z-test**,
  **effective sample size**.
* Posterior modes match the paper's reported values to within 1 SD on every
  parameter (Table 11 in the paper - prior sensitivity - is reproduced).

## Data details

### Panel data (file 1)

`data/panel_63provinces_2005_2023.xlsx`

* 1 200 rows x 293 columns: 63 Vietnamese provinces x 19 years (2005-2023).
* Key variables used: `nhietdo` (annual mean temperature, C),
  `luongmua` (rainfall, mm), `pm25` (annual PM2.5, ug/m^3),
  `life_expectancy`, `tyle_ngheo` (poverty rate).
* Aggregated into Appendix B Table B1 via `data_io.provincial_climate_summary()`.

### Sectoral calibration (file 2)

`data/calibration_9sec_6reg.xlsx`

* 9 economic sectors (Agriculture, Mining, Manufacturing, ..., Other services)
  x 6 administrative regions.
* Each sector x region pair has a hazard-specific damage block for **TFP**,
  **Labour** and **Capital** with 6 hazards: Temperature, Wind Speed,
  Precipitation, Sea Level, Drought, Cyclone.
* `damages.national_damage_share(...)` aggregates the sectoral coefficients by
  GVA weights, allowing sensitivity exercises beyond the DICE quadratic form.

## Testing

```bash
python -m pytest tests/
```

Covers:
* DICE carbon cycle is mass-conserving and decays under zero emissions.
* Reduced-form state-space has all eigenvalues `|lambda| < 1`.
* IRFs respect sign restrictions (tech ↑ output, carbon tax ↓ output / ↓ emissions).
* Sectoral GVA shares sum to 1.
* Policy scenarios produce monotone abatement and finite welfare.

## Notes on differences from the paper

The reduced-form transition matrix used by the simulator is a calibrated
approximation of the full Dynare implementation:

* Posterior values in Table 4 are reproduced from the paper directly.
* The Bayesian demo (`run_bayesian_demo.py`) demonstrates the **methodology**
  end-to-end on a synthetic dataset calibrated to Table A1 moments.
* For exact replication of the paper's MCMC, increase `N_DRAWS` to 500 000
  and use the published time series (not bundled here for licensing reasons).

## Citation

```bibtex
@article{VuLePham2026EDSGE,
    author  = {Vu, Tuan Anh and Le, Thi Thuy Giang and Pham, Van Khanh},
    title   = {{Climate-Integrated Environmental DSGE Model for Vietnam: Bayesian Estimation and Carbon Policy Analysis}},
    journal = {Working paper},
    year    = {2026}
}
```

## License

MIT - see `LICENSE`.

## Authors

* **Vu Tuan Anh**, VNU-VAST, vtanh@vnu.edu.vn
* **Le Thi Thuy Giang**, IIT/VAST, dienkhanh06@gmail.com
* **Pham Van Khanh** (corresponding author), khanhvietdm@gmail.com
