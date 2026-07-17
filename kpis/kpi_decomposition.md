# KPI Decomposition

## Total Revenue

Top-level KPI:

`total_revenue = SUM(amount)`

Breakdown:

```text
Total Revenue
  -> Revenue by Segment
      -> Enterprise
      -> SMB
      -> Startup
  -> Revenue by Product
      -> Product A
      -> Product B
      -> Product C
```

The segment totals and product totals each roll up from the same underlying transaction amounts. In a clean dataset, summing revenue by segment should equal total revenue, and summing revenue by product should also equal total revenue.

Example calculation:

```python
total_revenue = df["amount"].sum()
revenue_by_segment = df.groupby("customer_type")["amount"].sum()
revenue_by_product = df.groupby("product")["amount"].sum()
```

## Revenue per Customer

Formula:

`revenue_per_customer = total_revenue / unique_customers`

Component view:

`(Revenue from Enterprise + Revenue from SMB + Revenue from Startup) / (Enterprise customers + SMB customers + Startup customers)`

This KPI depends on the same revenue base as total revenue, but normalizes by the number of unique customers to show monetization efficiency.