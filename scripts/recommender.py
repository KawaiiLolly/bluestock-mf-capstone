"""
    recommender.py

    It is a simiple rule-based recommender, it takes investor's risk appetite (low/moderate/high),
    after that it filter funds by matching risk_category, rank by sharpe ratio within that group,
    and return Top 3 recommendations.
    Ouput: Printed recommendation table and saved in CSV.

Usage:
    # User-interactive
    python scripts/recommender.py

    # Command-line argument
    python scripts/recommender.py --risk Low
    python scripts/recommender.py --risk Moderate
    python scripts/recommender.py --risk High
"""

import sys
import argparse
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROC     = BASE_DIR / "data" / "processed"
PERF     = BASE_DIR / "reports" / "performance"
ADV      = BASE_DIR / "reports" / "advanced"

ADV.mkdir(parents=True, exist_ok=True)

# Risk mapping — investor appetite → fund risk grades
RISK_MAP = {
    "Low":      ["Low",],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}

# Load data
def load_data():
    fm     = pd.read_csv(PROC / "clean_fund_master.csv")
    sharpe = pd.read_csv(PERF / "sharpe_values.csv")
    score  = pd.read_csv(PERF / "fund_scorecard.csv")
    cagr   = pd.read_csv(PERF / "cagr_report.csv")
    dd     = pd.read_csv(PERF / "max_drawdown.csv")
    return fm, sharpe, score, cagr, dd

# Core recommendation function
def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    if risk_appetite not in RISK_MAP:
        raise ValueError(f"risk_appetite must be one of: {list(RISK_MAP.keys())}")

    fm, sharpe, score, cagr, dd = load_data()

    valid_grades = RISK_MAP[risk_appetite]

    rec = fm[["amfi_code","scheme_name","fund_house","category",
              "sub_category","risk_category","expense_ratio_pct"]].copy()

    rec = rec.merge(sharpe[["amfi_code","sharpe_ratio"]],  on="amfi_code", how="left")
    rec = rec.merge(score[["amfi_code","composite_score"]], on="amfi_code", how="left")
    rec = rec.merge(cagr[["amfi_code","cagr_3yr"]],        on="amfi_code", how="left")
    rec = rec.merge(dd[["amfi_code","max_drawdown_pct"]],  on="amfi_code", how="left")

    eligible = rec[rec["risk_category"].isin(valid_grades)].copy()

    if eligible.empty:
        print(f"No funds found for risk grades: {valid_grades}")
        return pd.DataFrame()

    eligible = eligible.sort_values(
        ["sharpe_ratio","composite_score"],
        ascending=[False, False]
    ).head(top_n).reset_index(drop=True)

    eligible["rank"] = range(1, len(eligible) + 1)

    return eligible[["rank","scheme_name","fund_house","category","risk_category",
                      "sharpe_ratio","cagr_3yr","max_drawdown_pct",
                      "expense_ratio_pct","composite_score"]]

# Pretty-print recommendation
def print_recommendation(risk_appetite: str):
    valid_grades = RISK_MAP[risk_appetite]
    print()
    print("=" * 100)
    print(f"  FUND RECOMMENDATIONS — Risk Appetite: {risk_appetite.upper()}")
    print(f"  Eligible risk grades: {', '.join(valid_grades)}")
    print("=" * 100)

    result = recommend(risk_appetite)

    if result.empty:
        print("  No recommendations available.")
        return result

    print(f"\n  {'Rank':<5} {'Scheme':<32} {'Category':<10}"
          f" {'Sharpe':>7} {'3Y CAGR%':>9} {'MaxDD%':>8}"
          f" {'ER%':>6} {'Score':>7}")
    print("  " + "-"*100)

    for _, row in result.iterrows():
        name  = " ".join(row["scheme_name"].split()[:4])
        cagr  = f"{row['cagr_3yr']:.2f}" if pd.notna(row["cagr_3yr"]) else "  N/A"
        maxdd = f"{row['max_drawdown_pct']:.2f}" if pd.notna(row["max_drawdown_pct"]) else " N/A"
        print(f"  {int(row['rank']):<5} {name:<32} {row['category']:<10}"
              f" {row['sharpe_ratio']:>7.3f} {cagr:>9} {maxdd:>8}"
              f" {row['expense_ratio_pct']:>6.2f} {row['composite_score']:>7.1f}")

    print()
    print("  Key:")
    print("  Sharpe   — higher is better (risk-adjusted return)")
    print("  3Y CAGR% — 3-year compounded annual growth rate")
    print("  MaxDD%   — maximum drawdown (more negative = higher loss risk)")
    print("  ER%      — expense ratio (lower is better)")
    print("  Score    — composite score 0–100 from fund scorecard")
    print("=" * 100)

    return result

# Run for all three appetites and save
def run_all():
    all_rows = []
    for appetite in ["Low", "Moderate", "High"]:
        result = recommend(appetite)
        result["investor_risk_appetite"] = appetite
        all_rows.append(result)

    combined = pd.concat(all_rows, ignore_index=True)
    out = ADV / "fund_recommendations.csv"
    combined.to_csv(out, index=False)
    print(f"\n  Full recommendation table saved → {out.relative_to(BASE_DIR)}")
    return combined

# Main
def main():
    parser = argparse.ArgumentParser(
        description="Bluestock MF Fund Recommender"
    )
    parser.add_argument("--risk", choices=["Low","Moderate","High"],
                        help="Investor risk appetite")
    parser.add_argument("--all",  action="store_true",
                        help="Show recommendations for all risk levels")
    args = parser.parse_args()

    print("\n  Bluestock MF — Fund Recommendation Engine")

    if args.all:
        for appetite in ["Low","Moderate","High"]:
            print_recommendation(appetite)
        run_all()
        return

    if args.risk:
        print_recommendation(args.risk)
        return

    print("\n  Choose your risk appetite:")
    print("  1. Low      - Capital preservation, stable returns")
    print("  2. Moderate - Balanced growth, some volatility accepted")
    print("  3. High     - Maximum growth, high volatility tolerance")
    print()
    choice = input("  Enter 1 / 2 / 3 (or type Low / Moderate / High): ").strip()

    mapping = {"1":"Low","2":"Moderate","3":"High",
               "low":"Low","moderate":"Moderate","high":"High"}
    appetite = mapping.get(choice.lower())

    if not appetite:
        print("  Invalid choice. Use 1/2/3 or Low/Moderate/High.")
        sys.exit(1)

    print_recommendation(appetite)


if __name__ == "__main__":
    main()
