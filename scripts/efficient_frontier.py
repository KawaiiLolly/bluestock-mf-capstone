"""
efficient_frontier.py
    Outputs
    -------
    reports/bonus/efficient_frontier.csv     - all frontier portfolio stats
    reports/bonus/optimal_weights.csv        - weights of MSR and MinVar portfolios
    reports/bonus/ef_chart.png               - classic mean-variance frontier chart
    reports/bonus/weights_chart.png          - portfolio weight bar charts

Usage
---
    python scripts/efficient_frontier.py

    # Select different funds by amfi_code
    python scripts/efficient_frontier.py --codes 100001 100005 100010 100015 100020
"""

import warnings
warnings.filterwarnings("ignore")

import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROC     = BASE_DIR / "data" / "processed"
PERF     = BASE_DIR / "reports" / "performance"
BONUS    = BASE_DIR / "reports" / "bonus"
BONUS.mkdir(parents=True, exist_ok=True)

# Constants
RF_ANNUAL    = 0.065      # risk-free rate
TRADING_DAYS = 252
N_PORTFOLIOS = 5000       # random portfolios for scatter backdrop


def save(fig, name):
    path = BONUS / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → reports/bonus/{name}")

# Select 5 funds and build returns matrix
def select_funds(nav_df, fm, target_codes=None):
    """
    If target_codes given, use those.
    Otherwise pick top 5 from fund scorecard by composite_score
    covering different categories for diversification.
    """
    if target_codes:
        codes = target_codes
    else:
        score = pd.read_csv(PERF / "fund_scorecard.csv")
        categories = ["Equity", "Debt", "Hybrid"]
        selected   = []
        for cat in categories:
            top = score[score["category"] == cat].sort_values(
                "composite_score", ascending=False
            ).head(2)["amfi_code"].tolist()
            selected.extend(top)
        codes = selected[:5]

    name_map   = dict(zip(fm["amfi_code"], fm["scheme_name"]))
    fund_names = {c: " ".join(name_map.get(c,"?").split()[:3]) for c in codes}

    print(f"\n  Selected funds for optimisation:")
    for i, c in enumerate(codes, 1):
        print(f"    {i}. [{c}] {fund_names[c]}")

    return codes, fund_names


# Build aligned daily returns matrix
def build_returns_matrix(nav_df, codes):
    """
    Pivot NAV history into a date × fund matrix, compute daily returns.
    Drop dates with missing data for any fund.
    """
    nav_sub = nav_df[nav_df["amfi_code"].isin(codes)].copy()
    pivot   = nav_sub.pivot_table(index="date", columns="amfi_code", values="nav")
    pivot   = pivot[codes]     # preserve fund order
    pivot   = pivot.dropna()   # only dates where ALL 5 funds have data

    daily_returns = pivot.pct_change().dropna()

    print(f"\n  Returns matrix: {daily_returns.shape[0]} trading days × {len(codes)} funds")
    print(f"  Date range: {daily_returns.index.min()} → {daily_returns.index.max()}")
    return daily_returns


# Portfolio statistics
def portfolio_stats(weights, mean_returns, cov_matrix):
    """
        Compute annualised portfolio return, volatility, and Sharpe ratio.
    """
    port_return = np.dot(weights, mean_returns) * TRADING_DAYS
    port_var    = np.dot(weights, np.dot(cov_matrix.values, weights))
    port_vol    = np.sqrt(port_var * TRADING_DAYS)
    sharpe      = (port_return - RF_ANNUAL) / port_vol if port_vol > 0 else 0
    return port_return, port_vol, sharpe


# Optimisation
def optimise_portfolios(mean_returns, cov_matrix, codes, fund_names):
    n = len(codes)
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
    bounds = tuple((0.0, 1.0) for _ in range(n))
    w0 = np.array([1 / n] * n)

    def neg_sharpe(w):
        r, v, s = portfolio_stats(w, mean_returns, cov_matrix)
        return -s

    msr_result = minimize(neg_sharpe, w0,
                          method="SLSQP",
                          bounds=bounds,
                          constraints=constraints,
                          options={"ftol": 1e-9, "maxiter": 1000})
    msr_weights = msr_result.x
    msr_r, msr_v, msr_s = portfolio_stats(msr_weights, mean_returns, cov_matrix)
    def portfolio_variance(w):
        return np.dot(w, np.dot(cov_matrix.values, w)) * TRADING_DAYS

    minvar_result = minimize(portfolio_variance, w0,
                             method="SLSQP",
                             bounds=bounds,
                             constraints=constraints,
                             options={"ftol": 1e-9, "maxiter": 1000})
    mv_weights = minvar_result.x
    mv_r, mv_v, mv_s = portfolio_stats(mv_weights, mean_returns, cov_matrix)
    ew_weights = np.array([1 / n] * n)
    ew_r, ew_v, ew_s = portfolio_stats(ew_weights, mean_returns, cov_matrix)

    print(f"\n  Optimisation results:")
    print(f"  {'Portfolio':<25} {'Return':>8} {'Vol':>8} {'Sharpe':>8}")
    print("  " + "-" * 52)
    for label, r, v, s in [
        ("Max Sharpe (MSR)",    msr_r, msr_v, msr_s),
        ("Min Variance",        mv_r,  mv_v,  mv_s),
        ("Equal Weight",        ew_r,  ew_v,  ew_s),
    ]:
        print(f"  {label:<25} {r*100:>7.2f}% {v*100:>7.2f}% {s:>8.3f}")

    return {
        "msr":    {"weights": msr_weights, "return": msr_r, "vol": msr_v, "sharpe": msr_s},
        "minvar": {"weights": mv_weights,  "return": mv_r,  "vol": mv_v,  "sharpe": mv_s},
        "ew":     {"weights": ew_weights,  "return": ew_r,  "vol": ew_v,  "sharpe": ew_s},
    }


