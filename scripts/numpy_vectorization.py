import os
import time

import numpy as np
import pandas as pd


def create_sample_data(rows=100000):
    """Create sample customer revenue data."""

    np.random.seed(42)

    data = {
        "customer_id": np.arange(1, rows + 1),
        "revenue": np.random.randint(
            1000,
            100000,
            size=rows
        )
    }

    return pd.DataFrame(data)


def min_max_normalization(df):
    """Normalize revenue between 0 and 1 using NumPy."""

    revenue_array = df["revenue"].values

    min_revenue = revenue_array.min()
    max_revenue = revenue_array.max()

    normalized_np = (
        revenue_array - min_revenue
    ) / (
        max_revenue - min_revenue
    )

    return normalized_np


def z_score_normalization(df):
    """Calculate revenue Z-scores using NumPy."""

    revenue_array = df["revenue"].values

    z_scores = (
        revenue_array - revenue_array.mean()
    ) / revenue_array.std()

    return z_scores


def calculate_revenue_rank(df):
    """Rank customers by revenue in descending order."""

    revenue_array = df["revenue"].values

    rankings = np.argsort(-revenue_array)

    revenue_rank = np.empty(
        len(rankings),
        dtype=int
    )

    revenue_rank[rankings] = np.arange(
        1,
        len(rankings) + 1
    )

    return revenue_rank


def compare_performance(df):
    """Compare Python loop and NumPy performance."""

    start = time.perf_counter()

    result_loop = []

    for value in df["revenue"]:
        result_loop.append(value * 1.1)

    loop_time = time.perf_counter() - start

    start = time.perf_counter()

    result_np = (
        df["revenue"].values * 1.1
    )

    np_time = time.perf_counter() - start

    print("\nPERFORMANCE COMPARISON")
    print("=" * 50)

    print(f"Loop: {loop_time:.6f}s")
    print(f"NumPy: {np_time:.6f}s")

    if np_time > 0:
        print(
            f"Speedup: "
            f"{loop_time / np_time:.0f}x"
        )

    return result_loop, result_np


if __name__ == "__main__":

    print("Starting NumPy vectorization workflow...\n")

    os.makedirs("output", exist_ok=True)

    # Create 100,000 customer records
    df = create_sample_data(
        rows=100000
    )

    print("ORIGINAL DATA")
    print(df.head())

    print(f"\nOriginal Shape: {df.shape}")

    # Task 1 - Min-Max Normalization
    print("\nTASK 1 - MIN-MAX NORMALIZATION")

    normalized_np = min_max_normalization(df)

    df["revenue_normalized"] = normalized_np

    print(
        df[
            [
                "revenue",
                "revenue_normalized"
            ]
        ].head()
    )

    print(
        "Normalized Minimum:",
        df["revenue_normalized"].min()
    )

    print(
        "Normalized Maximum:",
        df["revenue_normalized"].max()
    )

    # Task 2 - Z-Score Normalization
    print("\nTASK 2 - Z-SCORE NORMALIZATION")

    z_scores = z_score_normalization(df)

    df["revenue_zscore"] = z_scores

    print(
        df[
            [
                "revenue",
                "revenue_zscore"
            ]
        ].head()
    )

    print(
        "Z-Score Mean:",
        df["revenue_zscore"].mean()
    )

    print(
        "Z-Score Standard Deviation:",
        df["revenue_zscore"].std()
    )

    # Task 3 - Revenue Ranking
    print("\nTASK 3 - REVENUE RANKING")

    revenue_rank = calculate_revenue_rank(df)

    df["revenue_rank"] = revenue_rank

    print(
        df[
            [
                "customer_id",
                "revenue",
                "revenue_rank"
            ]
        ]
        .sort_values("revenue_rank")
        .head(10)
    )

    # Task 4 - Performance Comparison
    print("\nTASK 4 - PERFORMANCE TEST")

    result_loop, result_np = compare_performance(df)

    # Task 5 - DataFrame Integration
    print("\nTASK 5 - DATAFRAME INTEGRATION")

    print(f"Shape: {df.shape}")

    print("\nDtypes:")
    print(df.dtypes)

    print("\nFinal Data:")
    print(df.head())

    # Save output
    df.to_csv(
        "output/vectorized_customer_revenue.csv",
        index=False
    )

    print(
        "\nOutput saved to "
        "output/vectorized_customer_revenue.csv"
    )

    print(
        "\nNumPy vectorization workflow completed."
    )