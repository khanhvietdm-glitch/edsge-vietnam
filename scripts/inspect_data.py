"""Quick inspection of the two data workbooks shipped with the repo.

Prints variable lists, sample sizes, and head of every sheet for the
provincial panel and sectoral calibration files.

Usage:
    python scripts/inspect_data.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from edsge_vn.data_io import (
    load_panel, load_panel_variables, provincial_climate_summary,
    load_sectoral_shares, load_damage_function_block, sectoral_damage_summary,
)


def main():
    print("=" * 70)
    print("Provincial panel  (data/panel_63provinces_2005_2023.xlsx)")
    print("=" * 70)
    panel = load_panel()
    print(f"Shape: {panel.shape}")
    print(f"Years: {panel['year'].min()} - {panel['year'].max()}")
    print(f"Provinces: {panel['tinh'].nunique()}")
    print(f"First 5 columns: {list(panel.columns[:10])}")

    vars_df = load_panel_variables()
    print(f"\nVariable dictionary: {len(vars_df)} variables (showing first 15)")
    print(vars_df.head(15).to_string())

    summary = provincial_climate_summary()
    print("\nTable B1 (provincial climate summary):")
    print(summary.to_string())

    print("\n" + "=" * 70)
    print("Sectoral calibration  (data/calibration_9sec_6reg.xlsx)")
    print("=" * 70)
    shares = load_sectoral_shares()
    print("Sectoral shares:")
    print(shares.to_string(index=False))

    print("\nSectoral damage-function aggregates:")
    print(sectoral_damage_summary().to_string())

    print("\nLabour damage block for sector 1, region 1 (first 12 coefficients):")
    df = load_damage_function_block("Labour")
    print(df[(df["sector"] == 1) & (df["region"] == 1)].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
