import plotly.express as px
import pandas as pd


def complaint_category_chart(df):
    category_counts = (
        df["category"]
        .value_counts()
        .reset_index()
    )

    category_counts.columns = ["Category", "Count"]

    fig = px.bar(
        category_counts,
        x="Category",
        y="Count",
        color="Category",
        title="Complaints by Category"
    )

    return fig


def ticket_status_chart(df):
    fig = px.pie(
        df,
        names="status",
        title="Ticket Status Distribution"
    )

    return fig


def customer_segment_chart(df):
    segment_counts = (
        df["segment"]
        .value_counts()
        .reset_index()
    )

    segment_counts.columns = ["Segment", "Count"]

    fig = px.bar(
        segment_counts,
        x="Segment",
        y="Count",
        color="Segment",
        title="Customer Segments"
    )

    return fig


def resolution_chart(df):
    fig = px.histogram(
        df,
        x="resolution_days",
        nbins=15,
        title="Resolution Time Distribution"
    )

    return fig


def complaint_trend(df):
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

    return fig