"""
app.py
------
BSB 2.53 + 2.56 - Streamlit Filters, Widgets & Alert Monitoring

2.53 tasks:
  Task 1 : Four widget types — date picker, multi-select, slider, radio
  Task 2 : Filter chain wired to DataFrame; reactive charts + row count
  Task 3 : Meaningful defaults — full range on first load, nothing empty
  Task 4 : Empty-state handling — warning + st.stop() instead of crash
  Task 5 : Reset Filters button using st.rerun()

2.56 tasks:
  Task 1 : Five metrics monitored against thresholds (via alert_config.py)
  Task 2 : Visual alerts — st.error (critical) / st.warning (warning)
  Task 3 : Thresholds in alert_config.py, not hardcoded here
  Task 4 : Each alert message has metric name, value, threshold, action
  Task 5 : Alerts recalculate on every filter change (reactive)

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine

# BSB 2.56 — Task 3: import thresholds from config file, not hardcoded
from alert_config import ALERT_THRESHOLDS
from export_functions import generate_report, send_report_email

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
    "All charts and metrics update instantly. "
    "Alert banners appear automatically when a KPI crosses its threshold."
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
# Report generation and email delivery
# ─────────────────────────────────────────────

report_date = datetime.now().date()
report_text = generate_report(filtered_df, report_date)

st.sidebar.divider()
st.sidebar.header("📤 Report Actions")
recipient_email = st.sidebar.text_input("Recipient Email", key="recipient_email")

if st.sidebar.button("Send Report", use_container_width=True):
    if not recipient_email:
        st.sidebar.error("Enter a recipient email.")
    else:
        success = send_report_email(report_text, recipient_email)
        if success:
            st.sidebar.success(f"Report sent to {recipient_email}")
        else:
            st.sidebar.error("Failed to send. Check email config.")

st.sidebar.download_button(
    label="Download Report (TXT)",
    data=report_text,
    file_name=f"weekly_analytics_report_{report_date.isoformat()}.txt",
    mime="text/plain",
    use_container_width=True,
)

with st.expander("Generated Report Preview", expanded=False):
    st.text(report_text)


# ═════════════════════════════════════════════
# BSB 2.56 — ALERT MONITORING SYSTEM
# Tasks 1-5: compute metrics, check thresholds, display reactive alerts
# ═════════════════════════════════════════════

def compute_metrics(fdf: pd.DataFrame, full_df: pd.DataFrame) -> dict:
    """
    Compute all monitored metrics from the filtered DataFrame.
    Called on every rerun → alerts always reflect current filter state.

    Args:
        fdf:      Filtered DataFrame (current view)
        full_df:  Full unfiltered DataFrame (for coverage calculation)

    Returns:
        dict mapping threshold keys → current numeric values
    """
    # Churn rate: customers in full dataset not in filtered view
    # (proxy: filtered customers vs total unique customers)
    total_customers = full_df["customer_id"].nunique()
    filtered_customers = fdf["customer_id"].nunique()
    missing_customers = total_customers - filtered_customers
    churn_rate = (missing_customers / total_customers * 100) if total_customers else 0

    # Average order value
    avg_order_value = fdf["revenue"].mean() if len(fdf) > 0 else 0

    # Null percentage in revenue column
    null_pct = (fdf["revenue"].isna().sum() / len(fdf) * 100) if len(fdf) > 0 else 0

    # Coverage: what % of full dataset is visible in filtered view
    coverage_pct = (len(fdf) / len(full_df) * 100) if len(full_df) > 0 else 0

    # Unique customers in filtered view
    unique_customers = int(fdf["customer_id"].nunique())

    return {
        "churn_rate":       round(churn_rate, 2),
        "avg_order_value":  round(avg_order_value, 2),
        "null_percentage":  round(null_pct, 2),
        "coverage_pct":     round(coverage_pct, 2),
        "unique_customers": unique_customers,
    }


def check_alerts(metrics: dict, thresholds: dict) -> list:
    """
    Compare each metric against its configured threshold.

    Args:
        metrics:    Dict of {key: current_value} from compute_metrics()
        thresholds: ALERT_THRESHOLDS from alert_config.py

    Returns:
        List of triggered alert dicts, each with full message context.
    """
    triggered = []
    for key, config in thresholds.items():
        if key not in metrics:
            continue
        value = metrics[key]
        threshold = config["threshold"]
        breached = (
            (config["direction"] == "above" and value > threshold) or
            (config["direction"] == "below" and value < threshold)
        )
        if breached:
            triggered.append({
                "key":       key,
                "metric":    config["metric"],
                "value":     value,
                "threshold": threshold,
                "direction": config["direction"],
                "severity":  config["severity"],
                "message":   config["message"],
            })
    return triggered


# ── Task 1 & 5: compute metrics from filtered_df (reactive) ─────────────
current_metrics = compute_metrics(filtered_df, df)

# ── Task 2: check thresholds and display alerts ──────────────────────────
active_alerts = check_alerts(current_metrics, ALERT_THRESHOLDS)

if active_alerts:
    st.markdown("### 🚨 Active Alerts")
    for alert in active_alerts:
        direction_word = "above" if alert["direction"] == "above" else "below"

        # Task 4: message includes metric name, current value, threshold, action
        banner = (
            f"**{alert['metric']}** is **{alert['value']}** "
            f"({direction_word} threshold of {alert['threshold']}). "
            f"{alert['message']}"
        )

        if alert["severity"] == "critical":
            st.error(f"🔴 CRITICAL — {banner}")    # red banner
        else:
            st.warning(f"🟡 WARNING — {banner}")   # amber banner

    st.divider()
else:
    st.success("✅ All metrics within normal thresholds.")
    st.divider()

# Alert status sidebar summary
st.sidebar.divider()
st.sidebar.subheader("🚨 Alert Status")
if active_alerts:
    critical_count = sum(1 for a in active_alerts if a["severity"] == "critical")
    warning_count  = sum(1 for a in active_alerts if a["severity"] == "warning")
    if critical_count:
        st.sidebar.error(f"{critical_count} critical alert(s) active")
    if warning_count:
        st.sidebar.warning(f"{warning_count} warning(s) active")
else:
    st.sidebar.success("All clear ✅")


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

with st.expander("🚨 How the alert system works"):
    st.markdown("""
    **Alert flow on every filter change:**

    ```
    Sidebar widget changed
           ↓
    Streamlit reruns app.py
           ↓
    filtered_df recomputed
           ↓
    compute_metrics(filtered_df) → {churn_rate, avg_order_value, ...}
           ↓
    check_alerts(metrics, ALERT_THRESHOLDS) → list of triggered alerts
           ↓
    st.error() or st.warning() displayed at top of page
    ```

    **Monitored metrics:**

    | Metric Key | Threshold | Direction | Severity |
    |---|---|---|---|
    | `churn_rate` | 7.0% | above | 🔴 Critical |
    | `avg_order_value` | $80 | below | 🟡 Warning |
    | `null_percentage` | 5.0% | above | 🟡 Warning |
    | `coverage_pct` | 10.0% | below | 🟡 Warning |
    | `unique_customers` | 5 | below | 🔴 Critical |

    **To change a threshold:** edit `alert_config.py` only.
    The display logic in `app.py` never hardcodes a limit.

    **Task 5 — reactive alerts:**
    Filter to a single high-churn segment → alert fires.
    Switch to a healthy segment → alert clears automatically.
    No manual refresh needed; Streamlit's rerun model handles it.
    """)
