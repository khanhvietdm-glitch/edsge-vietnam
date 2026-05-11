"""Tests for policy scenarios."""
import numpy as np
import pytest

from edsge_vn import EDSGEModel, SCENARIOS, run_scenario


@pytest.fixture
def model():
    return EDSGEModel()


def test_no_policy_zero_difference(model):
    r = run_scenario(model, SCENARIOS["no_policy"], horizon=20)
    assert abs(r["gdp_5yr"]) < 1e-6
    assert abs(r["emi_20yr"]) < 1e-6


def test_higher_tax_more_abatement(model):
    r25 = run_scenario(model, SCENARIOS["tax_25"], horizon=20)
    r50 = run_scenario(model, SCENARIOS["tax_50"], horizon=20)
    r75 = run_scenario(model, SCENARIOS["tax_75"], horizon=20)
    assert r25["emi_20yr"] > r50["emi_20yr"] > r75["emi_20yr"]
    assert r25["gdp_5yr"] > r50["gdp_5yr"] > r75["gdp_5yr"]


def test_all_scenarios_finite(model):
    for name, scen in SCENARIOS.items():
        r = run_scenario(model, scen, horizon=20)
        for key in ("gdp_5yr", "gdp_20yr", "emi_20yr", "welfare_ev"):
            assert np.isfinite(r[key]), f"{name}: {key} not finite"


def test_ramsey_welfare_competitive(model):
    """Ramsey should deliver welfare at least as high as $50 tax."""
    r_ramsey = run_scenario(model, SCENARIOS["ramsey"], horizon=20)
    r_50 = run_scenario(model, SCENARIOS["tax_50"], horizon=20)
    assert r_ramsey["welfare_ev"] >= r_50["welfare_ev"] - 0.05
