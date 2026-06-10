"""
monte_carlo_simulation.py
==========================
    Outputs
    -------
    reports/bonus/monte_carlo_results.csv   — summary table: median, P5, P95 at 5-year horizon
    reports/bonus/mc_all_funds_chart.png    — grid chart of uncertainty bands (all funds)
    reports/bonus/mc_top6_chart.png         — detailed chart for the top 6 ranked funds
    reports/bonus/mc_single_<name>.png      — individual chart per fund (top 10 only)

    Usage
    ---
        python scripts/monte_carlo_simulation.py

        # Simulate only specific funds
        python scripts/monte_carlo_simulation.py --codes 100001 100002 100003
"""

import warnings
warnings.filterwarnings("ignore")

import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROC     = BASE_DIR / "data" / "processed"
PERF     = BASE_DIR / "reports" / "performance"
BONUS    = BASE_DIR / "reports" / "bonus"
BONUS.mkdir(parents=True, exist_ok=True)

N_SIMULATIONS  = 1000    
N_YEARS        = 5       
TRADING_DAYS   = 252     
N_DAYS         = N_YEARS * TRADING_DAYS   

COLORS = ["#1565C0","#2E7D32","#E65100","#B71C1C","#4A148C",
          "#006064","#BF360C","#33691E","#880E4F","#1A237E"]


def save(fig, name):
    path = BONUS / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → reports/bonus/{name}")


# Core Monte Carlo engine
def run_monte_carlo(nav_series: pd.Series, nav0: float,
                     n_sims: int = N_SIMULATIONS,
                     n_days: int = N_DAYS,
                     seed: int = 42) -> dict:
    """
        Simulate n_sims NAV paths over n_days trading days.
    """
    rng = np.random.default_rng(seed)
    log_returns  = np.log(nav_series / nav_series.shift(1)).dropna()
    mu_daily     = log_returns.mean()
    sigma_daily  = log_returns.std()
    rand_returns = rng.normal(mu_daily, sigma_daily, size=(n_sims, n_days))
    cum_returns  = np.cumsum(rand_returns, axis=1)
    nav_paths = nav0 * np.exp(cum_returns)   # shape (n_sims, n_days)

    days = np.arange(1, n_days + 1)
    p05  = np.percentile(nav_paths, 5,  axis=0)
    p25  = np.percentile(nav_paths, 25, axis=0)
    p50  = np.percentile(nav_paths, 50, axis=0)
    p75  = np.percentile(nav_paths, 75, axis=0)
    p95  = np.percentile(nav_paths, 95, axis=0)

    cagr_median = (p50[-1] / nav0) ** (1 / N_YEARS) - 1

    return {
        "days"       : days,
        "p05"        : p05,
        "p25"        : p25,
        "p50"        : p50,
        "p75"        : p75,
        "p95"        : p95,
        "mu_daily"   : mu_daily,
        "sigma_daily": sigma_daily,
        "cagr_median": cagr_median,
        "nav0"       : nav0,
    }


# Run all funds
def simulate_all_funds(nav_df, fm, target_codes=None):
    print(f"\n  Running {N_SIMULATIONS:,} simulations × {N_DAYS} days per fund ...")
    print(f"  Horizon: {N_YEARS} years  ({N_DAYS} trading days)\n")

    name_map = dict(zip(fm["amfi_code"], fm["scheme_name"]))
    results  = {}
    rows     = []

    codes = target_codes if target_codes else nav_df["amfi_code"].unique()

    for code in codes:
        grp = nav_df[nav_df["amfi_code"] == code].sort_values("date")
        if len(grp) < 100:
            continue

        nav0   = float(grp["nav"].iloc[-1])
        result = run_monte_carlo(grp["nav"], nav0)
        results[code] = result

        name   = name_map.get(code, str(code))
        short  = " ".join(name.split()[:3])

        rows.append({
            "amfi_code":       code,
            "scheme_name":     name,
            "current_nav":     round(nav0, 4),
            "mu_daily_pct":    round(result["mu_daily"] * 100, 4),
            "sigma_daily_pct": round(result["sigma_daily"] * 100, 4),
            "nav_p05_5yr":     round(result["p05"][-1], 2),
            "nav_p50_5yr":     round(result["p50"][-1], 2),
            "nav_p95_5yr":     round(result["p95"][-1], 2),
            "cagr_median_pct": round(result["cagr_median"] * 100, 2),
            "upside_pct":      round((result["p95"][-1] / nav0 - 1) * 100, 2),
            "downside_pct":    round((result["p05"][-1] / nav0 - 1) * 100, 2),
        })
        print(f"  ✓ {short:<35}  Nav₀={nav0:>7.2f}  "
              f"P50(5yr)={result['p50'][-1]:>7.2f}  "
              f"CAGR={result['cagr_median']*100:>5.1f}%")

    mc_df = pd.DataFrame(rows).sort_values("cagr_median_pct", ascending=False)
    mc_df.to_csv(BONUS / "monte_carlo_results.csv", index=False)
    print(f"\n  Summary saved → reports/bonus/monte_carlo_results.csv")
    return results, mc_df


