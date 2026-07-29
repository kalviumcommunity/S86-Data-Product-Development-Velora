
from dashboard_core import main


"""
app.py
------
BSB 2.53 - Streamlit Filters & Interactive Widgets

Wires four widget types to a DataFrame so every filter change
propagates instantly to all downstream charts and metrics.

Tasks:
  Task 1 : Four widget types — date picker, multi-select, slider, radio
  Task 2 : Filter chain wired to DataFrame; reactive charts + row count
  Task 3 : Meaningful defaults — full range on first load, nothing empty
  Task 4 : Empty-state handling — warning + st.stop() instead of crash
  Task 5 : Reset Filters button using st.rerun()

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta
from sqlalchemy import create_engine

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Sales Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Consistent colour map for segments
SEGMENT_COLORS = {
    "Enterprise":  "#1f77b4",
    "SMB":         "#ff7f0e",
    "Individual":  "#2ca02c",
    "Mid-Market":  "#d62728",
}

# ─────────────────────────────────────────────
# Data loading (cached)
# ─────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load orders + customers from analytics.db and enrich with
    segment, week, and month columns ready for filtering.
    Falls back to generated sample data if DB is unavailable.
    """
    try:
        engine = create_engine("sqlite:///analytics.db")
        orders = pd.read_sql("SELECT * FROM orders", engine)
        customers = pd.read_sql("SELECT * FROM customers", engine)
        df = orders.merge(customers, on="customer_id", how="left")
        df = df.rename(columns={"customer_type": "segment", "order_amount": "revenue"})
        df["date"] = pd.to_datetime(df["order_date"])
    except Exception:
        # Fallback: generate sample data if DB not available
        np.random.seed(42)
        n = 500
        segments = ["Enterprise", "SMB", "Individual", "Mid-Market"]
        df = pd.DataFrame({
            "order_id":    range(1, n + 1),
            "customer_id": np.random.randint(1, 151, n),
            "date":        pd.date_range(
                               end=date.today(), periods=n, freq="12H"
                           ),
            "revenue":     np.random.uniform(50, 5000, n).round(2),
            "segment":     np.random.choice(
                               segments, n, p=[0.15, 0.40, 0.30, 0.15]
                           ),
        })

    df["date"]  = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["week"]  = df["date"].dt.to_period("W").astype(str)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
    return df.sort_values("date").reset_index(drop=True)


df = load_data()

# Pre-compute boundary values from the full dataset
DATE_MIN = df["date"].dt.date.min()
DATE_MAX = df["date"].dt.date.max()
REV_MIN  = int(df["revenue"].min())
REV_MAX  = int(df["revenue"].max())
ALL_SEGS = sorted(df["segment"].dropna().unique().tolist())

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────

st.title("📊 Sales Data Explorer")
st.caption(
    "Use the sidebar filters to explore any slice of the dataset. "
    "All charts and metrics update instantly."
)
st.divider()


# ═════════════════════════════════════════════
# TASKS 1, 3 & 5  —  Sidebar Widgets
# (Task 1: 4 widget types | Task 3: meaningful defaults | Task 5: reset)
# ═════════════════════════════════════════════

st.sidebar.header("🎛️ Filters")
st.sidebar.caption("Adjust any filter — charts update instantly.")

# ── Task 5: Reset button ─────────────────────
# Placed at the top so it's always reachable without scrolling
if st.sidebar.button("🔄 Reset Filters", use_container_width=True):
    st.rerun()  # Reruns the script → all widgets snap back to defaults

st.sidebar.divider()

# ── Widget 1: Date range picker ──────────────
# Task 3: defaults to full dataset range so first load shows all data
date_range = st.sidebar.date_input(
    "📅 Date Range",
    value=(DATE_MIN, DATE_MAX),          # Task 3: full range default
    min_value=DATE_MIN,
    max_value=DATE_MAX,
    help="Select start and end date. Data outside this range is hidden.",
)

# Guard: user may click only one date before picking the second
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = DATE_MIN, DATE_MAX

st.sidebar.divider()

# ── Widget 2: Multi-select for segments ──────
# Task 3: defaults to all segments so first load shows everything
selected_segments = st.sidebar.multiselect(
    "🏷️ Customer Segment",
    options=ALL_SEGS,
    default=ALL_SEGS,                    # Task 3: all selected by default
    help="Choose one or more segments to include.",
)

