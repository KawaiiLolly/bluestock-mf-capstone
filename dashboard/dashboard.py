"""
    dashboard.py

    Run:
        streamlit run dashboard/dashboard.py

    All data loaded from data/processed/ and reports/performance/
    No hard-coded paths — uses pathlib relative to this file.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROC     = BASE_DIR / "data" / "processed"
PERF     = BASE_DIR / "reports" / "performance"

st.set_page_config(
    page_title="Bluestock MF Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY   = "#1565C0"
SECONDARY = "#43A047"
ACCENT    = "#FB8C00"
DANGER    = "#E53935"
COLORS    = [PRIMARY, SECONDARY, ACCENT, DANGER, "#7B1FA2",
             "#00838F", "#F4511E", "#558B2F", "#AD1457", "#283593"]

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)
st.markdown("""
<style>
    html, body, .stApp {
        font-family: 'Montserrat', sans-serif !important;
    }
    * {
        font-family: 'Montserrat', sans-serif !important;
    }
    h1,h2,h3,h4,h5,h6 {
        font-family: 'Montserrat', sans-serif !important;
    }
    p, div, span, label, button, input, textarea {
        font-family: 'Montserrat', sans-serif !important;
    }
w</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {background: #0D1B2A;}
    [data-testid="stSidebar"] * {color: #E0E0E0 !important;}

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%);
        border-radius: 12px;
        padding: 20px 18px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        margin: 4px 0;
    }
    .kpi-card.green  {background: linear-gradient(135deg,#2E7D32,#43A047);}
    .kpi-card.orange {background: linear-gradient(135deg,#E65100,#FB8C00);}
    .kpi-card.purple {background: linear-gradient(135deg,#4A148C,#7B1FA2);}

    .kpi-value {font-size:2.2rem; font-weight:800; color:#fff; line-height:1.1;}
    .kpi-label {font-size:0.85rem; color:rgba(255,255,255,0.85); margin-top:4px; font-weight:500;}
    .kpi-delta {font-size:0.75rem; color:rgba(255,255,255,0.7); margin-top:2px;}

    /* Page title */
    .page-title {
        font-size:1.6rem; font-weight:800; color:#1565C0;
        border-bottom: 3px solid #1565C0; padding-bottom:8px; margin-bottom:16px;
    }
    /* Header brand */
    .brand-header {
        background: linear-gradient(90deg,#0D1B2A,#1565C0);
        padding:14px 24px; border-radius:8px; margin-bottom:16px;
        display:flex; align-items:center; gap:12px;
    }
    .brand-title {color:#fff; font-size:1.4rem; font-weight:800;}
    .brand-sub   {color:rgba(255,255,255,0.7); font-size:0.85rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_all():
    fm      = pd.read_csv(PROC / "clean_fund_master.csv")
    nav     = pd.read_csv(PROC / "clean_nav_history.csv",         parse_dates=["date"])
    aum     = pd.read_csv(PROC / "clean_aum_by_fund_house.csv")
    sip     = pd.read_csv(PROC / "clean_monthly_sip_inflows.csv", parse_dates=["month"])
    cat     = pd.read_csv(PROC / "clean_category_inflows.csv")
    tx      = pd.read_csv(PROC / "clean_investor_transactions.csv", parse_dates=["transaction_date"])
    folio   = pd.read_csv(PROC / "clean_industry_folio_count.csv", parse_dates=["month"])
    bench   = pd.read_csv(PROC / "clean_benchmark_indices.csv",   parse_dates=["date"])
    hold    = pd.read_csv(PROC / "clean_portfolio_holdings.csv")
    score   = pd.read_csv(PERF  / "fund_scorecard.csv")
    ab      = pd.read_csv(PERF  / "alpha_beta.csv")
    cagr    = pd.read_csv(PERF  / "cagr_report.csv")
    sharpe  = pd.read_csv(PERF  / "sharpe_values.csv")
    dd      = pd.read_csv(PERF  / "max_drawdown.csv")
    return fm, nav, aum, sip, cat, tx, folio, bench, hold, score, ab, cagr, sharpe, dd

fm, nav, aum, sip, cat_inflow, tx, folio, bench, hold, score, ab, cagr, sharpe, dd = load_all()

score_full = score.merge(
    fm[["amfi_code","scheme_name","fund_house","category","sub_category","expense_ratio_pct"]],
    on="amfi_code", how="left", suffixes=("","_fm")
)

def kpi(value, label, delta="", color=""):
    css = f"kpi-card {color}".strip()
    return f"""
    <div class='{css}'>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-delta'>{delta}</div>
    </div>"""

st.sidebar.markdown("""
<div style='text-align:center; padding:12px 0 20px 0;'>
    <div style='font-size:1.5rem; font-weight:800; color:#64B5F6;'>Bluestock</div>
    <div style='font-size:0.75rem; color:#90A4AE;'>Mutual Fund Analytics</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["Industry Overview",
     "Fund Performance",
     "Investor Analytics",
     "SIP & Market Trends"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='font-size:0.7rem; color:#546E7A;'>Capstone I — Bluestock Fintech<br>Data as of Dec 2025</div>",
                    unsafe_allow_html=True)


# PAGE 1: Industry Overview
if "Industry Overview" in page:
    st.markdown("<div class='page-title'>Industry Overview</div>", unsafe_allow_html=True)

    aum["year"] = pd.to_datetime(aum["date"]).dt.year
    total_aum  = aum[aum["year"] == 2025]["aum_lakh_crore"].sum()
    
    latest_sip = (sip.sort_values("month").iloc[-1]["sip_inflow_crore"])
    latest_fol = (folio.sort_values("month").iloc[-1]["total_folios_crore"])
    n_schemes  = len(fm)
    yoy_sip    = ((sip.tail(12)["sip_inflow_crore"].mean() /
                   sip.iloc[-24:-12]["sip_inflow_crore"].mean() - 1) * 100)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi(f"₹{total_aum:.0f}L Cr", "Total Industry AUM", "FY 2025"),             unsafe_allow_html=True)
    c2.markdown(kpi(f"₹{latest_sip/1000:.1f}K Cr", "Monthly SIP Inflow", "Dec 2025 ATH", "green"),  unsafe_allow_html=True)
    c3.markdown(kpi(f"{latest_fol:.2f} Cr", "Total Folios", "Jan 2022 → Dec 2025", "orange"), unsafe_allow_html=True)
    c4.markdown(kpi(f"{n_schemes}", "Schemes in Dataset", f"SIP YoY ↑{yoy_sip:.1f}%", "purple"),  unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.4, 1])

    with col1:
        st.subheader("Industry AUM Trend (2022–2025)")
        aum_trend = aum.groupby("year")["aum_lakh_crore"].sum().reset_index()
        fig = px.area(aum_trend, x="year", y="aum_lakh_crore",
                      color_discrete_sequence=[PRIMARY],
                      labels={"aum_lakh_crore":"AUM (₹ Lakh Crore)","year":"Year"},
                      markers=True)
        fig.update_traces(fill="tozeroy", fillcolor="rgba(21,101,192,0.15)")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300)
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("AUM by Fund House — 2025")
        aum25 = aum[aum["year"]==2025].sort_values("aum_lakh_crore", ascending=True).tail(10)
        fig = px.bar(aum25, y="fund_house", x="aum_lakh_crore",
                     orientation="h", color="aum_lakh_crore",
                     color_continuous_scale=["#BBDEFB","#1565C0"],
                     labels={"aum_lakh_crore":"AUM (₹ Lakh Crore)","fund_house":"Fund House"},
                     text="aum_lakh_crore")
        fig.update_traces(texttemplate="₹%{x:.1f}L", textposition="outside")
        fig.update_layout(margin=dict(l=0,r=20,t=10,b=0), height=300,
                          showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Monthly SIP Inflow (Jan 2022 – Dec 2025)")
        fig = px.bar(sip, x="month", y="sip_inflow_crore",
                     color_discrete_sequence=[SECONDARY],
                     labels={"sip_inflow_crore":"SIP Inflow (₹ Cr)","month":"Month"})
        # Annotate ATH
        peak = sip.loc[sip["sip_inflow_crore"].idxmax()]
        fig.add_annotation(x=peak["month"], y=peak["sip_inflow_crore"],
                           text="₹31,002 Cr<br>ATH", showarrow=True,
                           arrowhead=2, ax=0, ay=-40,
                           bgcolor=ACCENT, font=dict(color="white", size=11))
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280)
        st.plotly_chart(fig, width='stretch')

    with col4:
        st.subheader("Industry Folio Count Growth")
        fig = px.line(folio, x="month", y="total_folios_crore",
                      color_discrete_sequence=[ACCENT], markers=False,
                      labels={"total_folios_crore":"Folios (Crore)","month":"Month"})
        fig.update_traces(line=dict(width=2.5))
        fig.add_hline(y=20, line_dash="dot", line_color="grey",
                      annotation_text="20 Cr milestone")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Category-wise Net Inflows — Latest Quarter")
    cat_latest = (cat_inflow.groupby("category")["net_inflow_crore"]
                  .sum().reset_index()
                  .sort_values("net_inflow_crore", ascending=False))
    fig = px.pie(cat_latest, values="net_inflow_crore", names="category",
                 hole=0.42, color_discrete_sequence=COLORS)
    fig.update_traces(textposition="outside", textinfo="label+percent")
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300,
                      legend=dict(orientation="h"))
    st.plotly_chart(fig, width='stretch')


# Page 2: Fund Performance
elif "Fund Performance" in page:
    st.markdown("<div class='page-title'>Fund Performance</div>", unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns(3)
    fund_houses = ["All"] + sorted(fm["fund_house"].unique().tolist())
    categories  = ["All"] + sorted(fm["category"].unique().tolist())
    sel_house   = sc1.selectbox("Fund House", fund_houses)
    sel_cat     = sc2.selectbox("Category",  categories)
    sel_metric  = sc3.selectbox("Sort Scorecard By",
                                ["composite_score","cagr_3yr","sharpe_ratio","alpha_annual","max_drawdown_pct"])

    df_filt = score_full.copy()
    if sel_house != "All":
        df_filt = df_filt[df_filt["fund_house"] == sel_house]
    if sel_cat != "All":
        df_filt = df_filt[df_filt["category"] == sel_cat]

    st.markdown(f"**{len(df_filt)} funds** matching filters")

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("Risk vs Return (3-Year)")
        scatter_df = df_filt.merge(
            sharpe[["amfi_code","std_daily"]], on="amfi_code", how="left"
        ).merge(
            cagr[["amfi_code","cagr_3yr"]], on="amfi_code", how="left", suffixes=("","_c")
        )
        scatter_df["risk_ann_pct"] = scatter_df["std_daily"] * np.sqrt(252) * 100
        scatter_df["short"] = scatter_df["scheme_name"].str.split().str[:2].str.join(" ")

        fig = px.scatter(scatter_df.dropna(subset=["cagr_3yr","risk_ann_pct"]),
                         x="cagr_3yr", y="risk_ann_pct",
                         color="category", size="composite_score",
                         hover_name="short",
                         size_max=35,
                         color_discrete_sequence=COLORS,
                         labels={"cagr_3yr":"3-Year CAGR (%)",
                                 "risk_ann_pct":"Annualised Risk (Std Dev %)",
                                 "aum_crore":"AUM (₹ Crore)"})
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=360,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Fund Scorecard")
        show_cols = ["scheme_name","composite_score","cagr_3yr","sharpe_ratio",
                     "alpha_annual","max_drawdown_pct","direct_plan_er"]
        existing  = [c for c in show_cols if c in df_filt.columns]
        tbl = df_filt.sort_values(sel_metric, ascending=(sel_metric=="max_drawdown_pct")).head(15)
        tbl = tbl[existing].rename(columns={
            "scheme_name":      "Fund",
            "composite_score":  "Score",
            "cagr_3yr":         "3Y CAGR%",
            "sharpe_ratio":     "Sharpe",
            "alpha_annual":     "Alpha%",
            "max_drawdown_pct": "MaxDD%",
            "direct_plan_er":   "ER%",
        })
        tbl = tbl.reset_index(drop=True)
        st.dataframe(tbl, width='stretch', height=360)

    st.subheader("NAV Trend — Select Fund vs Benchmark")
    fund_options = df_filt["scheme_name"].tolist() if len(df_filt) else fm["scheme_name"].tolist()
    sel_fund = st.selectbox("Select Fund", fund_options[:20])

    sel_code  = fm[fm["scheme_name"] == sel_fund]["amfi_code"].iloc[0]
    nav_fund  = nav[nav["amfi_code"] == sel_code].sort_values("date")
    nav_start = nav_fund["date"].max() - pd.DateOffset(years=3)
    nav_fund  = nav_fund[nav_fund["date"] >= nav_start].copy()
    base_f    = nav_fund["nav"].iloc[0]
    nav_fund["norm"] = nav_fund["nav"] / base_f * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nav_fund["date"], y=nav_fund["norm"],
                             name=sel_fund.split()[0]+" "+sel_fund.split()[1],
                             line=dict(color=PRIMARY, width=2)))

    for bname, bcolor, bstyle in [("Nifty 50", "#333", "dash"),
                                   ("Nifty 100","#888","dot")]:
        b = bench[bench["index_name"]==bname].sort_values("date")
        b = b[b["date"] >= nav_start]
        if len(b):
            base_b = b["close_value"].iloc[0]
            fig.add_trace(go.Scatter(x=b["date"], y=b["close_value"]/base_b*100,
                                     name=bname,
                                     line=dict(color=bcolor, dash=bstyle, width=1.5)))

    fig.add_hline(y=100, line_dash="dot", line_color="grey")
    fig.update_layout(
        margin=dict(l=0,r=0,t=10,b=0), height=320,
        yaxis_title="Normalised (Base=100)",
        legend=dict(orientation="h")
    )
    st.plotly_chart(fig, width='stretch')

    st.subheader("Alpha & Beta Summary")
    ab_show = df_filt.merge(ab[["amfi_code","r_squared"]],
                             on="amfi_code", how="left")
    ab_tbl = ab_show[["scheme_name","beta","alpha_annual","r_squared","category"]].dropna()
    ab_tbl.columns = ["Fund","Beta","Alpha%","R²","Category"]
    fig = px.bar(ab_tbl.sort_values("Alpha%", ascending=False).head(15),
                 x="Fund", y="Alpha%", color="Category",
                 color_discrete_sequence=COLORS,
                 labels={"Fund":"","Alpha%":"Alpha (Annualised %)"})
    fig.update_xaxes(tickangle=45)
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280,
                      legend=dict(orientation="h"))
    st.plotly_chart(fig, width='stretch')

# Page 3: Investor Analytics
elif "Investor Analytics" in page:
    st.markdown("<div class='page-title'>Investor Analytics</div>", unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns(3)
    states_list = ["All"] + sorted(tx["state"].dropna().unique().tolist())
    age_list    = ["All"] + ["18-25","26-35","36-45","46-55","56+"]
    tier_list   = ["All","T30","B30"]
    sel_state   = sc1.selectbox("State",     states_list)
    sel_age     = sc2.selectbox("Age Group", age_list)
    sel_tier    = sc3.selectbox("City Tier", tier_list)

    tx_f = tx.copy()
    if sel_state != "All": tx_f = tx_f[tx_f["state"]    == sel_state]
    if sel_age   != "All": tx_f = tx_f[tx_f["age_group"] == sel_age]
    if sel_tier  != "All": tx_f = tx_f[tx_f["city_tier"] == sel_tier]

    st.markdown(f"**{len(tx_f):,} transactions** matching filters")

    k1,k2,k3,k4 = st.columns(4)
    sip_count = len(tx_f[tx_f["transaction_type"]=="SIP"])
    k1.metric("Total Transactions",f"{len(tx_f):,}")
    k2.metric("SIP Transactions",  f"{sip_count:,}")
    k3.metric("Avg SIP Amount",    f"₹{tx_f[tx_f['transaction_type']=='SIP']['amount_inr'].mean():,.0f}")
    k4.metric("Unique Investors",  f"{tx_f['investor_id'].nunique():,}")

    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("SIP Amount by State")
        sip_state = (tx_f[tx_f["transaction_type"]=="SIP"]
                     .groupby("state")["amount_inr"].sum()
                     .reset_index()
                     .sort_values("amount_inr"))
        sip_state["amount_cr"] = (sip_state["amount_inr"] / 1e7).round(2)
        fig = px.bar(sip_state, y="state", x="amount_cr",
                     orientation="h", color="amount_cr",
                     color_continuous_scale=["#BBDEFB","#1565C0"],
                     labels={"amount_cr":"SIP Amount (₹ Crore)","state":"State"},
                     text="amount_cr")
        fig.update_traces(texttemplate="₹%{x:.1f}", textposition="outside")
        fig.update_layout(margin=dict(l=0,r=20,t=10,b=0), height=320,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Transaction Type Split")
        tx_split = tx_f["transaction_type"].value_counts().reset_index()
        tx_split.columns = ["type","count"]
        fig = px.pie(tx_split, values="count", names="type",
                     hole=0.45, color_discrete_sequence=COLORS)
        fig.update_traces(textposition="outside", textinfo="label+percent")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=320,
                          legend=dict(orientation="h"))
        st.plotly_chart(fig, width='stretch')

    col3, col4, col5 = st.columns([1.2, 1, 1])

    with col3:
        st.subheader("Avg SIP by Age Group")
        age_order = ["18-25","26-35","36-45","46-55","56+"]
        age_sip   = (tx_f[tx_f["transaction_type"]=="SIP"]
                     .groupby("age_group")["amount_inr"].mean()
                     .reindex(age_order).reset_index())
        age_sip.columns = ["age_group","avg_sip"]
        fig = px.bar(age_sip, x="age_group", y="avg_sip",
                     color="avg_sip",
                     color_continuous_scale=["#C8E6C9","#1B5E20"],
                     labels={"avg_sip":"Avg SIP (₹)","age_group":"Age Group"},
                     text_auto=",.0f")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=270,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

    with col4:
        st.subheader("Gender Split")
        gen = tx_f["gender"].value_counts().reset_index()
        gen.columns = ["gender","count"]
        fig = px.pie(gen, values="count", names="gender",
                     hole=0.45,
                     color_discrete_sequence=[PRIMARY, DANGER, ACCENT])
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=270,
                          showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col5:
        st.subheader("T30 vs B30")
        tier = tx_f["city_tier"].value_counts().reset_index()
        tier.columns = ["tier","count"]
        fig = px.pie(tier, values="count", names="tier",
                     hole=0.45,
                     color_discrete_sequence=[PRIMARY, ACCENT])
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=270,
                          showlegend=False)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Monthly Transaction Volume")
    tx_f["month"] = tx_f["transaction_date"].dt.to_period("M").astype(str)
    monthly = (tx_f.groupby(["month","transaction_type"])["amount_inr"]
               .sum().reset_index())
    fig = px.line(monthly, x="month", y="amount_inr",
                  color="transaction_type",
                  color_discrete_sequence=COLORS,
                  labels={"amount":"Amount (₹)","month":"Month","transaction_type":"Type"},
                  markers=False)
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=260,
                      legend=dict(orientation="h"))
    all_months = sorted(monthly["month"].unique())
    step = max(1, len(all_months)//12)
    fig.update_xaxes(tickvals=all_months[::step], tickangle=45)
    st.plotly_chart(fig, width='stretch')


# Page 4: SIP & Market Trends
elif "SIP & Market Trends" in page:
    st.markdown("<div class='page-title'>SIP & Market Trends</div>", unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    years_avail = sorted(sip["month"].dt.year.unique().tolist())
    year_range  = sc1.select_slider("Year Range",
                                     options=years_avail,
                                     value=(min(years_avail), max(years_avail)))
    sel_index  = sc2.selectbox("Benchmark Index",
                                ["Nifty 50","Nifty 100"])

    sip_f = sip[(sip["month"].dt.year >= year_range[0]) &
                (sip["month"].dt.year <= year_range[1])].copy()

    k1,k2,k3,k4 = st.columns(4)
    start_acc = sip_f["active_sip_accounts_crore"].iloc[0]
    end_acc   = sip_f["active_sip_accounts_crore"].iloc[-1]
    yoy_acc   = (end_acc - start_acc) / start_acc * 100
    k1.metric("SIP ATH",         f"₹{sip_f['sip_inflow_crore'].max():,.0f} Cr")
    k2.metric("SIP CAGR (period)",f"{((sip_f['sip_inflow_crore'].iloc[-1]/sip_f['sip_inflow_crore'].iloc[0])**(12/len(sip_f))-1)*100:.1f}%/yr")
    k3.metric("Folio ATH",       f"{folio['total_folios_crore'].max():.2f} Cr")
    k4.metric("Accounts YoY",    f"+{yoy_acc:.1f}%")

    st.subheader(f"SIP Inflow (Bar) vs {sel_index} (Line) — Dual Axis")
    bench_idx = bench[bench["index_name"] == sel_index].sort_values("date")
    # Monthly average index value
    bench_idx["month"] = bench_idx["date"].dt.to_period("M").dt.to_timestamp()
    bench_monthly = bench_idx.groupby("month")["close_value"].mean().reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=sip_f["month"], y=sip_f["sip_inflow_crore"],
               name="SIP Inflow (₹ Cr)", marker_color=SECONDARY, opacity=0.75),
        secondary_y=False
    )
    bm_filt = bench_monthly[
        (bench_monthly["month"].dt.year >= year_range[0]) &
        (bench_monthly["month"].dt.year <= year_range[1])
    ]
    fig.add_trace(
        go.Scatter(x=bm_filt["month"], y=bm_filt["close_value"],
                   name=sel_index, line=dict(color=PRIMARY, width=2.5)),
        secondary_y=True
    )
    fig.update_yaxes(title_text="SIP Inflow (₹ Crore)", secondary_y=False)
    fig.update_yaxes(title_text=f"{sel_index} Level", secondary_y=True)
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=320,
                      legend=dict(orientation="h"), barmode="overlay")
    st.plotly_chart(fig, width='stretch')

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.subheader("Category Inflow Heatmap (2022–2025)")
        cat_filt = cat_inflow[cat_inflow["month"].str[:4].astype(int).between(
            year_range[0], year_range[1]
        )]
        pivot = cat_filt.pivot_table(
            index="category", columns="month",
            values="net_inflow_crore", aggfunc="sum"
        )
        all_cols = list(pivot.columns)
        show_labels = {c: c if i % 3 == 0 else "" for i, c in enumerate(all_cols)}

        fig = px.imshow(pivot, color_continuous_scale="YlOrRd",
                        aspect="auto",
                        labels=dict(color="Net Inflow (₹ Cr)"))
        fig.update_xaxes(tickvals=list(show_labels.keys()),
                         ticktext=list(show_labels.values()),
                         tickangle=45)
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=320)
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Top Categories — Net Inflow FY25")
        fy25_months = [m for m in cat_inflow["month"].unique()
                       if m.startswith("2025") or m.startswith("2024")]
        top_cat = (cat_inflow[cat_inflow["month"].isin(fy25_months)]
                   .groupby("category")["net_inflow_crore"].sum()
                   .reset_index()
                   .sort_values("net_inflow_crore", ascending=True))
        fig = px.bar(top_cat, y="category", x="net_inflow_crore",
                     orientation="h", color="net_inflow_crore",
                     color_continuous_scale=["#FFF9C4","#F57F17"],
                     labels={"net_inflow_crore":"Net Inflow (₹ Cr)","category":""},
                     text_auto=",.0f")
        fig.update_layout(margin=dict(l=0,r=20,t=10,b=0), height=320,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Folio Count Growth")
        fol_f = folio[(folio["month"].dt.year >= year_range[0]) &
                      (folio["month"].dt.year <= year_range[1])]
        fig = px.area(fol_f, x="month", y="total_folios_crore",
                      color_discrete_sequence=[ACCENT],
                      labels={"total_folios_crore":"Folios (Crore)","month":"Month"})
        fig.update_traces(fill="tozeroy"    , fillcolor="rgba(251,140,0,0.15)")
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=270)
        st.plotly_chart(fig, width='stretch')

    with col4:
        st.subheader("SIP Accounts Growth (Crore)")
        fig = px.line(sip_f, x="month", y="active_sip_accounts_crore",
                      color_discrete_sequence=[PRIMARY],
                      labels={"sip_accounts_crore":"Accounts (Crore)","month":"Month"},
                      markers=True)
        fig.update_traces(line=dict(width=2))
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=270)
        st.plotly_chart(fig, width='stretch')
