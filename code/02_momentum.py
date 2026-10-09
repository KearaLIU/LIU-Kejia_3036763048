"""Step 02 — Momentum strategy (Jegadeesh & Titman, 1993).

Implements the overlapping relative-strength strategy:

  1. Each month, rank stocks by their trailing J-month compounded return.
  2. Form equal-weighted decile portfolios (P1 losers ... P10 winners).
  3. Hold each portfolio for K months, rolling over 1/K of it every month.
  4. The month-t strategy return is the equal-weighted average of the K
     portfolios formed in months t-K .. t-1.

Convention (documented): a portfolio formed at month t ranks on the compound
return over months [t-J+1 .. t] and is held over months [t+1 .. t+K]. There is
no skip month in the base case (Table 3 will add the skip).

Data handling:
  - Returns are floored at -0.999 only for the formation-period compounding, so
    that delisting-return artifacts below -100% do not produce non-positive gross
    returns (the raw returns are unchanged for holding-period returns).
  - A stock is ranked only if it has a return in every formation month; a stock
    is averaged into a holding-month portfolio only if it has a return that month.

Outputs:
  data/processed/momentum_deciles.parquet  -- tidy decile return series (month, J, K, decile, ret)
  outputs/tables/table1_deciles.csv      -- J=6, K=6 decile means + t-stats (Table 1)
  outputs/tables/table2_jk.csv           -- J x K winner-minus-loser means + t-stats (Table 2)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

N_DECILES = config.N_DECILES


def load_matrices():
    """Load the monthly panel and return dense (months x stocks) matrices."""
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
    return R, cap, months, permnos


def past_return(R: np.ndarray, J: int) -> np.ndarray:
    """Trailing J-month compounded return ending at each month.

    Returns a (T, S) array; NaN where the window spans fewer than J valid months.
    """
    Rc = np.clip(R, -0.999, None)          # floor below -100% (delisting artifacts)
    valid = ~np.isnan(Rc)
    X = np.where(valid, 1.0 + Rc, 1.0)     # gross returns; missing treated as 1 (no-op)
    cum = np.cumprod(X, axis=0)
    cum_prev = np.vstack([np.ones((1, R.shape[1])), cum[:-1]])  # cum_prev[m] = cum[m-1]

    miss = np.cumsum((~valid).astype(np.int64), axis=0)
    miss_prev = np.vstack([np.zeros((1, R.shape[1]), dtype=np.int64), miss[:-1]])

    mom = np.full_like(R, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        mom[J - 1:] = (cum[J - 1:] / cum_prev[: R.shape[0] - J + 1]) - 1.0

    window_miss = miss[J - 1:] - miss_prev[: R.shape[0] - J + 1]
    mom[J - 1:][window_miss > 0] = np.nan
    return mom


def decile_ranks(mom: np.ndarray, n_deciles: int = N_DECILES) -> np.ndarray:
    """Assign each stock a decile (0..n_deciles-1) per formation month."""
    T, S = mom.shape
    D = np.full((T, S), np.nan)
    for m in range(T):
        row = mom[m]
        idx = np.where(~np.isnan(row))[0]
        if idx.size < n_deciles:
            continue
        order = idx[np.argsort(row[idx], kind="stable")]
        for d, sub in enumerate(np.array_split(order, n_deciles)):
            D[m, sub] = d
    return D


def overlapping_decile_returns(R: np.ndarray, D: np.ndarray, K: int,
                               n_deciles: int = N_DECILES,
                               skip: int = 0) -> np.ndarray:
    """Overlapping equal-weighted decile return series, shape (n_deciles, T).

    ret[d, m] = mean over h in 1..K of the month-m return of the portfolio that
    was formed in month m - (h + skip). ``skip`` inserts that many idle months
    between the end of the formation period and the start of the holding period
    (skip=1 reproduces the paper's Table 3 one-week lag at monthly frequency).
    """
    T, S = R.shape
    ret_sum = np.zeros((n_deciles, T))
    ret_cnt = np.zeros((n_deciles, T))
    for h in range(1, K + 1):
        lag = h + skip
        D_shift = np.full((T, S), np.nan)
        D_shift[lag:] = D[: T - lag]
        for m in range(lag, T):
            g = D_shift[m]
            valid = ~np.isnan(g)
            if not valid.any():
                continue
            gg = g[valid].astype(np.int64)
            rr = R[m, valid]
            finite = np.isfinite(rr)
            rr0 = np.where(finite, rr, 0.0)
            # Average only over finite returns: a NaN return must not poison the
            # bin sum (np.bincount sets a bin to NaN if any weight is NaN), and the
            # denominator must be the number of finite returns, not of stocks.
            ret_sum[:, m] += np.bincount(gg, weights=rr0, minlength=n_deciles)
            ret_cnt[:, m] += np.bincount(gg, weights=finite.astype(np.float64),
                                         minlength=n_deciles)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ret_sum / ret_cnt


def newey_west_tstat(x, lags: int) -> float:
    """Newey-West t-statistic with Bartlett weights (lags = K-1 for overlap)."""
    x = np.asarray(x, dtype=np.float64)
    x = x[~np.isnan(x)]
    n = x.size
    if n < 2:
        return np.nan
    resid = x - x.mean()
    var = np.dot(resid, resid) / n
    for lag in range(1, int(lags) + 1):
        var += 2.0 * (1.0 - lag / (lags + 1.0)) * np.dot(resid[lag:], resid[:-lag]) / n
    se = np.sqrt(var / n)
    return float(x.mean() / se) if se > 0 else np.nan


def build_decile_table(R: np.ndarray, months: np.ndarray,
                       skip: int = 0) -> pd.DataFrame:
    """Compute the tidy decile return series for every (J, K)."""
    frames = []
    for J in config.J_VALUES:
        mom = past_return(R, J)
        D = decile_ranks(mom)
        for K in config.K_VALUES:
            ret = overlapping_decile_returns(R, D, K, skip=skip)
            for d in range(N_DECILES):
                series = ret[d]
                valid = np.isfinite(series)
                frames.append(pd.DataFrame({
                    "month": months[valid],
                    "J": J,
                    "K": K,
                    "decile": d + 1,          # 1 = P1 (losers) ... 10 = P10 (winners)
                    "ret": series[valid],
                }))
    return pd.concat(frames, ignore_index=True)


def table1(dec: pd.DataFrame) -> pd.DataFrame:
    """Table 1 analogue: J=6, K=6 decile means and Newey-West t-stats."""
    sub = dec[(dec["J"] == 6) & (dec["K"] == 6)]
    wide = sub.pivot(index="month", columns="decile", values="ret").sort_index()
    out = pd.DataFrame({"mean_ret_pct": wide.mean() * 100.0})
    out["tstat_nw"] = [newey_west_tstat(wide[c].to_numpy(), lags=5) for c in wide.columns]
    wml = wide[10] - wide[1]
    out.loc["P10-P1"] = [wml.mean() * 100.0, newey_west_tstat(wml.to_numpy(), lags=5)]
    out.index.name = "decile"
    return out


def table2(dec: pd.DataFrame) -> pd.DataFrame:
    """Table 2 analogue: winner-minus-loser mean and t-stat for every (J, K)."""
    rows = []
    for J in config.J_VALUES:
        for K in config.K_VALUES:
            sub = dec[(dec["J"] == J) & (dec["K"] == K)]
            wide = sub.pivot(index="month", columns="decile", values="ret")
            wml = (wide[10] - wide[1]).dropna()
            rows.append({
                "J": J, "K": K,
                "p10_minus_p1_mean_pct": wml.mean() * 100.0,
                "tstat_nw": newey_west_tstat(wml.to_numpy(), lags=K - 1),
                "n_months": len(wml),
            })
    return pd.DataFrame(rows)


def main() -> None:
    config.ensure_dirs()
    R, cap, months, permnos = load_matrices()
    print(f"return matrix: {R.shape[0]} months x {R.shape[1]} stocks "
          f"({np.datetime_as_string(months[0], unit='M')} .. "
          f"{np.datetime_as_string(months[-1], unit='M')})\n")

    dec = build_decile_table(R, months)
    dec.to_parquet(config.DATA_DIR / "momentum_deciles.parquet", index=False)

    t1 = table1(dec)
    t1.to_csv(config.TABLES_DIR / "table1_deciles.csv")
    print("Table 1 (J=6, K=6) - equal-weighted decile portfolios, monthly:\n")
    print(t1.round(3).to_string())
    print()

    t2 = table2(dec)
    t2.to_csv(config.TABLES_DIR / "table2_jk.csv", index=False)

    pivot = t2.pivot(index="J", columns="K", values="p10_minus_p1_mean_pct")
    print("Table 2 - winner-minus-loser (P10-P1) mean monthly return, %:\n")
    print(pivot.round(3).to_string())
    print("\n(t-stats in outputs/tables/table2_jk.csv)")
    print(f"\nwrote data/processed/momentum_deciles.parquet, outputs/tables/table1_deciles.csv, outputs/tables/table2_jk.csv")


if __name__ == "__main__":
    main()