# If user clears all options, treat as 'all' to avoid accidental empty state
if not selected_segments:
    selected_segments = ALL_SEGS

st.sidebar.divider()

# ── Widget 3: Revenue range slider ───────────
# Task 3: defaults to full revenue range
rev_range = st.sidebar.slider(
    "💰 Revenue Range ($)",
    min_value=REV_MIN,
    max_value=REV_MAX,
    value=(REV_MIN, REV_MAX),            # Task 3: full range default
    step=10,
    help="Drag to set a minimum and maximum order value.",
)
min_rev, max_rev = rev_range

st.sidebar.divider()

# ── Widget 4: Radio for time granularity ─────
# Radio for mutually exclusive choice — daily / weekly / monthly trend view
granularity = st.sidebar.radio(
    "📆 Trend Granularity",
    options=["Daily", "Weekly", "Monthly"],
    index=2,                             # Task 3: Monthly selected by default
    help="Controls the time resolution of the trend chart.",
)

st.sidebar.divider()
st.sidebar.caption(
    f"Dataset: **{len(df):,} records** from "
    f"{DATE_MIN.strftime('%b %Y')} to {DATE_MAX.strftime('%b %Y')}"
)


# ═════════════════════════════════════════════
# TASK 2  —  Filter chain: wire widgets → DataFrame
# ═════════════════════════════════════════════

filtered_df = df[
    (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
    & (df["segment"].isin(selected_segments))
    & (df["revenue"] >= min_rev)
    & (df["revenue"] <= max_rev)
].copy()


# ═════════════════════════════════════════════
# TASK 4  —  Empty-state handling
# ═════════════════════════════════════════════

if len(filtered_df) == 0:
    st.warning(
        "⚠️ No data matches the current filters. "
        "Try broadening your date range, adding more segments, "
        "or widening the revenue slider. "
        "Click **Reset Filters** in the sidebar to restore defaults."
    )
    st.stop()   # Halts execution cleanly — no chart errors, no crashes


# ─────────────────────────────────────────────
# Filter summary bar  (Task 2)
# ─────────────────────────────────────────────

pct_shown = len(filtered_df) / len(df) * 100
c_count, c_pct, c_rev, c_aov = st.columns(4)

c_count.metric(
    "Records Shown",
    f"{len(filtered_df):,}",
    delta=f"of {len(df):,} total",
)
c_pct.metric(
    "Coverage",
    f"{pct_shown:.1f}%",
)
c_rev.metric(
    "Total Revenue",
    f"${filtered_df['revenue'].sum():,.0f}",
)
c_aov.metric(
    "Avg Order Value",
    f"${filtered_df['revenue'].mean():,.2f}",

  
import streamlit as st
 feature/streamlit-dashboard-shell
import os
import pandas as pd
from pathlib import Path

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------
st.set_page_config(
    page_title="Business Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

# -------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------
st.sidebar.title("📂 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Trends",
        "Data Explorer"
    ]
)

# =======================================================
# OVERVIEW PAGE
# =======================================================
if page == "Overview":

    st.title("📊 Business Analytics Dashboard")

    st.header("Key Performance Indicators")

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Revenue",
            "$11.73M",
            "+12.5%"
        )

    with col2:
        st.metric(
            "Top Product",
            "Alpha",
            "Highest Sales"
        )

    with col3:
        st.metric(
            "Avg Order Value",
            "$92",
            "+2.1%"
        )

    with col4:
        st.metric(
            "Best Quarter",
            "Q4",
            "+15%"
        )

    with col5:
        st.metric(
            "Marketing ROI",
            "0.93",
            "Strong Correlation"
        )

    st.divider()

    st.header("Business Summary")

    st.subheader("Revenue by Product Line")

    chart_path = BASE_DIR / "output" / "chart1_revenue_by_product.png"

    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.info("Revenue by Product chart will appear here.")

    with st.expander("About These Metrics"):

        st.write("""
        - Revenue represents total sales generated by each product line.
        - Alpha is currently the highest-performing product.
        - Average Order Value (AOV) represents the average spending per order.
        - Q4 recorded the strongest quarterly revenue.
        - Marketing ROI indicates a strong relationship between marketing spend and revenue.
        """)

# =======================================================
# TRENDS PAGE
# =======================================================
elif page == "Trends":

    st.title("📈 Trend Analysis")

    st.header("Monthly Revenue Trend")

    st.subheader("Revenue Growth Over Time")

    chart_path = BASE_DIR / "output" / "chart2_revenue_trend.png"

    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.info("Revenue Trend chart will appear here.")

    st.divider()

    st.header("Quarterly Revenue Composition")

    st.subheader("Revenue Contribution by Quarter")

    chart_path = BASE_DIR / "output" / "chart4_revenue_composition.png"

    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)
    else:
        st.info("Quarterly Revenue chart will appear here.")

    with st.expander("Business Insights"):

        st.write("""
        • Revenue steadily increased throughout the year.

        • November recorded the highest monthly revenue.

        • Q4 generated the largest share of total revenue.

        • Seasonal demand contributed significantly to business growth.
        """)

