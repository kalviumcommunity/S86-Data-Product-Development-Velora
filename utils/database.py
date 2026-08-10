import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "database" / "velora.db"


def load_data():

    # --------------------------------------------------
    # Use uploaded CSV if available
    # --------------------------------------------------

    uploaded_data = st.session_state.get(
        "uploaded_data",
        None
    )

    if uploaded_data is not None:

        df = uploaded_data.copy()

    else:

        # --------------------------------------------------
        # Use built-in SQLite dataset
        # --------------------------------------------------

        connection = sqlite3.connect(
            DB_PATH
        )

        df = pd.read_sql_query(
            """
            SELECT *
            FROM master_dataset
            """,
            connection
        )

        connection.close()

    # --------------------------------------------------
    # Convert dates
    # --------------------------------------------------

    df["created_date"] = pd.to_datetime(
        df["created_date"]
    )

    df["resolved_date"] = pd.to_datetime(
        df["resolved_date"]
    )

    # --------------------------------------------------
    # Convert Boolean columns
    # --------------------------------------------------

    boolean_columns = [
        "is_unresolved",
        "is_escalated",
        "churned",
        "repeat_customer"
    ]

    for column in boolean_columns:

        if column in df.columns:

            if df[column].dtype != bool:
                df[column] = df[column].astype(bool)

    return df