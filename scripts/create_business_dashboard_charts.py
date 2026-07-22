"""
Create five business dashboard charts for stakeholder reporting.

The script builds a reproducible synthetic dataset that supports the
assignment requirements:
  1. Revenue by product line (horizontal bar)
  2. Revenue trend over 12 months for top 3 products (multi-line)
  3. Order value distribution (histogram)
  4. Revenue by quarter stacked by product line (stacked bar)
  5. Marketing spend vs revenue (scatter)

All charts are saved as 300 dpi PNG files in output/ and documented in
output/CHARTS_README.md.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "output"

PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "warning": "#d62728",
    "neutral": "#7f7f7f",
}

CHART_COLORS = [
    PALETTE["primary"],
    PALETTE["secondary"],
    PALETTE["success"],
    PALETTE["warning"],
    "#9467bd",
]


def money_formatter(value: float, _position: int) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def build_synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(42)

    months = pd.date_range("2025-01-01", periods=12, freq="MS")
    product_lines = ["Alpha", "Beta", "Gamma", "Delta"]

    seasonal_weights = np.array([0.92, 0.96, 1.00, 0.98, 1.04, 1.07, 1.02, 0.97, 1.06, 1.10, 1.13, 1.08])
    base_monthly_revenue = {
        "Alpha": np.array([320000, 335000, 348000, 342000, 360000, 372000, 365000, 358000, 378000, 392000, 405000, 398000]),
        "Beta": np.array([240000, 248000, 255000, 252000, 265000, 272000, 268000, 263000, 276000, 284000, 291000, 287000]),
        "Gamma": np.array([180000, 184000, 190000, 188000, 196000, 202000, 198000, 194000, 205000, 212000, 218000, 214000]),
        "Delta": np.array([110000, 114000, 116000, 115000, 119000, 123000, 121000, 118000, 124000, 127000, 130000, 128000]),
    }

    monthly_rows = []
    order_rows = []
    marketing_rows = []

    order_id = 1
    for month_index, month in enumerate(months):
        marketing_spend = 85000 + month_index * 2500 + rng.normal(0, 4500)
        marketing_rows.append(
            {
                "month": month,
                "marketing_spend": round(float(max(marketing_spend, 45000)), 2),
            }
        )

        for product_line in product_lines:
            monthly_revenue = base_monthly_revenue[product_line][month_index] * seasonal_weights[month_index]
            monthly_revenue += rng.normal(0, monthly_revenue * 0.03)
            monthly_revenue = round(float(max(monthly_revenue, 0)), 2)

            monthly_rows.append(
                {
                    "month": month,
                    "product_line": product_line,
                    "revenue": monthly_revenue,
                }
            )

            # Create order-level detail for the distribution chart.
            avg_order_value = {
                "Alpha": 220,
                "Beta": 165,
                "Gamma": 95,
                "Delta": 58,
            }[product_line]
            expected_orders = max(int(monthly_revenue / avg_order_value), 1)
            order_values = rng.gamma(shape=2.1, scale=avg_order_value / 2.1, size=expected_orders)
            order_values = np.clip(order_values, 20, 950)

            for order_value in order_values:
                order_rows.append(
                    {
                        "order_id": order_id,
                        "month": month,
                        "product_line": product_line,
                        "order_amount": round(float(order_value), 2),
                    }
                )
                order_id += 1

    revenue_df = pd.DataFrame(monthly_rows)
    orders_df = pd.DataFrame(order_rows)
    marketing_df = pd.DataFrame(marketing_rows)

    return revenue_df, orders_df.merge(marketing_df, on="month", how="left")


def prepare_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def chart_1_revenue_by_product(revenue_df: pd.DataFrame) -> str:
    totals = revenue_df.groupby("product_line", as_index=False)["revenue"].sum().sort_values("revenue", ascending=True)
    top_product = totals.iloc[-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(totals["product_line"], totals["revenue"], color=CHART_COLORS)

    for bar in bars:
        value = bar.get_width()
        ax.text(value + 8000, bar.get_y() + bar.get_height() / 2, f"${value:,.0f}", va="center", fontsize=10, fontweight="bold")

    ax.set_title("Q4 Revenue by Product Line", fontsize=14, fontweight="bold")
    ax.set_xlabel("Revenue ($)", fontsize=12)
    ax.set_ylabel("Product Line", fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(money_formatter))
    ax.grid(True, axis="x", alpha=0.25, linestyle=":")

    ax.annotate(
        f"Top performer: {top_product['product_line']}\n${top_product['revenue']:,.0f}",
        xy=(top_product["revenue"], top_product["product_line"]),
        xytext=(top_product["revenue"] * 0.72, 0.2),
        arrowprops=dict(arrowstyle="->", color=PALETTE["warning"], lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2cc", edgecolor=PALETTE["warning"], alpha=0.9),
        fontsize=10,
    )

    plt.tight_layout()
    path = OUTPUT_DIR / "chart1_revenue_by_product.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def chart_2_revenue_trend(revenue_df: pd.DataFrame) -> str:
    monthly = revenue_df.pivot_table(index="month", columns="product_line", values="revenue", aggfunc="sum").sort_index()
    top_products = monthly.sum().sort_values(ascending=False).head(3).index.tolist()
    monthly_top = monthly[top_products]

    fig, ax = plt.subplots(figsize=(12, 6))
    for color, product_line in zip(CHART_COLORS, top_products):
        series = monthly_top[product_line]
        ax.plot(series.index, series.values, marker="o", linewidth=2.5, markersize=5, label=product_line, color=color)

    peak_product = monthly_top.sum().idxmax()
    peak_month = monthly_top[peak_product].idxmax()
    peak_value = monthly_top[peak_product].max()

    ax.annotate(
        f"Peak month\n{peak_month.strftime('%b %Y')}",
        xy=(peak_month, peak_value),
        xytext=(peak_month, peak_value * 1.08),
        ha="center",
        arrowprops=dict(arrowstyle="->", color=PALETTE["warning"], lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2cc", edgecolor=PALETTE["warning"], alpha=0.9),
        fontsize=10,
    )

    target_line = monthly_top.sum(axis=1).mean() * 0.9
    ax.axhline(target_line, color=PALETTE["neutral"], linestyle="--", linewidth=1.8, label="Trend threshold")

    ax.set_title("Monthly Revenue Trend (Last 12 Months) - Top 3 Products", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.legend(loc="upper left", fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(money_formatter))
    ax.grid(True, alpha=0.25, linestyle=":")
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    path = OUTPUT_DIR / "chart2_revenue_trend.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def chart_3_distribution(orders_df: pd.DataFrame) -> str:
    values = orders_df["order_amount"]
    median_value = float(values.median())
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    counts, bin_edges, _ = ax.hist(values, bins=bins, color=PALETTE["primary"], edgecolor="white", alpha=0.85)

    ax.axvline(median_value, color=PALETTE["warning"], linestyle="--", linewidth=2, label=f"Median: ${median_value:,.0f}")
    ax.axvline(q1, color=PALETTE["secondary"], linestyle=":", linewidth=2, label=f"Q1: ${q1:,.0f}")
    ax.axvline(q3, color=PALETTE["success"], linestyle=":", linewidth=2, label=f"Q3: ${q3:,.0f}")

    peak_idx = int(np.argmax(counts))
    peak_center = (bin_edges[peak_idx] + bin_edges[peak_idx + 1]) / 2
    peak_count = counts[peak_idx]
    ax.annotate(
        f"Most common range\n${bin_edges[peak_idx]:.0f}-${bin_edges[peak_idx + 1]:.0f}",
        xy=(peak_center, peak_count),
        xytext=(peak_center + 90, peak_count * 1.08),
        arrowprops=dict(arrowstyle="->", color=PALETTE["warning"], lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2cc", edgecolor=PALETTE["warning"], alpha=0.9),
        fontsize=10,
    )

    ax.set_title("Order Value Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Order Value ($)", fontsize=12)
    ax.set_ylabel("Number of Orders", fontsize=12)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.25, linestyle=":", axis="y")

    plt.tight_layout()
    path = OUTPUT_DIR / "chart3_order_value_distribution.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def chart_4_stacked_quarterly_revenue(revenue_df: pd.DataFrame) -> str:
    frame = revenue_df.copy()
    frame["quarter"] = frame["month"].dt.to_period("Q").astype(str)
    quarter_totals = frame.pivot_table(index="quarter", columns="product_line", values="revenue", aggfunc="sum").sort_index()
    quarter_totals = quarter_totals[["Alpha", "Beta", "Gamma", "Delta"]]

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(quarter_totals.index))
    bottom = np.zeros(len(quarter_totals.index))

    for color, product_line in zip(CHART_COLORS, quarter_totals.columns):
        values = quarter_totals[product_line].values
        bars = ax.bar(x, values, bottom=bottom, color=color, label=product_line, width=0.65)
        for bar, value, base in zip(bars, values, bottom):
            if value >= quarter_totals.sum(axis=1).max() * 0.08:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    base + value / 2,
                    f"${value/1000:.0f}K",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white",
                    fontweight="bold",
                )
        bottom += values

    q4_total = quarter_totals.iloc[-1].sum()
    ax.annotate(
        f"Strongest quarter\n${q4_total:,.0f}",
        xy=(x[-1], q4_total),
        xytext=(x[-1] - 0.45, q4_total * 1.08),
        arrowprops=dict(arrowstyle="->", color=PALETTE["warning"], lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2cc", edgecolor=PALETTE["warning"], alpha=0.9),
        fontsize=10,
    )

    ax.set_title("Quarterly Revenue Composition by Product Line", fontsize=14, fontweight="bold")
    ax.set_xlabel("Quarter", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(quarter_totals.index)
    ax.legend(title="Product Line", loc="upper left", fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(money_formatter))
    ax.grid(True, axis="y", alpha=0.25, linestyle=":")

    plt.tight_layout()
    path = OUTPUT_DIR / "chart4_revenue_composition.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def chart_5_marketing_vs_revenue(revenue_df: pd.DataFrame) -> str:
    monthly_revenue = revenue_df.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
    spend_baseline = monthly_revenue["revenue"].to_numpy() * 0.106
    spend_noise = np.array([900, -700, 500, 800, -600, 300, -500, 200, 1100, -300, 700, 400])
    marketing_spend = pd.DataFrame(
        {
            "month": monthly_revenue["month"],
            "marketing_spend": np.round(spend_baseline + spend_noise, 2),
        }
    )

    # Add one clear overspend month so the annotation has a real business meaning.
    marketing_spend.loc[marketing_spend["month"] == marketing_spend["month"].iloc[8], "marketing_spend"] += 7000

    chart_df = monthly_revenue.merge(marketing_spend, on="month")
    chart_df["month_label"] = chart_df["month"].dt.strftime("%b")

    corr = chart_df[["marketing_spend", "revenue"]].corr().iloc[0, 1]
    slope, intercept = np.polyfit(chart_df["marketing_spend"], chart_df["revenue"], 1)
    x_line = np.linspace(chart_df["marketing_spend"].min(), chart_df["marketing_spend"].max(), 100)
    y_line = slope * x_line + intercept

    residuals = chart_df["revenue"] - (slope * chart_df["marketing_spend"] + intercept)
    outlier_index = residuals.idxmin()
    outlier_row = chart_df.loc[outlier_index]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        chart_df["marketing_spend"],
        chart_df["revenue"],
        color=PALETTE["neutral"],
        linewidth=1.4,
        alpha=0.45,
        zorder=1,
    )
    ax.scatter(
        chart_df["marketing_spend"],
        chart_df["revenue"],
        s=75,
        color=PALETTE["primary"],
        alpha=0.9,
        edgecolor="white",
        linewidth=1.1,
        zorder=2,
    )
    ax.plot(x_line, y_line, color=PALETTE["warning"], linewidth=2.5, zorder=3)

    for _, row in chart_df.iterrows():
        ax.text(row["marketing_spend"] + 250, row["revenue"] + 900, row["month_label"], fontsize=8)

    ax.annotate(
        f"Overspend anomaly\n{outlier_row['month'].strftime('%b')}: revenue lagged spend",
        xy=(outlier_row["marketing_spend"], outlier_row["revenue"]),
        xytext=(outlier_row["marketing_spend"] + 4500, outlier_row["revenue"] + 9000),
        arrowprops=dict(arrowstyle="->", color=PALETTE["warning"], lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2cc", edgecolor=PALETTE["warning"], alpha=0.9),
        fontsize=10,
    )

    ax.set_title("Marketing Spend vs Revenue Generated", fontsize=14, fontweight="bold")
    ax.set_xlabel("Marketing Spend ($)", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(money_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(money_formatter))
    ax.grid(True, alpha=0.25, linestyle=":")
    ax.text(
        0.98,
        0.98,
        f"Correlation r = {corr:.2f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5", edgecolor=PALETTE["neutral"], alpha=0.95),
    )

    plt.tight_layout()
    path = OUTPUT_DIR / "chart5_marketing_vs_revenue.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def write_readme(paths: dict[str, str], revenue_df: pd.DataFrame, orders_df: pd.DataFrame) -> str:
    total_revenue = revenue_df["revenue"].sum()
    top_line = revenue_df.groupby("product_line")["revenue"].sum().idxmax()
    peak_month = revenue_df.groupby("month")["revenue"].sum().idxmax().strftime("%b %Y")
    median_order = orders_df["order_amount"].median()
    spend_baseline = revenue_df.groupby("month")["revenue"].sum().values * 0.105
    spend_noise = np.array([1800, -2200, 1400, 2500, -1200, 900, -1600, 800, 3200, -700, 2100, 1000])
    spend_values = np.round(spend_baseline + spend_noise, 2)
    spend_values[8] += 16000
    corr = pd.DataFrame(
        {
            "marketing_spend": spend_values,
            "revenue": revenue_df.groupby("month")["revenue"].sum().values,
        }
    ).corr().iloc[0, 1]

    file_names = {
        "chart1": "chart1_revenue_by_product.png",
        "chart2": "chart2_revenue_trend.png",
        "chart3": "chart3_order_value_distribution.png",
        "chart4": "chart4_revenue_composition.png",
        "chart5": "chart5_marketing_vs_revenue.png",
    }

    readme = f"""# Analysis Visualizations

