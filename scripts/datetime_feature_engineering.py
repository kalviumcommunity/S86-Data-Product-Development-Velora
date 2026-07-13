import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
OUTPUT_DIR = Path("output")
DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load_sample_transaction_data() -> pd.DataFrame:
    """
    Build a sample transaction dataset where timestamps are raw strings.

    This intentionally keeps `transaction_date` as string to demonstrate
    explicit datetime parsing.
    """
    records = [
        {"transaction_id": 1, "customer_id": 101, "amount": 120.50, "transaction_date": "2025-01-15 14:30:45"},
        {"transaction_id": 2, "customer_id": 102, "amount": 75.00, "transaction_date": "2025-01-15 17:10:20"},
        {"transaction_id": 3, "customer_id": 101, "amount": 220.00, "transaction_date": "2025-01-16 09:05:11"},
        {"transaction_id": 4, "customer_id": 103, "amount": 40.25, "transaction_date": "2025-01-18 11:42:00"},
        {"transaction_id": 5, "customer_id": 104, "amount": 315.99, "transaction_date": "2025-01-18 20:18:34"},
        {"transaction_id": 6, "customer_id": 102, "amount": 65.75, "transaction_date": "2025-01-20 08:15:49"},
        {"transaction_id": 7, "customer_id": 105, "amount": 510.10, "transaction_date": "2025-01-22 13:27:02"},
        {"transaction_id": 8, "customer_id": 104, "amount": 85.90, "transaction_date": "2025-01-23 14:55:10"},
        {"transaction_id": 9, "customer_id": 106, "amount": 47.25, "transaction_date": "2025-01-25 19:44:58"},
        {"transaction_id": 10, "customer_id": 101, "amount": 138.35, "transaction_date": "2025-01-27 07:35:42"},
        {"transaction_id": 11, "customer_id": 103, "amount": 92.80, "transaction_date": "2025-01-30 10:30:00"},
        {"transaction_id": 12, "customer_id": 106, "amount": 60.00, "transaction_date": "2025-02-01 21:17:19"},
        {"transaction_id": 13, "customer_id": 102, "amount": 175.45, "transaction_date": "2025-02-04 16:03:05"},
        {"transaction_id": 14, "customer_id": 107, "amount": 42.00, "transaction_date": "2025-02-05 12:02:40"},
        {"transaction_id": 15, "customer_id": 105, "amount": 89.99, "transaction_date": "2025-02-08 09:48:27"},
        {"transaction_id": 16, "customer_id": 107, "amount": 320.00, "transaction_date": "2025-02-10 18:41:16"},
    ]
    df = pd.DataFrame(records)
    return df


def parse_transaction_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timestamp strings to datetime using explicit format only.
    """
    df_parsed = df.copy()

    invalid_mask = ~df_parsed["transaction_date"].astype(str).str.match(TIMESTAMP_PATTERN)
    if invalid_mask.any():
        invalid_values = df_parsed.loc[invalid_mask, "transaction_date"].head(5).tolist()
        raise ValueError(
            "Found timestamp strings that do not match required format "
            f"{DATETIME_FORMAT}. Sample invalid values: {invalid_values}"
        )

    df_parsed["transaction_date"] = pd.to_datetime(
        df_parsed["transaction_date"],
        format=DATETIME_FORMAT,
    )

    print("Datetime format used:", DATETIME_FORMAT)
    print("transaction_date dtype:", df_parsed["transaction_date"].dtype)

    return df_parsed


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 4+ datetime features for temporal analytics.
    """
    df_feat = df.copy()
    df_feat["day_of_week"] = df_feat["transaction_date"].dt.day_name()
    df_feat["hour"] = df_feat["transaction_date"].dt.hour
    df_feat["week_num"] = df_feat["transaction_date"].dt.isocalendar().week.astype(int)
    df_feat["month"] = df_feat["transaction_date"].dt.month
    df_feat["day_of_month"] = df_feat["transaction_date"].dt.day
    df_feat["is_weekend"] = df_feat["day_of_week"].isin(["Saturday", "Sunday"])

    hourly_volume = df_feat.groupby("hour").size().rename("transaction_count")
    day_volume = (
        df_feat.groupby("day_of_week")
        .size()
        .reindex(DAY_ORDER, fill_value=0)
        .rename("transaction_count")
    )

    print("\nHourly transaction volume:")
    print(hourly_volume)

    print("\nDay-of-week transaction volume:")
    print(day_volume)

    hourly_volume.to_csv(OUTPUT_DIR / "hourly_volume.csv")
    day_volume.to_csv(OUTPUT_DIR / "day_of_week_volume.csv")

    return df_feat


def build_weekly_aggregations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Set datetime as index and compute weekly sum/count/mean metrics.
    """
    df_ts = df.set_index("transaction_date").sort_index()
    weekly_metrics = df_ts["amount"].resample("W").agg(["sum", "count", "mean"])

    print("\nWeekly amount metrics (sum/count/mean):")
    print(weekly_metrics)

    weekly_metrics.to_csv(OUTPUT_DIR / "weekly_metrics.csv")
    return weekly_metrics


def compute_recency_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute days since each customer's last purchase for churn analysis.
    """
    today = pd.Timestamp.now().normalize()

    customer_last_purchase = df.groupby("customer_id")["transaction_date"].max()
    customer_recency_days = (today - customer_last_purchase).dt.days.rename("days_since_last_purchase")

    df_recency = df.copy()
    df_recency["days_since_last_purchase"] = df_recency["customer_id"].map(customer_recency_days)

    customer_recency = customer_recency_days.reset_index()
    inactive_customers = customer_recency[customer_recency["days_since_last_purchase"] > 30]

    print("\nRecency distribution (customer-level):")
    print(customer_recency["days_since_last_purchase"].describe())

    print("\nCustomers with no recent activity (>30 days since last purchase):")
    print(inactive_customers)

    customer_recency.to_csv(OUTPUT_DIR / "customer_recency.csv", index=False)
    return df_recency, customer_recency


