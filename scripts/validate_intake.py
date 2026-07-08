import os
import json
from datetime import datetime

import chardet
import pandas as pd

# -------------------------
# Configuration
# -------------------------

INPUT_FILE = "data/raw/sample.csv"
OUTPUT_FILE = "output/intake_report.json"

EXPECTED_COLUMNS = [
    "customer_id",
    "customer_name",
    "transaction_amount",
    "transaction_date"
]


def validate_file_exists(filepath):
    """
    Check whether the file exists and is not empty.

    Input:
        filepath (str)

    Returns:
        (bool, message)
    """

    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"

    return True, "PASS - File exists and has content"


def validate_file_format(filepath):
    """
    Check file extension.
    """

    allowed_formats = ["csv", "json", "xlsx"]

    extension = filepath.split(".")[-1].lower()

    if extension not in allowed_formats:
        return False, f"Unsupported format: {extension}"

    return True, f"PASS - Format valid: {extension}"


def validate_schema(df, expected_columns):
    """
    Validate required columns.
    """

    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    issues = []

    if missing:
        issues.append(f"Missing columns: {missing}")

    if extra:
        issues.append(f"Unexpected columns: {extra}")

    if issues:
        return False, " | ".join(issues)

    return True, f"PASS - Schema valid: {len(df.columns)} columns"


def detect_encoding(filepath):
    """
    Detect file encoding.
    """

    with open(filepath, "rb") as file:
        result = chardet.detect(file.read(10000))

    encoding = result.get("encoding")
    confidence = result.get("confidence")

    return encoding, f"{encoding} ({confidence:.1%})"


def capture_dataset_stats(filepath, df):
    """
    Capture dataset statistics.
    """

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 4),
        "bytes": os.path.getsize(filepath)
    }


def generate_intake_report(filepath, expected_columns):
    """
    Generate complete intake validation report.
    """

    report = {
        "timestamp": datetime.now().isoformat(),
        "filepath": filepath,
        "validations": {}
    }

    # File existence
    status, msg = validate_file_exists(filepath)
    report["validations"]["file_exists"] = msg

    if not status:
        return report

    # Format
    status, msg = validate_file_format(filepath)
    report["validations"]["format"] = msg

    # Load data
    df = pd.read_csv(filepath)

    # Schema
    status, msg = validate_schema(df, expected_columns)
    report["validations"]["schema"] = msg

    # Encoding
    encoding, msg = detect_encoding(filepath)
    report["validations"]["encoding"] = msg

    # Statistics
    report["statistics"] = capture_dataset_stats(filepath, df)

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w") as file:
        json.dump(report, file, indent=4)

    print("Validation completed successfully.")
    print(f"Report saved to {OUTPUT_FILE}")

    return report


if __name__ == "__main__":
    generate_intake_report(INPUT_FILE, EXPECTED_COLUMNS)