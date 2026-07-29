"""
streamlit_export_integration.py
--------------------------------
BSB 2.50 - Task 3: Streamlit Export Integration

Extends the KPI dashboard with one-click export to CSV and HTML.
Uses export_functions.py under the hood; all exports are auto-generated,
timestamped, and available for download directly in the browser.

Run: streamlit run streamlit_export_integration.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from io import StringIO, BytesIO
import os
from sqlalchemy import create_engine

from export_functions import export_analysis, verify_exports

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

DB_PATH = "analytics.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

st.set_page_config(
    page_title="Sales Dashboard + Export",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    'primary':   '#1f77b4',
    'secondary': '#ff7f0e',
    'success':   '#2ca02c',
    'danger':    '#d62728',
}


# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data():
    orders   = pd.read_sql("SELECT * FROM orders", engine)
    logins   = pd.read_sql("SELECT * FROM logins", engine)
    customers = pd.read_sql("SELECT * FROM customers", engine)

    orders['order_date'] = pd.to_datetime(orders['order_date'])
    logins['login_date'] = pd.to_datetime(logins['login_date'])

    # Monthly aggregates
    orders['month'] = orders['order_date'].dt.to_period('M').astype(str)
    monthly_rev = orders.groupby('month')['order_amount'].sum().reset_index()
    monthly_rev.columns = ['month', 'revenue']

    logins['month'] = logins['login_date'].dt.to_period('M').astype(str)
    monthly_users = logins.groupby('month')['user_id'].nunique().reset_index()
    monthly_users.columns = ['month', 'active_users']

    merged = monthly_rev.merge(monthly_users, on='month', how='left').sort_values('month')

    return orders, logins, customers, merged


@st.cache_data(ttl=300)
def compute_kpis_for_export(orders_df, logins_df):
    today = date.today()
    curr_start = str(today.replace(day=1))
    prev_start = str((today.replace(day=1) - timedelta(days=1)).replace(day=1))
    orders_df['order_date_str'] = orders_df['order_date'].dt.strftime('%Y-%m-%d')

    curr = orders_df[orders_df['order_date_str'] >= curr_start]
    prev = orders_df[(orders_df['order_date_str'] >= prev_start) &
                     (orders_df['order_date_str'] < curr_start)]

    def pct(a, b):
        return round((a - b) / b * 100, 1) if b else 0

    return pd.DataFrame([
        {'Metric': 'Revenue',      'Current': round(curr['order_amount'].sum(), 2),
         'Prior': round(prev['order_amount'].sum(), 2),
         'Change_Pct': pct(curr['order_amount'].sum(), prev['order_amount'].sum())},
        {'Metric': 'Avg Order Value', 'Current': round(curr['order_amount'].mean(), 2),
         'Prior': round(prev['order_amount'].mean(), 2),
         'Change_Pct': pct(curr['order_amount'].mean(), prev['order_amount'].mean())},
        {'Metric': 'Churn Rate',
         'Current': round(len(set(prev['customer_id']) - set(curr['customer_id'])) /
                          max(len(set(prev['customer_id'])), 1) * 100, 1),
         'Prior': 0, 'Change_Pct': 0},
    ])


# ─────────────────────────────────────────────
# Dashboard Main
# ─────────────────────────────────────────────

st.title("📊 Sales Dashboard + Export")
st.caption(f"Data refreshed: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
st.divider()

orders_df, logins_df, customers_df, monthly_df = load_data()
kpis_df = compute_kpis_for_export(orders_df, logins_df)

# KPI Cards
c1, c2, c3 = st.columns(3)
with c1:
    row = kpis_df[kpis_df['Metric'] == 'Revenue'].iloc[0]
    st.metric("💰 Monthly Revenue", f"${row['Current']:,.2f}", f"{row['Change_Pct']:+.1f}%")
with c2:
    row = kpis_df[kpis_df['Metric'] == 'Avg Order Value'].iloc[0]
    st.metric("🛒 Avg Order Value", f"${row['Current']:,.2f}", f"{row['Change_Pct']:+.1f}%")
with c3:
    row = kpis_df[kpis_df['Metric'] == 'Churn Rate'].iloc[0]
    st.metric("📉 Churn Rate", f"{row['Current']:.1f}%", delta_color='inverse')

st.divider()

# Trend Charts
col_a, col_b = st.columns(2)
with col_a:
    fig1, ax1 = plt.subplots(figsize=(6, 3.5))
    ax1.plot(monthly_df['month'], monthly_df['revenue'], marker='o',
             linewidth=2.5, color=COLORS['primary'])
    ax1.set_title('Monthly Revenue Trend', fontweight='bold')
    ax1.set_ylabel('Revenue ($)')
    ax1.tick_params(axis='x', rotation=30)
    ax1.grid(alpha=0.25, linestyle=':')
    plt.tight_layout()
    st.pyplot(fig1)

with col_b:
    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
    ax2.bar(monthly_df['month'], monthly_df['active_users'].fillna(0),
            color=COLORS['secondary'], alpha=0.8)
    ax2.set_title('Monthly Active Users', fontweight='bold')
    ax2.set_ylabel('Users')
    ax2.tick_params(axis='x', rotation=30)
    ax2.grid(axis='y', alpha=0.25, linestyle=':')
    plt.tight_layout()
    st.pyplot(fig2)

st.divider()


# ═════════════════════════════════════════════
# TASK 3: Sidebar Export Controls
# ═════════════════════════════════════════════

st.sidebar.header("📥 Export Analysis")
st.sidebar.markdown("Generate and download full analysis in multiple formats.")

export_trigger = st.sidebar.button("🚀 Export Analysis Now", use_container_width=True)

if export_trigger:
    with st.spinner("Generating exports..."):
        # Build summary text
        summary_md = f"""
