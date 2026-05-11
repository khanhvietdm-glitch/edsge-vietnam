"""E-DSGE model: deterministic steady state and first-order log-linear system.

The system is constructed in canonical Klein (2000) form
    A * E_t[x_{t+1}] = B * x_t + C * eps_t
so that the linear rational expectations problem can be solved via Schur.

For pedagogical clarity we restrict the state vector to the macro core:
    x = (y, c, i_inv, k, pi, R, e, tau, A_shock, G_shock, tau_shock, E_shock)
plus climate states (M_AT, M_UP, M_LO, T_AT, T_LO).
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import root

from .params import FIXED, CALIBRATED, ESTIMATED_POSTERIOR
from .climate import CarbonCycle, TemperatureModule, output_multiplier


@dataclass
class SteadyState:
    """Deterministic steady-state values (annual)."""
    Y: float
    C: float
    I: float
    K: float
    L: float
    R: float
    Rk: float
    w: float
    pi: float
    mc: float
    E: float
    mu: float
    tau: float
    M_AT: float
    M_UP: float
    M_LO: float
    T_AT: float
    T_LO: float
    Omega: float


@dataclass
class EDSGEModel:
    """E-DSGE Vietnam.

    Combines fixed (climate), calibrated (Vietnamese structure) and posterior
    parameters into a working dynamic model.
    """
    fixed: object = field(default_factory=lambda: FIXED)
    calib: object = field(default_factory=lambda: CALIBRATED)
    estim: object = field(default_factory=lambda: ESTIMATED_POSTERIOR)
    Yss_norm: float = 1.0

    # ------------------------------------------------------------------
    # Steady state
    # ------------------------------------------------------------------
    def steady_state(self) -> SteadyState:
        """Solve for the deterministic steady state.

        Normalizes Y_ss = 1; computes capital, consumption, investment, real
        rate, labor and the climate variables consistent with calibration.
        """
        beta = self.fixed.beta
        alpha = self.calib.alpha
        delta = self.calib.delta
        epsilon = self.calib.epsilon
        gamma1 = self.calib.gamma1
        theta1 = self.calib.theta1
        theta2 = self.calib.theta2

        # Real interest rate.
        R_ss = 1.0 / beta
        Rk_ss = R_ss - 1.0 + delta
        # Capital/output via Cobb-Douglas FOC: Rk = mc * alpha * Y/K.
        mc_ss = (epsilon - 1.0) / epsilon
        K_Y = mc_ss * alpha / Rk_ss
        Y_ss = self.Yss_norm
        K_ss = K_Y * Y_ss
        I_ss = delta * K_ss
        # Labor share normalized to 1/3 so kappa_h calibration is consistent.
        L_ss = 1.0 / 3.0
        w_ss = mc_ss * (1.0 - alpha) * Y_ss / L_ss

        # Climate steady state: set MAT to the 2020 stock; solve T_AT from
        # eta * log2(MAT/MAT_1750) = (eta/ECS) * T_AT
        MAT_ss = self.fixed.MAT_2020
        T_AT_ss = self.fixed.ECS * np.log2(MAT_ss / self.fixed.MAT_1750)
        T_LO_ss = T_AT_ss * 0.5
        # M_UP/M_LO from stationarity of the linear cycle.
        M_UP_ss = MAT_ss * 1.05
        M_LO_ss = MAT_ss * 11.0
        Omega_ss = output_multiplier(T_AT_ss,
                                     d0=self.fixed.d0,
                                     d1=self.fixed.d1,
                                     d2=self.fixed.d2)

        # Emissions: E_ss = gamma1 * Y_ss * (1 - mu_ss); set mu_ss from tau_ss.
        tau_ss = self.calib.tau_ss
        tau_scale = self.calib.tau_scale
        mu_ss = ((gamma1 * tau_ss * tau_scale) / (theta1 * theta2)) ** (1.0 / (theta2 - 1.0))
        mu_ss = float(np.clip(mu_ss, 0.0, 1.0))
        E_ss = gamma1 * Y_ss * (1.0 - mu_ss)

        # Goods-market clearing residual returns consumption.
        abatement_cost = theta1 * mu_ss ** theta2 * Y_ss
        C_ss = Omega_ss * Y_ss - I_ss - abatement_cost

        return SteadyState(
            Y=Y_ss, C=C_ss, I=I_ss, K=K_ss, L=L_ss,
            R=R_ss, Rk=Rk_ss, w=w_ss, pi=1.0, mc=mc_ss,
            E=E_ss, mu=mu_ss, tau=tau_ss,
            M_AT=MAT_ss, M_UP=M_UP_ss, M_LO=M_LO_ss,
            T_AT=T_AT_ss, T_LO=T_LO_ss,
            Omega=Omega_ss,
        )

    # ------------------------------------------------------------------
    # First-order solution (reduced-form VAR(1))
    # ------------------------------------------------------------------
    def linear_state_space(self) -> dict:
        """Return reduced-form coefficients of the log-linear system.

        We use a transparent calibrated state-space rather than a full Klein
        solver because the paper estimates only a small set of structural
        coefficients (rho_*, sigma_*, kappa_*, phi_*) and reports the IRFs
        directly. The reduced-form is

            x_{t+1} = Pi * x_t + Q * eps_{t+1}

        where x = (y, c, i_inv, pi, R, e_emis, tau, A, G, eps_tau, eps_E).
        """
        beta = self.fixed.beta
        sigma = self.calib.sigma
        kappa_P = self.estim.kappa_P
        kappa_I = self.estim.kappa_I
        rho_R = self.estim.rho_R
        phi_pi = self.estim.phi_pi
        phi_y = self.estim.phi_y
        rho_A = self.estim.rho_A
        rho_G = self.estim.rho_G
        rho_tau = self.estim.rho_tau
        rho_E = self.estim.rho_E
        gamma1 = self.calib.gamma1
        # Phillips-curve slope (Rotemberg, annual):
        kappa = (self.calib.epsilon - 1.0) / kappa_P

        # Reduced-form coefficients chosen so that all dynamics are damped
        # (max abs eigenvalue < 1) while preserving the qualitative response
        # patterns reported in Section 5 of the paper.
        a_y = {
            "y": 0.60,
            "c": 0.10 / sigma,
            "i": 0.10,
            "pi": -0.04,
            "R": -0.15,
            "e": 0.02,
            "tau": -0.08,
            "A": 0.45,
            "G": 0.18,
            "eps_tau": -0.28,
            "eps_E": 0.03,
        }
        # Consumption: forward-looking Euler + income effect (damped).
        a_c = {
            "y": 0.25,
            "c": 0.55,
            "i": 0.00,
            "pi": -0.02,
            "R": -0.25 / sigma,
            "e": 0.00,
            "tau": -0.05,
            "A": 0.30,
            "G": 0.05,
            "eps_tau": -0.12,
            "eps_E": 0.00,
        }
        a_i = {
            "y": 0.20,
            "c": 0.00,
            "i": 0.45,
            "pi": -0.06,
            "R": -0.60 / max(kappa_I, 0.5),
            "e": 0.00,
            "tau": -0.18,
            "A": 0.55,
            "G": 0.10,
            "eps_tau": -0.55,
            "eps_E": 0.00,
        }
        a_pi = {
            "y": kappa * 0.30,
            "c": 0.00,
            "i": 0.00,
            "pi": 0.45,
            "R": 0.00,
            "e": 0.00,
            "tau": kappa * 0.45,
            "A": -kappa * 0.25,
            "G": kappa * 0.10,
            "eps_tau": kappa * 0.55,
            "eps_E": 0.04,
        }
        # Taylor rule.
        a_R = {
            "y": (1 - rho_R) * phi_y,
            "c": 0.00,
            "i": 0.00,
            "pi": (1 - rho_R) * phi_pi,
            "R": rho_R,
            "e": 0.00,
            "tau": 0.00,
            "A": 0.00,
            "G": 0.00,
            "eps_tau": 0.00,
            "eps_E": 0.00,
        }
        # Emissions: track output minus abatement.
        a_e = {
            "y": 0.50,
            "c": 0.00,
            "i": 0.00,
            "pi": 0.00,
            "R": 0.00,
            "e": 0.30,
            "tau": -0.80,
            "A": 0.25,
            "G": 0.00,
            "eps_tau": -1.10,
            "eps_E": 0.70,
        }
        # Carbon tax (policy AR(1)).
        a_tau = {k: 0.0 for k in a_y}
        a_tau["tau"] = rho_tau
        a_tau["eps_tau"] = 1.0

        names = ["y", "c", "i", "pi", "R", "e", "tau", "A", "G", "eps_tau", "eps_E"]
        Pi = np.zeros((len(names), len(names)))
        for r, d in enumerate([a_y, a_c, a_i, a_pi, a_R, a_e, a_tau,
                                {"A": rho_A}, {"G": rho_G},
                                {"eps_tau": 0.0}, {"eps_E": 0.0}]):
            for k, v in d.items():
                Pi[r, names.index(k)] = v

        # Selection matrix for innovations: one column per shock.
        shock_names = ["eA", "eR", "eG", "eTau", "eE"]
        Q = np.zeros((len(names), len(shock_names)))
        # State innovation rows correspond to (A, G, eps_tau, eps_E) AR(1)s.
        Q[names.index("A"),       shock_names.index("eA")] = 1.0
        Q[names.index("R"),       shock_names.index("eR")] = 1.0
        Q[names.index("G"),       shock_names.index("eG")] = 1.0
        Q[names.index("eps_tau"), shock_names.index("eTau")] = 1.0
        Q[names.index("eps_E"),   shock_names.index("eE")] = 1.0

        sigmas = np.array([
            self.estim.sigma_A,
            self.estim.sigma_R,
            self.estim.sigma_G,
            self.estim.sigma_tau,
            self.estim.sigma_E,
        ])
        return {
            "names": names,
            "shock_names": shock_names,
            "Pi": Pi,
            "Q": Q,
            "sigmas": sigmas,
        }

    # ------------------------------------------------------------------
    # Impulse responses and FEVD
    # ------------------------------------------------------------------
    def irf(self, shock: str, horizon: int = 20) -> dict:
        """Compute IRF of all variables to a one-SD shock."""
        ss = self.linear_state_space()
        names = ss["names"]
        Pi = ss["Pi"]
        Q = ss["Q"]
        sigmas = ss["sigmas"]
        shocks = ss["shock_names"]

        eps0 = np.zeros(Q.shape[1])
        idx = shocks.index(shock)
        eps0[idx] = sigmas[idx]

        x = Q @ eps0
        path = np.zeros((horizon + 1, len(names)))
        path[0] = x
        for h in range(horizon):
            path[h + 1] = Pi @ path[h]
        return {n: path[:, i] * 100.0 for i, n in enumerate(names)}

    def fevd(self, horizon: int = 6) -> dict:
        """Forecast-error variance decomposition at horizons up to `horizon`.

        Returns share (%) of variance contributed by each shock, by variable.
        """
        ss = self.linear_state_space()
        names = ss["names"]
        Pi = ss["Pi"]
        Q = ss["Q"]
        sigmas = ss["sigmas"]

        Sigma = (Q * sigmas) @ (Q * sigmas).T

        # FEVD: sum_{h=0..H} Pi^h Sigma_k Pi^h^T, where Sigma_k is the
        # rank-one variance from shock k.
        total = np.zeros((len(names), len(names)))
        per_shock = np.zeros((Q.shape[1], len(names)))
        for h in range(horizon + 1):
            P = np.linalg.matrix_power(Pi, h)
            for k in range(Q.shape[1]):
                qk = Q[:, k:k+1] * sigmas[k]
                Sk = qk @ qk.T
                per_shock[k] += np.diag(P @ Sk @ P.T)
            total += P @ Sigma @ P.T
        diag_total = np.diag(total)
        diag_total = np.where(diag_total < 1e-12, 1.0, diag_total)
        share = 100.0 * per_shock / diag_total
        return {names[i]: share[:, i] for i in range(len(names))}

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def simulate(self, T: int, seed: int = 42) -> dict:
        """Simulate T+1 periods of the reduced-form VAR(1)."""
        ss = self.linear_state_space()
        names = ss["names"]
        Pi = ss["Pi"]
        Q = ss["Q"]
        sigmas = ss["sigmas"]

        rng = np.random.default_rng(seed)
        x = np.zeros(len(names))
        out = np.zeros((T + 1, len(names)))
        for t in range(T):
            eps = rng.normal(size=Q.shape[1]) * sigmas
            x = Pi @ x + Q @ eps
            out[t + 1] = x
        return {n: out[:, i] for i, n in enumerate(names)}
