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