## Sales Analysis Report
**Generated:** {datetime.now().strftime('%B %d, %Y')}

### Revenue Performance
- Monthly Revenue: ${kpis_df[kpis_df['Metric'] == 'Revenue']['Current'].values[0]:,.2f}
- Average Order Value: ${kpis_df[kpis_df['Metric'] == 'Avg Order Value']['Current'].values[0]:,.2f}

### Customer Metrics
- Total orders in database: {len(orders_df):,}
- Unique customers: {orders_df['customer_id'].nunique():,}
- Months covered: {monthly_df['month'].nunique()}

### Key Observations
- Revenue trend is visible in the time series chart
- Active user engagement tracked monthly via login data
- Churn computed using set-difference between prior and current month
        """
        
        # Charts for export
        fig_rev, ax_rev = plt.subplots(figsize=(10, 4))
        ax_rev.plot(monthly_df['month'], monthly_df['revenue'], marker='o',
                    linewidth=2.5, color=COLORS['primary'])
        ax_rev.set_title('Monthly Revenue Trend', fontweight='bold', fontsize=13)
        ax_rev.set_ylabel('Revenue ($)')
        ax_rev.tick_params(axis='x', rotation=30)
        ax_rev.grid(alpha=0.25, linestyle=':')
        plt.tight_layout()
        
        fig_kpi, ax_kpi = plt.subplots(figsize=(8, 4))
        colors_kpi = [COLORS['primary'], COLORS['secondary'], COLORS['danger']]
        bars = ax_kpi.bar(kpis_df['Metric'], kpis_df['Current'], color=colors_kpi, alpha=0.85)
        ax_kpi.set_title('Current Period KPIs', fontweight='bold', fontsize=13)
        ax_kpi.set_ylabel('Value')
        for bar, val in zip(bars, kpis_df['Current']):
            ax_kpi.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{val:.1f}', ha='center', fontsize=10, fontweight='bold')
        plt.tight_layout()
        
        charts = {
            'Monthly Revenue Trend': fig_rev,
            'KPI Overview': fig_kpi,
        }
        
        # Run export
        report_path = export_analysis(orders_df, summary_md, charts, 'output')
        
        plt.close('all')
        
        # Verify
        is_valid = verify_exports(report_path)
    
    if is_valid:
        st.success(f"✓ Analysis exported successfully to: `{report_path}`")
    else:
        st.warning(f"⚠ Export completed with some issues. Check: `{report_path}`")
    
    # ── CSV Download ─────────────────────────
    csv_buffer = StringIO()
    orders_df.to_csv(csv_buffer, index=False)
    st.sidebar.download_button(
        label="📊 Download Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"analysis_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    
    # ── HTML Download ─────────────────────────
    html_file = os.path.join(report_path, "interactive_report.html")
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.sidebar.download_button(
            label="🌐 Download Report (HTML)",
            data=html_content,
            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
        )
    
    # ── KPI Summary Download ──────────────────
    kpi_csv = kpis_df.to_csv(index=False)
    st.sidebar.download_button(
        label="📋 Download KPI Summary (CSV)",
        data=kpi_csv,
        file_name=f"kpi_summary_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    
    st.sidebar.caption(f"Exported at: {datetime.now().strftime('%H:%M:%S')}")


# Always-visible direct CSV download (no export button needed)
st.sidebar.divider()
st.sidebar.subheader("⚡ Quick Download")
csv_quick = orders_df.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download Orders Data",
    data=csv_quick,
    file_name="orders_data.csv",
    mime="text/csv",
    use_container_width=True,
)

kpi_summary_csv = kpis_df.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download KPI Summary",
    data=kpi_summary_csv,
    file_name="kpi_summary.csv",
    mime="text/csv",
    use_container_width=True,
)
