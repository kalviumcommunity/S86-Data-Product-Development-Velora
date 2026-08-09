import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import load_data

st.set_page_config(
    page_title="Executive Insights",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Executive Insights")
st.markdown(
    "Executive summary of customer support performance, churn risk, and business recommendations."
)

# --------------------------------------------------
# Load Data
# --------------------------------------------------

df = load_data()

# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_customers = df["customer_id"].nunique()
total_tickets = df["ticket_id"].nunique()

churn_customers = df[df["churned"]]["customer_id"].nunique()
churn_rate = round((churn_customers / total_customers) * 100, 2)

avg_resolution = round(df["resolution_days"].mean(), 2)

high_risk = df[df["priority_level"] == "High"]["customer_id"].nunique()

col1, col2, col3 = st.columns(3)

col1.metric("👥 Customers", total_customers)
col2.metric("🎫 Tickets", total_tickets)
col3.metric("📉 Churn Rate", f"{churn_rate}%")

col4, col5, col6 = st.columns(3)

col4.metric("🚨 High Risk Customers", high_risk)
col5.metric("⏱ Avg Resolution", f"{avg_resolution} Days")
col6.metric("❗ Churned Customers", churn_customers)

st.divider()

# --------------------------------------------------
# Key Insights
# --------------------------------------------------

top_category = df["category"].value_counts().idxmax()

top_segment = (
    df[df["churned"]]["segment"]
    .value_counts()
    .idxmax()
)

top_region = df["region"].value_counts().idxmax()

highest_escalation = (
    df[df["is_escalated"]]["category"]
    .value_counts()
    .idxmax()
)

st.subheader("📊 Key Insights")

left, right = st.columns(2)

with left:

    st.success(f"""
### Customer Support

• Total Tickets: **{total_tickets}**

• Most Frequent Complaint: **{top_category}**

• Highest Escalation Category: **{highest_escalation}**

• Average Resolution Time: **{avg_resolution} Days**
""")

with right:

    st.info(f"""
### Customer Behavior

• Churn Rate: **{churn_rate}%**

• Highest Churn Segment: **{top_segment}**

• Most Active Region: **{top_region}**

• High Risk Customers: **{high_risk}**
""")

st.divider()

# --------------------------------------------------
# Charts
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
        title="Complaint Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    segment = (
        df.groupby("segment")
        .size()
        .reset_index(name="Customers")
    )

    fig = px.pie(
        segment,
        names="segment",
        values="Customers",
        title="Customer Segments"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# --------------------------------------------------
# Executive Recommendations
# --------------------------------------------------

st.subheader("🎯 Executive Recommendations")

recommendations = pd.DataFrame({
    "Priority": [
        "High",
        "High",
        "Medium",
        "Medium",
        "Low"
    ],
    "Recommendation": [
        "Contact all High-Risk customers within 24 hours.",
        "Reduce ticket resolution time below 7 days.",
        "Improve first-contact resolution.",
        "Monitor repeat complainants weekly.",
        "Continue tracking complaint trends."
    ],
    "Expected Impact": [
        "Reduce customer churn",
        "Improve customer satisfaction",
        "Lower escalation rate",
        "Reduce repeat complaints",
        "Support continuous improvement"
    ]
})

st.dataframe(
    recommendations,
    use_container_width=True,
    hide_index=True
)

st.divider()

# --------------------------------------------------
# Overall Health
# --------------------------------------------------

st.subheader("🏆 Overall Support Health")

if churn_rate < 10:
    st.success("🟢 Overall customer support performance is healthy.")
elif churn_rate < 20:
    st.warning("🟡 Customer support requires attention in specific areas.")
else:
    st.error("🔴 High churn risk detected. Immediate intervention is recommended.")

st.info("""
### Velora Summary

Velora connects customer complaints, escalations, and resolution times
to identify customers at risk of churn.

The dashboard enables customer support teams to proactively identify
high-risk customers, prioritize interventions, and improve overall
customer retention through data-driven decision making.
""")