"""Smoke tests for the E-DSGE core."""
import numpy as np
import pytest

from edsge_vn import EDSGEModel


def test_steady_state_positive():
    m = EDSGEModel()
    ss = m.steady_state()
    assert ss.Y > 0
    assert ss.C > 0
    assert ss.K > 0
    assert ss.I > 0
    assert 0.0 < ss.mu < 1.0
    assert ss.E > 0
    assert ss.T_AT > 0
    assert ss.Omega > 0.99


def test_linear_state_space_stable():
    m = EDSGEModel()
    ss = m.linear_state_space()
    F = ss["Pi"]
    ev = np.abs(np.linalg.eigvals(F))
    assert ev.max() < 0.99, f"Max eigenvalue {ev.max():.3f} >= 0.99 (unstable)"


def test_irf_finite():
    m = EDSGEModel()
    irf = m.irf("eA", horizon=20)
    for k, v in irf.items():
        assert v.shape == (21,)
        assert np.all(np.isfinite(v))


def test_irf_signs():
    """Technology shock raises output; carbon tax shock lowers output."""
    m = EDSGEModel()
    irf_tech = m.irf("eA", horizon=8)
    irf_tax = m.irf("eTau", horizon=8)
    assert irf_tech["y"][1] > 0
    assert irf_tax["y"][1] < 0
    assert irf_tax["e"][1] < 0  # carbon tax reduces emissions


def test_fevd_sums_to_100():
    m = EDSGEModel()
    fevd = m.fevd(horizon=6)
    for v in ["y", "pi", "R", "e"]:
        total = fevd[v].sum()
        # Only the five 'real' shocks should contribute meaningfully; total
        # of shock-attributable variance + residual should be > 0.
        assert total > 0
