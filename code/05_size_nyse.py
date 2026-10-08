"""Step 05 - Extension (revised): momentum by firm size, NYSE breakpoints.

Step 04 split stocks into three *equal-count* market-capitalisation terciles.
That is not the standard size definition: CRSP is heavily small-cap, so an
equal-count "Small" tercile is dominated by micro-caps whose bid-ask bounce
contaminates the formation-period returns. The standard Fama-French approach
instead defines size groups by NYSE market-capitalisation breakpoints (30th and
70th percentiles), then applies those breakpoints to *all* stocks.

This step re-runs the size-conditional momentum with NYSE breakpoints and writes
its results to NEW files (table5_*), leaving the Step 04 equal-count results
(table4_*) intact so the two definitions can be compared.

Outputs:
  data/momentum_by_size_nyse.parquet  -- tidy (size, month, J, K, decile, ret)
  output/table5_size_deciles.csv      -- J=6,K=6 WML by NYSE size group (Table 5a)
  output/table5_size_jk.csv           -- J x K WML for Small and Large (Table 5b)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "momentum", Path(__file__).resolve().parent / "02_momentum.py"
)
momentum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(momentum)

N_DECILES = config.N_DECILES
N_SIZE = 3
SIZE_LABELS = {0: "Small", 1: "Mid", 2: "Large"}
NYSE_PCT = (30.0, 70.0)  # Fama-French 3-way size breakpoints (NYSE cap percentiles)


def load_with_exchange():
    """Load the monthly panel and return dense matrices, including the NYSE flag."""
    panel = pd.read_parquet(config.DATA_DIR / "monthly_panel.parquet")
    months = np.unique(panel["MthCalDt"].to_numpy())
    permnos = np.unique(panel["PERMNO"].to_numpy())
    month_code = pd.Categorical(panel["MthCalDt"], categories=months, ordered=True).codes
    permno_code = pd.Categorical(panel["PERMNO"], categories=permnos, ordered=True).codes

    T, S = len(months), len(permnos)
    R = np.full((T, S), np.nan)
    R[month_code, permno_code] = panel["MthRet"].to_numpy(dtype=np.float64)
    cap = np.full((T, S), np.nan)
    cap[month_code, permno_code] = panel["MthCap"].to_numpy(dtype=np.float64)
    is_nyse = np.zeros((T, S), dtype=bool)
    is_nyse[month_code, permno_code] = (panel["PrimaryExch"].to_numpy() == "N")
    return R, cap, is_nyse, months, permnos


def size_groups_nyse(cap: np.ndarray, is_nyse: np.ndarray,
                     pct: tuple = NYSE_PCT) -> np.ndarray:
    """Size terciles from NYSE market-cap breakpoints applied to all stocks.

    Each month, the low/high breakpoints are the ``pct`` percentiles of market
    capitalisation among NYSE-listed stocks; every stock is then assigned
    Small / Mid / Large by comparing its own cap to those breakpoints.
    """
    lo_pct, hi_pct = pct
    T, S = cap.shape
    G = np.full((T, S), np.nan)
    for m in range(T):
        nyse_cap = cap[m][is_nyse[m]]
        nyse_cap = nyse_cap[np.isfinite(nyse_cap)]
        if nyse_cap.size < 10:
            continue
        lo, hi = np.percentile(nyse_cap, [lo_pct, hi_pct])
        row = cap[m]
        G[m][row <= lo] = 0
        G[m][(row > lo) & (row <= hi)] = 1
        G[m][row > hi] = 2
    return G


def decile_ranks_within_size(mom: np.ndarray, G: np.ndarray, g: int) -> np.ndarray:
    """Momentum deciles (0..9) among stocks that are in size group ``g``."""
    T, S = mom.shape
    D = np.full((T, S), np.nan)
    for m in range(T):
        row = mom[m]
        idx = np.where((G[m] == g) & ~np.isnan(row))[0]
        if idx.size < N_DECILES:
            continue
        order = idx[np.argsort(row[idx], kind="stable")]
        for d, sub in enumerate(np.array_split(order, N_DECILES)):
            D[m, sub] = d
    return D


def build_decile_table_by_size(R, months, G, g: int) -> pd.DataFrame:
    """Tidy decile return series for one size group ``g``, across all (J, K)."""
    frames = []
    for J in config.J_VALUES:
        mom = momentum.past_return(R, J)
        D = decile_ranks_within_size(mom, G, g)
        for K in config.K_VALUES:
            ret = momentum.overlapping_decile_returns(R, D, K)
            for d in range(N_DECILES):
                series = ret[d]
                valid = np.isfinite(series)
                frames.append(pd.DataFrame({
                    "month": months[valid],
                    "J": J,
                    "K": K,
                    "decile": d + 1,
                    "ret": series[valid],
                }))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    config.ensure_dirs()
    R, cap, is_nyse, months, permnos = load_with_exchange()
    G = size_groups_nyse(cap, is_nyse)

    nyse_stocks_per_month = is_nyse.sum(axis=1)
    print(f"NYSE stocks per month: {nyse_stocks_per_month.mean():.0f} mean "
          f"(min {nyse_stocks_per_month.min()}, max {nyse_stocks_per_month.max()})")

    # --- tidy parquet covering all three size groups --------------------------
    frames = []
    for g in range(N_SIZE):
        d = build_decile_table_by_size(R, months, G, g)
        d["size"] = SIZE_LABELS[g]
        frames.append(d)
    tidy = pd.concat(frames, ignore_index=True)
    tidy.to_parquet(config.DATA_DIR / "momentum_by_size_nyse.parquet", index=False)

    # --- Table 5a: J=6, K=6 winner-minus-loser by NYSE size group -------------
    rows = []
    for g in range(N_SIZE):
        sub = tidy[(tidy["size"] == SIZE_LABELS[g])
                   & (tidy["J"] == 6) & (tidy["K"] == 6)]
        wide = sub.pivot(index="month", columns="decile", values="ret").sort_index()
        wml = (wide[10] - wide[1]).dropna()
        rows.append({
            "size": SIZE_LABELS[g],
            "wml_mean_pct": wml.mean() * 100.0,
            "tstat_nw": momentum.newey_west_tstat(wml.to_numpy(), lags=5),
            "n_months": len(wml),
        })
    t5a = pd.DataFrame(rows)
    t5a.to_csv(config.OUTPUT_DIR / "table5_size_deciles.csv", index=False)
    print("\nTable 5a - winner-minus-loser (P10-P1) mean monthly return, %, "
          "J=6, K=6, by NYSE size breakpoint:\n")
    print(t5a.round(3).to_string(index=False))
    print()

    # --- Table 5b: J x K winner-minus-loser for Small vs Large ----------------
    frames = []
    for label in ("Small", "Large"):
        sub = tidy[tidy["size"] == label]
        t = momentum.table2(sub)
        t["size"] = label
        frames.append(t)
    t5b = pd.concat(frames, ignore_index=True)
    t5b.to_csv(config.OUTPUT_DIR / "table5_size_jk.csv", index=False)

    for label in ("Small", "Large"):
        sub = t5b[t5b["size"] == label]
        pivot = sub.pivot(index="J", columns="K", values="p10_minus_p1_mean_pct")
        print(f"Table 5b - {label}-cap (NYSE breakpoint) winner-minus-loser "
              f"mean monthly return, %:\n")
        print(pivot.round(3).to_string())
        print()

    print("wrote data/momentum_by_size_nyse.parquet, "
          "output/table5_size_deciles.csv, output/table5_size_jk.csv")


if __name__ == "__main__":
    main()