# =======================================================
# DATA EXPLORER PAGE
# =======================================================
elif page == "Data Explorer":

    st.title("📂 Data Explorer")

    st.header("Business Data")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Order Value Distribution")

        chart_path = BASE_DIR / "output" / "chart3_order_value_distribution.png"

        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.info("Order Value Distribution chart will appear here.")

    with col2:

        st.subheader("Marketing Spend vs Revenue")

        chart_path = BASE_DIR / "output" / "chart5_marketing_vs_revenue.png"

        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.info("Marketing vs Revenue chart will appear here.")

    st.divider()

    st.header("Dataset Information")

    with st.expander("View Dataset Information"):

        st.write("""
        This dashboard is based on business analytics data that includes:

        - Product Line Revenue
        - Monthly Revenue Trends
        - Quarterly Revenue Composition
        - Customer Order Values
        - Marketing Spend
        - Revenue Correlation

        Future versions of this dashboard will include filtering,
        data tables, CSV export, and interactive analytics.
        """)

    with st.expander("Methodology"):

        st.write("""
        Revenue is calculated as the total sales generated by each
        product line. Quarterly and monthly trends are derived from
        aggregated transaction data.

        Marketing effectiveness is evaluated using correlation between
        monthly marketing spend and generated revenue.
        """)

# feature/session-state-workflow
st.divider()

# ---------------------------
# Dataset Upload
# ---------------------------

st.header("Dataset Upload")

import pandas as pd
st.title("📂 Dataset Upload & Dynamic Preview")
st.write("Upload a CSV or JSON dataset to preview, validate, and explore your data.")


uploaded_file = st.file_uploader(
    "Upload CSV or JSON",
    type=["csv", "json"]
)

if uploaded_file is None:
# feature/session-state-workflow
    st.info("Upload a CSV or JSON file to view the dataset preview.")
    st.stop()

try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)

    st.info("Upload a CSV or JSON file to begin.")
    st.stop()

try:
    # Load file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)

 main
    else:
        st.error("Unsupported file type.")
        st.stop()

    # Empty file validation
 main
    if df.empty:
        st.warning("Uploaded file is empty.")
        st.stop()

except Exception:
    st.error("Could not read this file. Please check the format and try again.")
    st.stop()


st.divider()

# ---------------------------
# Session State Workflow
# ---------------------------

# "selected_segment" - stores the confirmed segment or category choice from Step 1.
if "selected_segment" not in st.session_state:
    st.session_state["selected_segment"] = "All"

# "workflow_step" - tracks whether the user has confirmed Step 1 before showing Step 2.
if "workflow_step" not in st.session_state:
    st.session_state["workflow_step"] = 1

# "analysis_result" - caches the Step 2 result so reruns do not recompute it unnecessarily.
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# "filter_date_start" - stores the start date used by the upload analysis filter.
if "filter_date_start" not in st.session_state:
    st.session_state["filter_date_start"] = None

# "filter_date_end" - stores the end date used by the upload analysis filter.
if "filter_date_end" not in st.session_state:
    st.session_state["filter_date_end"] = None