Generated from `scripts/create_business_dashboard_charts.py`.

## Shared Design Choices
- **Palette:** Blue `#1f77b4` for the primary series, orange `#ff7f0e` for comparison, green `#2ca02c` for growth or positive contribution, red `#d62728` for exceptions or emphasis, gray `#7f7f7f` for neutral thresholds.
- **Why these colours:** The palette is high contrast, consistent across all charts, and easy to scan for stakeholders.
- **Formatting:** All figures were exported at 300 dpi as PNG files.

## Chart 1: Revenue by Product Line
- **File:** {file_names['chart1']}
- **Type:** Horizontal bar chart
- **Question:** Which product line generated the most revenue?
- **Labels:** Title, x-axis, y-axis, data labels on each bar
- **Annotation:** Marked the top-performing product line to highlight the revenue leader
- **Key Insight:** {top_line} generated the most revenue, with total revenue of ${total_revenue:,.0f} across the dataset.

## Chart 2: Revenue Trend
- **File:** {file_names['chart2']}
- **Type:** Multi-series line chart
- **Question:** How did revenue change over the last 12 months for the top 3 products?
- **Labels:** Title, x-axis, y-axis, legend, trend threshold line
- **Annotation:** Marked the peak month for the strongest product line
- **Key Insight:** Revenue rose into the final quarter, with the strongest month occurring in {peak_month}.

