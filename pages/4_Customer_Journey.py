import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data

st.set_page_config(
    page_title="Customer Journey",
    page_icon="👤",
    layout="wide"
)

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

customer_df = df[df["customer_id"] == selected_customer].copy()

if customer_df.empty:
    st.warning("Customer not found.")
    st.stop()

customer = customer_df.iloc[0]

# --------------------------------------------------
# Customer Profile
# --------------------------------------------------

st.subheader("📋 Customer Profile")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Customer", customer["customer_name"])
col2.metric("Segment", customer["segment"])
col3.metric("Region", customer["region"])
col4.metric("Support Channel", customer["support_channel"])

col5, col6, col7, col8 = st.columns(4)

col5.metric("Complaints", int(customer["complaint_count"]))
col6.metric("Priority", customer["priority_level"])
col7.metric("Priority Score", int(customer["priority_score"]))
col8.metric(
    "Cancelled",
    "Yes" if customer["churned"] else "No"
)

st.divider()

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
# Ticket Status
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

    category.columns = ["Category", "Tickets"]

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

resolved = (customer_df["status"] == "Resolved").sum()
unresolved = customer_df["is_unresolved"].sum()
escalated = customer_df["is_escalated"].sum()

st.success(f"""
### Customer Overview

- Total Complaints : **{customer['complaint_count']}**
- Resolved Tickets : **{resolved}**
- Unresolved Tickets : **{unresolved}**
- Escalated Tickets : **{escalated}**
- Current Priority : **{customer['priority_level']}**
- Churn Status : **{"Cancelled" if customer['churned'] else "Active"}**

### Recommendation

**{customer['recommended_action']}**
""")