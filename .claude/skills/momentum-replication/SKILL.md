---
name: momentum-replication
description: Replicate Jegadeesh & Titman (1993) momentum on CRSP monthly data — build the filtered panel, run the decile / J×K / skip-month / size-conditioned analyses, and regenerate Tables 1–3, the size extension, and the five figures. Use when asked to (re)run, extend, or reproduce this momentum project.
---

# Momentum Replication (Jegadeesh & Titman, 1993)

Reusable workflow for reproducing "Returns to Buying Winners and Selling Losers" on
CRSP common stocks. The pipeline turns the raw CRSP monthly stock file into the ten
decile portfolios, the J×K winner-minus-loser grid, the one-month-skip variant, and two
size-conditioned extensions, then renders the five report figures.

## Prerequisites

- The CRSP monthly stock file (`monthly_stock.csv`) from WRDS, placed at the location
  pointed to by `RAW_DATA_DIR` in `config.py` (default `../raw data/`, overridable via
  the `RAW_DATA_DIR` environment variable). No other source file is needed for the
  tables and figures.
- Python 3.14 with the pinned dependencies: `py -m pip install -r requirements.txt`.

## Workflow

Run from the repo root, in numbered order. Each script reads the raw/processed inputs
and writes deterministic outputs to `data/` or `output/`.

| Step | Script | Purpose | Key output |
|---|---|---|---|
| 1 | `py code/01_build_panel.py` | Filter to NYSE/AMEX/Nasdaq common shares (`EQTY`, `NS`) with non-null returns | `data/monthly_panel.parquet` |
| 2 | `py code/02_momentum.py` | Decile portfolios + J×K winner-minus-loser spread, Newey–West t-stats | `output/table1_deciles.csv`, `table2_jk.csv` |
| 3 | `py code/03_skip.py` | Same engine with a one-month skip between formation and holding | `output/table3_deciles.csv`, `table3_jk.csv` |
| 4 | `py code/04_size.py` | Equal-count size terciles × momentum | `output/table4_size_*.csv` |
| 5 | `py code/05_size_nyse.py` | NYSE 30th/70th percentile size terciles × momentum | `output/table5_size_*.csv` |
| 6 | `py code/06_figures.py` | Render the five report figures | `output/fig1..fig5.png` |

`py code/00_profile_data.py` is a read-only sanity check on the raw files (prints only).

## Method notes (preserve when reusing or extending)

- Rank stocks on the past **J-month compound return**, J ∈ {3, 6, 9, 12}; form **ten
  equal-weighted deciles** P1 (losers) … P10 (winners); hold for **K months**,
  K ∈ {3, 6, 9, 12}.
- Portfolios **overlap**: 1/K of each portfolio is re-formed each month, so the month-t
  return averages the K sub-portfolios formed in months t−K, …, t−1.
- Returns are **raw** (not excess), matching the original paper.
- The skip variant shifts holding to months t+2 … t+K+1 to neutralise bid–ask bounce.
- Report **Newey–West t-statistics with K−1 lags** (overlapping returns are
  autocorrelated).
- For the size extension, condition the decile sort on market-cap terciles; prefer the
  **NYSE 30th/70th breakpoints** over an equal-count split (an equal-count "Small" group
  is dominated by micro-caps).

## Changing the sample or reusing

- Sample period, strategy parameters, and paths all live in `config.py`
  (`START_YEAR` / `END_YEAR`, `J_VALUES` / `K_VALUES` / `N_DECILES`, `RAW_DATA_DIR`).
- To re-run on a new period, drop the new CRSP file at `RAW_DATA_DIR`, edit the sample
  years in `config.py`, and re-run the numbered scripts; tables and figures regenerate
  deterministically.
- Known feature (not a bug): the winner-minus-loser payoff is dominated by occasional
  **momentum crashes** (e.g. Jan 2001 ≈ −78%), in which past losers rebound violently
  after a market bottom — see report §6.
