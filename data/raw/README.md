# data/raw — original input data (NOT committed)

The original CRSP files used by this project are **licensed** and are therefore
**not** stored in this repository. This directory is a placeholder that mirrors where
they would live.

## What belongs here

| File | Used by | Notes |
|---|---|---|
| `02_Monthly_Stocks_and_Factors/data/monthly_stock.csv` | `code/01_build_panel.py` | Required for the tables and figures |
| `03_Daily_Stocks/data/daily_stock.csv` | `code/00_profile_data.py` | Optional (profiling only) |
| `02_Monthly_Stocks_and_Factors/data/F-F factors and RF.csv` | `code/00_profile_data.py` | Optional (profiling only) |

## How to reproduce with the original data

1. Download the files above from WRDS (CRSP / Fama-French).
2. Place them here under the structure shown above, **or** keep them elsewhere and
   point `RAW_DATA_DIR` at that location (via the environment variable of the same
   name, or by editing `config.py`).
3. Run `python code/run_all.py` from the repository root.

Without the raw files, the analysis can still be reproduced from the committed
intermediate panel in `data/processed/` (see the repository README).
