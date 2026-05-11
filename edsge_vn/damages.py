"""Aggregate damage function combining DICE-2016R quadratic damage and the
sectoral hazard regressions from the calibration workbook.

Given a sectoral block of coefficients
    f(hazard; sector, region) = sum_h [a_h1 * x_h + a_h2 * x_h ** a_h3]
this module computes a national aggregate damage (TFP loss share) by GVA
weights and exposes a `national_damage_share(T, sea_level, drought, cyclone)`
helper used by sensitivity scripts.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from .data_io import load_sectoral_shares, load_damage_function_block


HAZARDS = ("Temperature", "Wind Speed", "Percipitation", "Sea Level", "Drought", "Cyclone")


def coefficients_table() -> pd.DataFrame:
    """Return long-form table with TFP/Labour/Capital coefficients."""
    pieces = [load_damage_function_block(k) for k in ("TFP", "Labour", "Capital")]
    return pd.concat(pieces, ignore_index=True)


def sectoral_damage(hazards: dict[str, float],
                    kind: str = "TFP",
                    region: int = 1) -> pd.DataFrame:
    """Compute damage share per sector for one region given hazard intensities.

    `hazards` is a dict mapping hazard name -> hazard intensity (e.g. T in C).
    Returns a DataFrame with one row per sector and one column per hazard plus
    a `total` column.
    """
    df = coefficients_table()
    df = df[(df["kind"] == kind) & (df["region"] == region)]
    out = []
    for sector_id in range(1, 10):
        row = {"sector": sector_id}
        total = 0.0
        for hazard, x in hazards.items():
            sub = df[(df["sector"] == sector_id) & (df["hazard"] == hazard)]
            if sub.empty:
                row[hazard] = 0.0
                continue
            # Coefficients ordered as linear, quadratic, exponent.
            params = sub.sort_values("param")["value"].values
            if len(params) < 3:
                row[hazard] = 0.0
                continue
            a1, a2, a3 = params[0], params[1], params[2] if params[2] != 0 else 2.0
            damage_h = a1 * x + a2 * (x ** a3)
            row[hazard] = damage_h
            total += damage_h
        row["total"] = total
        out.append(row)
    return pd.DataFrame(out)


def national_damage_share(temperature: float = 1.0,
                           sea_level: float = 0.1,
                           drought: float = 0.05,
                           cyclone: float = 0.05,
                           precipitation: float = 0.0,
                           wind_speed: float = 0.0,
                           kind: str = "TFP") -> float:
    """National-aggregate damage share weighted by sectoral GVA shares."""
    shares = load_sectoral_shares()
    gva = shares["Gross Value Added Shares National Level"]
    weights = gva / gva.sum()
    hazards = {
        "Temperature": temperature,
        "Sea Level": sea_level,
        "Drought": drought,
        "Cyclone": cyclone,
        "Percipitation": precipitation,
        "Wind Speed": wind_speed,
    }
    total = 0.0
    # Average over 6 regions.
    for region in range(1, 7):
        sec_dmg = sectoral_damage(hazards, kind=kind, region=region)
        weighted = (sec_dmg["total"] * weights.values).sum()
        total += weighted / 6.0
    return float(total)
