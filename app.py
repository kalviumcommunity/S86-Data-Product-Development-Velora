import streamlit as st
from PIL import Image
import pandas as pd


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Velora",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# CSV Upload
# --------------------------------------------------

st.sidebar.header("Data Source")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV File",
    type=["csv"]
)


if uploaded_file is not None:

    uploaded_df = pd.read_csv(uploaded_file)

    required_columns = [
        "ticket_id",
        "customer_id",
        "category",
        "status",
        "created_date",
        "resolved_date",
        "customer_name",
        "segment",
        "region",
        "support_channel",
        "subscription_start",
        "subscription_status",
        "escalated",
        "escalation_level",
        "cancelled",
        "resolution_days",
        "is_unresolved",
        "is_escalated",
        "churned",
        "complaint_count",
        "repeat_customer",
        "priority_score",
        "priority_level",
        "recommended_action",
        "priority_reason"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in uploaded_df.columns
    ]

    if missing_columns:

        st.sidebar.error(
            "Invalid CSV file."
        )

        st.sidebar.write(
            "Missing columns:"
        )

        st.sidebar.write(
            missing_columns
        )

        st.session_state["uploaded_data"] = None

    else:

        uploaded_df["created_date"] = pd.to_datetime(
            uploaded_df["created_date"]
        )

        uploaded_df["resolved_date"] = pd.to_datetime(
            uploaded_df["resolved_date"]
        )

        st.session_state["uploaded_data"] = uploaded_df

        st.sidebar.success(
            "CSV uploaded successfully."
        )

        st.sidebar.caption(
            f"{len(uploaded_df)} tickets loaded"
        )

else:

    st.session_state["uploaded_data"] = None


# --------------------------------------------------
# Logo
# --------------------------------------------------

logo = Image.open(
    "assets/velora_logo.png"
)


# --------------------------------------------------
# Header
# --------------------------------------------------

col1, col2 = st.columns([1, 5])


with col1:

    st.image(
        logo,
        width=200
    )


with col2:

    st.title("Velora")

    st.markdown(
        "<h3 style='color:#5F6B7A;'>"
        "Customer Complaint Analytics & Churn Prevention Dashboard"
        "</h3>",
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

    st.info(
        """
        ### 🏠 Overview

        View key performance indicators and an overall summary
        of customer support operations.
        """
    )

    st.info(
        """
        ### 📊 Support Analytics

        Analyze complaint trends, escalations, ticket status,
        and resolution performance.
        """
    )

    st.info(
        """
        ### 🎯 Customer Risk Center

        Identify customers requiring immediate attention based
        on complaint history and support interactions.
        """
    )


with col2:

    st.info(
        """
        ### 👤 Customer Journey

        Explore the complete support journey and complaint history
        of individual customers.
        """
    )

    st.info(
        """
        ### 📉 Churn Analytics

        Understand how complaints, escalations, and delayed
        resolutions contribute to customer churn.
        """
    )

    st.info(
        """
        ### 💼 Executive Insights

        Review business KPIs, strategic insights, and recommendations
        for decision-making.
        """
    )


st.divider()


# --------------------------------------------------
# Quick Tip
# --------------------------------------------------

st.success(
    """
    💡 **Quick Tip**

    Use the navigation menu on the left to explore each dashboard.
    Apply filters to gain deeper insights and identify customers
    requiring proactive support.

    You can also upload a compatible CSV from the sidebar to
    analyze a different customer-support dataset.
    """
)


st.divider()


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.caption(
    "© 2026 Velora • Customer Complaint Analytics & Churn Prevention Dashboard"
)