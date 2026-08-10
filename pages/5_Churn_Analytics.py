import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data

st.set_page_config(
    page_title="Churn Analytics",
    page_icon="📉",
    layout="wide"
)

st.title("📉 Churn Analytics")
st.markdown(
    "Analyze how complaints, escalations and resolution delays contribute to customer churn."
)

# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------

st.sidebar.header("Filters")

segments = st.sidebar.multiselect(
    "Customer Segment",
    sorted(df["segment"].unique()),
    default=sorted(df["segment"].unique())
)

categories = st.sidebar.multiselect(
    "Complaint Category",
    sorted(df["category"].unique()),
    default=sorted(df["category"].unique())
)

df = df[
    (df["segment"].isin(segments)) &
    (df["category"].isin(categories))
]

# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_customers = df["customer_id"].nunique()

churn_customers = df[df["churned"]]["customer_id"].nunique()

churn_rate = round(
    (churn_customers / total_customers) * 100,
    2
)

avg_resolution = round(
    df[df["churned"]]["resolution_days"].mean(),
    2
)

escalated_churn = df[
    (df["churned"]) &
    (df["is_escalated"])
]["customer_id"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "📉 Churned Customers",
    churn_customers
)

c2.metric(
    "📊 Churn Rate",
    f"{churn_rate}%"
)

c3.metric(
    "🚨 Escalated Churn",
    escalated_churn
)

c4.metric(
    "⏱ Avg Resolution",
    avg_resolution
)

st.divider()

# --------------------------------------------------
# Row 1
# --------------------------------------------------

left, right = st.columns(2)

with left:

    churn_category = (
        df[df["churned"]]
        .groupby("category")
        .size()
        .reset_index(name="Customers")
    )

    fig = px.bar(
        churn_category,
        x="category",
        y="Customers",
        color="category",
        title="Churn by Complaint Category"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    churn_segment = (
        df[df["churned"]]
        .groupby("segment")
        .size()
        .reset_index(name="Customers")
    )

    fig = px.pie(
        churn_segment,
        names="segment",
        values="Customers",
        title="Churn by Customer Segment"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# --------------------------------------------------
# Row 2
# --------------------------------------------------

left, right = st.columns(2)

with left:

    fig = px.box(
        df,
        x="churned",
        y="resolution_days",
        color="churned",
        title="Resolution Time vs Churn"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    escalation = (
        df.groupby(["is_escalated", "churned"])
        .size()
        .reset_index(name="Customers")
    )

    fig = px.bar(
        escalation,
        x="is_escalated",
        y="Customers",
        color="churned",
        barmode="group",
        title="Escalation vs Churn"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# --------------------------------------------------
# Churned Customers Table
# --------------------------------------------------

# --------------------------------------------------
# Churned Customers Table
# --------------------------------------------------

st.subheader("📋 Churned Customers")

table = df[df["churned"]][[
    "customer_id",
    "customer_name",
    "segment",
    "category",
    "complaint_count",
    "resolution_days",
    "priority_level"
]].drop_duplicates()


# Color priority levels
def color_priority(value):
    if value == "High":
        return "background-color: #ffcccc; color: #b30000; font-weight: bold"
    elif value == "Medium":
        return "background-color: #fff0b3; color: #996600; font-weight: bold"
    elif value == "Low":
        return "background-color: #ccf2d6; color: #006b2e; font-weight: bold"
    return ""


styled_table = table.style.map(
    color_priority,
    subset=["priority_level"]
)


st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)

st.divider()

# --------------------------------------------------
# Business Insights
# --------------------------------------------------

st.subheader("💡 Business Insights")

top_category = (
    churn_category.sort_values(
        "Customers",
        ascending=False
    )
    .iloc[0]["category"]
    if not churn_category.empty else "N/A"
)

top_segment = (
    churn_segment.sort_values(
        "Customers",
        ascending=False
    )
    .iloc[0]["segment"]
    if not churn_segment.empty else "N/A"
)

st.success(f"📌 Highest churn complaint category: **{top_category}**")

st.info(f"📌 Customer segment with highest churn: **{top_segment}**")

st.warning(
    f"📌 Average resolution time for churned customers is **{avg_resolution} days**."
)

st.write("""
### Recommendations

- Reduce resolution time for unresolved complaints.
- Prioritize escalated technical and billing tickets.
- Contact high-risk customers before cancellation.
- Improve first-response resolution.
""")