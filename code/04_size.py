"""Step 04 - Extension: momentum by firm size.

Does the momentum premium differ across firm-size groups? Each month we sort
stocks into three equal-count market-capitalisation terciles (Small / Mid /
Large), then *within* each tercile rank on the trailing J-month compounded
return to form deciles and hold for K months (overlapping). Winner-minus-loser
(P10-P1) is then compared across the three size groups.

Both the size grouping and the momentum ranking are measured at the formation
month, so a portfolio's size membership is fixed at formation (consistent with
the overlapping-portfolio convention used in Steps 02-03).

Outputs:
  data/processed/momentum_by_size.parquet  -- tidy (size, month, J, K, decile, ret)
  outputs/tables/table4_size_deciles.csv -- J=6,K=6 WML by size group (Table 4a)
  outputs/tables/table4_size_jk.csv      -- J x K WML for Small and Large (Table 4b)
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


def size_terciles(cap: np.ndarray) -> np.ndarray:
    """Assign each stock a size tercile (0=Small .. 2=Large) per month.

    Groups are equal-count terciles of market capitalisation among stocks with a
    valid cap in that month.
    """
    T, S = cap.shape
    G = np.full((T, S), np.nan)
    for m in range(T):
        row = cap[m]
        idx = np.where(np.isfinite(row))[0]
        if idx.size < N_SIZE:
            continue
        order = idx[np.argsort(row[idx], kind="stable")]
        for g, sub in enumerate(np.array_split(order, N_SIZE)):
            G[m, sub] = g
    return G


def decile_ranks_within_size(mom: np.ndarray, G: np.ndarray, g: int) -> np.ndarray:
    """Momentum deciles (0..9) among stocks that are in size tercile ``g``.

    Stocks outside size group ``g`` are left NaN, so the overlapping-return
    routine averages over that size group only.
    """
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


def build_decile_table_by_size(R, cap, months, g: int) -> pd.DataFrame:
    """Tidy decile return series for one size tercile ``g``, across all (J, K)."""
    frames = []
    G = size_terciles(cap)
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
    R, cap, months, permnos = momentum.load_matrices()

    # --- tidy parquet covering all three size groups --------------------------
    frames = []
    for g in range(N_SIZE):
        d = build_decile_table_by_size(R, cap, months, g)
        d["size"] = SIZE_LABELS[g]
        frames.append(d)
    tidy = pd.concat(frames, ignore_index=True)
    tidy.to_parquet(config.DATA_DIR / "momentum_by_size.parquet", index=False)

    # --- Table 4a: J=6, K=6 winner-minus-loser by size group ------------------
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
    t4a = pd.DataFrame(rows)
    t4a.to_csv(config.TABLES_DIR / "table4_size_deciles.csv", index=False)
    print("Table 4a - winner-minus-loser (P10-P1) mean monthly return, %, "
          "J=6, K=6, by size tercile:\n")
    print(t4a.round(3).to_string(index=False))
    print()

    # --- Table 4b: J x K winner-minus-loser for Small vs Large ----------------
    frames = []
    for label in ("Small", "Large"):
        sub = tidy[tidy["size"] == label]
        t = momentum.table2(sub)          # reuses the J x K WML builder
        t["size"] = label
        frames.append(t)
    t4b = pd.concat(frames, ignore_index=True)
    t4b.to_csv(config.TABLES_DIR / "table4_size_jk.csv", index=False)

    for label in ("Small", "Large"):
        sub = t4b[t4b["size"] == label]
        pivot = sub.pivot(index="J", columns="K", values="p10_minus_p1_mean_pct")
        print(f"Table 4b - {label}-cap winner-minus-loser mean monthly return, %:\n")
        print(pivot.round(3).to_string())
        print()

    print("wrote data/processed/momentum_by_size.parquet, "
          "outputs/tables/table4_size_deciles.csv, outputs/tables/table4_size_jk.csv")


if __name__ == "__main__":
    main()
