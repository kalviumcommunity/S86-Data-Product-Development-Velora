import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "database" / "velora.db"


def load_data():

    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT *
        FROM master_dataset
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    # Convert date columns
    df["created_date"] = pd.to_datetime(
        df["created_date"]
    )

    df["resolved_date"] = pd.to_datetime(
        df["resolved_date"]
    )

    # Convert SQLite 0/1 values back to Boolean
    boolean_columns = [
        "is_unresolved",
        "is_escalated",
        "churned",
        "repeat_customer"
    ]

    for column in boolean_columns:
        if column in df.columns:
            df[column] = df[column].astype(bool)

    return df