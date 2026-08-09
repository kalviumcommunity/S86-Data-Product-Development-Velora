import streamlit as st
from PIL import Image

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Velora",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# Logo
# --------------------------------------------------

logo = Image.open("assets/velora_logo.png")

# --------------------------------------------------
# Header
# --------------------------------------------------

col1, col2 = st.columns([1, 5])

with col1:
    st.image(logo, width=200)

with col2:
    st.title("Velora")

    st.markdown(
        "<h3 style='color:#5F6B7A;'>Customer Complaint Analytics & Churn Prevention Dashboard</h3>",
        unsafe_allow_html=True
    )

    st.write(
        """
        Welcome to **Velora**.

        Analyze customer complaints, identify high-risk customers,
        understand churn behaviour, and make proactive support decisions
        through interactive dashboards.
        """
    )

st.divider()

# --------------------------------------------------
# Dashboard Modules
# --------------------------------------------------

st.header("📊 Dashboard Modules")

col1, col2 = st.columns(2)

with col1:

    st.info("""
### 🏠 Overview

View key performance indicators and an overall summary of customer support operations.
""")

    st.info("""
### 📊 Support Analytics

Analyze complaint trends, escalations, ticket status, and resolution performance.
""")

    st.info("""
### 🎯 Customer Risk Center

Identify customers requiring immediate attention based on complaint history and support interactions.
""")

with col2:

    st.info("""
### 👤 Customer Journey

Explore the complete support journey and complaint history of individual customers.
""")

    st.info("""
### 📉 Churn Analytics

Understand how complaints, escalations, and delayed resolutions contribute to customer churn.
""")

    st.info("""
### 💼 Executive Insights

Review business KPIs, strategic insights, and recommendations for decision-making.
""")

st.divider()

# --------------------------------------------------
# Quick Tip
# --------------------------------------------------

st.success("""
💡 **Quick Tip**

Use the navigation menu on the left to explore each dashboard.
Apply filters to gain deeper insights and identify customers requiring proactive support.
""")

st.divider()

# --------------------------------------------------
# Footer
# --------------------------------------------------

st.caption(
    "© 2026 Velora • Customer Complaint Analytics & Churn Prevention Dashboard"
)