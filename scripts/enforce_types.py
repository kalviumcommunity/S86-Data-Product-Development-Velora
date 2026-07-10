import json
import os

import numpy as np
import pandas as pd


def cast_columns_to_types(df, type_mapping):
    """
    Explicitly cast columns to correct dtypes.

    Args:
        df: Input DataFrame
        type_mapping: Dict of {column: target_dtype}

    Returns:
        DataFrame with corrected types and conversion log
    """
    df_typed = df.copy()
    conversion_log = {}

    for col, target_dtype in type_mapping.items():
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue

        original_dtype = df[col].dtype

        try:
            df_typed[col] = df_typed[col].astype(target_dtype)
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "success",
            }
            print(f"✓ {col}: {original_dtype} → {target_dtype}")
        except Exception as e:
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "failed",
                "error": str(e),
            }
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed, conversion_log


def convert_string_dates_to_datetime(df, date_columns, date_format=None):
    """
    Convert string columns to datetime with explicit format.

    Args:
        df: Input DataFrame
        date_columns: List of column names containing dates
        date_format: Datetime format string (e.g., '%Y-%m-%d')

    Returns:
        DataFrame with datetime columns converted

    Note: ALWAYS specify format. "01-02-2025" is ambiguous without it.
    """
    df_typed = df.copy()

    for col in date_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            if date_format:
                df_typed[col] = pd.to_datetime(df_typed[col], format=date_format)
            else:
                df_typed[col] = pd.to_datetime(df_typed[col])

            print(f"✓ {col}: Converted to datetime")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            print(f"  Sample values: {df[col].head(3).tolist()}")
            print(f"  Expected format: {date_format}")
            raise

    return df_typed


def convert_currency_to_float(df, currency_columns):
    """
    Strip currency symbols and convert to float.

    Example: '$150.50' → 150.50

    Args:
        df: Input DataFrame
        currency_columns: List of column names with currency

    Returns:
        DataFrame with clean numeric columns
    """
    df_typed = df.copy()

    for col in currency_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            df_typed[col] = (
                df_typed[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )

            df_typed[col] = pd.to_numeric(df_typed[col], errors="coerce")

            failed_conversions = df_typed[col].isnull().sum() - df[col].isnull().sum()
            if failed_conversions > 0:
                print(f"⚠ {col}: {failed_conversions} values could not be converted to numeric")

            print(f"✓ {col}: Stripped symbols, converted to float")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def convert_integers_to_boolean(df, boolean_columns):
    """
    Convert 0/1 or yes/no columns to proper boolean type.

    Args:
        df: Input DataFrame
        boolean_columns: List of column names with binary values

    Returns:
        DataFrame with bool columns
    """
    df_typed = df.copy()

    for col in boolean_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            unique_vals = df[col].unique()
            print(f"  {col} unique values: {unique_vals}")

            if df[col].dtype == "object":
                mapping = {
                    "yes": True,
                    "no": False,
                    "y": True,
                    "n": False,
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                    1: True,
                    0: False,
                    True: True,
                    False: False,
                }
                df_typed[col] = df_typed[col].map(mapping)
            else:
                df_typed[col] = df_typed[col].astype(bool)

            print(f"✓ {col}: Converted to boolean")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def compare_dtypes(df_original, df_typed):
    """
    Compare dtypes before and after conversion.

    Returns: Summary of all changes
    """
    comparison = pd.DataFrame(
        {
            "column": df_original.columns,
            "dtype_before": df_original.dtypes.values,
            "dtype_after": df_typed.dtypes.values,
            "changed": (df_original.dtypes != df_typed.dtypes).values,
        }
    )

    print("\n" + "=" * 70)
    print("DTYPE CONVERSION SUMMARY")
    print("=" * 70)
    print(comparison.to_string(index=False))

    os.makedirs("output", exist_ok=True)
    comparison.to_csv("output/dtype_conversion_report.csv", index=False)
    print("\nReport saved to output/dtype_conversion_report.csv")
    print("=" * 70)

    return comparison


def save_conversion_log(conversion_log, output_path="output/conversion_log.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(conversion_log, file_handle, indent=2)
    print(f"✓ Conversion log saved to {output_path}")


if __name__ == "__main__":
    df = pd.read_csv("data/raw/untyped_data.csv")

    print("=" * 70)
    print("BEFORE TYPE CONVERSION")
    print("=" * 70)
    print(df.dtypes)
    print("\nSample data:")
    print(df.head(3))

    df_typed = df.copy()
    conversion_log = {}

    print("\n1. Converting date columns...")
    df_typed = convert_string_dates_to_datetime(
        df_typed,
        ["transaction_date", "signup_date"],
        date_format="%Y-%m-%d",
    )
    for column in ["transaction_date", "signup_date"]:
        if column in df.columns:
            conversion_log[column] = {
                "from": str(df[column].dtype),
                "to": "datetime64[ns]",
                "status": "success",
            }

    print("\n2. Converting currency columns...")
    df_typed = convert_currency_to_float(
        df_typed,
        ["amount", "revenue"],
    )
    for column in ["amount", "revenue"]:
        if column in df.columns:
            conversion_log[column] = {
                "from": str(df[column].dtype),
                "to": "float64",
                "status": "success",
            }

    print("\n3. Converting boolean columns...")
    df_typed = convert_integers_to_boolean(
        df_typed,
        ["is_active", "is_premium"],
    )
    for column in ["is_active", "is_premium"]:
        if column in df.columns:
            conversion_log[column] = {
                "from": str(df[column].dtype),
                "to": "bool",
                "status": "success",
            }

    print("\n4. Comparing before/after types...")
    print("=" * 70)
    print("AFTER TYPE CONVERSION")
    print("=" * 70)
    print(df_typed.dtypes)
    print("\nSample data:")
    print(df_typed.head(3))

    compare_dtypes(df, df_typed)
    save_conversion_log(conversion_log)

    os.makedirs("data/processed", exist_ok=True)
    df_typed.to_csv("data/processed/typed_data.csv", index=False)
    print("\n✓ Typed data saved to data/processed/typed_data.csv")