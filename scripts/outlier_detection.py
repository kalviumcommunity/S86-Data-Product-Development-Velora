import os

import pandas as pd
import numpy as np
from scipy import stats

INPUT_FILE = "data/raw/revenue_data.csv"

OUTPUT_FILE = "data/processed/revenue_cleaned.csv"


def detect_zscore(df):
    """
    Detect revenue outliers using Z-score.
    """

    df["revenue_zscore"] = np.abs(stats.zscore(df["revenue"]))

    z_outliers = df[df["revenue_zscore"] > 3]

    print(f"Z-score outliers: {len(z_outliers)}")

    return df


def detect_iqr(df):
    """
    Detect revenue outliers using IQR.
    """

    q1 = df["revenue"].quantile(0.25)
    q3 = df["revenue"].quantile(0.75)

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    df["is_outlier_iqr"] = (
        (df["revenue"] < lower)
        | (df["revenue"] > upper)
    )

    return df, lower, upper


def cap_outliers(df, lower, upper):
    """
    Cap revenue values.
    """

    df["revenue_capped"] = df["revenue"].clip(
        lower=lower,
        upper=upper,
    )

    print(
        f"Before: min={df['revenue'].min()} max={df['revenue'].max()}"
    )

    print(
        f"After : min={df['revenue_capped'].min()} max={df['revenue_capped'].max()}"
    )

    return df


def flag_outliers(df):
    """
    Create binary outlier flag.
    """

    df["is_outlier"] = (
        df["is_outlier_iqr"]
        | (df["revenue_zscore"] > 3)
    )

    normal = df[~df["is_outlier"]]

    anomalies = df[df["is_outlier"]]

    print(f"Normal records : {len(normal)}")

    print(f"Anomalies : {len(anomalies)}")

    return df


def create_cleaning_log(df, lower, upper):
    """
    Save cleaning log.
    """

    log = [{
        "column": "revenue",
        "method": "IQR",
        "action": "Cap",
        "threshold_lower": lower,
        "threshold_upper": upper,
        "affected_rows": int(df["is_outlier_iqr"].sum()),
        "date": pd.Timestamp.now(),
    }]

    os.makedirs("output", exist_ok=True)

    pd.DataFrame(log).to_csv(
        "output/cleaning_log.csv",
        index=False,
    )


if __name__ == "__main__":

    df = pd.read_csv(INPUT_FILE)

    df = detect_zscore(df)

    df, lower, upper = detect_iqr(df)

    df = cap_outliers(df, lower, upper)

    df = flag_outliers(df)

    create_cleaning_log(df, lower, upper)

    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nWorkflow completed successfully.")