# Efficient Frontier curve
def compute_frontier(mean_returns, cov_matrix, n_points=200):
    """
        Generate the efficient frontier by solving for minimum variance
        at a range of target return levels.
    """
    n   = len(mean_returns)
    w0  = np.array([1 / n] * n)
    bds = tuple((0, 1) for _ in range(n))

    ret_min = mean_returns.min() * TRADING_DAYS * 1.2
    ret_max = mean_returns.max() * TRADING_DAYS * 0.9
    target_returns = np.linspace(ret_min, ret_max, n_points)

    frontier_vols    = []
    frontier_returns = []
    frontier_weights = []

    for target in target_returns:
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w,t=target:
             np.dot(w, mean_returns) * TRADING_DAYS - t},
        )
        res = minimize(
            lambda w: np.dot(w, np.dot(cov_matrix.values, w)) * TRADING_DAYS,
            w0, method="SLSQP", bounds=bds, constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 500}
        )
        if res.success:
            vol = np.sqrt(res.fun)
            frontier_vols.append(vol)
            frontier_returns.append(target)
            frontier_weights.append(res.x)

    return np.array(frontier_returns), np.array(frontier_vols)


# Save results
def save_results(portfolios, codes, fund_names, mean_returns, cov_matrix):
    weight_rows = []
    for port_name, data in portfolios.items():
        row = {"portfolio": port_name,
               "ann_return_pct": round(data["return"] * 100, 4),
               "ann_vol_pct":    round(data["vol"] * 100, 4),
               "sharpe_ratio":   round(data["sharpe"], 4)}
        for code, w in zip(codes, data["weights"]):
            row[f"weight_{fund_names[code].replace(' ','_')}"] = round(w, 4)
        weight_rows.append(row)

    weights_df = pd.DataFrame(weight_rows)
    weights_df.to_csv(BONUS / "optimal_weights.csv", index=False)
    print(f"\n  Saved → reports/bonus/optimal_weights.csv")

    rng = np.random.default_rng(42)
    rand_rows = []
    for _ in range(N_PORTFOLIOS):
        w  = rng.dirichlet(np.ones(len(codes)))
        r, v, s = portfolio_stats(w, mean_returns, cov_matrix)
        rand_rows.append({"ann_return": r, "ann_vol": v, "sharpe": s})
    frontier_df = pd.DataFrame(rand_rows)
    frontier_df.to_csv(BONUS / "efficient_frontier.csv", index=False)
    print(f"  Saved → reports/bonus/efficient_frontier.csv ({len(frontier_df)} random portfolios)")

    return frontier_df


