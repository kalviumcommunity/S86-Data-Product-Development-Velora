from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"
ROLLING_AVG_PLOT_FILE = OUTPUT_DIR / "rolling_avg.png"
CUMULATIVE_PLOT_FILE = OUTPUT_DIR / "cumulative.png"
TREND_ANALYSIS_FILE = OUTPUT_DIR / "trend_analysis.txt"


def build_daily_data(days: int = 180) -> pd.DataFrame:
    """Build a reproducible daily revenue series for the time-series tasks."""

    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    day_index = np.arange(days)

    trend = np.linspace(900, 1750, days)
    weekly_seasonality = 140 * np.sin(2 * np.pi * day_index / 7)
    monthly_seasonality = 180 * np.sin(2 * np.pi * day_index / 30)
    temporary_dip = np.where((day_index >= 60) & (day_index < 90), -550, 0)
    noise = rng.normal(0, 55, days)

    revenue = trend + weekly_seasonality + monthly_seasonality + temporary_dip + noise
    revenue = np.clip(revenue, a_min=100, a_max=None).round(2)

    orders = (
        70
        + 0.025 * trend
        + 10 * np.sin(2 * np.pi * day_index / 14)
        + rng.normal(0, 4, days)
    )
    orders = np.clip(np.rint(orders), a_min=1, a_max=None).astype(int)

    return pd.DataFrame({
        "date": dates,
        "revenue": revenue,
        "orders": orders,
    })


def resample_time_periods(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Aggregate revenue across weekly and monthly periods."""

    df_ts = df.set_index("date")

    weekly = pd.DataFrame({
        "revenue_sum": df_ts["revenue"].resample("W").sum(),
        "orders_count": df_ts["orders"].resample("W").count(),
        "revenue_mean": df_ts["revenue"].resample("W").mean(),
    })

    monthly = pd.DataFrame({
        "revenue_sum": df_ts["revenue"].resample("ME").sum(),
        "orders_count": df_ts["orders"].resample("ME").count(),
        "revenue_mean": df_ts["revenue"].resample("ME").mean(),
    })

    comparison = pd.DataFrame({
        "weekly": {
            "avg_bucket_revenue": weekly["revenue_sum"].mean(),
            "max_bucket_revenue": weekly["revenue_sum"].max(),
            "bucket_count": len(weekly),
        },
        "monthly": {
            "avg_bucket_revenue": monthly["revenue_sum"].mean(),
            "max_bucket_revenue": monthly["revenue_sum"].max(),
            "bucket_count": len(monthly),
        },
    }).T

    return weekly, monthly, comparison


def compute_rolling_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add 7-day and 30-day rolling revenue averages."""

    df = df.copy()
    df["revenue_ma7"] = df["revenue"].rolling(window=7).mean()
    df["revenue_ma30"] = df["revenue"].rolling(window=30).mean()
    return df


def compute_month_over_month(df: pd.DataFrame) -> pd.Series:
    """Calculate month-over-month revenue change."""

    monthly_revenue = df.set_index("date")["revenue"].resample("ME").sum()
    return monthly_revenue.pct_change() * 100


def compute_cumulative_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Track accumulated revenue over time."""

    df = df.copy()
    df["cumulative_revenue"] = df["revenue"].cumsum()
    return df


def save_plots(df: pd.DataFrame) -> None:
    """Save the rolling-average and cumulative-growth charts."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["revenue"], label="Raw", alpha=0.3, color="#7f8c8d")
    plt.plot(df["date"], df["revenue_ma7"], label="7-day MA", linewidth=2.0, color="#d35400")
    plt.plot(df["date"], df["revenue_ma30"], label="30-day MA", linewidth=2.5, color="#1f77b4")
    plt.title("Raw Revenue vs Rolling Averages")
    plt.xlabel("Date")
    plt.ylabel("Revenue")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROLLING_AVG_PLOT_FILE, dpi=150)
    plt.close()

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["cumulative_revenue"], color="#2c3e50", linewidth=2.5)
    plt.title("Cumulative Revenue Over Time")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Revenue")
    plt.tight_layout()
    plt.savefig(CUMULATIVE_PLOT_FILE, dpi=150)
    plt.close()


def summarize_trend(df: pd.DataFrame, mom_change: pd.Series) -> str:
    """Create the business interpretation text required for submission."""

    recent_ma30 = df["revenue_ma30"].dropna().iloc[-30:]
    if len(recent_ma30) < 2:
        raise ValueError("Not enough rolling-average data to determine trend.")

    delta_pct = ((recent_ma30.iloc[-1] - recent_ma30.iloc[0]) / recent_ma30.iloc[0]) * 100
    threshold = 1.0
    if delta_pct > threshold:
        trend_direction = "up"
    elif delta_pct < -threshold:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    latest_mom = mom_change.dropna().iloc[-1]
    volatility = df["revenue"].std()

    if trend_direction == "up":
        recommendation = "Maintain the current growth strategy and scale the channels supporting recent demand."
        implication = "The business is gaining momentum and the smoother trend suggests growth is not just daily noise."
    elif trend_direction == "down":
        recommendation = "Investigate demand drivers, pricing, and retention levers before the decline deepens."
        implication = "The business is losing momentum and the rolling average confirms the drop is persistent."
    else:
        recommendation = "Hold strategy steady and focus on stabilising promotions, inventory, or campaign timing."
        implication = "The business is broadly stable, but the trend is too small to call a clear directional change."

    growth_months = mom_change[mom_change > 0].dropna()
    decline_months = mom_change[mom_change < 0].dropna()

    growth_lines = "\n".join(
        f"- {idx.strftime('%Y-%m')}: +{value:.1f}%"
        for idx, value in growth_months.items()
    ) or "- None"
    decline_lines = "\n".join(
        f"- {idx.strftime('%Y-%m')}: {value:.1f}%"
        for idx, value in decline_months.items()
    ) or "- None"

    analysis = f"""TREND ANALYSIS

Rolling Average Trend: {trend_direction.upper()}
Change over the last 30 days: {delta_pct:.1f}%
Latest month-over-month change: {latest_mom:.1f}%
Revenue volatility (std dev): {volatility:.0f}

Months with positive growth:
{growth_lines}

Months with negative growth:
{decline_lines}

Business Implications:
{implication}

Recommended Action:
{recommendation}
"""

    return analysis


def main() -> None:
    df = build_daily_data()
    weekly, monthly, comparison = resample_time_periods(df)
    df = compute_rolling_averages(df)
    mom_change = compute_month_over_month(df)
    df = compute_cumulative_revenue(df)

    save_plots(df)

    trend_analysis = summarize_trend(df, mom_change)
    TREND_ANALYSIS_FILE.write_text(trend_analysis, encoding="utf-8")

    print("Weekly summary:\n", weekly.head().to_string())
    print("\nMonthly summary:\n", monthly.head().to_string())
    print("\nResample comparison:\n", comparison.to_string())
    print("\nMonth-over-month change (%):\n", mom_change.to_string())
    print("\nTotal revenue: ${:,.0f}".format(df["cumulative_revenue"].iloc[-1]))

    highest_period = comparison["avg_bucket_revenue"].idxmax()
    print(f"\nHighest average bucket revenue: {highest_period}")

    print("\n" + trend_analysis)

    print(
        json.dumps(
            {
                "rolling_avg_plot": str(ROLLING_AVG_PLOT_FILE),
                "cumulative_plot": str(CUMULATIVE_PLOT_FILE),
                "trend_analysis": str(TREND_ANALYSIS_FILE),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()