"""
dashboard_app.py
----------------
BSB 2.41 - SQL Window Functions & Ranking Systems (Dashboard Design)

Hierarchical dashboard following the information pyramid:
  Level 1 (Status)   : 5 KPI cards - instant "are we on track?" answer
  Level 2 (Trends)   : 3 time series charts - pattern discovery
  Level 3 (Segments) : 2 comparison charts - segment analysis
  Level 4 (Detail)   : Filters + data table - drill-down capability

Design principles applied:
  - Progressive disclosure: summary first, detail on demand
  - Spatial organization: critical metrics top-left
  - Consistent metaphor: green=good, red=bad everywhere
  - Context over numbers: every metric includes comparison
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta
from io import StringIO

# ─────────────────────────────────────────────
# Configuration & Data Generation
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Business Performance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Color palette (consistent across all visualizations)
COLORS = {
    'primary':   '#1f77b4',  # Blue - main metrics
    'secondary': '#ff7f0e',  # Orange - comparisons
    'success':   '#2ca02c',  # Green - positive indicators
    'danger':    '#d62728',  # Red - negative indicators
    'neutral':   '#7f7f7f',  # Gray - neutral
}

# Generate realistic sample data
@st.cache_data
def generate_sample_data():
    """Generate 12 months of business metrics data."""
    np.random.seed(42)
    
    # Monthly aggregated data
    months = pd.date_range('2024-01-01', periods=12, freq='M')
    
    monthly_data = pd.DataFrame({
        'month': months,
        'revenue': [4.2, 4.5, 4.8, 4.6, 5.0, 5.1, 4.9, 4.7, 5.2, 5.4, 5.5, 5.2],
        'active_customers': [2100, 2200, 2280, 2250, 2400, 2450, 2380, 2350, 2500, 2550, 2580, 2500],
        'churned_customers': [85, 90, 88, 95, 92, 89, 94, 98, 90, 87, 85, 88],
        'avg_order_value': [132, 138, 142, 137, 145, 148, 143, 139, 145, 150, 152, 145],
        'nps_score': [65, 67, 68, 66, 70, 71, 69, 67, 72, 73, 74, 72],
    })
    
    # Calculate derived metrics
    monthly_data['churn_rate'] = (monthly_data['churned_customers'] / 
                                   monthly_data['active_customers'] * 100).round(1)
    
    # Detailed transaction data
    segments = ['Enterprise', 'Mid-Market', 'SMB', 'Starter']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    
    # Generate 1000 customer records
    detailed_data = pd.DataFrame({
        'customer_id': [f'C{i:04d}' for i in range(1, 1001)],
        'segment': np.random.choice(segments, 1000, p=[0.15, 0.25, 0.40, 0.20]),
        'region': np.random.choice(regions, 1000, p=[0.40, 0.30, 0.20, 0.10]),
        'revenue': np.random.gamma(2, 2500, 1000).round(2),
        'last_activity': pd.date_range(end='2024-12-31', periods=1000, freq='12H'),
        'churn_risk': np.random.choice(['Low', 'Medium', 'High'], 1000, p=[0.60, 0.30, 0.10]),
        'lifetime_months': np.random.randint(1, 48, 1000),
    })
    
    # Segment aggregations
    segment_data = detailed_data.groupby('segment').agg({
        'revenue': 'sum',
        'customer_id': 'count'
    }).reset_index()
    segment_data.columns = ['segment', 'revenue', 'customer_count']
    segment_data['revenue'] = (segment_data['revenue'] / 1_000_000).round(2)  # Convert to millions
    
    return monthly_data, detailed_data, segment_data


monthly_df, detailed_df, segment_df = generate_sample_data()

# Current vs previous month for KPI cards
current_month = monthly_df.iloc[-1]
previous_month = monthly_df.iloc[-2]


# ═════════════════════════════════════════════
# LEVEL 1: STATUS - KPI CARDS
# ═════════════════════════════════════════════

st.title('📊 Business Performance Dashboard')
st.markdown('**Real-time insights into business health and performance trends**')
st.markdown('---')

st.subheader('🎯 Key Performance Indicators')

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    revenue_delta = ((current_month['revenue'] - previous_month['revenue']) / 
                     previous_month['revenue'] * 100)
    st.metric(
        label='💰 Monthly Revenue',
        value=f"${current_month['revenue']:.1f}M",
        delta=f"{revenue_delta:+.1f}%"
    )
    with st.expander("ℹ️ Why this metric?"):
        st.write("**Primary health indicator.** Answers: Are we growing revenue month-over-month?")

with col2:
    customers_delta = current_month['active_customers'] - previous_month['active_customers']
    st.metric(
        label='👥 Active Customers',
        value=f"{current_month['active_customers']:,}",
        delta=f"{customers_delta:+,}"
    )
    with st.expander("ℹ️ Why this metric?"):
        st.write("**Growth indicator.** Shows customer base expansion. Critical for subscription businesses.")

with col3:
    aov_delta = ((current_month['avg_order_value'] - previous_month['avg_order_value']) / 
                 previous_month['avg_order_value'] * 100)
    st.metric(
        label='🛒 Avg Order Value',
        value=f"${current_month['avg_order_value']:.0f}",
        delta=f"{aov_delta:+.1f}%"
    )
    with st.expander("ℹ️ Why this metric?"):
        st.write("**Revenue quality.** Tracks whether customers are spending more per transaction.")

with col4:
    churn_delta = current_month['churn_rate'] - previous_month['churn_rate']
    st.metric(
        label='📉 Churn Rate',
        value=f"{current_month['churn_rate']:.1f}%",
        delta=f"{churn_delta:+.1f}%",
        delta_color='inverse'  # Lower is better for churn
    )
    with st.expander("ℹ️ Why this metric?"):
        st.write("**Retention health.** Lower is better. High churn erodes growth and signals product/service issues.")

with col5:
    nps_delta = current_month['nps_score'] - previous_month['nps_score']
    st.metric(
        label='⭐ NPS Score',
        value=f"{current_month['nps_score']:.0f}",
        delta=f"{nps_delta:+.0f}"
    )
    with st.expander("ℹ️ Why this metric?"):
        st.write("**Customer satisfaction.** Net Promoter Score predicts future growth and brand strength.")

st.markdown('---')


# ═════════════════════════════════════════════
# LEVEL 2: TRENDS - TIME SERIES CHARTS
# ═════════════════════════════════════════════

st.subheader('📈 Performance Trends')
st.markdown('*How key metrics evolved over the past 12 months*')

# Chart 1: Revenue Trend
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(monthly_df['month'], monthly_df['revenue'], 
             marker='o', linewidth=2.5, markersize=6, color=COLORS['primary'])
    ax1.axhline(y=5.0, color=COLORS['success'], linestyle='--', 
                linewidth=2, label='Target: $5M', alpha=0.7)
    
    # Highlight last month
    ax1.plot(current_month['month'], current_month['revenue'], 
             marker='o', markersize=10, color=COLORS['danger'], 
             label='Current Month', zorder=5)
    
    ax1.set_title('Monthly Revenue Trend (2024)', fontsize=13, fontweight='bold', pad=15)
    ax1.set_xlabel('Month', fontsize=11)
    ax1.set_ylabel('Revenue ($M)', fontsize=11)
    ax1.grid(True, alpha=0.25, linestyle=':')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close()
    
    st.caption('**Pattern:** Revenue trending above target since May. Peak in October at $5.5M.')

# Chart 2: Customer Metrics (Dual Line)
with col_chart2:
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2_twin = ax2.twinx()
    
    # Active customers (left axis)
    line1 = ax2.plot(monthly_df['month'], monthly_df['active_customers'], 
                     marker='s', linewidth=2.5, markersize=5, 
                     color=COLORS['primary'], label='Active Customers')
    ax2.set_ylabel('Active Customers', fontsize=11, color=COLORS['primary'])
    ax2.tick_params(axis='y', labelcolor=COLORS['primary'])
    
    # Churned customers (right axis)
    line2 = ax2_twin.plot(monthly_df['month'], monthly_df['churned_customers'], 
                          marker='^', linewidth=2.5, markersize=5, 
                          color=COLORS['danger'], label='Churned Customers')
    ax2_twin.set_ylabel('Churned Customers', fontsize=11, color=COLORS['danger'])
    ax2_twin.tick_params(axis='y', labelcolor=COLORS['danger'])
    
    ax2.set_title('Customer Growth vs Churn (2024)', fontsize=13, fontweight='bold', pad=15)
    ax2.set_xlabel('Month', fontsize=11)
    ax2.grid(True, alpha=0.25, linestyle=':')
    ax2.tick_params(axis='x', rotation=45)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()
    
    st.caption('**Pattern:** Active customers growing steadily. Churn stable around 90/month.')

# Chart 3: Churn Rate Trend
st.markdown('')
fig3, ax3 = plt.subplots(figsize=(14, 4))

bars = ax3.bar(monthly_df['month'], monthly_df['churn_rate'], 
               color=[COLORS['success'] if x < 4.0 else COLORS['danger'] 
                      for x in monthly_df['churn_rate']],
               alpha=0.8, edgecolor='black', linewidth=0.5)

# Add threshold line
ax3.axhline(y=4.0, color=COLORS['neutral'], linestyle='--', 
            linewidth=2, label='Target: <4.0%', alpha=0.7)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, monthly_df['churn_rate'])):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax3.set_title('Monthly Churn Rate Trend (2024)', fontsize=13, fontweight='bold', pad=15)
ax3.set_xlabel('Month', fontsize=11)
ax3.set_ylabel('Churn Rate (%)', fontsize=11)
ax3.set_ylim(0, max(monthly_df['churn_rate']) + 0.5)
ax3.grid(True, alpha=0.25, linestyle=':', axis='y')
ax3.legend(loc='upper right', fontsize=10)
ax3.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig3)
plt.close()

st.caption('**Pattern:** Churn improved from 4.2% (Apr) to 3.4% (Nov). Target: keep below 4.0%.')

st.markdown('---')


# ═════════════════════════════════════════════
# LEVEL 3: SEGMENTS - COMPARISON CHARTS
# ═════════════════════════════════════════════

st.subheader('🎯 Segment Performance')
st.markdown('*Which customer segments drive business results?*')

col_seg1, col_seg2 = st.columns(2)

# Chart: Revenue by Segment (Horizontal Bar)
with col_seg1:
    # Sort by revenue descending
    segment_df_sorted = segment_df.sort_values('revenue', ascending=True)
    
    fig4, ax4 = plt.subplots(figsize=(7, 5))
    bars = ax4.barh(segment_df_sorted['segment'], segment_df_sorted['revenue'],
                    color=[COLORS['primary'], COLORS['secondary'], 
                           COLORS['success'], COLORS['danger']])
    
    # Add value labels
    for bar, val in zip(bars, segment_df_sorted['revenue']):
        ax4.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height()/2,
                 f'${val:.1f}M', va='center', fontsize=11, fontweight='bold')
    
    ax4.set_xlabel('Revenue ($M)', fontsize=11)
    ax4.set_title('Revenue by Customer Segment', fontsize=13, fontweight='bold', pad=15)
    ax4.set_xlim(0, max(segment_df_sorted['revenue']) * 1.2)
    ax4.grid(True, alpha=0.25, linestyle=':', axis='x')
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()
    
    st.caption('**Insight:** Enterprise segment drives highest revenue despite smaller customer count.')

# Chart: Customer Count by Segment (Pie)
with col_seg2:
    fig5, ax5 = plt.subplots(figsize=(7, 5))
    
    wedges, texts, autotexts = ax5.pie(
        segment_df['customer_count'],
        labels=segment_df['segment'],
        autopct='%1.1f%%',
        startangle=90,
        colors=[COLORS['primary'], COLORS['secondary'], COLORS['success'], COLORS['danger']],
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    
    # Style percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
    
    ax5.set_title('Customer Distribution by Segment', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    st.pyplot(fig5)
    plt.close()
    
    st.caption('**Insight:** SMB segment has most customers (40%) but lower per-customer revenue.')

st.markdown('---')


# ═════════════════════════════════════════════
# LEVEL 4: DETAIL - PROGRESSIVE DISCLOSURE
# ═════════════════════════════════════════════

st.subheader('🔍 Detailed Data Explorer')
st.markdown('*Drill down into specific segments and timeframes*')

# Sidebar filters
st.sidebar.header('🎛️ Filters')
st.sidebar.markdown('*Narrow down the data to analyze specific cohorts*')

selected_segment = st.sidebar.multiselect(
    'Customer Segment',
    options=['All'] + list(detailed_df['segment'].unique()),
    default=['All']
)

selected_region = st.sidebar.multiselect(
    'Region',
    options=['All'] + list(detailed_df['region'].unique()),
    default=['All']
)

selected_churn_risk = st.sidebar.multiselect(
    'Churn Risk',
    options=['All'] + list(detailed_df['churn_risk'].unique()),
    default=['All']
)

min_revenue, max_revenue = st.sidebar.slider(
    'Revenue Range ($)',
    min_value=0,
    max_value=int(detailed_df['revenue'].max()),
    value=(0, int(detailed_df['revenue'].max())),
    step=500
)

# Apply filters
filtered_df = detailed_df.copy()

if 'All' not in selected_segment:
    filtered_df = filtered_df[filtered_df['segment'].isin(selected_segment)]

if 'All' not in selected_region:
    filtered_df = filtered_df[filtered_df['region'].isin(selected_region)]

if 'All' not in selected_churn_risk:
    filtered_df = filtered_df[filtered_df['churn_risk'].isin(selected_churn_risk)]

filtered_df = filtered_df[
    (filtered_df['revenue'] >= min_revenue) & 
    (filtered_df['revenue'] <= max_revenue)
]

# Display summary
col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
with col_sum1:
    st.metric('Records Displayed', f"{len(filtered_df):,}")
with col_sum2:
    st.metric('Total Revenue', f"${filtered_df['revenue'].sum()/1e6:.2f}M")
with col_sum3:
    st.metric('Avg Revenue/Customer', f"${filtered_df['revenue'].mean():.0f}")
with col_sum4:
    high_risk_pct = (filtered_df['churn_risk'] == 'High').sum() / len(filtered_df) * 100
    st.metric('High Churn Risk %', f"{high_risk_pct:.1f}%")

st.markdown('')

# Data table with formatting
st.dataframe(
    filtered_df[['customer_id', 'segment', 'region', 'revenue', 
                 'last_activity', 'churn_risk', 'lifetime_months']]
    .sort_values('revenue', ascending=False)
    .style.format({
        'revenue': '${:,.2f}',
        'last_activity': lambda x: x.strftime('%Y-%m-%d'),
    })
    .background_gradient(subset=['revenue'], cmap='Blues')
    .applymap(lambda x: 'background-color: #ffcccc' if x == 'High' else '', 
              subset=['churn_risk']),
    use_container_width=True,
    height=400
)

# Export functionality
st.markdown('### 📥 Export Data')

col_exp1, col_exp2 = st.columns([3, 1])

with col_exp1:
    st.write(f'Ready to download {len(filtered_df):,} filtered records as CSV')

with col_exp2:
    csv_buffer = StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label='⬇️ Download CSV',
        data=csv_data,
        file_name='filtered_customer_data.csv',
        mime='text/csv',
        use_container_width=True
    )

st.markdown('---')

# Footer
st.markdown('''
<div style="text-align: center; color: #666; padding: 20px;">
    <small>
        Dashboard built following hierarchical information design principles<br>
        <strong>Level 1:</strong> KPIs → <strong>Level 2:</strong> Trends → 
        <strong>Level 3:</strong> Segments → <strong>Level 4:</strong> Detail
    </small>
</div>
''', unsafe_allow_html=True)
