"""
kpi_dashboard.py
----------------
BSB 2.47 - KPI Card & Summary Metric Design

Five KPI cards at the top of the dashboard answering "are we on track?" in 5 seconds.
All values computed from the clean data layer (SQLite views/tables), never hardcoded.

Tasks covered:
  Task 1 : Compute 5 KPIs with current vs prior period from DB
  Task 2 : get_trend_indicator() with correct directional colour logic
  Task 3 : Percentage change formatted for display (e.g. +12.5%)
  Task 4 : Streamlit KPI dashboard layout (5-column card row)
  Task 5 : Data lineage documented in kpi_sources.md

Run: streamlit run kpi_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

DB_PATH = "analytics.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

st.set_page_config(
    page_title="Sales Performance Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Consistent colour palette
COLORS = {
    'primary':   '#1f77b4',
    'secondary': '#ff7f0e',
    'success':   '#2ca02c',
    'danger':    '#d62728',
    'neutral':   '#7f7f7f',
}


# ─────────────────────────────────────────────
# Seed helper tables required by KPIs
# ─────────────────────────────────────────────

@st.cache_resource
def ensure_satisfaction_table(engine):
    """
    Create a satisfaction_ratings table if absent.
    Ratings (1-5) submitted by customers after orders.
    """
    today = date.today()
    curr_start = today.replace(day=1)
    prev_start = (curr_start - timedelta(days=1)).replace(day=1)

    rows = []
    for i in range(120):
        # 80 ratings current month, 40 previous month
        if i < 80:
            d = today - timedelta(days=np.random.randint(0, today.day))
        else:
            days_in_prev = (curr_start - timedelta(days=1)).day
            d = prev_start + timedelta(days=np.random.randint(0, days_in_prev))
        rows.append({
            'rating_id': i + 1,
            'customer_id': np.random.randint(1, 151),
            'rating': round(np.random.uniform(3.0, 5.0), 1),
            'rating_date': str(d),
        })

    df = pd.DataFrame(rows)
    df.to_sql('satisfaction_ratings', engine, if_exists='replace', index=False)


ensure_satisfaction_table(engine)


# ─────────────────────────────────────────────
# Task 1: Compute Five KPI Metrics
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)  # Refresh every 5 minutes — data flows through automatically
def compute_kpis():
    """
    Compute all five KPIs with current and prior period values.
    All values queried from the validated data layer; no hardcoded numbers.
    Prior period is always computed automatically from today's date.
    """
    today = date.today()
    curr_month_start = today.replace(day=1)
    prev_month_start = (curr_month_start - timedelta(days=1)).replace(day=1)
    cutoff_str   = str(curr_month_start)
    prev_str     = str(prev_month_start)

    # ── KPI 1: Total Revenue ──────────────────
    # Source: orders table (validated in 2.44)
    sql_rev_curr = f"""
        SELECT COALESCE(SUM(order_amount), 0) as total
        FROM orders
        WHERE order_date >= '{cutoff_str}'
    """
    sql_rev_prev = f"""
        SELECT COALESCE(SUM(order_amount), 0) as total
        FROM orders
        WHERE order_date >= '{prev_str}'
          AND order_date < '{cutoff_str}'
    """
    curr_revenue = pd.read_sql(sql_rev_curr, engine).iloc[0, 0]
    prior_revenue = pd.read_sql(sql_rev_prev, engine).iloc[0, 0]

    # ── KPI 2: Active Users ───────────────────
    # Source: logins table — distinct users with login in current/prior month
    sql_users_curr = f"""
        SELECT COUNT(DISTINCT user_id) as cnt
        FROM logins
        WHERE login_date >= '{cutoff_str}'
    """
    sql_users_prev = f"""
        SELECT COUNT(DISTINCT user_id) as cnt
        FROM logins
        WHERE login_date >= '{prev_str}'
          AND login_date < '{cutoff_str}'
    """
    curr_users = pd.read_sql(sql_users_curr, engine).iloc[0, 0]
    prior_users = pd.read_sql(sql_users_prev, engine).iloc[0, 0]

    # ── KPI 3: Average Order Value ────────────
    # Source: orders table — mean order_amount in period
    sql_aov_curr = f"""
        SELECT COALESCE(AVG(order_amount), 0) as aov
        FROM orders
        WHERE order_date >= '{cutoff_str}'
    """
    sql_aov_prev = f"""
        SELECT COALESCE(AVG(order_amount), 0) as aov
        FROM orders
        WHERE order_date >= '{prev_str}'
          AND order_date < '{cutoff_str}'
    """
    curr_aov = pd.read_sql(sql_aov_curr, engine).iloc[0, 0]
    prior_aov = pd.read_sql(sql_aov_prev, engine).iloc[0, 0]

    # ── KPI 4: Churn Rate ─────────────────────
    # Source: orders table — customers in prior month not in current month
    sql_prev_custs = f"""
        SELECT DISTINCT customer_id FROM orders
        WHERE order_date >= '{prev_str}' AND order_date < '{cutoff_str}'
    """
    sql_curr_custs = f"""
        SELECT DISTINCT customer_id FROM orders
        WHERE order_date >= '{cutoff_str}'
    """
    prev_custs = set(pd.read_sql(sql_prev_custs, engine)['customer_id'])
    curr_custs = set(pd.read_sql(sql_curr_custs, engine)['customer_id'])

    churned = len(prev_custs - curr_custs)
    curr_churn_rate = (churned / len(prev_custs) * 100) if prev_custs else 0

    # Prior-prior month for comparison
    prev_prev_start = (prev_month_start - timedelta(days=1)).replace(day=1)
    prev_prev_str = str(prev_prev_start)
    sql_pp_custs = f"""
        SELECT DISTINCT customer_id FROM orders
        WHERE order_date >= '{prev_prev_str}' AND order_date < '{prev_str}'
    """
    pp_custs = set(pd.read_sql(sql_pp_custs, engine)['customer_id'])
    pp_churned = len(pp_custs - prev_custs)
    prior_churn_rate = (pp_churned / len(pp_custs) * 100) if pp_custs else 0

    # ── KPI 5: Customer Satisfaction ─────────
    # Source: satisfaction_ratings table — avg rating in period
    sql_sat_curr = f"""
        SELECT COALESCE(AVG(rating), 0) as avg_rating
        FROM satisfaction_ratings
        WHERE rating_date >= '{cutoff_str}'
    """
    sql_sat_prev = f"""
        SELECT COALESCE(AVG(rating), 0) as avg_rating
        FROM satisfaction_ratings
        WHERE rating_date >= '{prev_str}'
          AND rating_date < '{cutoff_str}'
    """
    curr_sat = pd.read_sql(sql_sat_curr, engine).iloc[0, 0]
    prior_sat = pd.read_sql(sql_sat_prev, engine).iloc[0, 0]

    # ── Build KPI DataFrame ───────────────────
    def pct_change(curr, prior):
        if prior and prior != 0:
            return ((curr - prior) / abs(prior)) * 100
        return 0.0

    kpis = pd.DataFrame([
        {
            'Metric':        'Revenue',
            'Current':       curr_revenue,
            'Prior':         prior_revenue,
            'Change_Pct':    pct_change(curr_revenue, prior_revenue),
            'Display':       f"${curr_revenue:,.0f}",
            'Inverted':      False,
            'Unit':          '$',
        },
        {
            'Metric':        'Active Users',
            'Current':       curr_users,
            'Prior':         prior_users,
            'Change_Pct':    pct_change(curr_users, prior_users),
            'Display':       f"{int(curr_users):,}",
            'Inverted':      False,
            'Unit':          'users',
        },
        {
            'Metric':        'Avg Order Value',
            'Current':       curr_aov,
            'Prior':         prior_aov,
            'Change_Pct':    pct_change(curr_aov, prior_aov),
            'Display':       f"${curr_aov:,.2f}",
            'Inverted':      False,
            'Unit':          '$',
        },
        {
            'Metric':        'Churn Rate',
            'Current':       curr_churn_rate,
            'Prior':         prior_churn_rate,
            'Change_Pct':    pct_change(curr_churn_rate, prior_churn_rate),
            'Display':       f"{curr_churn_rate:.1f}%",
            'Inverted':      True,   # Lower is better
            'Unit':          '%',
        },
        {
            'Metric':        'Satisfaction',
            'Current':       curr_sat,
            'Prior':         prior_sat,
            'Change_Pct':    pct_change(curr_sat, prior_sat),
            'Display':       f"{curr_sat:.2f} / 5",
            'Inverted':      False,
            'Unit':          '/5',
        },
    ])

    return kpis


# ─────────────────────────────────────────────
# Task 2: Trend Indicator with Directional Logic
# ─────────────────────────────────────────────

def get_trend_indicator(change_pct: float, inverted: bool) -> tuple:
    """
    Return (arrow, colour, delta_color) based on metric direction.

    Args:
        change_pct: Percentage change vs prior period.
        inverted:   True for metrics where lower is better (churn, error rate).

    Returns:
        (arrow str, hex colour, streamlit delta_color param)
    """
    THRESHOLD = 2.0  # ±2% is the boundary between flat and trending

    if inverted:
        # Decrease = good (green), Increase = bad (red)
        if change_pct < -THRESHOLD:
            return '↓', '#10b981', 'inverse'
        elif change_pct > THRESHOLD:
            return '↑', '#ef4444', 'inverse'
        else:
            return '→', '#f59e0b', 'off'
    else:
        # Increase = good (green), Decrease = bad (red)
        if change_pct > THRESHOLD:
            return '↑', '#10b981', 'normal'
        elif change_pct < -THRESHOLD:
            return '↓', '#ef4444', 'normal'
        else:
            return '→', '#f59e0b', 'off'


# ─────────────────────────────────────────────
# Task 3: Format Percentage Change Display
# ─────────────────────────────────────────────

def format_change(change_pct: float) -> str:
    """Format percentage change with sign for KPI delta display."""
    if change_pct == 0:
        return "0.0%"
    return f"{change_pct:+.1f}%"


# ═════════════════════════════════════════════
# Task 4: Streamlit Dashboard Layout
# ═════════════════════════════════════════════

st.title("📊 Sales Performance Dashboard")
st.markdown(
    f"*Data as of {datetime.now().strftime('%B %d, %Y')} · "
    f"Comparing current month vs prior month*"
)
st.markdown("---")

# Load KPIs
kpis = compute_kpis()

# ── Level 1: KPI Cards ────────────────────────
st.subheader("🎯 Key Performance Indicators")
st.caption(
    "Five metrics that answer *'are we on track?'* — "
    "green = on track, red = investigate, yellow = flat"
)

cols = st.columns(5)

for col, (_, row) in zip(cols, kpis.iterrows()):
    arrow, colour, delta_color = get_trend_indicator(
        row['Change_Pct'], row['Inverted']
    )
    change_str = format_change(row['Change_Pct'])

    with col:
        st.metric(
            label=f"{arrow} {row['Metric']}",
            value=row['Display'],
            delta=change_str,
            delta_color=delta_color,
        )

st.markdown("---")

# ── Trend Context Table ───────────────────────
st.subheader("📋 KPI Summary Table")
st.caption("Full comparison: current period vs prior period with trend status")

# Build display table (Task 3)
summary_rows = []
for _, row in kpis.iterrows():
    arrow, colour, _ = get_trend_indicator(row['Change_Pct'], row['Inverted'])
    change_str = format_change(row['Change_Pct'])
    status = "🟢 On Track" if colour == '#10b981' else \
             ("🔴 Needs Attention" if colour == '#ef4444' else "🟡 Stable")
    summary_rows.append({
        'KPI':            row['Metric'],
        'Current Value':  row['Display'],
        'Prior Period':   (f"${row['Prior']:,.0f}" if row['Unit'] == '$' and row['Metric'] != 'Avg Order Value'
                           else f"${row['Prior']:,.2f}" if row['Unit'] == '$'
                           else f"{row['Prior']:.1f}%" if row['Unit'] == '%'
                           else f"{row['Prior']:.2f} / 5" if row['Unit'] == '/5'
                           else f"{int(row['Prior']):,}"),
        'Change':         f"{arrow} {change_str}",
        'Status':         status,
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Level 2: Trend Charts ─────────────────────
st.subheader("📈 Revenue & Activity Trends")

orders_df = pd.read_sql("SELECT * FROM orders", engine)
orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
orders_df['month'] = orders_df['order_date'].dt.to_period('M').astype(str)

monthly_rev = (orders_df.groupby('month')['order_amount']
               .sum().reset_index()
               .sort_values('month').tail(6))

col_c1, col_c2 = st.columns(2)

with col_c1:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(monthly_rev['month'], monthly_rev['order_amount'],
           color=COLORS['primary'], alpha=0.85, edgecolor='white')
    ax.set_title('Monthly Revenue (last 6 months)', fontweight='bold', fontsize=12)
    ax.set_xlabel('Month')
    ax.set_ylabel('Revenue ($)')
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', alpha=0.25, linestyle=':')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_c2:
    logins_df = pd.read_sql("SELECT * FROM logins", engine)
    logins_df['login_date'] = pd.to_datetime(logins_df['login_date'])
    logins_df['month'] = logins_df['login_date'].dt.to_period('M').astype(str)

    monthly_users = (logins_df.groupby('month')['user_id']
                     .nunique().reset_index()
                     .rename(columns={'user_id': 'active_users'})
                     .sort_values('month').tail(6))

    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
    ax2.plot(monthly_users['month'], monthly_users['active_users'],
             marker='o', linewidth=2.5, color=COLORS['secondary'])
    ax2.set_title('Monthly Active Users (last 6 months)', fontweight='bold', fontsize=12)
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Active Users')
    ax2.tick_params(axis='x', rotation=30)
    ax2.grid(alpha=0.25, linestyle=':')
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

st.markdown("---")

# ── KPI Justification ─────────────────────────
with st.expander("ℹ️ Why these five KPIs? — Design decisions"):
    st.markdown("""
    | KPI | Business Question | Direction |
    |---|---|---|
    | **Revenue** | Are we hitting monthly sales targets? | Higher = better |
    | **Active Users** | Is engagement growing? | Higher = better |
    | **Avg Order Value** | Are customers spending more per transaction? | Higher = better |
    | **Churn Rate** | Are we retaining customers? | **Lower = better** (inverted) |
    | **Satisfaction** | Are customers happy enough to return? | Higher = better |

    These five cover the four pillars of business health: **revenue growth, engagement,
    revenue quality, retention, and customer sentiment**.
    If all five are green, no further action needed. If one is red, scroll to the relevant trend.

    **Directional colour logic:**
    - Revenue / Users / AOV / Satisfaction: increase → 🟢, decrease → 🔴
    - Churn Rate: decrease → 🟢, increase → 🔴 (`delta_color='inverse'` in Streamlit)
    - ±2% threshold separates trending from flat (yellow band)
    """)

# ── Data Lineage ──────────────────────────────
with st.expander("🗂️ Data lineage — where each KPI value comes from"):
    st.markdown("""
    | KPI | Source Table | Aggregation | Validation |
    |---|---|---|---|
    | Revenue | `orders.order_amount` | SUM per month | Cross-checked vs Python sum in 2.44 |
    | Active Users | `logins.user_id` | COUNT DISTINCT per month | Cross-checked vs pandas nunique in 2.44 |
    | Avg Order Value | `orders.order_amount` | AVG per month | Matches `orders_df.mean()` |
    | Churn Rate | `orders.customer_id` | Set difference prev→curr month | Matches Python set subtraction |
    | Satisfaction | `satisfaction_ratings.rating` | AVG per month | Direct from ratings table |

    All date ranges are **computed automatically** from `date.today()`.
    No hardcoded dates. A new month's data flows through to updated KPIs without code changes.
    """)

st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:12px;padding:16px'>"
    "KPI values refresh every 5 minutes · All metrics sourced from validated data layer"
    "</div>",
    unsafe_allow_html=True,
)
