"""Step 01 — Build the clean monthly return panel.

Reads the raw monthly CRSP file and produces the long panel consumed by the
momentum strategy. Every sample-construction choice is documented here.

Filters:
  1. Common equity only   : SecurityType == "EQTY"   (excludes funds/ETFs)
  2. Common shares        : ShareType == "NS"
  3. Exchange             : PrimaryExch in {N, A, Q} (NYSE, AMEX, NASDAQ)
  4. Valid return         : MthRet notna
  5. Sample period        : 2000-01 .. 2025-12 (config)

Notes:
  - Returns (MthRet) are kept as-is (no winsorization) to stay faithful to the
    original paper; the extreme microcap returns are examined in the report as a
    robustness consideration.
  - MthCap appears to be in thousands of dollars (ShrOut[thousand] x price).

Output: data/processed/monthly_panel.parquet (long panel: PERMNO, MthCalDt, MthRet, MthCap, PrimaryExch)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

COLS = ["PERMNO", "MthCalDt", "MthRet", "MthCap", "PrimaryExch", "SecurityType", "ShareType"]
DTYPES = {"MthRet": "float32", "MthCap": "float64"}
EXCHANGES = {"N", "A", "Q"}  # NYSE, AMEX, NASDAQ


def main() -> None:
    config.ensure_dirs()
    out = config.DATA_DIR / "monthly_panel.parquet"
    if out.exists():
        print(f"skipping: {out} already exists (delete it to rebuild)")
        return
    n_in = n_exch = n_eqty = n_share = n_ret = 0
    chunks = []

    reader = pd.read_csv(
        config.MONTHLY_STOCK_CSV, usecols=COLS, dtype=DTYPES,
        parse_dates=["MthCalDt"], chunksize=1_000_000,
    )
    for chunk in reader:
        n_in += len(chunk)
        chunk = chunk[chunk["PrimaryExch"].isin(EXCHANGES)]
        n_exch += len(chunk)
        chunk = chunk[chunk["SecurityType"] == "EQTY"]
        n_eqty += len(chunk)
        chunk = chunk[chunk["ShareType"] == "NS"]
        n_share += len(chunk)
        chunk = chunk[chunk["MthRet"].notna()]
        n_ret += len(chunk)
        chunks.append(chunk[["PERMNO", "MthCalDt", "MthRet", "MthCap", "PrimaryExch"]])

    panel = pd.concat(chunks, ignore_index=True)
    panel = panel.sort_values(["PERMNO", "MthCalDt"]).reset_index(drop=True)
    panel["PERMNO"] = panel["PERMNO"].astype("int32")

    print(f"rows read                : {n_in:,}")
    print(f"after exchange N/A/Q     : {n_exch:,}")
    print(f"after SecurityType EQTY  : {n_eqty:,}")
    print(f"after ShareType NS       : {n_share:,}")
    print(f"after MthRet notna       : {n_ret:,}")
    print()
    print(f"final panel rows         : {len(panel):,}")
    print(f"unique PERMNO            : {panel['PERMNO'].nunique():,}")
    print(f"date range               : {panel['MthCalDt'].min():%Y-%m} .. {panel['MthCalDt'].max():%Y-%m}")
    print(f"months                   : {panel['MthCalDt'].dt.to_period('M').nunique():,}")
    print(f"MthRet mean/median       : {panel['MthRet'].mean():.4f} / {panel['MthRet'].median():.4f}")

    panel.to_parquet(out, index=False)
    print(f"\nwrote {out}  ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
