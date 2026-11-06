"""
🪔 Diwali Sale 2025 — Interactive Executive Dashboard
=======================================================
A multi-page Streamlit dashboard with Plotly charts, KPI cards,
interactive filters, and statistical insights.

Run:  streamlit run dashboard/app.py
"""

import os, sys, json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="🪔 Diwali Sale 2025 — Executive Dashboard",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1E2A3A 0%, #243B5C 100%);
        border: 1px solid #FF6F0040;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: #FF6F00; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #FF6F00; margin: 4px 0; }
    .kpi-label { font-size: 13px; color: #B0BEC5; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-delta { font-size: 12px; margin-top: 4px; }
    .kpi-delta.good { color: #4CAF50; }
    .kpi-delta.bad { color: #F44336; }

    /* Section headers */
    .section-header {
        color: #FFD700;
        font-size: 18px;
        font-weight: 600;
        margin: 24px 0 12px;
        padding-bottom: 6px;
        border-bottom: 2px solid #FF6F0040;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0a0f1a; }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] { color: #B0BEC5; }
    .stTabs [aria-selected="true"] { color: #FF6F00 !important; }

    /* Title bar */
    .title-bar {
        background: linear-gradient(90deg, #1B2A4A, #0E1117);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #FF6F0030;
    }
    .title-bar h1 { color: #FFD700; margin: 0; font-size: 28px; }
    .title-bar p { color: #B0BEC5; margin: 4px 0 0; font-size: 14px; }

    div[data-testid="stMetric"] { background: #1E2A3A; border-radius: 8px; padding: 12px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING (cached)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """Load and merge all dimension + fact tables."""
    # Try cleaned first, then fall back to clean
    fact_path = cfg.CLEANED_ORDERS_PATH if os.path.exists(cfg.CLEANED_ORDERS_PATH) else cfg.CLEAN_ORDERS_PATH
    if not os.path.exists(fact_path):
        st.error(f"❌ Data not found at `{fact_path}`. Run the pipeline first: `python main.py all`")
        st.stop()

    fact = pd.read_csv(fact_path)
    redundant_cols = [c for c in ["City_Name", "Category", "Sub_Category"] if c in fact.columns]
    if redundant_cols:
        fact = fact.drop(columns=redundant_cols)

    cities = pd.read_csv(cfg.DIM_CITIES_PATH)
    products = pd.read_csv(cfg.DIM_PRODUCTS_PATH)
    customers = pd.read_csv(cfg.DIM_CUSTOMERS_PATH)
    dates = pd.read_csv(cfg.DIM_DATES_PATH)

    df = (
        fact
        .merge(cities, on="City_ID", how="left")
        .merge(products, on="Product_ID", how="left")
        .merge(customers, on="Customer_ID", how="left")
        .merge(dates, left_on="Order_Date", right_on="Date", how="left")
    )
    df["Order_Hour"] = df["Order_Time"].str[:2].astype(int)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    return df

@st.cache_data
def load_stats_results():
    """Load statistical analysis results if available."""
    if os.path.exists(cfg.STATS_RESULTS_PATH):
        with open(cfg.STATS_RESULTS_PATH, "r") as f:
            return json.load(f)
    return None

PALETTE = cfg.COLORS["chart_palette"]

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def format_inr(value):
    """Format number in Indian Lakhs/Crore notation."""
    if value >= 1e7:
        return f"₹{value/1e7:.2f} Cr"
    elif value >= 1e5:
        return f"₹{value/1e5:.2f} L"
    else:
        return f"₹{value:,.0f}"

def kpi_card(label, value, delta=None, delta_good=True):
    """Render a styled KPI card."""
    delta_html = ""
    if delta:
        cls = "good" if delta_good else "bad"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """

def plotly_defaults(fig, height=400):
    """Apply consistent Diwali theme to plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=20, t=40, b=40),
        colorway=PALETTE,
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

def main():
    df_full = load_data()

    # ── SIDEBAR FILTERS ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🪔 Filters")
        st.markdown("---")

        # Date range
        all_dates = sorted(df_full["Order_Date"].unique())
        date_range = st.date_input(
            "📅 Date Range",
            value=(all_dates[0], all_dates[-1]),
            min_value=all_dates[0],
            max_value=all_dates[-1],
        )

        # City tier
        all_tiers = sorted(df_full["City_Tier"].dropna().unique())
        selected_tiers = st.multiselect("🏙️ City Tier", all_tiers, default=all_tiers)

        # Category
        all_cats = sorted(df_full["Category"].dropna().unique())
        selected_cats = st.multiselect("📦 Category", all_cats, default=all_cats)

        # Payment
        all_payments = sorted(df_full["Payment_Method"].dropna().unique())
        selected_payments = st.multiselect("💳 Payment Method", all_payments, default=all_payments)

        st.markdown("---")
        st.caption("Data: Synthetic · 10K orders · Oct 2025")
        st.caption("Built for portfolio demonstration")

    # ── APPLY FILTERS ──────────────────────────────────────────────────
    df = df_full.copy()
    if len(date_range) == 2:
        df = df[(df["Order_Date"] >= pd.Timestamp(date_range[0])) &
                (df["Order_Date"] <= pd.Timestamp(date_range[1]))]
    df = df[df["City_Tier"].isin(selected_tiers)]
    df = df[df["Category"].isin(selected_cats)]
    df = df[df["Payment_Method"].isin(selected_payments)]

    delivered = df[df["Delivery_Status"] != "Cancelled"]

    # ── HEADER ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="title-bar">
        <h1>🪔 Diwali Sale 2025 — Executive Performance Dashboard</h1>
        <p>Festive e-commerce analytics · 7-day sale event · 23–29 October 2025</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI ROW ────────────────────────────────────────────────────────
    gmv = df["Order_Value_INR"].sum()
    net_rev = delivered["Order_Value_INR"].sum()
    total_orders = len(df)
    total_units = df["Quantity"].sum()
    aov = df["Order_Value_INR"].mean()
    unique_customers = df["Customer_ID"].nunique()
    delay_pct = 100 * (df["Delivery_Status"] == "Delayed").mean() if len(df) > 0 else 0
    return_pct = 100 * (delivered["Return_Status"] == "Returned").mean() if len(delivered) > 0 else 0

    cols = st.columns(6)
    kpis = [
        ("Gross GMV", format_inr(gmv), f"{total_orders:,} orders", True),
        ("Net Revenue", format_inr(net_rev), f"{100*net_rev/gmv:.0f}% of GMV" if gmv > 0 else "", True),
        ("Units Sold", f"{total_units:,}", f"{unique_customers:,} customers", True),
        ("Avg Order Value", f"₹{aov:,.0f}" if not np.isnan(aov) else "—", f"Median: ₹{df['Order_Value_INR'].median():,.0f}" if len(df) > 0 else "", True),
        ("Delayed Orders", f"{delay_pct:.1f}%", "Target: <15%", delay_pct < 15),
        ("Return Rate", f"{return_pct:.1f}%", "Target: <10%", return_pct < 10),
    ]
    for col, (label, value, delta, good) in zip(cols, kpis):
        col.markdown(kpi_card(label, value, delta, good), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ───────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Revenue Overview",
        "📦 Product & Category",
        "👥 Customer Intelligence",
        "🚚 Operations",
        "📐 Statistical Insights",
    ])

    # ── TAB 1: REVENUE OVERVIEW ────────────────────────────────────────
    with tab1:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<div class="section-header">Daily Revenue & Order Trend</div>', unsafe_allow_html=True)
            daily = df.groupby("Order_Date").agg(
                revenue=("Order_Value_INR", "sum"),
                orders=("Order_ID", "count"),
            ).reset_index()

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=daily["Order_Date"], y=daily["revenue"], name="Revenue (₹)",
                           fill="tozeroy", line=dict(color="#FF6F00", width=2),
                           fillcolor="rgba(255,111,0,0.15)"),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=daily["Order_Date"], y=daily["orders"], name="Orders",
                           line=dict(color="#FFD700", width=2, dash="dot"),
                           mode="lines+markers"),
                secondary_y=True,
            )
            fig.update_yaxes(title_text="Revenue (₹)", secondary_y=False, gridcolor="#1a2a3a")
            fig.update_yaxes(title_text="Order Count", secondary_y=True, gridcolor="#1a2a3a")
            fig.update_xaxes(gridcolor="#1a2a3a")
            plotly_defaults(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">Revenue by City Tier</div>', unsafe_allow_html=True)
            tier_rev = df.groupby("City_Tier")["Order_Value_INR"].sum().reset_index()
            fig = px.pie(tier_rev, values="Order_Value_INR", names="City_Tier",
                         color_discrete_sequence=["#FF6F00", "#FFD700", "#4FC3F7"],
                         hole=0.45)
            fig.update_traces(textinfo="percent+label", textfont_size=13)
            plotly_defaults(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)

        # Hourly heatmap
        st.markdown('<div class="section-header">📊 Order Volume Heatmap — Day × Hour</div>', unsafe_allow_html=True)
        heatmap_data = df.groupby([df["Order_Date"].dt.strftime("%b %d (%a)"), "Order_Hour"]).size().reset_index(name="Orders")
        heatmap_pivot = heatmap_data.pivot(index=heatmap_data.columns[0], columns="Order_Hour", values="Orders").fillna(0)
        # Sort by date
        heatmap_pivot = heatmap_pivot.sort_index()

        fig = px.imshow(
            heatmap_pivot.values,
            x=[f"{h:02d}:00" for h in heatmap_pivot.columns],
            y=heatmap_pivot.index.tolist(),
            color_continuous_scale=["#0E1117", "#FF6F00", "#FFD700"],
            aspect="auto",
            labels=dict(x="Hour of Day", y="Date", color="Orders"),
        )
        plotly_defaults(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2: PRODUCT & CATEGORY ──────────────────────────────────────
    with tab2:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown('<div class="section-header">Revenue by Category</div>', unsafe_allow_html=True)
            cat_rev = (df.groupby("Category")["Order_Value_INR"].sum()
                       .sort_values(ascending=True).reset_index())
            fig = px.bar(cat_rev, y="Category", x="Order_Value_INR", orientation="h",
                         color="Order_Value_INR", color_continuous_scale=["#1B2A4A", "#FF6F00", "#FFD700"])
            fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="inside")
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            plotly_defaults(fig, height=420)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">Sub-Category Treemap</div>', unsafe_allow_html=True)
            subcat = df.groupby(["Category", "Sub_Category"])["Order_Value_INR"].sum().reset_index()
            fig = px.treemap(subcat, path=["Category", "Sub_Category"], values="Order_Value_INR",
                             color="Order_Value_INR",
                             color_continuous_scale=["#1B2A4A", "#FF6F00", "#FFD700"])
            fig.update_layout(coloraxis_showscale=False)
            plotly_defaults(fig, height=420)
            st.plotly_chart(fig, use_container_width=True)

        # Discount effectiveness
        st.markdown('<div class="section-header">Discount Effectiveness Analysis</div>', unsafe_allow_html=True)
        disc = df.groupby("Discount_Pct").agg(
            orders=("Order_ID", "count"),
            revenue=("Order_Value_INR", "sum"),
            aov=("Order_Value_INR", "mean"),
        ).reset_index()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(disc, x="Discount_Pct", y="orders", color="revenue",
                         color_continuous_scale=["#1B2A4A", "#FFD700"],
                         labels={"Discount_Pct": "Discount %", "orders": "Orders"})
            fig.update_layout(coloraxis_showscale=False)
            plotly_defaults(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(disc, x="Discount_Pct", y="aov", size="orders",
                             color_discrete_sequence=["#FF6F00"],
                             labels={"Discount_Pct": "Discount %", "aov": "Avg Order Value (₹)"})
            plotly_defaults(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

        # Category performance table
        st.markdown('<div class="section-header">Category Performance Table</div>', unsafe_allow_html=True)
        cat_table = df.groupby("Category").agg(
            Orders=("Order_ID", "count"),
            Units=("Quantity", "sum"),
            Revenue=("Order_Value_INR", "sum"),
            AOV=("Order_Value_INR", "mean"),
        ).round(0)
        # Add cancel and return rates
        cancel_rates = ((df["Delivery_Status"] == "Cancelled").groupby(df["Category"]).mean() * 100).rename("Cancel %")
        delivered_mask = df["Delivery_Status"] != "Cancelled"
        return_rates = ((df.loc[delivered_mask, "Return_Status"] == "Returned").groupby(df.loc[delivered_mask, "Category"]).mean() * 100).rename("Return %")
        cat_table = cat_table.join(cancel_rates).join(return_rates).fillna(0).round(1)
        cat_table["Revenue"] = cat_table["Revenue"].apply(lambda x: f"₹{x:,.0f}")
        cat_table["AOV"] = cat_table["AOV"].apply(lambda x: f"₹{x:,.0f}")
        cat_table["Cancel %"] = cat_table["Cancel %"].apply(lambda x: f"{x:.1f}%")
        cat_table["Return %"] = cat_table["Return %"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(cat_table.sort_values("Orders", ascending=False), use_container_width=True)

    # ── TAB 3: CUSTOMER INTELLIGENCE ───────────────────────────────────
    with tab3:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown('<div class="section-header">New vs Repeat Customers</div>', unsafe_allow_html=True)
            cohort = df.groupby(df["Is_Repeat_Customer"].map({True: "Repeat", False: "New"})).agg(
                Customers=("Customer_ID", "nunique"),
                Orders=("Order_ID", "count"),
                Revenue=("Order_Value_INR", "sum"),
                AOV=("Order_Value_INR", "mean"),
            ).reset_index().rename(columns={"Is_Repeat_Customer": "Type"})

            fig = make_subplots(rows=1, cols=2, subplot_titles=("Orders", "Revenue (₹)"),
                                specs=[[{"type": "pie"}, {"type": "pie"}]])
            fig.add_trace(go.Pie(labels=cohort["Type"], values=cohort["Orders"],
                                  marker_colors=["#4FC3F7", "#FF6F00"], hole=0.4,
                                  textinfo="percent+label"), row=1, col=1)
            fig.add_trace(go.Pie(labels=cohort["Type"], values=cohort["Revenue"],
                                  marker_colors=["#4FC3F7", "#FF6F00"], hole=0.4,
                                  textinfo="percent+label"), row=1, col=2)
            plotly_defaults(fig, height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">Orders by Age Group & Gender</div>', unsafe_allow_html=True)
            demo = df.groupby(["Age_Group", "Gender"]).size().reset_index(name="Orders")
            fig = px.bar(demo, x="Age_Group", y="Orders", color="Gender", barmode="group",
                         color_discrete_sequence=["#FF6F00", "#4FC3F7", "#FFD700"])
            plotly_defaults(fig, height=350)
            st.plotly_chart(fig, use_container_width=True)

        # RFM Segmentation
        st.markdown('<div class="section-header">RFM Customer Segmentation</div>', unsafe_allow_html=True)
        rfm = delivered.groupby("Customer_ID").agg(
            last_order=("Order_Date", "max"),
            frequency=("Order_ID", "count"),
            monetary=("Order_Value_INR", "sum"),
        ).reset_index()

        for col_name in ["last_order", "frequency", "monetary"]:
            rfm[f"{col_name[0].upper()}_score"] = pd.qcut(
                rfm[col_name].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
            ).astype(int)

        # Rename for clarity
        rfm.rename(columns={"L_score": "R_score"}, inplace=True)

        def segment(row):
            r, f, m = row["R_score"], row["F_score"], row["M_score"]
            if r >= 4 and f >= 4 and m >= 4: return "Champion"
            if r >= 3 and f >= 3 and m >= 3: return "Loyal"
            if r >= 4 and f <= 2:            return "New High-Value"
            if r <= 2 and f >= 3:            return "At Risk"
            if r <= 2 and f <= 2 and m <= 2: return "Hibernating"
            return "Potential"

        rfm["Segment"] = rfm.apply(segment, axis=1)
        seg_counts = rfm["Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customers"]

        segment_colors = {
            "Champion": "#4CAF50", "Loyal": "#FF6F00", "Potential": "#FFD700",
            "New High-Value": "#4FC3F7", "At Risk": "#FFC107", "Hibernating": "#F44336",
        }

        fig = px.bar(seg_counts, x="Segment", y="Customers",
                     color="Segment", color_discrete_map=segment_colors)
        fig.update_layout(showlegend=False)
        plotly_defaults(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

        # Top customers table
        st.markdown('<div class="section-header">Top 10 Customers by Spend</div>', unsafe_allow_html=True)
        top_cust = (
            delivered.groupby(["Customer_ID", "Customer_Name", "Gender", "Age_Group"])
            .agg(Orders=("Order_ID", "count"), Total_Spend=("Order_Value_INR", "sum"))
            .sort_values("Total_Spend", ascending=False)
            .head(10)
            .reset_index()
        )
        top_cust["Total_Spend"] = top_cust["Total_Spend"].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(top_cust, use_container_width=True, hide_index=True)

    # ── TAB 4: OPERATIONS ──────────────────────────────────────────────
    with tab4:
        col_left, col_mid, col_right = st.columns(3)

        with col_left:
            st.markdown('<div class="section-header">Delivery Performance</div>', unsafe_allow_html=True)
            del_counts = df["Delivery_Status"].value_counts().reset_index()
            del_counts.columns = ["Status", "Count"]
            fig = px.pie(del_counts, values="Count", names="Status",
                         color="Status", color_discrete_map=cfg.COLORS["delivery"],
                         hole=0.5)
            fig.update_traces(textinfo="percent+label")
            plotly_defaults(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)

        with col_mid:
            st.markdown('<div class="section-header">Return Status</div>', unsafe_allow_html=True)
            ret_counts = delivered["Return_Status"].value_counts().reset_index()
            ret_counts.columns = ["Status", "Count"]
            fig = px.pie(ret_counts, values="Count", names="Status",
                         color="Status",
                         color_discrete_map={"Kept": "#4CAF50", "Returned": "#F44336"},
                         hole=0.5)
            fig.update_traces(textinfo="percent+label")
            plotly_defaults(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">Payment Methods</div>', unsafe_allow_html=True)
            pay_counts = df["Payment_Method"].value_counts().reset_index()
            pay_counts.columns = ["Method", "Count"]
            fig = px.bar(pay_counts, y="Method", x="Count", orientation="h",
                         color="Count", color_continuous_scale=["#1B2A4A", "#FF6F00"])
            fig.update_layout(coloraxis_showscale=False, showlegend=False)
            plotly_defaults(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)

        # Regional analysis
        st.markdown('<div class="section-header">Regional Performance</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            region_stats = df.groupby(["Region", "City_Tier"]).agg(
                Orders=("Order_ID", "count"),
                Revenue=("Order_Value_INR", "sum"),
            ).reset_index()
            fig = px.bar(region_stats, x="Region", y="Revenue", color="City_Tier",
                         barmode="stack", color_discrete_sequence=["#FF6F00", "#FFD700", "#4FC3F7"])
            plotly_defaults(fig, height=360)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top cities treemap
            city_stats = df.groupby(["City_Tier", "City_Name"]).agg(
                Orders=("Order_ID", "count"),
            ).reset_index()
            fig = px.treemap(city_stats, path=["City_Tier", "City_Name"], values="Orders",
                             color="Orders",
                             color_continuous_scale=["#1B2A4A", "#FF6F00", "#FFD700"])
            fig.update_layout(coloraxis_showscale=False)
            plotly_defaults(fig, height=360)
            st.plotly_chart(fig, use_container_width=True)

        # Delay analysis by category
        st.markdown('<div class="section-header">Delay & Return Rate by Category</div>', unsafe_allow_html=True)
        del_mask = df["Delivery_Status"] != "Cancelled"
        delay_s = ((df["Delivery_Status"] == "Delayed").groupby(df["Category"]).mean() * 100).rename("Delay Rate (%)")
        canc_s = ((df["Delivery_Status"] == "Cancelled").groupby(df["Category"]).mean() * 100).rename("Cancel Rate (%)")
        ret_s = ((df.loc[del_mask, "Return_Status"] == "Returned").groupby(df.loc[del_mask, "Category"]).mean() * 100).rename("Return Rate (%)")
        ops_stats = pd.concat([delay_s, canc_s, ret_s], axis=1).fillna(0).reset_index()

        fig = px.bar(ops_stats.melt(id_vars="Category", var_name="Metric", value_name="Rate"),
                     x="Category", y="Rate", color="Metric", barmode="group",
                     color_discrete_sequence=["#FFC107", "#F44336", "#FF6F00"])
        plotly_defaults(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)

    # ── TAB 5: STATISTICAL INSIGHTS ────────────────────────────────────
    with tab5:
        stats_results = load_stats_results()

        if stats_results is None:
            st.warning("⚠️ Statistical analysis not yet run. Execute: `python main.py analyze`")
            st.info("This tab displays hypothesis test results including t-tests, ANOVA, "
                    "chi-squared tests, and correlation analysis.")
        else:
            st.markdown('<div class="section-header">Hypothesis Test Results</div>', unsafe_allow_html=True)

            for i, result in enumerate(stats_results):
                sig = result.get("significant_at_05", False)
                icon = "✅" if sig else "❌"
                color = "#4CAF50" if sig else "#F44336"

                with st.expander(f"{icon} {result['test_name']}", expanded=(i < 3)):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Test Type", result["test_type"])
                    col2.metric("p-value", f"{result['p_value']:.6f}")
                    if result.get("effect_size") is not None:
                        col3.metric("Effect Size", f"{result['effect_size']:.4f}")
                    else:
                        col3.metric("Statistic", f"{result['statistic']:.4f}")

                    st.markdown(f"**Hypothesis:** {result['hypothesis']}")
                    st.markdown(f"**Conclusion:** {result['conclusion']}")

                    if result.get("details"):
                        with st.popover("📋 View Details"):
                            st.json(result["details"])

            # Summary
            sig_count = sum(1 for r in stats_results if r.get("significant_at_05"))
            st.markdown("---")
            st.markdown(f"### Summary: **{sig_count}/{len(stats_results)}** tests significant at α = 0.05")

    # ── FOOTER ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; color:#666; font-size:12px;">'
        '🪔 Diwali Sale 2025 — Festive E-Commerce Analytics Dashboard · '
        'Data: Synthetic · 10,000 orders · Portfolio Project'
        '</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

