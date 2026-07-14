import os

import pandas as pd

INPUT_FILE = "data/raw/customer_features.csv"
OUTPUT_FILE = "data/processed/customer_features_engineered.csv"


def create_ratio_features(df):
    """
    Create ratio-based business features.
    """

    df["transactions_per_month"] = (
        df["total_transactions"] /
        (df["days_as_customer"] / 30)
    )

    df["avg_spend_per_transaction"] = (
        df["total_spent"] /
        df["total_transactions"]
    )

    df["lifetime_value_per_month"] = (
        df["total_spent"] /
        (df["days_as_customer"] / 30)
    )

    print("\nRatio Features")
    print(df[
        [
            "transactions_per_month",
            "avg_spend_per_transaction",
            "lifetime_value_per_month"
        ]
    ].describe())

    return df


def create_engagement_tier(df):
    """
    Equal-width bins.
    """

    df["engagement_tier"] = pd.cut(
        df["transactions_per_month"],
        bins=[0, 2, 10, float("inf")],
        labels=["Low", "Medium", "High"],
    )

    print("\nEngagement Tier")
    print(df["engagement_tier"].value_counts())

    return df


def create_spend_quartile(df):
    """
    Quantile-based spend tiers.
    """

    df["spend_quartile"] = pd.qcut(
        df["total_spent"],
        q=4,
        labels=["Q1", "Q2", "Q3", "Q4"],
    )

    print("\nSpend Quartiles")
    print(df["spend_quartile"].value_counts())

    return df


def create_rfm_score(df):
    """
    Create composite RFM score.
    """

    df["recency_score"] = pd.qcut(
        df["days_since_last_purchase"],
        q=5,
        labels=[5, 4, 3, 2, 1],
    )

    df["frequency_score"] = pd.qcut(
        df["purchase_count"],
        q=5,
        labels=[1, 2, 3, 4, 5],
    )

    df["monetary_score"] = pd.qcut(
        df["total_spent"],
        q=5,
        labels=[1, 2, 3, 4, 5],
    )

    df["rfm_score"] = (
        df["recency_score"].astype(int)
        + df["frequency_score"].astype(int)
        + df["monetary_score"].astype(int)
    )

    return df


def validate_features(df):
    """
    Validate engineered features.
    """

    print("\nValidation")

    print("\nEngagement Tier Distribution")
    print(df["engagement_tier"].value_counts())

    print(
        f"\nRFM Score Range: "
        f"{df['rfm_score'].min()} - {df['rfm_score'].max()}"
    )

    print("\nMissing Values")

    print(
        df[
            [
                "engagement_tier",
                "spend_quartile",
                "rfm_score",
            ]
        ].isna().sum()
    )

    return df


if __name__ == "__main__":

    df = pd.read_csv(INPUT_FILE)

    df = create_ratio_features(df)

    df = create_engagement_tier(df)

    df = create_spend_quartile(df)

    df = create_rfm_score(df)

    df = validate_features(df)

    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nFeature Engineering Completed Successfully.")