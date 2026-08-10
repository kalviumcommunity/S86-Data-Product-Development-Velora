import streamlit as st

from utils.database import load_data
from utils.filters import apply_filters
from utils.metrics import (
    total_customers,
    total_tickets,
    unresolved_tickets,
    escalated_tickets,
    average_resolution,
    churn_rate,
    repeat_customers,
    high_priority_customers
)

from utils.charts import (
    complaint_category_chart,
    ticket_status_chart,
    customer_segment_chart,
    resolution_chart,
    complaint_trend
)

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Overview",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Overview Dashboard")
st.caption("Customer Complaint Analytics & Churn Prevention")

# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------

df = apply_filters(df)

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "👥 Customers",
    total_customers(df)
)

c2.metric(
    "🎫 Tickets",
    total_tickets(df)
)

c3.metric(
    "⚠️ Unresolved",
    unresolved_tickets(df)
)

c4.metric(
    "🚨 Escalated",
    escalated_tickets(df)
)

c5, c6, c7 = st.columns(3)

c5.metric(
    "⏱ Avg Resolution",
    f"{average_resolution(df)} Days"
)

c6.metric(
    "📉 Churn Rate",
    f"{churn_rate(df)} %"
)

c7.metric(
    "🔁 Repeat Customers",
    repeat_customers(df)
)

st.divider()

# --------------------------------------------------
# Charts Row 1
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.plotly_chart(
        complaint_category_chart(df),
        use_container_width=True
    )

with right:
    st.plotly_chart(
        ticket_status_chart(df),
        use_container_width=True
    )

# --------------------------------------------------
# Charts Row 2
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.plotly_chart(
        customer_segment_chart(df),
        use_container_width=True
    )

with right:
    st.plotly_chart(
        resolution_chart(df),
        use_container_width=True
    )

# --------------------------------------------------
# Complaint Trend
# --------------------------------------------------

st.plotly_chart(
    complaint_trend(df),
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# High Risk Customers
# --------------------------------------------------

st.subheader("🎯 Customers Requiring Attention")

high_risk = df[
    (df["repeat_customer"] == True)
    |
    (df["is_unresolved"] == True)
    |
    (df["is_escalated"] == True)
]

columns = [
    "customer_id",
    "customer_name",
    "category",
    "status",
    "resolution_days",
    "segment"
]

table = (
    high_risk[columns]
    .drop_duplicates()
    .head(20)
)


# --------------------------------------------------
# Color Status Rows
# --------------------------------------------------

def color_status(row):

    if row["status"] == "Resolved":
        return [
            "background-color: #ccf2d6; color: #006b2e; font-weight: bold"
        ] * len(row)

    elif row["status"] == "Pending":
        return [
            "background-color: #fff0b3; color: #806000; font-weight: bold"
        ] * len(row)

    elif row["status"] == "Open":
        return [
            "background-color: #ffcccc; color: #8b0000; font-weight: bold"
        ] * len(row)

    return [""] * len(row)


styled_table = table.style.apply(
    color_status,
    axis=1
)


st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Business Insights
# --------------------------------------------------

st.subheader("📌 Business Insights")

st.info(
    f"""
• Total Customers: **{total_customers(df)}**

• Total Tickets: **{total_tickets(df)}**

• Unresolved Tickets: **{unresolved_tickets(df)}**

• Escalated Tickets: **{escalated_tickets(df)}**

• Repeat Customers: **{repeat_customers(df)}**

• High Priority Customers: **{high_priority_customers(df)}**
"""
)