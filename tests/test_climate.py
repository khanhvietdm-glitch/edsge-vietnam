"""Smoke tests for the DICE climate block."""
import numpy as np
import pytest

from edsge_vn.climate import (
    CarbonCycle, TemperatureModule, damage,
    abatement_share, optimal_abatement,
)


def test_carbon_cycle_steady_state():
    cc = CarbonCycle()
    M0 = np.array([851.0, 894.0, 9362.0])
    # Zero emissions -> stocks should decay but not blow up.
    path = cc.simulate(M0, emissions_path=np.zeros(50))
    assert path.shape == (51, 3)
    assert np.all(np.isfinite(path))
    assert path[-1, 0] <= path[0, 0] + 1e-6  # atmospheric stock should not grow


def test_temperature_step():
    tm = TemperatureModule()
    T_AT, T_LO = tm.step(1.2, 0.5, 851.0)
    assert 1.0 <= T_AT <= 1.4
    assert 0.5 <= T_LO <= 0.7


def test_damage_quadratic():
    d = damage(1.0)
    assert d == pytest.approx(0.00236, rel=1e-3)
    d2 = damage(2.0)
    assert d2 == pytest.approx(0.00944, rel=1e-3)


def test_abatement_optimal_monotone():
    # Higher tax => more abatement, all else equal.
    mu_low = optimal_abatement(25.0)
    mu_high = optimal_abatement(75.0)
    assert 0.0 < mu_low < mu_high <= 1.0


def test_abatement_share_zero():
    assert abatement_share(0.0) == pytest.approx(0.0)
    assert abatement_share(1.0) == pytest.approx(0.0741, rel=1e-2)
