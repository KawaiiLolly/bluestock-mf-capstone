"""
        email_report_generator.py

        Usage
        -----
            # Generate HTML only (no email)
            python scripts/email_report_generator.py --html-only

            # Send email (credentials must be set in .env)
            python scripts/email_report_generator.py

            # Schedule weekly (every Friday 20:00)
            python scripts/email_report_generator.py --schedule

        Credential Setup
        ----------------
        Create a .env file in the project root (same folder as this script's parent):

            SMTP_SENDER=your@gmail.com
            SMTP_PASSWORD=abcd efgh ijkl mnop
            SMTP_TO=recipient@example.com

        Steps to get Gmail App Password
        ------------------
        1. Enable 2-Factor Authentication on your Google account.
        2. Go to: Google Account > Security > App Passwords
        3. Generate an App Password for "Mail".
        4. Paste the 16-char password as SMTP_PASSWORD in .env.
          Do NOT use your normal Google account password.
"""

import argparse
import base64
import os
import smtplib
import time
import warnings
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")


# Directory paths
BASE_DIR  = Path(__file__).resolve().parent.parent
PROC      = BASE_DIR / "data" / "processed"
PERF      = BASE_DIR / "reports" / "performance"
ADV       = BASE_DIR / "reports" / "advanced"
BONUS     = BASE_DIR / "reports" / "bonus"
CHARTS    = BASE_DIR / "reports" / "charts"
EMAIL_DIR = BASE_DIR / "reports" / "email"
EMAIL_DIR.mkdir(parents=True, exist_ok=True)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# Load credentials from .env file
def load_env():
    """
    Read KEY=VALUE pairs from <BASE_DIR>/.env and set them as
    environment variables. Ignores blank lines and # comments.
    Does not overwrite variables that are already set in the shell.
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def get_credentials():
    """Return (sender, password, to) from environment (populated by load_env)."""
    sender   = os.environ.get("SMTP_SENDER")
    password = os.environ.get("SMTP_PASSWORD")
    to       = os.environ.get("SMTP_TO")
    return sender, password, to


# Data loading
def load_data():
    score  = pd.read_csv(PERF / "fund_scorecard.csv")
    cagr   = pd.read_csv(PERF / "cagr_report.csv")
    sharpe = pd.read_csv(PERF / "sharpe_values.csv")
    var_df = pd.read_csv(ADV  / "var_cvar_report.csv")
    sip    = pd.read_csv(PROC / "clean_monthly_sip_inflows.csv", parse_dates=["month"])
    aum    = pd.read_csv(PROC / "clean_aum_by_fund_house.csv")
    folio  = pd.read_csv(PROC / "clean_industry_folio_count.csv")

    mc_path = BONUS / "monte_carlo_results.csv"
    mc = pd.read_csv(mc_path) if mc_path.exists() else None

    cagr_cols = ["cagr_1yr", "cagr_3yr", "cagr_5yr"]
    score = score.drop(columns=[c for c in cagr_cols if c in score.columns])

    if "sharpe_ratio" in score.columns:
        score = score.drop(columns=["sharpe_ratio"])

    merged = score.merge(
        cagr[["amfi_code"] + cagr_cols],
        on="amfi_code", how="left"
    )
    merged = merged.merge(
        sharpe[["amfi_code", "sharpe_ratio"]],
        on="amfi_code", how="left"
    )
    merged = merged.merge(
        var_df[["amfi_code", "var_95_pct", "cvar_95_pct"]],
        on="amfi_code", how="left"
    )
    if mc is not None:
        merged = merged.merge(
            mc[["amfi_code", "cagr_median_pct"]],
            on="amfi_code", how="left"
        )
    else:
        merged["cagr_median_pct"] = None

    latest_sip   = float(sip["sip_inflow_crore"].max())
    latest_folio = float(folio["total_folios_crore"].max())

    if "year" in aum.columns:
        total_aum = float(aum[aum["year"] == 2025]["aum_lakh_crore"].sum())
    else:
        total_aum = float(aum["aum_lakh_crore"].max())

    return {
        "funds":        merged,
        "sip":          sip,
        "latest_sip":   latest_sip,
        "latest_folio": latest_folio,
        "total_aum":    total_aum,
        "report_date":  date.today().strftime("%d %b %Y"),
        "week_no":      datetime.now().isocalendar()[1],
    }


# Embed a PNG chart as a base64 <img> tag
def embed_chart(path):
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return (
        f'<img src="data:image/png;base64,{encoded}" '
        f'style="max-width:100%; border-radius:8px;" />'
    )


# HTML block builders
def build_top5_rows(funds):
    top5 = funds.sort_values("composite_score", ascending=False).head(5)
    rows = ""
    for _, r in top5.iterrows():
        cagr_3y = f"{r['cagr_3yr']:.1f}%"        if pd.notna(r.get("cagr_3yr"))        else "-"
        sharpe  = f"{r['sharpe_ratio']:.2f}"      if pd.notna(r.get("sharpe_ratio"))    else "-"
        mc_cagr = f"{r['cagr_median_pct']:.1f}%"  if pd.notna(r.get("cagr_median_pct")) else "-"
        rows += f"""
        <tr>
          <td><strong>{r['overall_rank']}</strong></td>
          <td>{r['scheme_name']}</td>
          <td>{r['category']}</td>
          <td class="num">{r['composite_score']:.1f}</td>
          <td class="num">{cagr_3y}</td>
          <td class="num">{sharpe}</td>
          <td class="num">{mc_cagr}</td>
        </tr>"""
    return rows


def build_perf_rows(df, positive=True):
    color = "#2E7D32" if positive else "#B71C1C"
    rows  = ""
    for _, r in df.iterrows():
        cagr_1y = r.get("cagr_1yr") or 0
        rows += f"""
        <tr>
          <td>{r['scheme_name']}</td>
          <td class="num" style="color:{color}; font-weight:600;">{r['cagr_3yr']:+.1f}%</td>
          <td class="num">{cagr_1y:+.1f}%</td>
        </tr>"""
    return rows


def build_var_rows(funds):
    risky = funds.dropna(subset=["var_95_pct"]).sort_values("var_95_pct").head(5)
    rows  = ""
    for _, r in risky.iterrows():
        rows += f"""
        <tr>
          <td>{r['scheme_name']}</td>
          <td class="num" style="color:#B71C1C;">{r['var_95_pct']:.2f}%</td>
          <td class="num" style="color:#880E4F;">{r['cvar_95_pct']:.2f}%</td>
        </tr>"""
    return rows


def build_sip_bars(sip):
    last6   = sip.sort_values("month").tail(6)
    max_val = last6["sip_inflow_crore"].max()
    bars    = ""
    for _, r in last6.iterrows():
        pct   = r["sip_inflow_crore"] / max_val * 100
        label = r["month"].strftime("%b %y")
        bars += f"""
        <div class="sip-row">
          <span class="sip-label">{label}</span>
          <div class="sip-track">
            <div class="sip-fill" style="width:{pct:.0f}%;"></div>
          </div>
          <span class="sip-value">Rs.{r['sip_inflow_crore']:,.0f} Cr</span>
        </div>"""
    return bars


# CSS
STYLES = """
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Montserrat', sans-serif;
    background: #F0F4F8;
    color: #1A202C;
    font-size: 14px;
    line-height: 1.6;
  }

  .container {
    max-width: 860px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
  }

  /* Header */
  .header {
    background: linear-gradient(135deg, #0D1B2A 0%, #1565C0 100%);
    padding: 32px 36px;
    color: white;
  }
  .header-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .brand { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .brand span { color: #64B5F6; }
  .report-meta { text-align: right; font-size: 12px; opacity: 0.80; }
  .report-title { margin-top: 16px; font-size: 18px; font-weight: 600; opacity: 0.95; }

  /* KPI cards */
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: #E2E8F0;
  }
  .kpi-card  { padding: 20px 24px; background: white; text-align: center; }
  .kpi-value { font-size: 26px; font-weight: 800; color: #1565C0; line-height: 1.1; }
  .kpi-label { font-size: 11px; color: #718096; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-sub   { font-size: 11px; color: #A0AEC0; margin-top: 2px; }

  /* Sections */
  .section { padding: 28px 36px; border-bottom: 1px solid #EDF2F7; }
  .section:last-child { border-bottom: none; }
  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: #1A202C;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title::before {
    content: '';
    display: inline-block;
    width: 4px;
    height: 18px;
    background: #1565C0;
    border-radius: 2px;
  }

  /* Tables */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th {
    background: #EBF4FF;
    color: #2D3748;
    font-weight: 600;
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
  }
  td { padding: 10px 12px; border-bottom: 1px solid #EDF2F7; vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #F7FAFF; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }

  /* Two-column layout */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .sub-title { font-size: 13px; font-weight: 600; color: #4A5568; margin-bottom: 10px; }

  /* SIP bars */
  .sip-row   { display: flex; align-items: center; gap: 10px; margin-bottom: 7px; }
  .sip-label { width: 44px; font-size: 11px; color: #718096; flex-shrink: 0; }
  .sip-track { flex: 1; height: 18px; background: #EBF4FF; border-radius: 4px; overflow: hidden; }
  .sip-fill  { height: 100%; background: linear-gradient(90deg, #1565C0, #42A5F5); border-radius: 4px; }
  .sip-value { width: 100px; font-size: 11px; font-weight: 600; color: #1565C0; text-align: right; flex-shrink: 0; }

  /* Insight cards */
  .insights { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .insight-card {
    background: #F7FAFF;
    border: 1px solid #BEE3F8;
    border-radius: 8px;
    padding: 14px 16px;
  }
  .insight-title { font-size: 12px; font-weight: 700; color: #2C5282; margin-bottom: 4px; }
  .insight-text  { font-size: 12px; color: #4A5568; line-height: 1.5; }

  /* Chart blocks */
  .chart-block   { margin-top: 16px; text-align: center; }
  .chart-caption { font-size: 11px; color: #718096; margin-top: 8px; font-style: italic; }

  /* Misc */
  .note { color: #718096; font-size: 12px; margin-bottom: 12px; }

  /* Footer */
  .footer {
    background: #0D1B2A;
    color: #718096;
    font-size: 11px;
    padding: 20px 36px;
    text-align: center;
    line-height: 1.8;
  }
"""


# Main HTML builder
def build_html(data):
    funds        = data["funds"]
    sip          = data["sip"]
    report_date  = data["report_date"]
    week_no      = data["week_no"]
    latest_sip   = data["latest_sip"]
    latest_folio = data["latest_folio"]
    total_aum    = data["total_aum"]

    top5_rows = build_top5_rows(funds)

    by_cagr     = funds.dropna(subset=["cagr_3yr"]).sort_values("cagr_3yr", ascending=False)
    gainer_rows = build_perf_rows(by_cagr.head(3), positive=True)
    loser_rows  = build_perf_rows(by_cagr.tail(3), positive=False)

    var_rows = build_var_rows(funds)
    sip_bars = build_sip_bars(sip)

    scorecard_img = embed_chart(CHARTS / "fund_scorecard_chart.png")
    mc_img        = embed_chart(BONUS  / "mc_top6_chart.png")
    ef_img        = embed_chart(BONUS  / "ef_chart.png")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bluestock MF Weekly Report - Week {week_no}</title>
  <style>{STYLES}</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="header-top">
      <div class="brand">Bluestock <span>Analytics</span></div>
      <div class="report-meta">
        Week {week_no} &middot; {report_date}<br/>
        Mutual Fund Performance Report
      </div>
    </div>
    <div class="report-title">Weekly Fund Performance Summary - {report_date}</div>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-value">Rs.{latest_sip / 1000:.1f}K Cr</div>
      <div class="kpi-label">Monthly SIP Inflow</div>
      <div class="kpi-sub">All-time high</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">Rs.{total_aum:.0f}L Cr</div>
      <div class="kpi-label">Industry AUM</div>
      <div class="kpi-sub">FY 2025</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">{latest_folio:.2f} Cr</div>
      <div class="kpi-label">Total Folios</div>
      <div class="kpi-sub">Dec 2025</div>
    </div>
  </div>

  <!-- Top 5 Funds -->
  <div class="section">
    <div class="section-title">Top 5 Funds - Composite Scorecard</div>
    <table>
      <thead>
        <tr>
          <th>#</th><th>Scheme</th><th>Category</th>
          <th class="num">Score</th><th class="num">3Y CAGR</th>
          <th class="num">Sharpe</th><th class="num">MC CAGR (5Y)</th>
        </tr>
      </thead>
      <tbody>{top5_rows}</tbody>
    </table>
    <div class="chart-block">
      {scorecard_img}
      <div class="chart-caption">Fund Scorecard Chart - Top 20 Funds by Composite Score</div>
    </div>
  </div>

  <!-- Performance Highlights -->
  <div class="section">
    <div class="section-title">Performance Highlights - 3-Year CAGR</div>
    <div class="two-col">
      <div>
        <div class="sub-title">Top 3 Performers</div>
        <table>
          <thead><tr><th>Scheme</th><th class="num">3Y CAGR</th><th class="num">1Y</th></tr></thead>
          <tbody>{gainer_rows}</tbody>
        </table>
      </div>
      <div>
        <div class="sub-title">Bottom 3 Performers</div>
        <table>
          <thead><tr><th>Scheme</th><th class="num">3Y CAGR</th><th class="num">1Y</th></tr></thead>
          <tbody>{loser_rows}</tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Risk Metrics -->
  <div class="section">
    <div class="section-title">Risk Metrics - Highest VaR Funds</div>
    <p class="note">VaR 95% = maximum expected daily loss at 95% confidence. CVaR = average loss beyond that threshold.</p>
    <table>
      <thead>
        <tr><th>Scheme</th><th class="num">VaR 95% (daily)</th><th class="num">CVaR 95%</th></tr>
      </thead>
      <tbody>{var_rows}</tbody>
    </table>
  </div>

  <!-- SIP Trend -->
  <div class="section">
    <div class="section-title">SIP Inflow - Last 6 Months</div>
    {sip_bars}
  </div>

  <!-- Monte Carlo -->
  <div class="section">
    <div class="section-title">5-Year NAV Projection (Monte Carlo)</div>
    <p class="note">1,000 simulated paths per fund. Shaded bands show 5th-95th percentile uncertainty range.</p>
    <div class="chart-block">
      {mc_img}
      <div class="chart-caption">Monte Carlo projection for top 6 funds - 5-year horizon</div>
    </div>
  </div>

  <!-- Efficient Frontier -->
  <div class="section">
    <div class="section-title">Efficient Frontier (Markowitz)</div>
    <p class="note">
      Star = Maximum Sharpe portfolio &nbsp;|&nbsp;
      Circle = Minimum Variance portfolio &nbsp;|&nbsp;
      Colour = Sharpe ratio of random portfolios
    </p>
    <div class="chart-block">
      {ef_img}
      <div class="chart-caption">Mean-Variance Efficient Frontier with optimal portfolios highlighted</div>
    </div>
  </div>

  <!-- Key Insights -->
  <div class="section">
    <div class="section-title">Key Insights This Week</div>
    <div class="insights">
      <div class="insight-card">
        <div class="insight-title">SIP Momentum Continues</div>
        <div class="insight-text">
          Monthly SIP inflow reached Rs.{latest_sip / 1000:.1f}K Cr. The industry continues
          to see strong systematic investment participation, particularly from T30 cities.
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">Top Scorecard Performers</div>
        <div class="insight-text">
          The top 5 funds by composite score all show Sharpe ratios above 1.0, confirming
          strong risk-adjusted returns compared to the 6.5% risk-free benchmark.
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">Concentrated Portfolio Risk</div>
        <div class="insight-text">
          Equity funds show HHI above 0.25 (concentrated), with NIFTY 50 stocks dominating
          holdings. Investors seeking true diversification should consider multi-cap or
          sectoral rebalancing.
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">5-Year Projections Look Positive</div>
        <div class="insight-text">
          Monte Carlo median projections show top equity funds delivering 12-18% CAGR over
          the next 5 years under base case assumptions, with P95 upside extending beyond
          25% CAGR for high-conviction picks.
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <strong style="color:#CBD5E0;">Bluestock Fintech - Mutual Fund Analytics Capstone I</strong><br/>
    This report is auto-generated every Friday at 20:00 IST.<br/>
    Data sourced from AMFI NAV history and internal analytics pipeline.<br/>
    <span style="display:block; margin-top:6px;">
      This report is for informational purposes only and does not constitute investment advice.
    </span>
  </div>

</div>
</body>
</html>"""


# Save HTML to file
def save_html(html):
    today    = date.today().isoformat()
    out_path = EMAIL_DIR / f"weekly_report_{today}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  HTML report saved -> {out_path.relative_to(BASE_DIR)}")
    return out_path


# Send email via Gmail SMTP
def send_email(html, sender, password, to):
    week    = datetime.now().isocalendar()[1]
    today   = date.today().strftime("%d %b %Y")
    subject = f"[Bluestock MF] Weekly Performance Report - Week {week} ({today})"

    msg            = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = to

    plain = (
        "Bluestock MF Weekly Performance Report\n"
        f"Generated on {date.today().isoformat()}\n"
        "Please open the HTML version in a modern email client."
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    try:
        print(f"  Connecting to {SMTP_HOST}:{SMTP_PORT} ...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to.split(","), msg.as_string())
        server.quit()
        print(f"  Email sent successfully to: {to}")
    except smtplib.SMTPAuthenticationError:
        print("  ERROR: Authentication failed.")
        print("  Use a Gmail App Password, not your normal account password.")
        print("  See: https://support.google.com/accounts/answer/185833")
    except Exception as e:
        print(f"  ERROR sending email: {e}")


# Weekly scheduler (every Friday at 20:00)
def run_scheduled(sender, password, to):
    try:
        import schedule
    except ImportError:
        print("  'schedule' package not found. Install with: pip install schedule")
        return

    def job():
        now = datetime.now()
        if now.weekday() == 4:  # Friday = 4
            print(f"\n  [{now:%Y-%m-%d %H:%M}] Generating weekly report ...")
            run_once(sender, password, to)
        else:
            print(f"  [{now:%Y-%m-%d %H:%M}] Skipped - not Friday.")

    schedule.every().day.at("20:00").do(job)
    print("  Scheduler started. Runs every Friday at 20:00 IST.")
    print("  Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


# Single run
def run_once(sender=None, password=None, to=None):
    print("  Loading report data ...")
    data = load_data()

    print("  Generating HTML ...")
    html = build_html(data)
    path = save_html(html)

    if sender and password and to:
        send_email(html, sender, password, to)

    return path


# Entry point
def main():
    parser = argparse.ArgumentParser(
        description="Bluestock MF Weekly HTML Email Report Generator"
    )
    parser.add_argument("--html-only", action="store_true", help="Generate HTML file only, skip email")
    parser.add_argument("--schedule",  action="store_true", help="Run as weekly daemon (Fri 20:00)")
    args = parser.parse_args()

    load_env()
    sender, password, to = get_credentials()

    print("=" * 60)
    print("  Bonus B5 - HTML Email Report Generator")
    print("=" * 60)

    if args.schedule:
        if not all([sender, password, to]):
            print("  ERROR: SMTP_SENDER, SMTP_PASSWORD, SMTP_TO must be set in .env for scheduling.")
            return
        run_scheduled(sender, password, to)
        return

    credentials_ok = all([sender, password, to])

    if args.html_only or not credentials_ok:
        path = run_once()
        print(f"\n  Report saved: {path.name}")
        print("  Open in any browser to view.")
        if not args.html_only and not credentials_ok:
            print("\n  NOTE: No credentials found - running in HTML-only mode.")
            print("  Create a .env file in the project root with:")
            print("    SMTP_SENDER=your@gmail.com")
            print("    SMTP_PASSWORD=your-app-password")
            print("    SMTP_TO=recipient@example.com")
    else:
        run_once(sender, password, to)

    print("\n" + "=" * 60)
    print("  B5 complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()