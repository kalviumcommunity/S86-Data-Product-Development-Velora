import os
import numpy as np
import pandas as pd

# -----------------------------
# Create Sample Dataset
# -----------------------------
np.random.seed(42)

customer_types = ["Enterprise", "SMB", "Startup"]
products = ["Product A", "Product B", "Product C"]

rows = 100

df = pd.DataFrame({
    "customer_id": np.arange(1, rows + 1),
    "customer_type": np.random.choice(customer_types, rows),
    "product": np.random.choice(products, rows),
    "revenue": np.random.randint(5000, 100000, rows),
    "support_tickets": np.random.randint(1, 15, rows),
    "churn": np.random.choice([0,1], rows, p=[0.9,0.1])
})

print("\nOriginal Data")
print(df.head())

# -----------------------------
# Task 1
# Single Level GroupBy
# -----------------------------

segment_metrics = df.groupby("customer_type").agg({
    "churn":"mean",
    "revenue":"sum",
    "customer_id":"count",
    "support_tickets":"mean"
})

segment_metrics.columns = [
    "churn_rate",
    "total_revenue",
    "customer_count",
    "avg_support_tickets"
]

print("\nSegment Metrics")
print(segment_metrics)

# -----------------------------
# Task 2
# Multi-Level GroupBy
# -----------------------------

product_segment = df.groupby(
    ["customer_type","product"]
).agg({
    "revenue":"sum",
    "customer_id":"count"
})

product_segment.columns = [
    "total_revenue",
    "customer_count"
]

print("\nMulti Level GroupBy")
print(product_segment)

print("\nUnstacked View")
print(product_segment.unstack())

# -----------------------------
# Task 3
# Pivot Table
# -----------------------------

pivot = pd.pivot_table(
    df,
    values="revenue",
    index="customer_type",
    columns="product",
    aggfunc="sum"
)

print("\nPivot Table")
print(pivot)

# -----------------------------
# Task 4
# Ranking
# -----------------------------

segment_metrics["churn_rank"] = (
    segment_metrics["churn_rate"]
    .rank(ascending=False)
)

segment_metrics["revenue_contribution"] = (
    segment_metrics["total_revenue"] /
    segment_metrics["total_revenue"].sum()
)*100

print("\nWorst Churn First")

print(
    segment_metrics.sort_values(
        "churn_rate",
        ascending=False
    )
)

# -----------------------------
# Task 5
# Business Insights
# -----------------------------

insights=[]

for segment in segment_metrics.index:

    row = segment_metrics.loc[segment]

    if row["churn_rate"] > 0.10:
        action="HIGH PRIORITY: Improve retention"

    elif row["churn_rate"] < 0.02:
        action="Healthy segment"

    else:
        action="Monitor closely"

    insights.append({
        "segment":segment,
        "customer_count":int(row["customer_count"]),
        "churn_rate":f"{row['churn_rate']:.1%}",
        "total_revenue":f"${row['total_revenue']:.0f}",
        "revenue_contribution":f"{row['revenue_contribution']:.1f}%",
        "action":action
    })

insights_df = pd.DataFrame(insights)

print("\nSegment Insights")
print(insights_df)

os.makedirs("output",exist_ok=True)

insights_df.to_csv(
    "output/segment_insights.csv",
    index=False
)

print("\nFile Saved")
print("output/segment_insights.csv")