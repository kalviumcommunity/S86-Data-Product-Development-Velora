import streamlit as st


def apply_filters(df):

    st.sidebar.header("Filters")

    categories = st.sidebar.multiselect(
        "Category",
        sorted(df["category"].unique()),
        default=sorted(df["category"].unique())
    )

    status = st.sidebar.multiselect(
        "Status",
        sorted(df["status"].unique()),
        default=sorted(df["status"].unique())
    )

    segment = st.sidebar.multiselect(
        "Customer Segment",
        sorted(df["segment"].unique()),
        default=sorted(df["segment"].unique())
    )

    df = df[
        (df["category"].isin(categories)) &
        (df["status"].isin(status)) &
        (df["segment"].isin(segment))
    ]

    return df