def build_day_hour_aggregation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Group by day and hour with sum/count/mean and build a day-hour pivot.
    """
    day_hour_agg = (
        df.groupby(["day_of_week", "hour"])["amount"]
        .agg(["sum", "count", "mean"])
        .reset_index()
    )

    day_hour_agg["day_of_week"] = pd.Categorical(
        day_hour_agg["day_of_week"],
        categories=DAY_ORDER,
        ordered=True,
    )
    day_hour_agg = day_hour_agg.sort_values(["day_of_week", "hour"])

    pivot_table = pd.pivot_table(
        df,
        values="amount",
        index="hour",
        columns="day_of_week",
        aggfunc="sum",
        fill_value=0,
    )
    pivot_table = pivot_table.reindex(columns=DAY_ORDER, fill_value=0)

    peak_idx = pivot_table.stack().idxmax()
    peak_value = pivot_table.stack().max()

    print("\nDay x hour aggregation sample:")
    print(day_hour_agg.head(10))

    print("\nHour x day-of-week pivot (sum of amount):")
    print(pivot_table)

    print(
        f"\nPeak activity window: {peak_idx[1]} at hour {peak_idx[0]} "
        f"with amount sum {peak_value:.2f}"
    )

    day_hour_agg.to_csv(OUTPUT_DIR / "day_hour_aggregation.csv", index=False)
    pivot_table.to_csv(OUTPUT_DIR / "day_hour_pivot.csv")

    return day_hour_agg, pivot_table


def plot_outputs(df: pd.DataFrame, weekly_metrics: pd.DataFrame, pivot_table: pd.DataFrame, customer_recency: pd.DataFrame) -> None:
    """
    Save required temporal distribution plots.
    """
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(10, 5))
    plt.hist(df["hour"], bins=24, edgecolor="black")
    plt.title("Transaction Distribution by Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Transaction Count")
    plt.xticks(range(0, 24, 2))
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "hour_distribution.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    weekly_metrics["sum"].plot(marker="o")
    plt.title("Weekly Revenue Trend")
    plt.xlabel("Week")
    plt.ylabel("Revenue (sum)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "weekly_revenue_trend.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_table, cmap="YlOrRd", linewidths=0.5)
    plt.title("Revenue Heatmap: Hour x Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Hour")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "day_hour_heatmap.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.hist(customer_recency["days_since_last_purchase"], bins=10, edgecolor="black")
    plt.title("Customer Recency Distribution")
    plt.xlabel("Days Since Last Purchase")
    plt.ylabel("Customer Count")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "recency_distribution.png", dpi=150)
    plt.close()


def run_edge_case_format_tests() -> None:
    """
    Validate strict format parsing behavior against mixed date strings.
    """
    test_dates = [
        "2025-01-15 14:30:45",
        "2025-1-15 14:30:45",
        "15/01/2025 14:30:45",
        "2025-01-15T14:30:45Z",
    ]

    print("\nStrict format checks:")
    for date_str in test_dates:
        try:
            if not pd.Series([date_str]).str.match(TIMESTAMP_PATTERN).iloc[0]:
                raise ValueError("regex format mismatch")
            pd.to_datetime(date_str, format=DATETIME_FORMAT)
            print(f"PASS  {date_str}")
        except ValueError:
            print(f"FAIL  {date_str} - format mismatch")


def print_test_checks(df: pd.DataFrame) -> None:
    """
    Run the checkpoint prints requested in the assignment.
    """
    print("\nValidation checks:")
    print(f"Min date: {df['transaction_date'].min()}")
    print(f"Max date: {df['transaction_date'].max()}")
    print(f"Days in dataset: {(df['transaction_date'].max() - df['transaction_date'].min()).days}")
    print(f"Hours with data: {sorted(df['hour'].unique().tolist())}")
    print(f"Weeks in dataset: {df['week_num'].nunique()}")
    print(f"Min days since purchase: {df['days_since_last_purchase'].min()}")
    print(f"Max days since purchase: {df['days_since_last_purchase'].max()}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df_raw = load_sample_transaction_data()
    df_parsed = parse_transaction_dates(df_raw)
    df_features = extract_temporal_features(df_parsed)
    weekly_metrics = build_weekly_aggregations(df_features)
    df_recency, customer_recency = compute_recency_metrics(df_features)
    _, pivot_table = build_day_hour_aggregation(df_recency)

    df_recency.to_csv(OUTPUT_DIR / "temporal_features.csv", index=False)

    plot_outputs(df_recency, weekly_metrics, pivot_table, customer_recency)
    run_edge_case_format_tests()
    print_test_checks(df_recency)

    print("\nTimezone note:")
    print("If source timestamps are UTC, convert first with .dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata') before extracting hour/day features.")
    print("\nPipeline complete. Outputs saved in output/ directory.")


if __name__ == "__main__":
    main()
