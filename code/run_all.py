"""run_all.py — Regenerate every output of the replication in one shot.

Run from the repository root::

    python code/run_all.py     # or:  py code/run_all.py

The pipeline is idempotent: step 01 skips the raw -> panel build when the panel
already exists in ``data/processed/``, so the analysis can be reproduced with or
without the licensed CRSP raw files. ``00_profile_data.py`` is intentionally not
included — it only prints raw-file diagnostics and produces no outputs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import config  # noqa: E402

STEPS = [
    "01_build_panel.py",   # raw CRSP -> data/processed/monthly_panel.parquet
    "02_momentum.py",      # Tables 1 & 2             -> outputs/tables/
    "03_skip.py",          # Table 3 (one-month skip) -> outputs/tables/
    "04_size.py",          # Table 4 (equal-count)    -> outputs/tables/
    "05_size_nyse.py",     # Table 5 (NYSE size)      -> outputs/tables/
    "06_figures.py",       # Figures 1-5              -> outputs/figures/
]


def main() -> None:
    config.ensure_dirs()
    failed = False
    for name in STEPS:
        script = REPO_ROOT / "code" / name
        print(f"\n=== {name} ===", flush=True)
        result = subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT)
        if result.returncode != 0:
            print(f"FAILED: {name} (exit {result.returncode})", flush=True)
            failed = True
            break
    if failed:
        sys.exit(1)
    print("\nAll steps finished.")


if __name__ == "__main__":
    main()
