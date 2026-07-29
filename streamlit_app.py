import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Interactive Sales Dashboard")

dates = pd.date_range("2024-01-01", periods=10)

revenue = [1000,1200,1500,1700,1600,1800,2100,2500,2400,2800]

df = pd.DataFrame({
    "date":dates,
    "revenue":revenue
})

minimum = st.sidebar.slider(
    "Minimum Revenue",
    0,
    3000,
    1000
)

filtered = df[
    df["revenue"]>=minimum
]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=filtered["date"],
    y=filtered["revenue"],
    mode="lines+markers",
    hovertemplate=
    "<b>%{x}</b><br>"
    "Revenue : $%{y}"
))

st.plotly_chart(
    fig,
    use_container_width=True
)

st.dataframe(filtered)