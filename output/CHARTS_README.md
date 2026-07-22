# Analysis Visualizations

Generated from `scripts/create_business_dashboard_charts.py`.

## Shared Design Choices
- **Palette:** Blue `#1f77b4` for the primary series, orange `#ff7f0e` for comparison, green `#2ca02c` for growth or positive contribution, red `#d62728` for exceptions or emphasis, gray `#7f7f7f` for neutral thresholds.
- **Why these colours:** The palette is high contrast, consistent across all charts, and easy to scan for stakeholders.
- **Formatting:** All figures were exported at 300 dpi as PNG files.

## Chart 1: Revenue by Product Line
- **File:** chart1_revenue_by_product.png
- **Type:** Horizontal bar chart
- **Question:** Which product line generated the most revenue?
- **Labels:** Title, x-axis, y-axis, data labels on each bar
- **Annotation:** Marked the top-performing product line to highlight the revenue leader
- **Key Insight:** Alpha generated the most revenue, with total revenue of $11,725,497 across the dataset.

## Chart 2: Revenue Trend
- **File:** chart2_revenue_trend.png
- **Type:** Multi-series line chart
- **Question:** How did revenue change over the last 12 months for the top 3 products?
- **Labels:** Title, x-axis, y-axis, legend, trend threshold line
- **Annotation:** Marked the peak month for the strongest product line
- **Key Insight:** Revenue rose into the final quarter, with the strongest month occurring in Nov 2025.

## Chart 3: Order Value Distribution
- **File:** chart3_order_value_distribution.png
- **Type:** Histogram
- **Question:** What order value ranges are most common?
- **Labels:** Title, x-axis, y-axis, legend for median and quartiles
- **Annotation:** Marked the most common order-value range
- **Key Insight:** The median order value is $92, and most orders cluster in the lower-value ranges.

## Chart 4: Revenue Composition
- **File:** chart4_revenue_composition.png
- **Type:** Stacked bar chart
- **Question:** How is revenue composed by product line each quarter?
- **Labels:** Title, x-axis, y-axis, legend, in-bar labels for large segments
- **Annotation:** Marked the strongest quarter to show the largest total revenue period
- **Key Insight:** The quarter with the highest total revenue is highlighted to show the strongest combined performance.

## Chart 5: Marketing vs Revenue
- **File:** chart5_marketing_vs_revenue.png
- **Type:** Scatter plot with trend line
- **Question:** Does more marketing spend correspond to more revenue?
- **Labels:** Title, x-axis, y-axis, trend line, correlation note
- **Annotation:** Marked the overspend month where revenue lagged the marketing investment
- **Key Insight:** The relationship shows a strong positive correlation of r = 0.93.

## Output Files
- `chart1_revenue_by_product.png`
- `chart2_revenue_trend.png`
- `chart3_order_value_distribution.png`
- `chart4_revenue_composition.png`
- `chart5_marketing_vs_revenue.png`
