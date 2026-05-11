"""Tests for the data loaders."""
import pandas as pd
import pytest

from edsge_vn.data_io import (
    load_panel, provincial_climate_summary,
    load_sectoral_shares, load_damage_function_block,
)


def test_panel_loads():
    df = load_panel()
    assert len(df) > 1000
    assert "year" in df.columns
    assert df["year"].min() >= 2005
    assert df["year"].max() <= 2023


def test_provincial_climate_summary():
    s = provincial_climate_summary()
    assert "temperature" in s.columns
    assert "rainfall" in s.columns
    assert "pm25" in s.columns
    # PM2.5 around 24-29 ug/m3 historically.
    assert 20 < s["pm25"].mean() < 35


def test_sectoral_shares_sum_to_one():
    df = load_sectoral_shares()
    for col in df.columns:
        if "Share" in col:
            assert abs(df[col].sum() - 1.0) < 0.05, f"{col} does not sum to 1"


def test_damage_block_loads():
    df = load_damage_function_block("TFP")
    assert len(df) > 100
    assert {"sector", "region", "hazard"} <= set(df.columns)
    # All 6 hazards should be represented.
    assert df["hazard"].nunique() >= 5
