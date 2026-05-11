"""DICE-2016R climate block: three-reservoir carbon cycle, two-layer
temperature module and quadratic damage function.

State equations are annualized (paper uses T = 34 annual obs).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .params import FIXED


@dataclass
class CarbonCycle:
    """Three-reservoir carbon cycle (atmosphere - upper ocean - deep ocean).

    Stock evolution (GtC):
        M_{t+1} = Phi * M_t + e_t * [1, 0, 0]^T
    """
    phi11: float = FIXED.phi11
    phi12: float = FIXED.phi12
    phi22: float = FIXED.phi22
    phi33: float = FIXED.phi33

    @property
    def Phi(self) -> np.ndarray:
        """Mass-conserving carbon-transition matrix Phi.

        M_{t+1} = Phi @ M_t + e_t * [1, 0, 0]^T.

        Columns sum to 1 (no mass loss). The four diagonal-ish parameters
        (phi11, phi12, phi22, phi33) come from DICE-2016R; the remaining
        entries are pinned by mass conservation.
        """
        phi11 = self.phi11
        phi12 = self.phi12
        phi22 = self.phi22
        phi33 = self.phi33
        # UP -> ATM and UP -> LO splits, given UP retention.
        residual_up = max(1.0 - phi22, 0.0)
        phi21 = residual_up * 0.60   # ~60% returns to ATM
        phi23 = residual_up * 0.40   # ~40% to deep ocean
        phi32 = 1.0 - phi33          # LO -> UP only
        return np.array([
            [phi11,        phi21,        0.0],
            [1.0 - phi11,  phi22,        phi32],
            [0.0,          phi23,        phi33],
        ])

    def step(self, M: np.ndarray, emissions: float) -> np.ndarray:
        """One-step update; emissions enter the atmospheric reservoir only."""
        M_next = self.Phi @ M
        M_next[0] += emissions
        return M_next

    def simulate(self, M0: np.ndarray, emissions_path: np.ndarray) -> np.ndarray:
        """Roll forward for length-T emissions; returns (T+1, 3) trajectory."""
        T = len(emissions_path)
        out = np.zeros((T + 1, 3))
        out[0] = M0
        for t in range(T):
            out[t + 1] = self.step(out[t], emissions_path[t])
        return out


@dataclass
class TemperatureModule:
    """Two-layer temperature module (atmosphere + deep ocean)."""
    xi1: float = FIXED.xi1
    xi2: float = FIXED.xi2
    xi3: float = FIXED.xi3
    xi4: float = FIXED.xi4
    eta: float = FIXED.eta
    ECS: float = FIXED.ECS
    MAT_1750: float = FIXED.MAT_1750

    def forcing(self, MAT: float) -> float:
        """Radiative forcing F_t = eta * log2(MAT_t / MAT_1750)."""
        return self.eta * np.log2(max(MAT / self.MAT_1750, 1e-6))

    def step(self, T_AT: float, T_LO: float, MAT: float) -> tuple[float, float]:
        """One-step update of atmospheric and deep-ocean temperatures."""
        F = self.forcing(MAT)
        lam = self.eta / self.ECS
        T_AT_new = T_AT + self.xi1 * (F - lam * T_AT - self.xi3 * (T_AT - T_LO))
        T_LO_new = T_LO + self.xi4 * (T_AT - T_LO)
        return T_AT_new, T_LO_new

    def simulate(
        self,
        T_AT0: float,
        T_LO0: float,
        MAT_path: np.ndarray,
    ) -> np.ndarray:
        """Roll forward; returns (T+1, 2) array with columns [T_AT, T_LO]."""
        T = len(MAT_path)
        out = np.zeros((T + 1, 2))
        out[0] = [T_AT0, T_LO0]
        T_AT, T_LO = T_AT0, T_LO0
        for t in range(T):
            T_AT, T_LO = self.step(T_AT, T_LO, MAT_path[t])
            out[t + 1] = [T_AT, T_LO]
        return out


def damage(T_AT: float | np.ndarray,
           d0: float = FIXED.d0,
           d1: float = FIXED.d1,
           d2: float = FIXED.d2) -> float | np.ndarray:
    """DICE damage function: 1 - Omega_t (output loss share)."""
    return d0 + d1 * T_AT + d2 * T_AT ** 2


def output_multiplier(T_AT: float | np.ndarray, **kwargs) -> float | np.ndarray:
    """Damage-corrected output multiplier Omega_t = 1 / (1 + damage)."""
    return 1.0 / (1.0 + damage(T_AT, **kwargs))


def abatement_share(mu: float | np.ndarray,
                    theta1: float = 0.0741,
                    theta2: float = 2.6) -> float | np.ndarray:
    """Abatement cost share Theta(mu) = theta1 * mu^theta2.

    mu = abatement rate in [0, 1]; theta1 -> backstop intensity, theta2 -> curvature.
    """
    mu_arr = np.asarray(mu, dtype=float)
    return theta1 * np.power(np.clip(mu_arr, 0.0, 1.0), theta2)


def optimal_abatement(tau: float | np.ndarray,
                      gamma1: float = 0.55,
                      theta1: float = 0.0741,
                      theta2: float = 2.6,
                      tau_scale: float = 0.001) -> float | np.ndarray:
    """Solve FOC theta1 * theta2 * mu^(theta2 - 1) = gamma1 * (tau * tau_scale).

    `tau` is the carbon price in $/tCO2 (paper units); `tau_scale` converts to
    model-internal fractional units. Returns mu* clipped to [0, 1].
    """
    tau_arr = np.asarray(tau, dtype=float)
    rhs = gamma1 * tau_arr * tau_scale / (theta1 * theta2)
    mu_star = np.power(np.maximum(rhs, 0.0), 1.0 / (theta2 - 1.0))
    return np.clip(mu_star, 0.0, 1.0)
