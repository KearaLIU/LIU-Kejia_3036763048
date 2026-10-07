"""Central configuration: paths, sample period, and analysis settings.

This is the ONLY file that points to the raw data. If your raw data lives
somewhere else, set the RAW_DATA_DIR environment variable (or edit RAW_DATA_DIR
below) — do not hard-code paths in the analysis scripts.

Raw data is deliberately kept OUTSIDE this repository (a sibling ``raw data/``
folder) so that restricted CRSP data is never committed to GitHub. See README.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repo root = directory that contains this file.
REPO_ROOT = Path(__file__).resolve().parent

# --- Raw data location -------------------------------------------------------
# Default: a sibling folder "../raw data" relative to the repo root.
RAW_DATA_DIR = Path(
    os.environ.get("RAW_DATA_DIR", REPO_ROOT.parent / "raw data")
).resolve()

MONTHLY_STOCK_CSV = (
    RAW_DATA_DIR / "02_Monthly_Stocks_and_Factors" / "data" / "monthly_stock.csv"
)
DAILY_STOCK_CSV = RAW_DATA_DIR / "03_Daily_Stocks" / "data" / "daily_stock.csv"
FF_FACTORS_CSV = (
    RAW_DATA_DIR / "02_Monthly_Stocks_and_Factors" / "data" / "F-F factors and RF.csv"
)

# --- Derived directories ------------------------------------------------------
DATA_DIR = REPO_ROOT / "data"          # processed / intermediate data (gitignored)
OUTPUT_DIR = REPO_ROOT / "output"      # final tables & figures (tracked)
REPORT_DIR = REPO_ROOT / "report"      # empirical report (tracked)

# --- Sample period (assignment default for capital-market papers) ------------
START_YEAR = 2000
END_YEAR = 2025
START_YYYYMM = START_YEAR * 100 + 1      # 200001
END_YYYYMM = END_YEAR * 100 + 12         # 202512

# --- Momentum strategy parameters (Jegadeesh & Titman, 1993) -----------------
# J = formation (ranking) period in months; K = holding period in months.
J_VALUES = [3, 6, 9, 12]
K_VALUES = [3, 6, 9, 12]
N_DECILES = 10  # P1 = losers ... P10 = winners


def ensure_dirs() -> None:
    """Create the derived output directories if they do not exist yet."""
    for d in (DATA_DIR, OUTPUT_DIR, REPORT_DIR):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(f"REPO_ROOT       = {REPO_ROOT}")
    print(f"RAW_DATA_DIR    = {RAW_DATA_DIR}")
    print(f"MONTHLY_STOCK   = {MONTHLY_STOCK_CSV}")
    print(f"DAILY_STOCK     = {DAILY_STOCK_CSV}")
    print(f"FF_FACTORS      = {FF_FACTORS_CSV}")
    print(f"Sample period   = {START_YYYYMM}..{END_YYYYMM}")
