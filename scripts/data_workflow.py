import pandas as pd
import os

INPUT_FILE = "data/raw/sample.csv"
OUTPUT_FILE = "output/processed.csv"


def ingest_data(filepath):
    """
    Read customer support data from a CSV file.

    Input:
        filepath (str): Path to CSV file

    Returns:
        Pandas DataFrame containing raw data.
    """

    print("Loading data...")

    df = pd.read_csv(filepath)

    return df


def process_data(df):
    """
    Clean and prepare the dataset.

    Input:
        Raw DataFrame

    Returns:
        Clean DataFrame
    """

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Fill missing resolution time with median
    df["resolution_time"] = df["resolution_time"].fillna(
        df["resolution_time"].median()
    )

    return df


def output_results(df, output_path):
    """
    Save processed dataset.

    Input:
        Clean DataFrame

    Output:
        CSV file
    """

    os.makedirs("output", exist_ok=True)

    df.to_csv(output_path, index=False)

    print("Data successfully processed")
    print(f"Rows processed: {len(df)}")
    print(f"Output saved to {output_path}")


if __name__ == "__main__":

    try:

        data = ingest_data(INPUT_FILE)

        clean_data = process_data(data)

        output_results(clean_data, OUTPUT_FILE)

    except Exception as e:

        print(f"Workflow Failed: {e}")