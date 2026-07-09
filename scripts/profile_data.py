import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_INPUT_FILE = "data/raw/quality_test.csv"
DEFAULT_OUTPUT_FILE = "output/profile_report.json"


def profile_nulls_and_duplicates(df):
    """
    Compute null percentage and duplicate counts per column.

    Returns: Dictionary with null analysis by column
    """
    profile = {
        "null_counts": {},
        "null_percentages": {},
        "exact_duplicate_count": 0,
    }

    record_count = len(df)

    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / record_count) * 100 if record_count else 0
        profile["null_counts"][col] = int(null_count)
        profile["null_percentages"][col] = round(null_pct, 2)

    exact_duplicate_count = int(df.duplicated().sum())
    profile["exact_duplicate_count"] = exact_duplicate_count
    profile["duplicate_percentage"] = round(
        (exact_duplicate_count / record_count) * 100 if record_count else 0,
        2,
    )

    return profile


def profile_numerical_columns(df):
    """
    Summarise numerical columns with statistical measures.

    Returns: DataFrame with min, max, mean, median, std
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns

    stats = {}
    for col in numerical_cols:
        stats[col] = {
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
            "mean": round(df[col].mean(), 2),
            "median": round(df[col].median(), 2),
            "std": round(df[col].std(), 2),
            "null_count": int(df[col].isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """
    Summarise categorical columns with value distributions.

    Returns: Dictionary with unique counts and top values
    """
    categorical_cols = df.select_dtypes(include=["object"]).columns

    profile = {}
    for col in categorical_cols:
        profile[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": df[col].value_counts().head(top_n).to_dict(),
            "null_count": int(df[col].isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """
    Identify data quality problems based on thresholds.

    Returns: List of issues found with severity and recommendations
    """
    issues = []

    if len(df) == 0:
        return issues

    # Check nulls
    null_pcts = (df.isnull().sum() / len(df)) * 100
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append(
                {
                    "type": "High nulls",
                    "column": col,
                    "severity": "HIGH",
                    "value": f"{pct:.1f}% missing",
                    "recommendation": "Consider imputation or column exclusion",
                }
            )

    # Check duplicates
    dup_count = int(df.duplicated().sum())
    dup_pct = (dup_count / len(df)) * 100
    if dup_pct > duplicate_threshold:
        issues.append(
            {
                "type": "High duplicates",
                "column": "Full row",
                "severity": "HIGH",
                "value": f"{dup_pct:.1f}% duplicated",
                "recommendation": "Deduplication required before analysis",
            }
        )

    # Check for invalid ranges
    for col in df.select_dtypes(include=[np.number]).columns:
        if (df[col] < 0).any() and "amount" in col.lower():
            issues.append(
                {
                    "type": "Invalid range",
                    "column": col,
                    "severity": "MEDIUM",
                    "value": "Contains negative values",
                    "recommendation": "Investigate negative entries",
                }
            )

    # Check for suspicious categorical values that look corrupted
    numeric_like_pattern = re.compile(r"^-?\d+(\.\d+)?$")
    for col in df.select_dtypes(include=["object"]).columns:
        suspicious_values = [
            value
            for value in df[col].dropna().astype(str).unique()
            if numeric_like_pattern.match(value.strip())
        ]

        if suspicious_values:
            issues.append(
                {
                    "type": "Suspicious categorical value",
                    "column": col,
                    "severity": "MEDIUM",
                    "value": f"Numeric-like entries: {', '.join(map(str, suspicious_values[:3]))}",
                    "recommendation": "Review categorical values for corruption or wrong column mapping",
                }
            )

    return issues


def generate_profile_report(df, filepath):
    """
    Generate complete data quality report and save to JSON.

    Returns: Complete profile report dictionary
    """
    numerical_stats = profile_numerical_columns(df)

    report = {
        "dataset": filepath,
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": numerical_stats.to_dict(),
        "categorical_stats": profile_categorical_columns(df),
        "quality_issues": identify_quality_issues(df),
    }

    output_path = Path(DEFAULT_OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} -> {issue['recommendation']}")
    print(f"{'=' * 60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="Profile raw data quality")
    parser.add_argument(
        "filepath",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to input data file (default: {DEFAULT_INPUT_FILE})",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.filepath)
    generate_profile_report(df, args.filepath)


if __name__ == "__main__":
    main()