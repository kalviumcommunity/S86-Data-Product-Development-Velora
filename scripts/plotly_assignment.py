import os
import pandas as pd
import plotly.graph_objects as go

os.makedirs("interactive_charts", exist_ok=True)

# -----------------------
# Sample Data
# -----------------------

dates = pd.date_range("2024-01-01", periods=10)

revenue = [1000,1200,1500,1700,1600,1800,2100,2500,2400,2800]

orders = [10,12,15,17,16,18,20,25,24,28]

products = ["Laptop","Mouse","Keyboard","Monitor"]

product_revenue=[50000,30000,25000,40000]

product_orders=[400,700,350,600]

avg_order=[125,43,71,67]

# -----------------------
# Chart 1
# -----------------------

fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=dates,
    y=revenue,
    mode="lines+markers",
    hovertemplate=
    "<b>%{x}</b><br>"
    "Revenue : $%{y}<extra></extra>"
))

fig1.update_layout(
    title="Revenue Trend",
    xaxis_title="Date",
    yaxis_title="Revenue"
)

fig1.write_html(
    "interactive_charts/chart1_revenue_trend.html"
)

# -----------------------
# Chart 2
# -----------------------

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=products,
    y=product_revenue,
    customdata=list(zip(product_orders,avg_order)),
    hovertemplate=
    "<b>%{x}</b><br>"
    "Revenue : $%{y}<br>"
    "Orders : %{customdata[0]}<br>"
    "Average Order : $%{customdata[1]}"
    "<extra></extra>"
))

fig2.update_layout(
    title="Product Performance"
)

fig2.write_html(
    "interactive_charts/chart2_product_performance.html"
)

# -----------------------
# Dropdown Chart
# -----------------------

fig3 = go.Figure()

fig3.add_trace(go.Bar(
    x=products,
    y=product_revenue,
    name="Revenue",
    visible=True
))

fig3.add_trace(go.Bar(
    x=products,
    y=[12000,7000,6000,9000],
    name="Profit",
    visible=False
))

fig3.add_trace(go.Bar(
    x=products,
    y=product_orders,
    name="Orders",
    visible=False
))

fig3.update_layout(

    updatemenus=[dict(

        buttons=[

            dict(
                label="Revenue",
                method="update",
                args=[{"visible":[True,False,False]}]
            ),

            dict(
                label="Profit",
                method="update",
                args=[{"visible":[False,True,False]}]
            ),

            dict(
                label="Orders",
                method="update",
                args=[{"visible":[False,False,True]}]
            )

        ]

    )]

)

fig3.write_html(
    "interactive_charts/chart3_metric_selector.html"
)

# -----------------------
# Interactive Chart
# -----------------------

fig4 = go.Figure()

fig4.add_trace(go.Scatter(
    x=dates,
    y=orders,
    mode="markers+lines"
))

fig4.update_layout(
    dragmode="zoom",
    title="Interactive Orders"
)

fig4.write_html(
    "interactive_charts/chart4_interactive.html"
)

print("Charts Created Successfully")
