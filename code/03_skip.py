"""Step 03 - Table 3: momentum with a one-month skip between formation and holding.

Jegadeesh & Titman (1993, Table 3) insert a lag between the end of the formation
period and the start of the holding period to check that momentum profits are not
an artifact of microstructure noise (bid-ask bounce / short-horizon reversal).
With monthly data the paper's one-week lag is approximated by a one-month skip:
rank on returns through month t, skip month t+1, hold months t+2 .. t+K+1.

Outputs:
  data/momentum_deciles_skip1.parquet  -- tidy decile series (skip=1)
  output/table3_deciles.csv            -- J=6, K=6 decile means + t-stats (Table 3a)
  output/table3_jk.csv                 -- J x K WML means + t-stats (Table 3b)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np  # noqa: F401  (kept for parity with 02; not required here)
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

# ``02_momentum.py`` starts with a digit, so it is not a valid import name; load it
# explicitly to reuse its strategy functions unchanged.
_spec = importlib.util.spec_from_file_location(
    "momentum", Path(__file__).resolve().parent / "02_momentum.py"
)
momentum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(momentum)

SKIP = 1  # one-month skip (monthly analogue of the paper's one-week lag)


def main() -> None:
    config.ensure_dirs()
    R, cap, months, permnos = momentum.load_matrices()

    dec = momentum.build_decile_table(R, months, skip=SKIP)
    dec.to_parquet(config.DATA_DIR / "momentum_deciles_skip1.parquet", index=False)

    t1 = momentum.table1(dec)
    t1.to_csv(config.OUTPUT_DIR / "table3_deciles.csv")
    print("Table 3a (J=6, K=6, skip=1 month) - equal-weighted decile portfolios:\n")
    print(t1.round(3).to_string())
    print()

    t2 = momentum.table2(dec)
    t2.to_csv(config.OUTPUT_DIR / "table3_jk.csv", index=False)

    pivot = t2.pivot(index="J", columns="K", values="p10_minus_p1_mean_pct")
    print("Table 3b - winner-minus-loser (P10-P1) mean monthly return, %, skip=1 month:\n")
    print(pivot.round(3).to_string())
    print("\n(t-stats in output/table3_jk.csv)")
    print(f"\nwrote data/momentum_deciles_skip1.parquet, "
          f"output/table3_deciles.csv, output/table3_jk.csv")


if __name__ == "__main__":
    main()
