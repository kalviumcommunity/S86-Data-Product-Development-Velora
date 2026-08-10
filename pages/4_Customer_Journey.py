import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data


st.set_page_config(
    page_title="Customer Journey",
    page_icon="👤",
    layout="wide"
)


# --------------------------------------------------
# Custom Styling
# --------------------------------------------------

st.markdown("""
<style>

[data-testid="stMetricValue"] {
    font-size: 22px !important;
}

[data-testid="stMetricLabel"] {
    font-size: 13px !important;
}

[data-testid="stMetric"] {
    padding: 5px 0px !important;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Page Header
# --------------------------------------------------

st.title("👤 Customer Journey")

st.markdown(
    "Explore a customer's complete support history, complaint timeline and churn risk."
)


# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()


# --------------------------------------------------
# Customer Selection
# --------------------------------------------------

customer_ids = sorted(df["customer_id"].unique())

selected_customer = st.selectbox(
    "Select Customer ID",
    customer_ids
)

customer_df = df[
    df["customer_id"] == selected_customer
].copy()


if customer_df.empty:
    st.warning("Customer not found.")
    st.stop()


customer = customer_df.iloc[0]


# --------------------------------------------------
# Customer Profile
# --------------------------------------------------

st.subheader("📋 Customer Profile")


# First row

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Customer",
    customer["customer_name"]
)

c2.metric(
    "Segment",
    customer["segment"]
)

c3.metric(
    "Region",
    customer["region"]
)

c4.metric(
    "Channel",
    customer["support_channel"]
)


# Second row

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Complaints",
    customer["complaint_count"]
)

c2.metric(
    "Priority",
    customer["priority_level"]
)

c3.metric(
    "Risk Score",
    customer["priority_score"]
)

c4.metric(
    "Cancelled",
    customer["cancelled"]
)


# --------------------------------------------------
# Complaint Timeline
# --------------------------------------------------

st.subheader("📈 Complaint Timeline")


timeline = customer_df.sort_values("created_date")


fig = px.line(
    timeline,
    x="created_date",
    y="resolution_days",
    markers=True,
    title="Resolution Time Across Complaints"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# Ticket Status & Complaint Categories
# --------------------------------------------------

left, right = st.columns(2)


with left:

    fig = px.pie(
        customer_df,
        names="status",
        title="Ticket Status"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with right:

    category = (
        customer_df["category"]
        .value_counts()
        .reset_index()
    )

    category.columns = [
        "Category",
        "Tickets"
    ]

    fig = px.bar(
        category,
        x="Category",
        y="Tickets",
        color="Category",
        title="Complaint Categories"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.divider()


# --------------------------------------------------
# Ticket History
# --------------------------------------------------

st.subheader("🎫 Ticket History")


history = customer_df[
    [
        "ticket_id",
        "category",
        "status",
        "created_date",
        "resolved_date",
        "resolution_days",
        "escalation_level"
    ]
].sort_values("created_date")


st.dataframe(
    history,
    use_container_width=True,
    hide_index=True
)


st.divider()


# --------------------------------------------------
# Risk Assessment
# --------------------------------------------------

st.subheader("🚨 Current Risk Assessment")


left, right = st.columns([1, 2])


with left:

    st.metric(
        "Priority Level",
        customer["priority_level"]
    )

    st.metric(
        "Priority Score",
        int(customer["priority_score"])
    )


with right:

    st.info(
        f"""
### Why is this customer at this risk level?

**Reason**

{customer['priority_reason']}

**Recommended Action**

{customer['recommended_action']}
"""
    )


st.divider()


# --------------------------------------------------
# Journey Summary
# --------------------------------------------------

st.subheader("📌 Journey Summary")


resolved = (
    customer_df["status"] == "Resolved"
).sum()

unresolved = (
    customer_df["is_unresolved"]
).sum()

escalated = (
    customer_df["is_escalated"]
).sum()


st.success(
    f"""
### Customer Overview

- Total Complaints : **{customer['complaint_count']}**
- Resolved Tickets : **{resolved}**
- Unresolved Tickets : **{unresolved}**
- Escalated Tickets : **{escalated}**
- Current Priority : **{customer['priority_level']}**
- Churn Status : **{"Cancelled" if customer['churned'] else "Active"}**

### Recommendation

**{customer['recommended_action']}**
"""
)