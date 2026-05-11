"""E-DSGE Vietnam replication package.

Implements the climate-integrated Environmental DSGE model from:

    Vu Tuan Anh, Le Thi Thuy Giang, Pham Van Khanh (2026).
    "Climate-Integrated Environmental DSGE Model for Vietnam:
     Bayesian Estimation and Carbon Policy Analysis".

The model combines:
  * representative household with investment adjustment costs;
  * Rotemberg-pricing intermediate goods firms;
  * endogenous CO2 emissions with convex abatement;
  * 3-reservoir carbon cycle + 2-layer temperature module (DICE-2016R);
  * Taylor-rule monetary policy with carbon tax instruments.
"""

from .params import FIXED, CALIBRATED, ESTIMATED_POSTERIOR, ESTIMATED_PRIOR
from .climate import CarbonCycle, TemperatureModule, damage
from .model import EDSGEModel, SteadyState
from .bayesian import KalmanLogLik, run_rwmh, geweke_diag, gelman_rubin
from .policy import PolicyScenario, run_scenario, ramsey_optimal, SCENARIOS

__all__ = [
    "FIXED",
    "CALIBRATED",
    "ESTIMATED_POSTERIOR",
    "ESTIMATED_PRIOR",
    "CarbonCycle",
    "TemperatureModule",
    "damage",
    "EDSGEModel",
    "SteadyState",
    "KalmanLogLik",
    "run_rwmh",
    "geweke_diag",
    "gelman_rubin",
    "PolicyScenario",
    "run_scenario",
    "ramsey_optimal",
    "SCENARIOS",
]

__version__ = "1.0.0"