# Charts
def chart_top6(results, mc_df, fm):
    """Detailed chart for top 6 funds by projected CAGR."""
    name_map = dict(zip(fm["amfi_code"], fm["scheme_name"]))
    top6     = mc_df.head(6)["amfi_code"].tolist()

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes      = axes.flatten()

    year_ticks = [i * TRADING_DAYS for i in range(N_YEARS + 1)]
    year_labels= [f"Yr {i}" for i in range(N_YEARS + 1)]

    for i, code in enumerate(top6):
        r   = results[code]
        ax  = axes[i]
        col = COLORS[i]
        days = r["days"]
        ax.fill_between(days, r["p05"], r["p95"],
                        alpha=0.15, color=col, label="5th–95th pct")
        ax.fill_between(days, r["p25"], r["p75"],
                        alpha=0.25, color=col, label="25th–75th pct")
        ax.plot(days, r["p50"], color=col, lw=2.2, label="Median")
        ax.axhline(r["nav0"], color="grey", lw=0.8, ls="--", alpha=0.6)
        ax.annotate(f"P95: ₹{r['p95'][-1]:.0f}",
                    xy=(days[-1], r["p95"][-1]),
                    xytext=(-60, 5), textcoords="offset points",
                    fontsize=7.5, color="#2E7D32")
        ax.annotate(f"Median: ₹{r['p50'][-1]:.0f}",
                    xy=(days[-1], r["p50"][-1]),
                    xytext=(-70, 5), textcoords="offset points",
                    fontsize=8, fontweight="bold", color=col)
        ax.annotate(f"P05: ₹{r['p05'][-1]:.0f}",
                    xy=(days[-1], r["p05"][-1]),
                    xytext=(-60, -12), textcoords="offset points",
                    fontsize=7.5, color="#B71C1C")

        name  = name_map.get(code, str(code))
        short = " ".join(name.split()[:3])
        ax.set_title(f"{short}\nCAGR={r['cagr_median']*100:.1f}%  "
                     f"Nav₀=₹{r['nav0']:.0f}",
                     fontweight="bold", fontsize=10)
        ax.set_xticks(year_ticks)
        ax.set_xticklabels(year_labels, fontsize=8)
        ax.set_ylabel("NAV (₹)", fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_facecolor("#F8F9FA")

        if i == 0:
            ax.legend(fontsize=7, loc="upper left")

    plt.suptitle(f"Monte Carlo NAV Projection — Top 6 Funds\n"
                 f"({N_SIMULATIONS:,} simulations, {N_YEARS}-year horizon, "
                 f"shaded = uncertainty bands)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "mc_top6_chart.png")


def chart_all_funds_grid(results, mc_df, fm):
    """Small multiples grid for all funds."""
    name_map = dict(zip(fm["amfi_code"], fm["scheme_name"]))
    codes    = mc_df["amfi_code"].tolist()
    n        = len(codes)
    cols     = 5
    rows_    = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows_, cols, figsize=(20, rows_ * 3.2))
    axes      = axes.flatten()
    year_ticks= [i * TRADING_DAYS for i in range(N_YEARS + 1)]
    year_labs = [f"Y{i}" for i in range(N_YEARS + 1)]

    for i, code in enumerate(codes):
        r  = results.get(code)
        ax = axes[i]
        if r is None:
            ax.set_visible(False)
            continue
        col = COLORS[i % len(COLORS)]
        d   = r["days"]
        ax.fill_between(d, r["p05"], r["p95"], alpha=0.15, color=col)
        ax.fill_between(d, r["p25"], r["p75"], alpha=0.25, color=col)
        ax.plot(d, r["p50"], color=col, lw=1.8)
        ax.axhline(r["nav0"], color="grey", lw=0.6, ls="--", alpha=0.5)
        name  = name_map.get(code, str(code))
        short = " ".join(name.split()[:2])
        ax.set_title(f"{short}\n{r['cagr_median']*100:.1f}% CAGR",
                     fontsize=7.5, fontweight="bold")
        ax.set_xticks(year_ticks)
        ax.set_xticklabels(year_labs, fontsize=6)
        ax.tick_params(axis="y", labelsize=6)
        ax.grid(alpha=0.25)
        ax.set_facecolor("#F8F9FA")

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle(f"Monte Carlo NAV Projection — All {n} Funds  "
                 f"({N_SIMULATIONS:,} paths, {N_YEARS}yr horizon)",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    save(fig, "mc_all_funds_chart.png")


# Main
def main():
    parser = argparse.ArgumentParser(
        description="Monte Carlo NAV simulation for mutual fund schemes"
    )
    parser.add_argument("--codes", nargs="+", type=int, default=None,
                        help="Specific amfi_codes to simulate (default: all)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Bonus B3 — Monte Carlo NAV Simulation")
    print(f"  {N_SIMULATIONS:,} paths × {N_YEARS} years × {N_DAYS} trading days")
    print("=" * 60)

    nav = pd.read_csv(PROC / "clean_nav_history.csv", parse_dates=["date"])
    nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)
    fm  = pd.read_csv(PROC / "clean_fund_master.csv")

    results, mc_df = simulate_all_funds(nav, fm, target_codes=args.codes)

    print("\n  Generating charts ...")
    chart_top6(results, mc_df, fm)
    chart_all_funds_grid(results, mc_df, fm)

    print("\n  Top 10 projected CAGRs (median):")
    print(mc_df[["scheme_name","cagr_median_pct","nav_p50_5yr","nav_p05_5yr","nav_p95_5yr"]]
          .head(10).to_string(index=False))

if __name__ == "__main__":
    main()