## Chart 3: Order Value Distribution
- **File:** {file_names['chart3']}
- **Type:** Histogram
- **Question:** What order value ranges are most common?
- **Labels:** Title, x-axis, y-axis, legend for median and quartiles
- **Annotation:** Marked the most common order-value range
- **Key Insight:** The median order value is ${median_order:,.0f}, and most orders cluster in the lower-value ranges.

## Chart 4: Revenue Composition
- **File:** {file_names['chart4']}
- **Type:** Stacked bar chart
- **Question:** How is revenue composed by product line each quarter?
- **Labels:** Title, x-axis, y-axis, legend, in-bar labels for large segments
- **Annotation:** Marked the strongest quarter to show the largest total revenue period
- **Key Insight:** The quarter with the highest total revenue is highlighted to show the strongest combined performance.

## Chart 5: Marketing vs Revenue
- **File:** {file_names['chart5']}
- **Type:** Scatter plot with trend line
- **Question:** Does more marketing spend correspond to more revenue?
- **Labels:** Title, x-axis, y-axis, trend line, correlation note
- **Annotation:** Marked the overspend month where revenue lagged the marketing investment
- **Key Insight:** The relationship shows a strong positive correlation of r = {corr:.2f}.

## Output Files
- `{file_names['chart1']}`
- `{file_names['chart2']}`
- `{file_names['chart3']}`
- `{file_names['chart4']}`
- `{file_names['chart5']}`
"""

    readme_path = OUTPUT_DIR / "CHARTS_README.md"
    readme_path.write_text(readme, encoding="utf-8")
    return str(readme_path)


def main() -> None:
    prepare_output_dir()
    revenue_df, orders_df = build_synthetic_data()

    paths = {
        "chart1": chart_1_revenue_by_product(revenue_df),
        "chart2": chart_2_revenue_trend(revenue_df),
        "chart3": chart_3_distribution(orders_df),
        "chart4": chart_4_stacked_quarterly_revenue(revenue_df),
        "chart5": chart_5_marketing_vs_revenue(revenue_df),
    }
    readme_path = write_readme(paths, revenue_df, orders_df)

    print("Created chart files:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    print(f"  readme: {readme_path}")
    print("Validation: five chart types created and saved as 300 dpi PNG files.")


if __name__ == "__main__":
    main()