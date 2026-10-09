"""Central configuration: paths, sample period, and analysis settings.

This is the ONLY file that points to the raw data. If your raw data lives
somewhere else, set the RAW_DATA_DIR environment variable (or edit RAW_DATA_DIR
below) — do not hard-code paths in the analysis scripts.

Directory layout follows the submission structure::

    data/raw/        original input data (NOT committed — CRSP is licensed; see README)
    data/processed/  intermediate panel & strategy results (committed, regenerable)
    outputs/tables/  final tables (.csv)
    outputs/figures/ final figures (.png)
    report/          empirical report
"""
from __future__ import annotations

import os
from pathlib import Path

# Repo root = directory that contains this file.
REPO_ROOT = Path(__file__).resolve().parent

# --- Raw data location -------------------------------------------------------
# The original CRSP files live OUTSIDE the repo (licensed, ~28 GB) and are never
# committed. ``data/raw/`` is a documented placeholder in the submission; point
# RAW_DATA_DIR at wherever you keep the files, or set the RAW_DATA_DIR env var.
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

# --- Submission directory structure -------------------------------------------
RAW_INPUT_DIR = REPO_ROOT / "data" / "raw"          # original input (placeholder; not committed)
DATA_DIR = REPO_ROOT / "data" / "processed"         # intermediate panel & strategy results
TABLES_DIR = REPO_ROOT / "outputs" / "tables"       # final tables
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"     # final figures
REPORT_DIR = REPO_ROOT / "report"                   # empirical report

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
    for d in (RAW_INPUT_DIR, DATA_DIR, TABLES_DIR, FIGURES_DIR, REPORT_DIR):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(f"REPO_ROOT       = {REPO_ROOT}")
    print(f"RAW_DATA_DIR    = {RAW_DATA_DIR}")
    print(f"MONTHLY_STOCK   = {MONTHLY_STOCK_CSV}")
    print(f"RAW_INPUT_DIR   = {RAW_INPUT_DIR}")
    print(f"DATA_DIR        = {DATA_DIR}")
    print(f"TABLES_DIR      = {TABLES_DIR}")
    print(f"FIGURES_DIR     = {FIGURES_DIR}")
    print(f"Sample period   = {START_YYYYMM}..{END_YYYYMM}")
