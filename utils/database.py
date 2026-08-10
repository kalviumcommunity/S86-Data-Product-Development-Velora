import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# Database Path
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "database" / "velora.db"


# --------------------------------------------------
# Load Data
# --------------------------------------------------

def load_data():

    # --------------------------------------------------
    # Check for Uploaded CSV
    # --------------------------------------------------

    uploaded_data = st.session_state.get(
        "uploaded_data",
        None
    )

    if uploaded_data is not None:

        # Use uploaded dataset
        df = uploaded_data.copy()

    else:

        # --------------------------------------------------
        # Use Built-in SQLite Dataset
        # --------------------------------------------------

        connection = sqlite3.connect(DB_PATH)

        df = pd.read_sql_query(
            """
            SELECT *
            FROM master_dataset
            """,
            connection
        )

        connection.close()

    # --------------------------------------------------
    # Convert Date Columns
    # --------------------------------------------------

    if "created_date" in df.columns:

        df["created_date"] = pd.to_datetime(
            df["created_date"],
            errors="coerce"
        )

    if "resolved_date" in df.columns:

        df["resolved_date"] = pd.to_datetime(
            df["resolved_date"],
            errors="coerce"
        )

    # --------------------------------------------------
    # Convert Boolean Columns Safely
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

                df[column] = (
                    df[column]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .map({
                        "true": True,
                        "false": False,
                        "1": True,
                        "0": False,
                        "yes": True,
                        "no": False
                    })
                    .fillna(False)
                )

    return df