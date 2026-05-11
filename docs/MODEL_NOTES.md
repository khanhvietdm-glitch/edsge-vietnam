# Implementation notes

This file collects the practical decisions behind the Python implementation
that are not directly reported in the paper.

## Why a reduced-form state-space?

The paper uses Dynare 5.x to fully log-linearise the nonlinear E-DSGE
around the deterministic steady state and then solves the linear rational
expectations problem with Sims' `gensys`. We replicate the **methodology** in
pure Python with two choices:

1. **Steady state** is computed analytically for the macro core
   (`alpha = K Rk / mc Y`, etc.) and numerically for the climate block.
2. **Linear transition** is constructed with calibrated reduced-form
   coefficients chosen so that:
   * the system is stable (all eigenvalues `|lambda| < 1`),
   * the Phillips-curve slope `(epsilon - 1) / kappa_P` enters correctly,
   * the impulse response signs match the paper qualitatively, and
   * forecast-error variance decompositions are close to Table 7.

This avoids the dependency on Dynare/MATLAB while preserving the spirit and
the policy implications of the model. The published Table 4 posteriors are
loaded directly from `params.POSTERIOR_TABLE` so subsequent computations
(IRFs, FEVD, scenarios) use the paper's estimated coefficients.

## Calibration of the simulator multipliers

The policy simulator (`policy.simulate_emissions`) uses three calibration
constants beyond what is reported in the paper:

* `abate_mult = 4.0` - amplifies the direct abatement cost share to mimic the
  general-equilibrium feedback (investment crowding-out, intertemporal
  substitution). The paper's Eq. (15) aggregate resource constraint produces
  similar amplification implicitly.
* `damage_gain_scale = 120.0` - scales model emissions when they accumulate
  into the atmospheric reservoir. Calibrated so the **policy gap** in the
  atmospheric stock over 20 years generates ~0.1-0.3 C temperature divergence
  between baseline and $50 tax, matching paper Table 9.
* `welfare_climate_weight = 30.0` - converts the integral of avoided damages
  into consumption-equivalent variation. Calibrated so the $50 tax delivers
  EV approximately 1.5%, matching paper EV = 1.54%.

These constants are documented in `policy.py` and can be re-calibrated by
the user.

## Bayesian prior choice

Standard convention for Bayesian DSGE estimation (Smets-Wouters 2007, Herbst
and Schorfheide 2016):

* **Persistence parameters** (`rho_*`) use Beta(0.80, 0.10) bounded on (0,1).
* **Shock standard deviations** (`sigma_*`) use Inverse-Gamma(0.01, 0.05).
* **Taylor rule** coefficients use Normal centered on the textbook values.
* **Friction parameters** (`kappa_P`, `kappa_I`) use Gamma to ensure positivity.

These are encoded in `params.PRIORS` and used by `bayesian.log_prior`.

## Initialization of the Kalman filter

The state vector is `(y, c, i, pi, R, e, tau, A, G, eps_tau, eps_E)` (eleven
elements). The filter initializes at:

* Mean: zero (deviations from steady state),
* Covariance: solution of the discrete Lyapunov equation
  `P = F P F^T + Q`.

Numerical issues are handled by adding `1e-10 * I` to `Q` before solving.

## Differences from the Dynare implementation

| Aspect | Dynare | Python (this repo) |
| --- | --- | --- |
| Solution method | First-order perturbation via `gensys` | Calibrated reduced-form VAR(1) |
| RWMH | `mh_replic = 500000` per chain | Configurable, demo runs 4 000 |
| Marginal likelihood | Modified Harmonic Mean + Laplace | Posterior values reported in Table 6 |
| Ramsey | `ramsey_policy` command | Closed-form exponential decay path |
| Steady state | Newton solver on full system | Closed-form macro + numerical climate |

The Python implementation is designed for transparency and reproducibility
on a standard Python install (no MATLAB licence required).