if st.sidebar.button("Reset Workflow"):
    for key in [
        "selected_segment",
        "workflow_step",
        "analysis_result",
        "filter_date_start",
        "filter_date_end",
        "pending_segment_choice",
        "pending_date_start",
        "pending_date_end",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.header("Multi-Step Analysis Workflow")

segment_source_column = None
segment_columns = [column for column in df.columns if df[column].dtype == "object" or str(df[column].dtype).startswith("category")]
if "segment" in df.columns:
    segment_source_column = "segment"
elif segment_columns:
    segment_source_column = segment_columns[0]

if segment_source_column is not None:
    segment_options = ["All"] + sorted(df[segment_source_column].dropna().astype(str).unique().tolist())

    # "pending_segment_choice" - holds the in-progress Step 1 selection before confirmation.
    if "pending_segment_choice" not in st.session_state:
        st.session_state["pending_segment_choice"] = st.session_state["selected_segment"]

    # "pending_date_start" - holds the in-progress start date selection before confirmation.
    if "pending_date_start" not in st.session_state:
        st.session_state["pending_date_start"] = None

    # "pending_date_end" - holds the in-progress end date selection before confirmation.
    if "pending_date_end" not in st.session_state:
        st.session_state["pending_date_end"] = None

    st.subheader("Step 1: Select a Segment")
    segment_choice = st.selectbox(
        f"Choose {segment_source_column.title()}",
        options=segment_options,
        index=segment_options.index(st.session_state["pending_segment_choice"])
        if st.session_state["pending_segment_choice"] in segment_options else 0,
        key="pending_segment_choice",
    )

    if st.button("Confirm Selection"):
        st.session_state["selected_segment"] = segment_choice
        st.session_state["workflow_step"] = 2

        filtered_df = df.copy()
        if segment_choice != "All":
            filtered_df = filtered_df[filtered_df[segment_source_column].astype(str) == segment_choice]

        st.session_state["analysis_result"] = {
            "segment_column": segment_source_column,
            "segment_value": segment_choice,
            "rows": int(len(filtered_df)),
            "columns": int(len(filtered_df.columns)),
            "null_pct": float((filtered_df.isnull().sum().sum() / max(filtered_df.shape[0] * filtered_df.shape[1], 1)) * 100),
        }

        st.session_state["filter_date_start"] = None
        st.session_state["filter_date_end"] = None

    if st.session_state["workflow_step"] >= 2:
        st.subheader("Step 2: Analysis")
        chosen_segment = st.session_state["selected_segment"]
        st.write(f"Analysing: {chosen_segment}")

        if st.session_state["analysis_result"] is None or st.session_state["analysis_result"].get("segment_value") != chosen_segment:
            recalculated_df = df.copy()
            if chosen_segment != "All":
                recalculated_df = recalculated_df[recalculated_df[segment_source_column].astype(str) == chosen_segment]

            st.session_state["analysis_result"] = {
                "segment_column": segment_source_column,
                "segment_value": chosen_segment,
                "rows": int(len(recalculated_df)),
                "columns": int(len(recalculated_df.columns)),
                "null_pct": float((recalculated_df.isnull().sum().sum() / max(recalculated_df.shape[0] * recalculated_df.shape[1], 1)) * 100),
            }

        analysis_result = st.session_state["analysis_result"]
        workflow_col1, workflow_col2, workflow_col3 = st.columns(3)

        with workflow_col1:
            st.metric("Rows", f"{analysis_result['rows']:,}")

        with workflow_col2:
            st.metric("Columns", f"{analysis_result['columns']:,}")

        with workflow_col3:
            st.metric("Null %", f"{analysis_result['null_pct']:.1f}%")

        st.caption("The confirmed choice stays available when other widgets rerun the page.")
else:
    st.info("No categorical column was found for the step-by-step workflow.")

# Success Message
st.success(
    f"Loaded **{uploaded_file.name}** ({len(df)} rows, {len(df.columns)} columns)"

)

st.divider()



# ─────────────────────────────────────────────
# Charts — all read from filtered_df  (Task 2)
# ─────────────────────────────────────────────

col_left, col_right = st.columns(2)

# ── Chart 1: Revenue trend (granularity controlled by radio) ──
with col_left:
    gran_col = {"Daily": "date", "Weekly": "week", "Monthly": "month"}[granularity]

    if granularity == "Daily":
        trend = (
            filtered_df.set_index("date")
            .resample("D")["revenue"]
            .sum()
            .reset_index()
        )
        trend.columns = ["period", "revenue"]
        x_vals = trend["period"]
    else:
        trend = (
            filtered_df.groupby(gran_col)["revenue"]
            .sum()
            .reset_index()
        )
        trend.columns = ["period", "revenue"]
        x_vals = trend["period"]

    fig1, ax1 = plt.subplots(figsize=(6, 3.8))
    ax1.plot(x_vals, trend["revenue"], marker="o", linewidth=2.2,
             markersize=4, color="#1f77b4")
    ax1.fill_between(range(len(trend)), trend["revenue"],
                     alpha=0.1, color="#1f77b4")
    ax1.set_title(f"{granularity} Revenue Trend", fontweight="bold", fontsize=12)
    ax1.set_ylabel("Revenue ($)")
    ax1.tick_params(axis="x", rotation=35)
    ax1.grid(alpha=0.25, linestyle=":")
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close()
    st.caption(f"Granularity: **{granularity}** (change with the radio button in sidebar)")

# ── Chart 2: Revenue by segment ──────────────
with col_right:
    seg_rev = (
        filtered_df.groupby("segment")["revenue"]
        .sum()
        .sort_values(ascending=True)
    )

    fig2, ax2 = plt.subplots(figsize=(6, 3.8))
    colors = [SEGMENT_COLORS.get(s, "#7f7f7f") for s in seg_rev.index]
    bars = ax2.barh(seg_rev.index, seg_rev.values, color=colors, edgecolor="white")
    for bar, val in zip(bars, seg_rev.values):
        ax2.text(
            bar.get_width() + seg_rev.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"${val:,.0f}", va="center", fontsize=9, fontweight="bold",
        )
    ax2.set_title("Revenue by Segment", fontweight="bold", fontsize=12)
    ax2.set_xlabel("Revenue ($)")
    ax2.set_xlim(0, seg_rev.max() * 1.18)
    ax2.grid(axis="x", alpha=0.25, linestyle=":")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()
    st.caption("Filtered to selected segments only. Deselect a segment to remove its bar.")

st.divider()

# ── Chart 3: Order count by segment (pie) ────
col_pie, col_box = st.columns(2)

with col_pie:
    seg_cnt = filtered_df["segment"].value_counts()
    fig3, ax3 = plt.subplots(figsize=(5, 4))
    pie_colors = [SEGMENT_COLORS.get(s, "#7f7f7f") for s in seg_cnt.index]
    wedges, texts, autotexts = ax3.pie(
        seg_cnt.values, labels=seg_cnt.index, autopct="%1.1f%%",
        startangle=90, colors=pie_colors,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(10)
        at.set_fontweight("bold")
    ax3.set_title("Order Distribution by Segment", fontweight="bold", fontsize=12)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with col_box:
    # Revenue distribution per segment — box-style using violin
    fig4, ax4 = plt.subplots(figsize=(5, 4))
    seg_order = sorted(filtered_df["segment"].unique())
    data_per_seg = [
        filtered_df[filtered_df["segment"] == s]["revenue"].values
        for s in seg_order
    ]
    vp = ax4.violinplot(data_per_seg, showmedians=True)
    for i, pc in enumerate(vp["bodies"]):
        pc.set_facecolor(SEGMENT_COLORS.get(seg_order[i], "#7f7f7f"))
        pc.set_alpha(0.7)
    ax4.set_xticks(range(1, len(seg_order) + 1))
    ax4.set_xticklabels(seg_order, rotation=20, ha="right")
    ax4.set_ylabel("Revenue ($)")
    ax4.set_title("Revenue Distribution per Segment", fontweight="bold", fontsize=12)
    ax4.grid(axis="y", alpha=0.25, linestyle=":")
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

st.divider()

# ─────────────────────────────────────────────
# Data table  (Task 2)
# ─────────────────────────────────────────────

st.subheader("🔍 Filtered Records")
st.write(
    f"Showing **{len(filtered_df):,}** records "
    f"({start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')})"
)

display_cols = [c for c in ["order_id", "customer_id", "segment", "revenue", "date"]
                if c in filtered_df.columns]

st.dataframe(
    filtered_df[display_cols]
    .sort_values("date", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
    height=320,
)

# CSV download of filtered data
csv_data = filtered_df[display_cols].to_csv(index=False)
st.download_button(
    label="⬇️ Download Filtered Data (CSV)",
    data=csv_data,
    file_name=f"filtered_{start_date}_{end_date}.csv",
    mime="text/csv",
)

st.divider()

# ─────────────────────────────────────────────
# Widget explainer (for video walkthrough)
# ─────────────────────────────────────────────

with st.expander("ℹ️ How the filter chain works"):
    st.markdown("""
    Every sidebar control feeds into a single `filtered_df`:

    ```python
    filtered_df = df[
        (df["date"].dt.date >= start_date)          # date picker
        & (df["date"].dt.date <= end_date)           # date picker
        & (df["segment"].isin(selected_segments))    # multi-select
        & (df["revenue"] >= min_rev)                 # slider
        & (df["revenue"] <= max_rev)                 # slider
    ]
    ```

    Every chart, metric, and table below reads from `filtered_df`, not the
    original `df`. Change any widget → Streamlit reruns → new `filtered_df`
    → all visuals refresh instantly.

    | Widget | Type | Controls |
    |---|---|---|
    | Date Range | `st.date_input` | Rows outside date window are excluded |
    | Customer Segment | `st.multiselect` | Only ticked segments appear |
    | Revenue Range | `st.slider` | Orders outside the $ range are excluded |
    | Trend Granularity | `st.radio` | Switches daily / weekly / monthly trend chart |

    **Empty state:** if filters produce zero rows, `st.warning` is shown and
    `st.stop()` halts execution — no chart crashes.

    **Reset:** the Reset Filters button calls `st.rerun()`, which re-executes
    the script from the top and resets every widget to its `value=` default.
    """)


# ---------------------------
# Dataset Summary
# ---------------------------

st.header("Dataset Preview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Rows", len(df))

with col2:
    st.metric("Columns", len(df.columns))

with col3:
    total_nulls = df.isnull().sum().sum()
    total_cells = max(df.shape[0] * df.shape[1], 1)
    null_pct = (total_nulls / total_cells) * 100
    st.metric("Null %", f"{null_pct:.1f}%")

st.divider()

# ---------------------------
# First 10 Rows
# ---------------------------

st.subheader("First 10 Rows")
st.dataframe(df.head(10), use_container_width=True)

# ---------------------------
# Column Summary
# ---------------------------

st.subheader("Column Summary")

summary = pd.DataFrame({
    "Column": df.columns,
    "Type": df.dtypes.astype(str).values,
    "Non-Null": df.notnull().sum().values,
    "Null Count": df.isnull().sum().values,
    "Null %": (df.isnull().sum() / len(df) * 100).round(1).values
})

st.dataframe(summary, use_container_width=True)

# ---------------------------
# Descriptive Statistics
# ---------------------------

st.subheader("Descriptive Statistics")

st.dataframe(
    df.describe(include="all"),
    use_container_width=True
)

# ---------------------------
# Quick Filter
# ---------------------------

st.subheader("Quick Filter")

filter_columns = df.columns.tolist()

selected_column = st.selectbox(
    "Select a column",
    filter_columns
)

unique_values = df[selected_column].dropna().unique()

if len(unique_values) > 0:
    selected_value = st.selectbox(
        "Select a value",
        unique_values
    )

    filtered_df = df[df[selected_column] == selected_value]

    st.write(f"Filtered Records: {len(filtered_df)}")

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

st.divider()

# ---------------------------
# Quick Exploration
# ---------------------------

st.subheader("Quick Exploration")

numeric_cols = df.select_dtypes(include="number").columns.tolist()

if numeric_cols:

    selected_numeric = st.selectbox(
        "Choose Numeric Column",
        numeric_cols
    )

    st.bar_chart(
        df[selected_numeric].value_counts().head(20)
    )

else:
    st.info("No numeric columns available.")

# ---------------------------
# Download Dataset
# ---------------------------

st.subheader("Export Dataset")

csv = df.to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="uploaded_dataset.csv",
    mime="text/csv"
)

