import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data
from utils.filters import apply_filters

st.set_page_config(
    page_title="Support Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Support Analytics")
st.markdown(
    "Analyze complaints, escalations, resolution performance and overall support efficiency."
)

# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()

# Sidebar Filters
df = apply_filters(df)

# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

total_tickets = df["ticket_id"].nunique()
open_tickets = (df["status"] == "Open").sum()
pending_tickets = (df["status"] == "Pending").sum()
resolved_tickets = (df["status"] == "Resolved").sum()
escalated_tickets = df["is_escalated"].sum()
avg_resolution = round(df["resolution_days"].mean(), 2)

c1, c2, c3 = st.columns(3)

c1.metric("🎫 Total Tickets", total_tickets)
c2.metric("📂 Open Tickets", open_tickets)
c3.metric("⏳ Pending Tickets", pending_tickets)

c4, c5, c6 = st.columns(3)

c4.metric("✅ Resolved Tickets", resolved_tickets)
c5.metric("🚨 Escalated Tickets", escalated_tickets)
c6.metric("⏱ Avg Resolution Days", avg_resolution)

st.divider()

# --------------------------------------------------
# Row 1
# --------------------------------------------------

left, right = st.columns(2)

with left:

    category = (
        df.groupby("category")
        .size()
        .reset_index(name="Tickets")
    )

    fig = px.bar(
        category,
        x="category",
        y="Tickets",
        color="category",
        title="Complaints by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

with right:

    fig = px.pie(
        df,
        names="status",
        title="Ticket Status Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Row 2
# --------------------------------------------------

left, right = st.columns(2)

with left:

    esc = (
        df[df["is_escalated"]]
        .groupby("escalation_level")
        .size()
        .reset_index(name="Tickets")
    )

    if len(esc) > 0:

        fig = px.bar(
            esc,
            x="escalation_level",
            y="Tickets",
            color="escalation_level",
            title="Escalation Levels"
        )

        st.plotly_chart(fig, use_container_width=True)

with right:

    fig = px.histogram(
        df,
        x="resolution_days",
        nbins=15,
        title="Resolution Time Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Complaint Trend
# --------------------------------------------------

trend = (
    df.groupby(df["created_date"].dt.date)
    .size()
    .reset_index(name="Tickets")
)

trend.columns = ["Date", "Tickets"]

fig = px.line(
    trend,
    x="Date",
    y="Tickets",
    markers=True,
    title="Complaint Trend"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------
# Delayed Tickets
# --------------------------------------------------

st.subheader("⏰ Delayed Tickets")

delayed = df[
    df["resolution_days"] > 7
][[
    "ticket_id",
    "customer_id",
    "customer_name",
    "category",
    "resolution_days",
    "status"
]]


# --------------------------------------------------
# Color Rows Based on Status
# --------------------------------------------------

def color_delayed_row(row):

    if row["status"] == "Resolved":
        return [
            "background-color: #ccf2d6; "
            "color: #006b2e; "
            "font-weight: bold"
        ] * len(row)

    elif row["status"] == "Open":
        return [
            "background-color: #fff0b3; "
            "color: #806000; "
            "font-weight: bold"
        ] * len(row)

    elif row["status"] == "Pending":
        return [
            "background-color: #ffcccc; "
            "color: #8b0000; "
            "font-weight: bold"
        ] * len(row)

    return [""] * len(row)


styled_delayed = delayed.style.apply(
    color_delayed_row,
    axis=1
)


st.dataframe(
    styled_delayed,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# Escalated Tickets
# --------------------------------------------------

st.subheader("🚨 Escalated Tickets")

escalated = df[
    df["is_escalated"]
][[
    "ticket_id",
    "customer_id",
    "customer_name",
    "category",
    "escalation_level",
    "status"
]]


def color_escalated_row(row):

    if row["escalation_level"] == "L3":
        return [
            "background-color: #ffcccc; "
            "color: #8b0000; "
            "font-weight: bold"
        ] * len(row)

    elif row["escalation_level"] == "L2":
        return [
            "background-color: #fff0b3; "
            "color: #806000; "
            "font-weight: bold"
        ] * len(row)

    elif row["escalation_level"] == "L1":
        return [
            "background-color: #ccf2d6; "
            "color: #006b2e; "
            "font-weight: bold"
        ] * len(row)

    return [""] * len(row)


styled_escalated = escalated.style.apply(
    color_escalated_row,
    axis=1
)


st.dataframe(
    styled_escalated,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Business Insights
# --------------------------------------------------

st.subheader("💡 Business Insights")

top_category = (
    df["category"]
    .value_counts()
    .idxmax()
)

top_escalation = (
    df[df["is_escalated"]]["category"]
    .value_counts()
    .idxmax()
)

repeat = df[df["repeat_customer"]]["customer_id"].nunique()

st.success(f"📌 Most common complaint category: **{top_category}**")

st.info(f"🚨 Category with highest escalations: **{top_escalation}**")

st.warning(f"🔁 Repeat customers: **{repeat}**")

st.write(
    f"""
Average ticket resolution time is **{avg_resolution} days**.
Focus on reducing delayed tickets to improve customer satisfaction and reduce churn risk.
"""
)