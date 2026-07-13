import os
import json
from datetime import datetime

import pandas as pd

INPUT_FILE = "data/raw/data_with_dupes.csv"
OUTPUT_FILE = "data/processed/deduplicated_data.csv"


def detect_exact_duplicates(df):
    """
    Detect rows where every column is identical.
    """

    exact_count = df.duplicated().sum()

    duplicate_rows = df[df.duplicated(keep=False)]

    print("\nEXACT DUPLICATES")
    print("---------------------------")
    print(f"Exact duplicates found : {exact_count}")

    return exact_count, duplicate_rows


def detect_near_duplicates(df, key_columns):
    """
    Detect duplicate records based on key columns.
    """

    near_duplicates = df[df.duplicated(subset=key_columns, keep=False)]

    print("\nNEAR DUPLICATES")
    print("---------------------------")
    print(f"Duplicate key records : {len(near_duplicates)}")

    return near_duplicates


def remove_exact_duplicates(df):
    """
    Remove identical rows.
    """

    before = len(df)

    df = df.drop_duplicates(keep="first")

    after = len(df)

    print("\nREMOVE EXACT DUPLICATES")
    print("---------------------------")
    print(f"Rows before : {before}")
    print(f"Rows after  : {after}")

    return df


def remove_near_duplicates(df, key_columns):
    """
    Keep the first record for duplicate customer/date combinations.
    """

    before = len(df)

    df = df.drop_duplicates(subset=key_columns, keep="first")

    after = len(df)

    print("\nREMOVE NEAR DUPLICATES")
    print("---------------------------")
    print(f"Rows before : {before}")
    print(f"Rows after  : {after}")

    return df


def log_removed_duplicates(original, dedup):
    """
    Save removed records.
    """

    removed = original.loc[~original.index.isin(dedup.index)]

    os.makedirs("output", exist_ok=True)

    removed.to_csv(
        "output/removed_duplicates_audit.csv",
        index=False,
    )

    summary = {
        "timestamp": datetime.now().isoformat(),
        "rows_removed": len(removed),
        "reason": "Duplicate removal"
    }

    with open("output/dedup_audit_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    return removed


def compare_before_after(original, dedup):
    """
    Compare before and after.
    """

    summary = {
        "rows_before": len(original),
        "rows_after": len(dedup),
        "rows_removed": len(original) - len(dedup),
        "removal_percentage": round(
            (len(original) - len(dedup)) / len(original) * 100,
            2,
        ),
        "timestamp": datetime.now().isoformat(),
    }

    with open("output/dedup_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    print("\nFINAL SUMMARY")
    print("---------------------------")
    print(summary)

    return summary


if __name__ == "__main__":

    df_original = pd.read_csv(INPUT_FILE)

    print("\nStarting Duplicate Detection...\n")

    detect_exact_duplicates(df_original)

    detect_near_duplicates(
        df_original,
        ["customer_id", "transaction_date"],
    )

    df_clean = remove_exact_duplicates(df_original)

    df_clean = remove_near_duplicates(
        df_clean,
        ["customer_id", "transaction_date"],
    )

    log_removed_duplicates(df_original, df_clean)

    compare_before_after(df_original, df_clean)

    os.makedirs("data/processed", exist_ok=True)

    df_clean.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nDeduplicated file saved successfully.")