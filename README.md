# Jegadeesh & Titman (1993) Momentum Replication

Replication of:

> Jegadeesh, N., & Titman, S. (1993). *Returns to Buying Winners and Selling
> Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65–91.

## What this project does

This project reconstructs the relative-strength (momentum) strategy on CRSP common
stocks, **2000–2025**: rank stocks on their past *J*-month compounded return, buy the top
decile of past winners, sell the bottom decile of past losers, and hold for *K* months.
It replicates **Tables 1–3** of the paper and adds one independent extension — whether
momentum profitability differs across firm size.

## Method (in brief)

- **Formation.** At the end of each month *t*, rank stocks on their compounded return
  over the past *J* months, *J* ∈ {3, 6, 9, 12}.
- **Portfolios.** Ten equal-weighted deciles, P1 (losers) … P10 (winners).
- **Holding.** Hold for *K* months, *K* ∈ {3, 6, 9, 12}, with overlapping sub-portfolios
  (1/*K* re-formed each month).
- **Skip month (Table 3).** Insert a one-month gap between formation and holding to rule
  out bid–ask bounce.
- **Inference.** Returns are raw (not excess), and Newey–West *t*-statistics with *K*−1
  lags account for the overlap-induced autocorrelation.

## Results at a glance

| Result | Value |
|---|---|
| P10 − P1, *J*=6, *K*=6 (Table 1) | **+0.52%/mo** (*t* = 1.10) |
| P10 − P1 with a one-month skip (Table 3) | **+0.65%/mo** (*t* = 1.38) |
| Momentum by size, NYSE breakpoints (Table 5) | Small 0.48 / Mid 0.65 / Large 0.50 %/mo |
| Cumulative P10 − P1, 2000–2025 | 0.94 (flat, due to momentum crashes) |

Decile returns rise monotonically from losers (P1) to winners (P10), as in the paper, but
the spread is weaker than the original ≈1%/mo — consistent with the well-documented
post-2000 decay of momentum. The extension shows momentum survives in all size groups but
is weakest among micro-caps; the cumulative payoff is periodically wiped out by
**momentum crashes** (Jan 2001 −78%, 2009), a small-cap phenomenon (Daniel & Moskowitz,
2016).

## Repository layout

```
.
├── README.md                # this file
├── report.pdf               # final research report (draft currently in report/)
├── AI_USE_DISCLOSURE.md     # how AI was used at each stage
├── config.py                # single source of truth for paths & settings
├── requirements.txt         # pinned Python dependencies
├── code/
│   ├── run_all.py           # regenerate ALL tables and figures in one command
│   ├── 00_profile_data.py   # raw-data diagnostics (optional, prints only)
│   ├── 01_build_panel.py    # raw CRSP -> clean monthly panel
│   ├── 02_momentum.py       # Tables 1 & 2 (deciles, J×K WML)
│   ├── 03_skip.py           # Table 3 (one-month skip)
│   ├── 04_size.py           # extension: equal-count size terciles
│   ├── 05_size_nyse.py      # extension: NYSE size breakpoints
│   └── 06_figures.py        # five report figures
├── data/
│   ├── raw/                 # original input (placeholder; licensed, not committed)
│   └── processed/           # intermediate panel & strategy results (committed)
├── outputs/
│   ├── tables/              # final tables (.csv)
│   └── figures/             # final figures (.png)
└── skills/
    └── SKILL.md             # reusable skill for regenerating the main outputs
```

## Data

The original CRSP files are **licensed** and therefore **not committed**. The
submission's `data/raw/` is a placeholder (see `data/raw/README.md`) that documents where
the files belong. The intermediate panel and strategy results in `data/processed/` are
committed, so the tables and figures can be reproduced without access to the raw files.

## Environment

- Python 3.14. Install dependencies with `py -m pip install -r requirements.txt`.
- Pinned: `pandas==3.0.6`, `numpy==2.5.3`, `matplotlib==3.11.2`, `pyarrow==25.0.1`.

## How to reproduce

**One command, from the repository root:**

```bash
python code/run_all.py        # or:  py code/run_all.py
```

This runs the pipeline in order and regenerates every table in `outputs/tables/` and
every figure in `outputs/figures/`. Step `01` skips the raw → panel build when
`data/processed/monthly_panel.parquet` already exists, so the pipeline works with or
without the licensed raw files.

To reproduce from the original data, download the CRSP files, place them at the location
given in `config.py` (or set the `RAW_DATA_DIR` environment variable), and re-run the
command above.

### What each script does

| Script | What it does |
|---|---|
| `00_profile_data.py` | Summarises the raw monthly/daily files (prints only; not part of `run_all.py`). |
| `01_build_panel.py` | Applies the universe screens (exchanges N/A/Q, `EQTY`, `NS`, non-null returns) → `data/processed/monthly_panel.parquet`. |
| `02_momentum.py` | Momentum engine: past-*J* compounded returns, decile ranks, overlapping *K*-month returns, Newey–West *t*-stats → Tables 1–2. |
| `03_skip.py` | Re-runs the engine with a one-month skip between formation and holding (Table 3). |
| `04_size.py` | Extension: equal-count size terciles × momentum (Table 4). |
| `05_size_nyse.py` | Extension (revised): NYSE 30th/70th market-cap terciles × momentum (Table 5). |
| `06_figures.py` | Renders the five report figures from the computed tables. |

## The extension

The independent extension studies **momentum across firm size**. A naive equal-count
tercile split (`04_size.py`) wrongly suggests small-firm momentum is weakest — the
problem is that CRSP is dominated by micro-caps, so an equal-count "Small" group is
mostly micro-caps whose bid–ask bounce contaminates formation-period returns. Re-grouping
by NYSE market-capitalisation breakpoints (`05_size_nyse.py`) shows momentum present in
all size groups and weakest only at the micro-cap tail. Both versions are kept in the
output so the "found a problem → re-grouped" process is visible in the results.

## Reusable skill

A reusable Claude Code skill that documents this same workflow is in `skills/SKILL.md`.
