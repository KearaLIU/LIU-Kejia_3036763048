# ENCO6067 Individual Project — Jegadeesh & Titman (1993) Momentum Replication

Replication of

> Jegadeesh, N., & Titman, S. (1993). *Returns to Buying Winners and Selling
> Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65–91.

**Core task.** Reconstruct the relative-strength (momentum) strategy — rank stocks on
past *J*-month returns, buy past winners, sell past losers, hold for *K* months — and
replicate **Tables 1–3** of the paper on CRSP data, sample period **2000–2025**, plus one
independent extension.

## Results at a glance

| Result | Value |
|---|---|
| P10 − P1, *J*=6, *K*=6 (Table 1) | **+0.52%/mo** (*t* = 1.10) |
| P10 − P1 with a one-month skip (Table 3) | **+0.65%/mo** (*t* = 1.38) |
| Momentum by size, NYSE breakpoints (Table 5) | Small 0.48 / Mid 0.65 / Large 0.50 %/mo |
| Cumulative P10 − P1, 2000–2025 | 0.94 (flat, due to momentum crashes) |

Decile returns rise monotonically from losers (P1) to winners (P10), as in the paper,
but the spread is weaker than the original ≈1%/mo — consistent with the well-documented
post-2000 decay of momentum. The extension shows momentum survives in all size groups
but is weakest among micro-caps; the cumulative payoff is periodically wiped out by
**momentum crashes** (Jan 2001 −78%, 2009), a small-cap phenomenon (Daniel & Moskowitz,
2016).

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

## Data prerequisites

The final results are already committed in `output/` (tables and figures), so the
reported numbers can be verified without any data. To **re-run** the pipeline from
scratch you need the restricted CRSP source files, which are licensed and therefore not
distributed in this repository. Download them from WRDS and place them one level above
the repo (or point `RAW_DATA_DIR` at them):

```
../raw data/
├── 02_Monthly_Stocks_and_Factors/data/
│   ├── monthly_stock.csv          # monthly CRSP stock file (PERMNO, MthRet, MthCap, …)
│   └── F-F factors and RF.csv     # Fama-French factors + risk-free rate
└── 03_Daily_Stocks/data/
    └── daily_stock.csv            # daily CRSP stock file (PERMNO, DlyRet, DlyCap, …)
```

Only `monthly_stock.csv` is required for the tables and figures; the daily file and the
Fama-French factors are used only by the profiling step (`00_profile_data.py`). The
location is configured in `config.py` via `RAW_DATA_DIR` (default `../raw data`).

## Environment

- Python 3.14 (`py` launcher). Install dependencies with
  `py -m pip install -r requirements.txt`.
- Pinned: `pandas==3.0.6`, `numpy==2.5.3`, `matplotlib==3.11.2`, `pyarrow==25.0.1`.
- Data-access terms apply; do not redistribute the raw files.

## How to reproduce

Run the scripts in numbered order from the repo root. Each writes processed data to
`data/` and final tables/figures to `output/`.

```bash
py code/00_profile_data.py    # inspect raw data coverage & quality (prints only)
py code/01_build_panel.py    # build the filtered monthly panel   -> data/monthly_panel.parquet
py code/02_momentum.py       # Tables 1 & 2 (deciles, JxK WML)    -> output/table1_deciles.csv, table2_jk.csv
py code/03_skip.py           # Table 3 (one-month skip)           -> output/table3_deciles.csv, table3_jk.csv
py code/04_size.py           # extension: equal-count terciles    -> output/table4_size_*.csv
py code/05_size_nyse.py      # extension: NYSE size breakpoints   -> output/table5_size_*.csv
py code/06_figures.py        # five report figures                -> output/fig1..fig5.png
```

| Script | What it does |
|---|---|
| `00_profile_data.py` | Summarises the raw monthly/daily files: row counts, date range, missingness, return distribution. |
| `01_build_panel.py` | Applies the universe screens (exchanges N/A/Q, `EQTY`, `NS`, non-null returns) and writes `data/monthly_panel.parquet`. |
| `02_momentum.py` | Momentum engine: past-*J* compounded returns, decile ranks, overlapping *K*-month returns, Newey–West *t*-stats; writes Tables 1–2. |
| `03_skip.py` | Re-runs the engine with a one-month skip between formation and holding (Table 3). |
| `04_size.py` | Extension: splits stocks into equal-count size terciles and runs momentum within each (Table 4). |
| `05_size_nyse.py` | Extension (revised): size terciles from NYSE 30th/70th market-cap percentiles (Table 5). |
| `06_figures.py` | Renders the five report figures from the computed tables. |

## The extension

The independent extension studies **momentum across firm size**. A naive equal-count
tercile split (`04_size.py`) wrongly suggests small-firm momentum is weakest — the
problem is that CRSP is dominated by micro-caps, so an equal-count "Small" group is
mostly micro-caps whose bid–ask bounce contaminates formation-period returns. Re-grouping
by NYSE market-capitalisation breakpoints (`05_size_nyse.py`) shows momentum present in
all size groups and weakest only at the micro-cap tail. Both versions are kept in the
output so the "found a problem → re-grouped" process is visible in the results.
