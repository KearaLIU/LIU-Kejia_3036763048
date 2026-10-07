# ENCO6067 Individual Project — Jegadeesh & Titman (1993) Momentum Replication

Replication of

> Jegadeesh, N., & Titman, S. (1993). *Returns to Buying Winners and Selling
> Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65–91.

**Core task.** Reconstruct the relative-strength (momentum) strategy — rank stocks on
past *J*-month returns, buy past winners, sell past losers, hold for *K* months — and
replicate **Tables 1–3** of the paper on CRSP data, default sample period **2000–2025**,
plus one independent extension.

## Repository layout

```
ECON6067/
├── config.py              # single source of truth for paths & settings
├── requirements.txt       # pinned Python dependencies
├── README.md              # this file
├── code/                  # analysis scripts (run in numbered order)
├── data/                  # processed / intermediate data (gitignored, regenerated)
├── output/                # final tables & figures (tracked)
└── report/                # empirical report (tracked)
```

## Raw data (NOT in this repository)

Restricted CRSP data is **not** committed. It lives in a sibling folder, one level up
from this repo:

```
../raw data/
├── 02_Monthly_Stocks_and_Factors/data/
│   ├── monthly_stock.csv          # monthly CRSP stock file (PERMNO, MthRet, MthCap, …)
│   └── F-F factors and RF.csv     # Fama-French factors + risk-free rate
└── 03_Daily_Stocks/data/
    └── daily_stock.csv            # daily CRSP stock file (PERMNO, DlyRet, DlyCap, …)
```

The path is configured in `config.py` (`RAW_DATA_DIR`, default `../raw data`). To run the
workflow on a different machine:

1. Clone this repository.
2. Place the downloaded `02_Monthly_Stocks_and_Factors/` and `03_Daily_Stocks/` folders
   in a `raw data/` folder next to the repo **or** set the environment variable
   `RAW_DATA_DIR` to the folder that contains them.

## Environment

- Python 3.14 (`py` launcher). Install dependencies with `py -m pip install -r requirements.txt`.
- Data access terms apply; do not redistribute the raw files.

## How to reproduce

```bash
py code/00_profile_data.py            # inspect data coverage & quality
# ... subsequent steps (build panel -> momentum portfolios -> tables/figures)
```

Run the scripts in the numbered order shown in `code/`. They write processed data to
`data/` and final tables/figures to `output/`.