# Charts
def chart_efficient_frontier(portfolios, frontier_returns, frontier_vols,
                              codes, fund_names, mean_returns, cov_matrix):
    """Classic mean-variance frontier chart."""
    rng = np.random.default_rng(42)
    n   = len(codes)

    rand_vols, rand_rets, rand_sharpes = [], [], []
    for _ in range(N_PORTFOLIOS):
        w = rng.dirichlet(np.ones(n))
        r, v, s = portfolio_stats(w, mean_returns, cov_matrix)
        rand_vols.append(v * 100)
        rand_rets.append(r * 100)
        rand_sharpes.append(s)

    fig, ax = plt.subplots(figsize=(12, 8))
    sc = ax.scatter(rand_vols, rand_rets, c=rand_sharpes,
                    cmap="RdYlGn", s=6, alpha=0.4, zorder=1)
    plt.colorbar(sc, ax=ax, label="Sharpe Ratio", shrink=0.8)
    if len(frontier_vols) > 5:
        ax.plot(frontier_vols * 100, frontier_returns * 100,
                "b-", lw=2.5, zorder=3, label="Efficient Frontier")
    for i, code in enumerate(codes):
        fund_ret = mean_returns[code] * TRADING_DAYS * 100
        fund_vol = np.sqrt(cov_matrix.loc[code, code] * TRADING_DAYS) * 100
        ax.scatter(fund_vol, fund_ret, s=100, zorder=5,
                   marker="D", color="#333", edgecolors="white", linewidth=0.5)
        ax.annotate(fund_names[code].split()[0],
                    (fund_vol, fund_ret),
                    textcoords="offset points", xytext=(6, 4), fontsize=8)

    markers = {
        "msr":    ("*",  "#FFD700", 300, "Max Sharpe (MSR)"),
        "minvar": ("o",  "#1565C0", 180, "Min Variance"),
        "ew":     ("^",  "#E65100", 150, "Equal Weight"),
    }
    for key, (mk, col, sz, lbl) in markers.items():
        p = portfolios[key]
        ax.scatter(p["vol"] * 100, p["return"] * 100,
                   marker=mk, s=sz, color=col,
                   edgecolors="black", linewidths=0.8,
                   zorder=6, label=f"{lbl} (S={p['sharpe']:.2f})")

    vol_range = np.linspace(0, max(rand_vols), 100)
    msr = portfolios["msr"]
    cml = RF_ANNUAL * 100 + msr["sharpe"] * vol_range
    ax.plot(vol_range, cml, "k--", lw=1.2, alpha=0.5, label="Capital Market Line")
    ax.axhline(RF_ANNUAL * 100, color="grey", lw=0.8, ls=":",
               label=f"Risk-free rate ({RF_ANNUAL*100:.1f}%)")

    ax.set_xlabel("Annualised Volatility (%)", fontsize=12)
    ax.set_ylabel("Annualised Return (%)", fontsize=12)
    ax.set_title("Markowitz Efficient Frontier\n"
                 "(each dot = a random portfolio; ★ = Maximum Sharpe, "
                 "● = Minimum Variance)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_facecolor("#F8F9FA")
    save(fig, "ef_chart.png")


def chart_weights(portfolios, fund_names):
    """Bar charts showing portfolio weights for each optimal portfolio."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    labels    = [name.split()[0] + "\n" + name.split()[1] if len(name.split()) > 1
                 else name for name in fund_names.values()]
    colors    = ["#1565C0","#2E7D32","#E65100","#B71C1C","#4A148C"]
    titles    = {"msr":"Max Sharpe (MSR)","minvar":"Min Variance","ew":"Equal Weight"}

    for i, (key, title) in enumerate(titles.items()):
        w  = portfolios[key]["weights"]
        p  = portfolios[key]
        ax = axes[i]
        bars = ax.bar(labels, w * 100, color=colors[:len(w)],
                      edgecolor="white", width=0.55)
        ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
        ax.set_title(f"{title}\nReturn={p['return']*100:.1f}%  "
                     f"Vol={p['vol']*100:.1f}%  Sharpe={p['sharpe']:.2f}",
                     fontweight="bold", fontsize=10)
        ax.set_ylabel("Portfolio Weight (%)")
        ax.set_ylim(0, 115)
        ax.grid(axis="y", alpha=0.3)
        ax.set_facecolor("#F8F9FA")

    plt.suptitle("Optimal Portfolio Weights Comparison",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "weights_chart.png")


# Main
def main():
    parser = argparse.ArgumentParser(
        description="Markowitz Efficient Frontier for mutual fund portfolios"
    )
    parser.add_argument("--codes", nargs="+", type=int, default=None,
                        help="5 amfi_codes to include (default: auto-selected)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Bonus B4 — Markowitz Efficient Frontier")
    print("=" * 60)

    nav = pd.read_csv(PROC / "clean_nav_history.csv", parse_dates=["date"])
    nav = nav.sort_values(["amfi_code","date"]).reset_index(drop=True)
    fm  = pd.read_csv(PROC / "clean_fund_master.csv")
    codes, fund_names = select_funds(nav, fm, target_codes=args.codes)
    returns_matrix = build_returns_matrix(nav, codes)
    mean_returns   = returns_matrix.mean()       
    cov_matrix     = returns_matrix.cov()        

    # Optimise
    portfolios = optimise_portfolios(mean_returns, cov_matrix, codes, fund_names)

    # Efficient frontier curve
    print("\n  Computing efficient frontier curve ...")
    frontier_returns, frontier_vols = compute_frontier(mean_returns, cov_matrix)
    print(f"  Frontier computed with {len(frontier_returns)} feasible points")

    # Save results
    save_results(portfolios, codes, fund_names, mean_returns, cov_matrix)

    # Charts
    print("\n  Generating charts ...")
    chart_efficient_frontier(portfolios, frontier_returns, frontier_vols,
                             codes, fund_names, mean_returns, cov_matrix)
    chart_weights(portfolios, fund_names)

    print("\n  MSR portfolio weights:")
    for code, w in zip(codes, portfolios["msr"]["weights"]):
        print(f"    {fund_names[code]:<35}  {w*100:.1f}%")

if __name__ == "__main__":
    main()
