import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "database" / "velora.db"
DATA_DIR = BASE_DIR / "data"


def load_table(connection, file_name, table_name):
    file_path = DATA_DIR / file_name

    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False
    )

    print(f"{table_name} loaded successfully.")


def main():

    connection = sqlite3.connect(DB_PATH)

    # Clean source tables
    load_table(
        connection,
        "customers_clean.csv",
        "customers"
    )

    load_table(
        connection,
        "tickets_clean.csv",
        "tickets"
    )

    load_table(
        connection,
        "escalations_clean.csv",
        "escalations"
    )

    load_table(
        connection,
        "cancellations_clean.csv",
        "cancellations"
    )

    # Final feature-engineered dataset
    load_table(
        connection,
        "master_dataset.csv",
        "master_dataset"
    )

    connection.close()

    print()
    print("Velora SQLite database loaded successfully.")


if __name__ == "__main__":
    main()