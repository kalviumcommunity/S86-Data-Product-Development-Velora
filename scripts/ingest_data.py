import os
import pandas as pd


def ingest_csv(filepath, delimiter=",", encoding="utf-8", dtype_dict=None):
    """
    Load a CSV file with explicit parameters.

    Args:
        filepath: Path to CSV file
        delimiter: Field delimiter
        encoding: File encoding
        dtype_dict: Optional dictionary of column data types

    Returns:
        Pandas DataFrame
    """
    try:
        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            dtype=dtype_dict
        )

        print(f"✓ CSV loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}")

        return df

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise

    except UnicodeDecodeError:
        print(f"Encoding error: Could not decode with {encoding}")
        print("Try: latin-1, iso-8859-1, or cp1252")
        raise


def ingest_json(filepath, is_nested=False):
    """
    Load a JSON file and optionally flatten nested structures.

    Args:
        filepath: Path to JSON file
        is_nested: If True, flatten nested JSON structures

    Returns:
        Pandas DataFrame
    """
    try:
        df = pd.read_json(filepath)

        if is_nested:
            df = pd.json_normalize(df.to_dict(orient="records"))
            print("✓ Nested JSON flattened to tabular format")

        print(f"✓ JSON loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows x {df.shape[1]} columns")

        return df

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise


def ingest_csv_with_fallback(
    filepath,
    delimiters=None,
    fallback_encodings=None
):
    """
    Load CSV by trying multiple delimiters and encodings.
    """
    if delimiters is None:
        delimiters = [",", ";", "\t"]

    if fallback_encodings is None:
        fallback_encodings = [
            "utf-8",
            "latin-1",
            "iso-8859-1",
            "cp1252"
        ]

    for delimiter in delimiters:
        for encoding in fallback_encodings:
            try:
                df = pd.read_csv(
                    filepath,
                    delimiter=delimiter,
                    encoding=encoding
                )

                print(
                    f"✓ Successfully loaded with "
                    f"delimiter='{delimiter}', "
                    f"encoding='{encoding}'"
                )

                return df

            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError(
        f"Could not load {filepath} "
        "with any encoding/delimiter combination"
    )


def document_ingestion(df, source_file):
    """
    Print a detailed ingestion report.
    """
    print("\n" + "=" * 60)
    print(f"INGESTION REPORT: {source_file}")
    print("=" * 60)

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn Names & Data Types:")
    print(df.dtypes)

    print("\nNull Values Per Column:")
    print(df.isnull().sum())

    print("\nFirst 3 Rows:")
    print(df.head(3).to_string())

    print("=" * 60 + "\n")

    return df


if __name__ == "__main__":
    print("Starting multi-format ingestion...\n")

    os.makedirs("data/processed", exist_ok=True)

    # CSV:
    # delimiter is explicitly comma because customers.csv is comma-separated.
    # encoding is explicitly UTF-8 for predictable text decoding.
    csv_df = ingest_csv(
        "data/raw/customers.csv",
        delimiter=",",
        encoding="utf-8"
    )

    document_ingestion(
        csv_df,
        "customers.csv"
    )

    # JSON:
    # is_nested=True demonstrates flattening into tabular columns.
    json_df = ingest_json(
        "data/raw/transactions.json",
        is_nested=True
    )

    document_ingestion(
        json_df,
        "transactions.json"
    )

    csv_df.to_csv(
        "data/processed/customers_ingested.csv",
        index=False
    )

    json_df.to_csv(
        "data/processed/transactions_ingested.csv",
        index=False
    )

    print("✓ All data ingested and saved to data/processed/")