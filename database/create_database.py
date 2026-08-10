import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "velora.db"


def create_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT,
            segment TEXT,
            region TEXT,
            support_channel TEXT,
            subscription_start TEXT,
            subscription_status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            customer_id TEXT,
            category TEXT,
            status TEXT,
            created_date TEXT,
            resolved_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            ticket_id TEXT,
            escalated TEXT,
            escalation_level TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cancellations (
            customer_id TEXT,
            cancelled TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_dataset (
            ticket_id TEXT,
            customer_id TEXT,
            category TEXT,
            status TEXT,
            created_date TEXT,
            resolved_date TEXT,
            customer_name TEXT,
            segment TEXT,
            region TEXT,
            support_channel TEXT,
            subscription_start TEXT,
            subscription_status TEXT,
            escalated TEXT,
            escalation_level TEXT,
            cancelled TEXT,
            resolution_days REAL,
            is_unresolved INTEGER,
            is_escalated INTEGER,
            churned INTEGER,
            complaint_count INTEGER,
            repeat_customer INTEGER,
            priority_score REAL,
            priority_level TEXT,
            recommended_action TEXT,
            priority_reason TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("SQLite database structure created successfully.")


if __name__ == "__main__":
    create_database()