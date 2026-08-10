import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data

st.set_page_config(
    page_title="Customer Risk Center",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Customer Risk Center")
st.write("Identify customers who require immediate attention to reduce churn.")

# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()

# --------------------------------------------------
# Create missing columns if needed
# --------------------------------------------------

if "priority_score" not in df.columns:

    df["priority_score"] = (
        df["is_unresolved"].astype(int) * 30 +
        df["is_escalated"].astype(int) * 20 +
        df["repeat_customer"].astype(int) * 20 +
        (df["resolution_days"] > 7).astype(int) * 20
    )

if "priority_level" not in df.columns:

    def get_priority(score):
        if score >= 80:
            return "High"
        elif score >= 50:
            return "Medium"
        return "Low"

    df["priority_level"] = df["priority_score"].apply(get_priority)

if "recommended_action" not in df.columns:

    def get_action(level):
        if level == "High":
            return "📞 Contact Customer Immediately"
        elif level == "Medium":
            return "📧 Follow Up Within 24 Hours"
        return "👀 Monitor"

    df["recommended_action"] = df["priority_level"].apply(get_action)

if "priority_reason" not in df.columns:

    def get_reason(row):

        reasons = []

        if row["is_unresolved"]:
            reasons.append("Unresolved Ticket")

        if row["is_escalated"]:
            reasons.append("Escalated")

        if row["repeat_customer"]:
            reasons.append("Repeat Complaints")

        if row["resolution_days"] > 7:
            reasons.append("Delayed Resolution")

        if len(reasons) == 0:
            return "No Immediate Risk"

        return ", ".join(reasons)

    df["priority_reason"] = df.apply(get_reason, axis=1)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.header("Filters")

segments = st.sidebar.multiselect(
    "Segment",
    sorted(df["segment"].unique()),
    default=sorted(df["segment"].unique())
)

categories = st.sidebar.multiselect(
    "Category",
    sorted(df["category"].unique()),
    default=sorted(df["category"].unique())
)

priorities = st.sidebar.multiselect(
    "Priority",
    sorted(df["priority_level"].unique()),
    default=sorted(df["priority_level"].unique())
)

filtered = df[
    (df["segment"].isin(segments)) &
    (df["category"].isin(categories)) &
    (df["priority_level"].isin(priorities))
]

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

high = filtered[filtered["priority_level"] == "High"]["customer_id"].nunique()
medium = filtered[filtered["priority_level"] == "Medium"]["customer_id"].nunique()
low = filtered[filtered["priority_level"] == "Low"]["customer_id"].nunique()

avg_score = round(filtered["priority_score"].mean(), 2)

c1, c2, c3, c4 = st.columns(4)

c1.metric("🔴 High Risk", high)
c2.metric("🟡 Medium Risk", medium)
c3.metric("🟢 Low Risk", low)
c4.metric("⭐ Avg Score", avg_score)

st.divider()

# --------------------------------------------------
# Risk Distribution
# --------------------------------------------------

risk = (
    filtered["priority_level"]
    .value_counts()
    .reset_index()
)

risk.columns = ["Priority", "Customers"]

fig = px.pie(
    risk,
    names="Priority",
    values="Customers",
    title="Customer Risk Distribution"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Search
# --------------------------------------------------

search = st.text_input("🔍 Search Customer ID")

if search:

    filtered = filtered[
        filtered["customer_id"].astype(str).str.contains(search, case=False)
    ]

# --------------------------------------------------
# Table
# --------------------------------------------------

st.subheader("Customers Requiring Attention")

table = (
    filtered
    .sort_values("priority_score", ascending=False)
    .drop_duplicates("customer_id")
)

display_columns = [
    "customer_id",
    "customer_name",
    "priority_level",
    "priority_score",
    "priority_reason",
    "complaint_count",
    "resolution_days",
    "recommended_action"
]


def color_priority(row):
    styles = [""] * len(row)

    priority_index = row.index.get_loc("priority_level")

    if row["priority_level"] == "High":
        styles[priority_index] = (
            "background-color: #ffcccc; "
            "color: #b30000; "
            "font-weight: bold"
        )

    elif row["priority_level"] == "Medium":
        styles[priority_index] = (
            "background-color: #fff0b3; "
            "color: #996600; "
            "font-weight: bold"
        )

    elif row["priority_level"] == "Low":
        styles[priority_index] = (
            "background-color: #ccffcc; "
            "color: #006600; "
            "font-weight: bold"
        )

    return styles


styled_table = (
    table[display_columns]
    .style
    .apply(color_priority, axis=1)
)

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Top Risk Customers
# --------------------------------------------------

top = table.head(10)

fig = px.bar(
    top,
    x="customer_name",
    y="priority_score",
    color="priority_level",
    title="Top High Risk Customers"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Insights
# --------------------------------------------------

st.subheader("Business Recommendations")

st.info(f"""
**High Risk Customers:** {high}

**Average Priority Score:** {avg_score}

Recommended Actions:

• Contact all High Risk customers immediately.

• Resolve unresolved tickets within 7 days.

• Prioritize repeat complainants.

• Review escalated technical complaints first.
""")

# --------------------------------------------------
# Download
# --------------------------------------------------

csv = table.to_csv(index=False)

st.download_button(
    "📥 Download Risk Report",
    csv,
    "customer_risk_report.csv",
    "text/csv"
)