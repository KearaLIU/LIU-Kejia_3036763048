"""Step 00 — Profile the raw data.

Reads the three raw CSVs and prints a coverage / quality summary so that
every data choice downstream is grounded in what the files actually contain.

Usage:
    py code/00_profile_data.py            # monthly stock + FF factors (fast)
    py code/00_profile_data.py --daily    # also scan the 27 GB daily file (slow)
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# Make `config` importable from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def profile_monthly_stock() -> None:
    path = config.MONTHLY_STOCK_CSV
    print("=" * 70)
    print(f"MONTHLY STOCK: {path.name}")
    print("=" * 70)
    cols = [
        "PERMNO", "MthCalDt", "MthRet", "MthRetx", "MthCap",
        "PrimaryExch", "SecurityType", "ShareType", "USIncFlg", "MthDelFlg",
    ]
    dtypes = {"MthRet": "float32", "MthRetx": "float32", "MthCap": "float64"}

    n_rows = 0
    n_ret_nn = n_retx_nn = n_cap_nn = 0
    permnos: set[int] = set()
    in_sample_permnos: set[int] = set()
    in_sample_rows = 0
    d_min = d_max = None
    rets: list[np.ndarray] = []
    exch: Counter = Counter()
    stype: Counter = Counter()
    shtype: Counter = Counter()

    reader = pd.read_csv(
        path, usecols=cols, dtype=dtypes, parse_dates=["MthCalDt"], chunksize=500_000
    )
    for chunk in reader:
        n_rows += len(chunk)
        permnos.update(chunk["PERMNO"].dropna().astype(int).tolist())
        n_ret_nn += int(chunk["MthRet"].notna().sum())
        n_retx_nn += int(chunk["MthRetx"].notna().sum())
        n_cap_nn += int(chunk["MthCap"].notna().sum())
        rets.append(chunk["MthRet"].dropna().to_numpy(dtype="float32"))
        dt = chunk["MthCalDt"]
        lo, hi = dt.min(), dt.max()
        d_min = lo if d_min is None or lo < d_min else d_min
        d_max = hi if d_max is None or hi > d_max else d_max
        for c, counter in [("PrimaryExch", exch), ("SecurityType", stype), ("ShareType", shtype)]:
            counter.update(chunk[c].astype(str).value_counts(dropna=False).to_dict())
        in_ = dt.dt.year.between(config.START_YEAR, config.END_YEAR)
        in_sample_rows += int(in_.sum())
        in_sample_permnos.update(chunk.loc[in_, "PERMNO"].dropna().astype(int).tolist())
        print(f"  ... {n_rows:>10,} rows scanned", end="\r")

    print()
    print(f"rows                     : {n_rows:,}")
    print(f"date range               : {d_min:%Y-%m} .. {d_max:%Y-%m}")
    print(f"unique PERMNO            : {len(permnos):,}")
    for c, n_nn in [("MthRet", n_ret_nn), ("MthRetx", n_retx_nn), ("MthCap", n_cap_nn)]:
        print(f"{c:12s} non-null      : {n_nn:>12,}  ({n_nn / n_rows:.1%})")

    r = np.concatenate(rets) if rets else np.array([], dtype="float32")
    print(f"MthRet  mean/median      : {r.mean():.4f} / {np.median(r):.4f}")
    print(f"MthRet  min / max        : {r.min():.4f} / {r.max():.4f}")
    print(f"MthRet  |r|<=1 fraction  : {(np.abs(r) <= 1).mean():.2%}")
    print(f"MthRet  <-0.9 fraction   : {(r < -0.9).mean():.2%}  (delisting/missing -0.9/-1 conventions)")

    for name, counter in [("PrimaryExch", exch), ("SecurityType", stype), ("ShareType", shtype)]:
        print(f"\n{name} value counts (top 10):")
        for k, v in counter.most_common(10):
            print(f"   {k:>12}: {v:,}")

    print(f"\nrows in {config.START_YEAR}-{config.END_YEAR}: {in_sample_rows:,} "
          f"({in_sample_rows / n_rows:.1%}); unique PERMNO = {len(in_sample_permnos):,}")
    print()


def profile_ff_factors() -> None:
    path = config.FF_FACTORS_CSV
    print("=" * 70)
    print(f"FF FACTORS + RF: {path.name}")
    print("=" * 70)
    # First 3 lines are prose, line 4 blank, line 5 is the header.
    ff = pd.read_csv(path, skiprows=4)
    ff = ff.rename(columns={ff.columns[0]: "YYYYMM"})
    ff["YYYYMM"] = ff["YYYYMM"].astype(str)
    monthly = ff[ff["YYYYMM"].str.fullmatch(r"\d{6}")].copy()
    monthly["YYYYMM"] = monthly["YYYYMM"].astype(int)
    print(f"monthly rows             : {len(monthly):,} "
          f"({monthly['YYYYMM'].min()} .. {monthly['YYYYMM'].max()})")
    print(f"columns                  : {list(monthly.columns)}")

    r = monthly["RF"].astype(float)
    print(f"RF (percent, monthly)    : mean {r.mean():.3f}, median {r.median():.3f}, "
          f"min {r.min():.3f}, max {r.max():.3f}")

    in_sample = monthly["YYYYMM"].between(config.START_YYYYMM, config.END_YYYYMM)
    sub = monthly.loc[in_sample, "RF"].astype(float) / 100.0
    print(f"RF {config.START_YEAR}-{config.END_YEAR} (decimal): mean {sub.mean():.6f}, "
          f"median {sub.median():.6f}")
    print()


def profile_daily_stock() -> None:
    path = config.DAILY_STOCK_CSV
    print("=" * 70)
    print(f"DAILY STOCK (chunked scan): {path.name}")
    print("=" * 70)
    cols = ["PERMNO", "DlyCalDt", "DlyRet", "DlyCap"]
    permnos: set[int] = set()
    n_rows = 0
    n_ret_nn = 0
    n_cap_nn = 0
    d_min = d_max = None

    dtypes = {"DlyRet": "float32", "DlyCap": "float64"}
    reader = pd.read_csv(path, usecols=cols, dtype=dtypes, chunksize=1_000_000)
    for chunk in reader:
        n_rows += len(chunk)
        permnos.update(chunk["PERMNO"].dropna().astype(int).tolist())
        n_ret_nn += chunk["DlyRet"].notna().sum()
        n_cap_nn += chunk["DlyCap"].notna().sum()
        dt = pd.to_datetime(chunk["DlyCalDt"])
        lo, hi = dt.min(), dt.max()
        d_min = lo if d_min is None or lo < d_min else d_min
        d_max = hi if d_max is None or hi > d_max else d_max
        print(f"  ... {n_rows:>14,} rows scanned", end="\r")

    print()
    print(f"rows                     : {n_rows:,}")
    print(f"date range               : {d_min:%Y-%m-%d} .. {d_max:%Y-%m-%d}")
    print(f"unique PERMNO            : {len(permnos):,}")
    print(f"DlyRet non-null          : {n_ret_nn:,}  ({n_ret_nn / n_rows:.1%})")
    print(f"DlyCap non-null          : {n_cap_nn:,}  ({n_cap_nn / n_rows:.1%})")
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true", help="also scan the 27 GB daily file (slow)")
    args = ap.parse_args()

    config.ensure_dirs()
    print(f"RAW_DATA_DIR = {config.RAW_DATA_DIR}\n")
    profile_monthly_stock()
    profile_ff_factors()
    if args.daily:
        profile_daily_stock()
    else:
        print("(Daily file skipped. Re-run with --daily to scan it; this takes several minutes.)")


if __name__ == "__main__":
    main()
