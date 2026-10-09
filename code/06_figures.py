"""Step 06 — Figures for the empirical report.

Renders the five report figures from the already-computed tables. Colors follow
the reference data-viz palette (see the project's design notes): categorical
slots are fixed-order blue/orange, ordinal and sequential magnitudes use a
single blue ramp (light -> dark), and ink/grid are the muted chart tokens.

Figures (all written to outputs/figures/):
  fig1_decile_returns.png       -- decile portfolio means (Table 1), ordinal ramp
  fig2_jk_heatmap.png           -- winner-minus-loser J x K grid (Table 2)
  fig3_cumulative_wml.png       -- cumulative P10-P1 wealth (J=6, K=6)
  fig4_size_momentum.png        -- WML by size, equal-count vs NYSE (Tables 4/5)
  fig5_skip_comparison.png      -- deciles with/without one-month skip (Tables 1/3)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

# --- palette (documented reference values) ------------------------------------
BLUE = "#2a78d6"      # categorical slot 1
ORANGE = "#eb6834"    # categorical slot 2
INK = "#0b0b0b"
SEC_INK = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# ordinal/sequential blue ramp, light -> dark (steps 250..700 of the reference ramp)
DECILE_RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
               "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
BLUE_CMAP = LinearSegmentedColormap.from_list(
    "blue_seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "axes.labelcolor": SEC_INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
})


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)


def _deciles_only(df: pd.DataFrame) -> pd.DataFrame:
    """Return the ten decile rows (1..10) as int, sorted, dropping the P10-P1 row."""
    d = df[df["decile"] != "P10-P1"].copy()
    d["decile"] = d["decile"].astype(int)
    return d.sort_values("decile").reset_index(drop=True)


# --- Figure 1: decile portfolios ----------------------------------------------
def fig1(tables: Path, figs: Path):
    df = pd.read_csv(tables / "table1_deciles.csv")
    dec = _deciles_only(df)
    wml = df[df["decile"] == "P10-P1"].iloc[0]["mean_ret_pct"]

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    style_ax(ax)
    bars = ax.bar(dec["decile"], dec["mean_ret_pct"], color=DECILE_RAMP, width=0.72)
    ax.axhline(0, color=BASELINE, linewidth=0.8)
    ax.set_xticks(dec["decile"])
    ax.set_xticklabels([f"P{d}" for d in dec["decile"]])
    ax.set_xlabel("Decile (P1 = losers ... P10 = winners)")
    ax.set_ylabel("Mean monthly return (%)")
    ax.set_title("Momentum decile portfolios (J=6, K=6)")

    # selective direct labels on the extremes only
    for d, bar in zip(dec["decile"], bars):
        if d in (1, 10):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{bar.get_height():.2f}", ha="center", va="bottom",
                    fontsize=9, color=SEC_INK)
    ax.text(0.02, 0.97, f"P10 $-$ P1 = {wml:.2f}%/mo", transform=ax.transAxes,
            ha="left", va="top", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(figs / "fig1_decile_returns.png")
    plt.close(fig)


# --- Figure 2: J x K heatmap --------------------------------------------------
def fig2(tables: Path, figs: Path):
    df = pd.read_csv(tables / "table2_jk.csv")
    pivot = df.pivot(index="J", columns="K", values="p10_minus_p1_mean_pct")

    fig, ax = plt.subplots(figsize=(5.6, 4.6), dpi=200)
    style_ax(ax)
    im = ax.imshow(pivot.values, cmap=BLUE_CMAP, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_xlabel("Holding period K (months)")
    ax.set_ylabel("Formation period J (months)")
    ax.set_title("Winner-minus-loser (P10$-$P1), %/mo")

    vmin, vmax = pivot.values.min(), pivot.values.max()
    mid = (vmin + vmax) / 2
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color=("white" if v > mid else INK), fontsize=9)
    fig.colorbar(im, ax=ax, label="%/mo", fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(figs / "fig2_jk_heatmap.png")
    plt.close(fig)


# --- Figure 3: cumulative winner-minus-loser ----------------------------------
def fig3(data: Path, figs: Path):
    dec = pd.read_parquet(data / "momentum_deciles.parquet")
    sub = dec[(dec["J"] == 6) & (dec["K"] == 6)]
    wide = sub.pivot(index="month", columns="decile", values="ret").sort_index()
    wml = (wide[10] - wide[1]).dropna()
    cum = (1.0 + wml).cumprod()

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    style_ax(ax)
    ax.plot(cum.index, cum.values, color=BLUE, linewidth=1.6)
    ax.axhline(1.0, color=BASELINE, linewidth=0.8)

    # Annotate the sharpest momentum-crash months (largest one-month WML drops):
    # after a market bottom, past losers snap back and winner-minus-loser collapses.
    for ts, r in wml.nsmallest(4).items():
        ax.scatter([ts], [cum.loc[ts]], color=ORANGE, s=18, zorder=5)
        ax.annotate(f"{pd.Timestamp(ts).strftime('%b %Y')}: {r * 100:.0f}%",
                    (ts, cum.loc[ts]), textcoords="offset points", xytext=(4, -12),
                    ha="left", va="top", fontsize=8, color=SEC_INK)

    ax.set_xlabel("Year")
    ax.set_ylabel("Growth of $1 invested in P10$-$P1")
    ax.set_title("Cumulative winner-minus-loser return (J=6, K=6)")
    fig.text(0.99, 0.01,
             "Dips mark momentum crashes: past losers rebound after market bottoms "
             "(Jan 2001 dot-com, 2009 GFC).",
             ha="right", va="bottom", fontsize=8, color=MUTED)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(figs / "fig3_cumulative_wml.png")
    plt.close(fig)


# --- Figure 4: size comparison (equal-count vs NYSE) --------------------------
def fig4(tables: Path, figs: Path):
    t4 = pd.read_csv(tables / "table4_size_deciles.csv")
    t5 = pd.read_csv(tables / "table5_size_deciles.csv")
    sizes = ["Small", "Mid", "Large"]
    x = np.arange(len(sizes))
    w = 0.38
    v4 = [t4[t4["size"] == s]["wml_mean_pct"].iloc[0] for s in sizes]
    v5 = [t5[t5["size"] == s]["wml_mean_pct"].iloc[0] for s in sizes]

    fig, ax = plt.subplots(figsize=(7.0, 4.4), dpi=200)
    style_ax(ax)
    b1 = ax.bar(x - w / 2, v4, w, color=BLUE, label="Equal-count terciles")
    b2 = ax.bar(x + w / 2, v5, w, color=ORANGE, label="NYSE breakpoints")
    ax.axhline(0, color=BASELINE, linewidth=0.8)
    ax.set_xticks(x, sizes)
    ax.set_xlabel("Firm-size group")
    ax.set_ylabel("Winner-minus-loser, %/mo")
    ax.set_title("Momentum by firm size (J=6, K=6)")
    ax.legend(frameon=False)

    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02,
                    f"{b.get_height():.2f}", ha="center", va="bottom",
                    fontsize=8.5, color=SEC_INK)
    fig.tight_layout()
    fig.savefig(figs / "fig4_size_momentum.png")
    plt.close(fig)


# --- Figure 5: skip-month comparison (Table 1 vs Table 3) ---------------------
def fig5(tables: Path, figs: Path):
    t1 = pd.read_csv(tables / "table1_deciles.csv")
    t3 = pd.read_csv(tables / "table3_deciles.csv")
    d1 = _deciles_only(t1)
    d3 = _deciles_only(t3)
    x = np.arange(len(d1))
    w = 0.4

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    style_ax(ax)
    ax.bar(x - w / 2, d1["mean_ret_pct"], w, color=BLUE, label="No skip")
    ax.bar(x + w / 2, d3["mean_ret_pct"], w, color=ORANGE, label="One-month skip")
    ax.axhline(0, color=BASELINE, linewidth=0.8)
    ax.set_xticks(x, [f"P{d}" for d in d1["decile"]])
    ax.set_xlabel("Decile")
    ax.set_ylabel("Mean monthly return (%)")
    ax.set_title("Momentum deciles with and without a one-month skip")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figs / "fig5_skip_comparison.png")
    plt.close(fig)


def main() -> None:
    config.ensure_dirs()
    tables = config.TABLES_DIR
    figs = config.FIGURES_DIR
    data = config.DATA_DIR
    fig1(tables, figs)
    fig2(tables, figs)
    fig3(data, figs)
    fig4(tables, figs)
    fig5(tables, figs)
    print("wrote:")
    for p in sorted(figs.glob("fig*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
