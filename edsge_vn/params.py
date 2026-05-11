"""Calibration: fixed climate parameters + Vietnam-specific calibrated values
plus prior and posterior of the 14 Bayesian-estimated parameters.

Numerical values come from Tables 2, 3 and 4 of the paper.
All annual frequency.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class FixedParams:
    """Climate block + normalizations (Table 2)."""
    beta: float = 0.96
    eta: float = 3.681
    ECS: float = 3.0
    d0: float = 0.0
    d1: float = 0.0
    d2: float = 0.00236
    phi11: float = 0.88
    phi12: float = 0.12
    phi22: float = 0.9975
    phi33: float = 0.999
    xi1: float = 0.098
    xi2: float = 1.13
    xi3: float = 0.73
    xi4: float = 0.025
    MAT_1750: float = 588.0
    MAT_2020: float = 851.0
    pi_ss: float = 1.0


@dataclass(frozen=True)
class CalibratedParams:
    """Vietnam-specific calibrated parameters (Table 3 initial column)."""
    alpha: float = 0.33
    delta: float = 0.10
    sigma: float = 1.5
    phi: float = 2.0
    epsilon: float = 6.0
    kappa_h: float = 1.0
    gamma1: float = 0.55
    gamma2: float = 0.0
    theta1: float = 0.0741
    theta2: float = 2.6
    phi_pi: float = 1.5
    phi_y: float = 0.2
    rho_R: float = 0.7
    tau_ss: float = 25.0
    # Conversion from $/tCO2 (paper units) to model-internal fractional units.
    # Vietnam GDP ~ $300B, emissions ~ 350 MtCO2 -> 0.00117 tCO2 per $ GDP;
    # tau_scale = 0.001 gives well-calibrated abatement rates for $25-$75 taxes.
    tau_scale: float = 0.001


@dataclass(frozen=True)
class EstimatedPosterior:
    """Posterior means from Table 4 (Bayesian estimates)."""
    rho_R: float = 0.7420
    phi_pi: float = 1.623
    phi_y: float = 0.156
    kappa_P: float = 63.41
    kappa_I: float = 5.28
    rho_A: float = 0.853
    rho_G: float = 0.791
    rho_tau: float = 0.874
    rho_E: float = 0.812
    sigma_A: float = 0.0132
    sigma_R: float = 0.0078
    sigma_G: float = 0.0215
    sigma_tau: float = 0.0183
    sigma_E: float = 0.0247


# Prior specification: (distribution_family, mean, sd) keyed by parameter name.
# Distribution families: 'beta', 'normal', 'gamma', 'inv_gamma'.
PRIORS = {
    "rho_R":     ("beta",      0.700, 0.100),
    "phi_pi":    ("normal",    1.500, 0.250),
    "phi_y":     ("normal",    0.200, 0.100),
    "kappa_P":   ("gamma",    50.000, 20.000),
    "kappa_I":   ("gamma",     4.000, 1.500),
    "rho_A":     ("beta",      0.800, 0.100),
    "rho_G":     ("beta",      0.800, 0.100),
    "rho_tau":   ("beta",      0.800, 0.100),
    "rho_E":     ("beta",      0.800, 0.100),
    "sigma_A":   ("inv_gamma", 0.010, 0.050),
    "sigma_R":   ("inv_gamma", 0.010, 0.050),
    "sigma_G":   ("inv_gamma", 0.010, 0.050),
    "sigma_tau": ("inv_gamma", 0.010, 0.050),
    "sigma_E":   ("inv_gamma", 0.010, 0.050),
}

# Singletons exposed at package level.
FIXED = FixedParams()
CALIBRATED = CalibratedParams()
ESTIMATED_POSTERIOR = EstimatedPosterior()
ESTIMATED_PRIOR = PRIORS


# Summary statistics of the estimation sample (Table A1).
# Used to construct the simulated national time series for replication.
DATA_MOMENTS = {
    "dlogY":  {"mean": 0.064, "sd": 0.018, "min":  0.025, "max": 0.095},
    "dlogC":  {"mean": 0.058, "sd": 0.024, "min":  0.018, "max": 0.092},
    "dlogI":  {"mean": 0.081, "sd": 0.047, "min": -0.021, "max": 0.183},
    "pi":     {"mean": 0.072, "sd": 0.058, "min":  0.006, "max": 0.231},
    "i":      {"mean": 0.083, "sd": 0.034, "min":  0.042, "max": 0.156},
    "dlogE":  {"mean": 0.048, "sd": 0.032, "min": -0.014, "max": 0.112},
}


# Posterior moments used by external scripts (matches Table 4 columns).
POSTERIOR_TABLE = {
    "rho_R":     (0.7420, 0.0630, 0.631, 0.854),
    "phi_pi":    (1.6230, 0.1890, 1.300, 1.970),
    "phi_y":     (0.1560, 0.0720, 0.037, 0.284),
    "kappa_P":   (63.410, 14.820, 38.91, 89.72),
    "kappa_I":   (5.2800, 1.1400, 3.270, 7.310),
    "rho_A":     (0.8530, 0.0470, 0.771, 0.938),
    "rho_G":     (0.7910, 0.0680, 0.672, 0.911),
    "rho_tau":   (0.8740, 0.0520, 0.783, 0.967),
    "rho_E":     (0.8120, 0.0710, 0.686, 0.940),
    "sigma_A":   (0.0132, 0.0024, 0.009, 0.017),
    "sigma_R":   (0.0078, 0.0013, 0.006, 0.010),
    "sigma_G":   (0.0215, 0.0041, 0.014, 0.029),
    "sigma_tau": (0.0183, 0.0047, 0.010, 0.027),
    "sigma_E":   (0.0247, 0.0058, 0.015, 0.035),
}
