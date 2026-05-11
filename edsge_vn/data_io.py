"""Loaders for the two source Excel workbooks shipped with this repo.

* `data/panel_63provinces_2005_2023.xlsx` -> provincial climate panel
  (Appendix B summary statistics).
* `data/calibration_9sec_6reg.xlsx` -> 9 sector x 6 region sectoral shares
  and damage-function coefficients (DICE-style hazard model).
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


# ----------------------------------------------------------------------
# Provincial panel (63 provinces x 19 years)
# ----------------------------------------------------------------------
def load_panel() -> pd.DataFrame:
    """Return the cleaned 63 provinces x 2005-2023 climate panel."""
    src = DATA_DIR / "panel_63provinces_2005_2023.xlsx"
    df = pd.read_excel(src, sheet_name="Data")
    df = df.dropna(subset=["year", "tinh"]).copy()
    df["year"] = df["year"].astype(int)
    return df


def load_panel_variables() -> pd.DataFrame:
    """Variable dictionary of the panel."""
    src = DATA_DIR / "panel_63provinces_2005_2023.xlsx"
    df = pd.read_excel(src, sheet_name="Variables", header=1)
    return df


def provincial_climate_summary() -> pd.DataFrame:
    """Compute Table B1 of the paper (provincial annual cross-sectional means).

    Columns: temperature (nhietdo), rainfall (luongmua), PM2.5 (pm25),
             life expectancy, poverty rate (tyle_ngheo).
    """
    df = load_panel()
    yearly = df.groupby("year").agg(
        temperature=("nhietdo", "mean"),
        rainfall=("luongmua", "mean"),
        pm25=("pm25", "mean"),
        life_expectancy=("life_expectancy", "mean"),
        poverty_rate=("tyle_ngheo", "mean"),
    )
    yearly = yearly.dropna()
    return yearly.round(2)


# ----------------------------------------------------------------------
# Sectoral calibration (9 sectors x 6 regions)
# ----------------------------------------------------------------------
SECTOR_NAMES = [
    "Agriculture, forestry, fishing",
    "Mining and quarrying",
    "Manufacturing",
    "Electricity, gas, steam",
    "Water supply, sewerage, waste",
    "Construction",
    "Wholesale and retail trade",
    "Transportation and storage",
    "Other services",
]


def load_sectoral_shares() -> pd.DataFrame:
    """Return sectoral GVA, employment and labour-cost shares."""
    src = DATA_DIR / "calibration_9sec_6reg.xlsx"
    raw = pd.read_excel(src, sheet_name="Data", header=None)
    # The sheet repeats blocks of (header, 9 sector rows). We parse the first
    # three meaningful blocks: GVA shares, employment shares, labour shares.
    blocks = {}
    cur_label = None
    cur_rows = []
    for _, row in raw.iterrows():
        a, b = row[0], row[1]
        if pd.isna(a) and pd.isna(b):
            continue
        if str(a).strip().lower() == "sector" and isinstance(b, str):
            if cur_label is not None and cur_rows:
                blocks[cur_label] = cur_rows
            cur_label = b
            cur_rows = []
        else:
            try:
                idx = int(float(a))
                val = float(b)
                cur_rows.append((idx, val))
            except (ValueError, TypeError):
                continue
    if cur_label is not None and cur_rows:
        blocks[cur_label] = cur_rows

    # Convert to DataFrame indexed by sector.
    df = pd.DataFrame({"sector_id": range(1, 10), "sector": SECTOR_NAMES})
    for label, rows in blocks.items():
        col = {idx: v for idx, v in rows}
        df[label] = [col.get(i, np.nan) for i in df["sector_id"]]
    return df


def load_damage_function_block(kind: str) -> pd.DataFrame:
    """Load one of the damage-function sheets.

    `kind` is "TFP", "Labour", or "Capital". Returns a long-form DataFrame
    keyed by (sector_id, region_id, hazard, coef_type) with coefficient value.
    """
    sheet = f"Damage Functions {kind}"
    src = DATA_DIR / "calibration_9sec_6reg.xlsx"
    raw = pd.read_excel(src, sheet_name=sheet, header=None)
    records = []
    cur_sector = cur_region = None
    cur_hazard = None
    for _, row in raw.iterrows():
        a, b = row[0], row[1]
        # sector x region header.
        if isinstance(a, str) and a.lower().startswith("sector"):
            parts = a.lower().replace("sector", "").replace("and", "").replace("region", "").split()
            try:
                cur_sector = int(parts[0]); cur_region = int(parts[1])
            except (IndexError, ValueError):
                cur_sector = cur_region = None
            cur_hazard = None
            continue
        # Hazard header rows.
        if isinstance(a, str) and a in (
            "Temperature", "Wind Speed", "Percipitation",
            "Sea Level", "Drought", "Cyclone",
        ):
            cur_hazard = a
            continue
        # Coefficient rows.
        if isinstance(a, str) and "_" in a and cur_sector and cur_hazard:
            try:
                value = float(b)
            except (ValueError, TypeError):
                continue
            coef_type = a.split("_")[-2] if "_" in a else ""
            records.append({
                "kind": kind,
                "sector": cur_sector,
                "region": cur_region,
                "hazard": cur_hazard,
                "param": a,
                "value": value,
            })
    return pd.DataFrame(records)


def sectoral_damage_summary() -> pd.DataFrame:
    """Aggregate sectoral damage coefficients across regions for each hazard."""
    pieces = []
    for kind in ("TFP", "Labour", "Capital"):
        df = load_damage_function_block(kind)
        pieces.append(df)
    long = pd.concat(pieces, ignore_index=True)
    agg = long.groupby(["kind", "hazard"])["value"].agg(["mean", "max", "count"])
    return agg.round(4)
