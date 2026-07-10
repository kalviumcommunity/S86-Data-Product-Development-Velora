import os
import json
import pandas as pd


def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.
    """
    missing_analysis = pd.DataFrame({
        "column": df.columns,
        "null_count": df.isnull().sum().values,
        "null_percentage": (
            df.isnull().sum() / len(df) * 100
        ).round(2).values,
        "data_type": df.dtypes.astype(str).values,
        "null_meaning": ""
    })

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))

    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy="median"):
    """
    Fill numerical nulls using mean or median.
    """
    df_imputed = df.copy()

    for col in numerical_cols:

        # Skip column if it does not exist
        if col not in df_imputed.columns:
            print(f"  ! Skipping missing column: {col}")
            continue

        null_count = df_imputed[col].isnull().sum()

        if null_count > 0:

            if strategy == "median":
                fill_value = df_imputed[col].median()

            elif strategy == "mean":
                fill_value = df_imputed[col].mean()

            else:
                raise ValueError(
                    "strategy must be either 'mean' or 'median'"
                )

            df_imputed[col] = df_imputed[col].fillna(fill_value)

            print(
                f"  ✓ {col}: filled {null_count} nulls "
                f"with {strategy} ({fill_value:.2f})"
            )

    return df_imputed


def impute_mode(df, categorical_cols):
    """
    Fill categorical nulls with mode.
    Mode = most common value.
    """
    df_imputed = df.copy()

    for col in categorical_cols:

        if col not in df_imputed.columns:
            print(f"  ! Skipping missing column: {col}")
            continue

        null_count = df_imputed[col].isnull().sum()

        if null_count > 0:

            mode_values = df_imputed[col].mode()

            # Make sure a mode exists
            if not mode_values.empty:
                mode_val = mode_values.iloc[0]

                df_imputed[col] = (
                    df_imputed[col].fillna(mode_val)
                )

                print(
                    f"  ✓ {col}: filled {null_count} nulls "
                    f"with mode '{mode_val}'"
                )

    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """
    Fill missing values using the previous known value.
    Appropriate for ordered time-series data.
    """
    df_imputed = df.copy()

    for col in time_series_cols:

        if col not in df_imputed.columns:
            print(f"  ! Skipping missing column: {col}")
            continue

        null_count = df_imputed[col].isnull().sum()

        if null_count > 0:
            df_imputed[col] = df_imputed[col].ffill()

            print(
                f"  ✓ {col}: forward-filled "
                f"{null_count} nulls"
            )

    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """
    Drop rows where critical identifier columns are null.
    """
    existing_cols = [
        col for col in critical_cols
        if col in df.columns
    ]

    rows_before = len(df)

    df_imputed = df.dropna(
        subset=existing_cols
    ).copy()

    rows_dropped = rows_before - len(df_imputed)

    print(
        f"  ✓ Dropped {rows_dropped} rows "
        f"with null in: {existing_cols}"
    )

    return df_imputed


def document_imputation_decisions(df_original, df_imputed):
    """
    Document imputation decisions with business reasoning.
    """

    decisions = {
        "amount": {
            "column_type": "numerical",
            "null_count_before": int(
                df_original["amount"].isnull().sum()
            ) if "amount" in df_original.columns else 0,

            "null_count_after": int(
                df_imputed["amount"].isnull().sum()
            ) if "amount" in df_imputed.columns else 0,

            "strategy": "median_imputation",

            "value_used": float(
                df_original["amount"].median()
            ) if "amount" in df_original.columns else None,

            "business_reasoning":
                "Median represents a typical transaction "
                "and is resistant to high-value outliers.",

            "risk_assessment":
                "Low to medium - imputed values are synthetic "
                "and must not be treated as observed values."
        },

        "category": {
            "column_type": "categorical",

            "null_count_before": int(
                df_original["category"].isnull().sum()
            ) if "category" in df_original.columns else 0,

            "null_count_after": int(
                df_imputed["category"].isnull().sum()
            ) if "category" in df_imputed.columns else 0,

            "strategy": "mode_imputation",

            "business_reasoning":
                "The most frequent category is used because "
                "the column is categorical and cannot be "
                "meaningfully averaged.",

            "risk_assessment":
                "Medium - mode imputation can increase the "
                "dominance of the most common category."
        },

        "last_updated": {
            "column_type": "time_series",

            "null_count_before": int(
                df_original["last_updated"].isnull().sum()
            ) if "last_updated" in df_original.columns else 0,

            "null_count_after": int(
                df_imputed["last_updated"].isnull().sum()
            ) if "last_updated" in df_imputed.columns else 0,

            "strategy": "forward_fill",

            "business_reasoning":
                "The previous known timestamp is carried "
                "forward to preserve continuity in ordered data.",

            "risk_assessment":
                "Medium - assumes the previous known state "
                "remains valid until a new observation appears."
        },

        "customer_id": {
            "column_type": "critical_identifier",

            "null_count_before": int(
                df_original["customer_id"].isnull().sum()
            ) if "customer_id" in df_original.columns else 0,

            "strategy": "drop_rows",

            "business_reasoning":
                "A missing customer_id cannot be safely guessed "
                "because identifiers must uniquely trace records.",

            "risk_assessment":
                "Rows are lost, so the number and percentage "
                "of removed records must be documented."
        }
    }

    os.makedirs("output", exist_ok=True)

    with open(
        "output/imputation_decisions.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            decisions,
            file,
            indent=2,
            default=str
        )

    print(
        "  ✓ Decisions saved to "
        "output/imputation_decisions.json"
    )

    return decisions


def validate_imputation(df_original, df_imputed):
    """
    Compare before and after imputation metrics.
    """

    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)

    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")

    print(
        f"Rows removed: "
        f"{len(df_original) - len(df_imputed)}"
    )

    print(
        f"\nTotal nulls before: "
        f"{df_original.isnull().sum().sum()}"
    )

    print(
        f"Total nulls after:  "
        f"{df_imputed.isnull().sum().sum()}"
    )

    missing_after = pd.DataFrame({
        "column": df_imputed.columns,

        "null_count_after":
            df_imputed.isnull().sum().values,

        "null_percentage_after": (
            df_imputed.isnull().sum()
            / len(df_imputed)
            * 100
        ).round(2).values
    })

    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)

    return missing_after


if __name__ == "__main__":

    # Create required output folders
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # Load raw data
    df = pd.read_csv(
        "data/raw/raw_data.csv"
    )

    # IMPORTANT:
    # Preserve untouched original data for comparison
    df_original = df.copy()

    # STEP 1
    print("Step 1: Analyzing missing values...")
    analyze_missing_values(df_original)

    # STEP 2
    print("\nStep 2: Applying imputation strategies...")

    # Critical identifiers should not be invented
    df = drop_rows_with_nulls(
        df,
        ["customer_id", "email"]
    )

    # Numerical columns -> median
    df = impute_mean_median(
        df,
        ["amount", "quantity"],
        strategy="median"
    )

    # Categorical columns -> mode
    df = impute_mode(
        df,
        ["category", "region"]
    )

    # Time-series columns -> forward fill
    df = impute_forward_fill(
        df,
        ["last_updated"]
    )

    # STEP 3
    print("\nStep 3: Documenting decisions...")

    document_imputation_decisions(
        df_original,
        df
    )

    # STEP 4
    print("\nStep 4: Validating imputation...")

    validate_imputation(
        df_original,
        df
    )

    # STEP 5
    df.to_csv(
        "data/processed/cleaned_data.csv",
        index=False
    )

    print(
        "\n✓ Cleaned data saved to "
        "data/processed/cleaned_data.csv"
    )