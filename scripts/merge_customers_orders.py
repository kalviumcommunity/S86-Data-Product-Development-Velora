import json
import os
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
CUSTOMERS_FILE = BASE_DIR / "data" / "raw" / "customers.csv"
ORDERS_FILE = BASE_DIR / "data" / "processed" / "transactions_ingested.csv"
OUTPUT_DIR = BASE_DIR / "output"
UNMATCHED_CUSTOMERS_FILE = OUTPUT_DIR / "unmatched_customers.csv"
UNMATCHED_ORDERS_FILE = OUTPUT_DIR / "unmatched_orders.csv"
JOIN_REPORT_FILE = OUTPUT_DIR / "join_report.json"


def load_tables(customers_file, orders_file):
    """Load customer and order tables."""

    df_customers = pd.read_csv(customers_file)
    df_orders = pd.read_csv(orders_file)

    return df_customers, df_orders


def merge_tables(df_customers, df_orders):
    """Merge customers to orders using a left join."""

    df_merged = pd.merge(
        df_customers,
        df_orders,
        on="customer_id",
        how="left",
        validate="one_to_many"
    )

    return df_merged


def detect_unmatched_keys(df_customers, df_orders):
    """Find unmatched customers and orphaned orders."""

    unmatched_customers = df_customers[
        ~df_customers["customer_id"].isin(df_orders["customer_id"])
    ]

    unmatched_orders = df_orders[
        ~df_orders["customer_id"].isin(df_customers["customer_id"])
    ]

    return unmatched_customers, unmatched_orders


def compare_join_types(df_customers, df_orders):
    """Compare inner, left, and outer join row counts."""

    inner = pd.merge(df_customers, df_orders, on="customer_id", how="inner")
    left = pd.merge(df_customers, df_orders, on="customer_id", how="left")
    outer = pd.merge(df_customers, df_orders, on="customer_id", how="outer")

    return inner, left, outer


def document_join_decision(df_customers, df_orders, df_merged, unmatched_customers, unmatched_orders):
    """Build a structured join decision report."""

    return {
        "join_type": "left",
        "left_table": "customers",
        "right_table": "orders",
        "join_key": "customer_id",
        "left_rows": len(df_customers),
        "right_rows": len(df_orders),
        "result_rows": len(df_merged),
        "unmatched_left": len(unmatched_customers),
        "unmatched_right": len(unmatched_orders),
        "reasoning": (
            "Left join preserves every customer record, which is the business "
            "master list. Orders are the many-side fact table, so multiple "
            "orders per customer are expected and customers with no orders "
            "should remain visible for coverage and retention analysis."
        )
    }


def save_outputs(unmatched_customers, unmatched_orders, join_report):
    """Persist audit outputs to disk."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    unmatched_customers.to_csv(UNMATCHED_CUSTOMERS_FILE, index=False)
    unmatched_orders.to_csv(UNMATCHED_ORDERS_FILE, index=False)

    with open(JOIN_REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(join_report, file, indent=2)


def main():
    df_customers, df_orders = load_tables(CUSTOMERS_FILE, ORDERS_FILE)

    print(f"Left: {len(df_customers)}")
    print(f"Right: {len(df_orders)}")

    df_merged = merge_tables(df_customers, df_orders)

    print(f"Merged: {len(df_merged)}")
    print(f"Change: {len(df_merged) - len(df_customers)}")

    unmatched_customers, unmatched_orders = detect_unmatched_keys(
        df_customers,
        df_orders
    )

    print(f"Customers without orders: {len(unmatched_customers)}")
    print(f"Orphaned orders: {len(unmatched_orders)}")

    inner, left, outer = compare_join_types(df_customers, df_orders)
    print(f"Inner: {len(inner)}, Left: {len(left)}, Outer: {len(outer)}")

    print(df_merged.columns)

    key_counts = df_merged["customer_id"].value_counts()
    print(f"Max orders per customer: {key_counts.max()}")

    join_report = document_join_decision(
        df_customers,
        df_orders,
        df_merged,
        unmatched_customers,
        unmatched_orders
    )

    save_outputs(unmatched_customers, unmatched_orders, join_report)

    print(json.dumps(join_report, indent=2))


if __name__ == "__main__":
    main()