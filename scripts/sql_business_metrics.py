"""
sql_business_metrics.py
-----------------------
BSB 2.38 - SQL Business Metrics Query Design

Tasks covered:
  Task 1 : monthly_active_users.sql   (written/stored separately)
  Task 2 : revenue_by_segment.sql     (written/stored separately)
  Task 3 : conversion_funnel.sql      (written/stored separately)
  Task 4 : load_query() + execute all three queries from Python
  Task 5 : validate_metrics()         (null checks, range checks, consistency)

One truth: every team loads from the same .sql file.
"""

import os
import json
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

DB_PATH     = "analytics.db"
QUERIES_DIR = "queries"
OUTPUT_DIR  = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")

with engine.connect():
    print("✓ Database connection successful")


# ─────────────────────────────────────────────
# Seed database with realistic sample data
# ─────────────────────────────────────────────

def seed_database(engine):
    """
    Populate the analytics DB with three tables required by the metric queries:
      - customers      : customer_id, customer_type
      - transactions   : order_id, customer_id, amount, transaction_date, customer_type
      - users          : user_id, created_at, email_verified_at, first_purchase_at
    Tables are replaced on every run so the script is idempotent.
    """

    today = date.today()

    # ── customers ───────────────────────────────
    customers = pd.DataFrame([
        {"customer_id": 1,  "customer_type": "Enterprise"},
        {"customer_id": 2,  "customer_type": "Enterprise"},
        {"customer_id": 3,  "customer_type": "SMB"},
        {"customer_id": 4,  "customer_type": "SMB"},
        {"customer_id": 5,  "customer_type": "SMB"},
        {"customer_id": 6,  "customer_type": "Individual"},
        {"customer_id": 7,  "customer_type": "Individual"},
        {"customer_id": 8,  "customer_type": "Enterprise"},
        {"customer_id": 9,  "customer_type": "SMB"},
        {"customer_id": 10, "customer_type": "Individual"},
    ])

    # ── transactions ────────────────────────────
    # Spread across the past 14 months so the 12-month filter has meaningful data
    raw_txns = [
        # Enterprise customers – large orders
        (1,  1, 1,  2800.00, today - timedelta(days=10)),
        (2,  1, 2,  3100.00, today - timedelta(days=40)),
        (3,  2, 3,  4200.00, today - timedelta(days=15)),
        (4,  2, 4,  3900.00, today - timedelta(days=75)),
        (5,  8, 5,  5100.00, today - timedelta(days=20)),
        (6,  8, 6,  4700.00, today - timedelta(days=200)),  # >12 months ago → filtered out
        # SMB customers – medium orders
        (7,  3, 7,   900.00, today - timedelta(days=5)),
        (8,  3, 8,   750.00, today - timedelta(days=35)),
        (9,  4, 9,  1200.00, today - timedelta(days=60)),
        (10, 4, 10, 1050.00, today - timedelta(days=90)),
        (11, 5, 11,  820.00, today - timedelta(days=120)),
        (12, 9, 12,  670.00, today - timedelta(days=150)),
        # Individual customers – small orders
        (13, 6, 13,  180.00, today - timedelta(days=8)),
        (14, 6, 14,  220.00, today - timedelta(days=45)),
        (15, 7, 15,  150.00, today - timedelta(days=70)),
        (16, 10,16,  195.00, today - timedelta(days=100)),
    ]

    transactions = pd.DataFrame(raw_txns,
        columns=["order_id", "customer_id", "order_id_dup",
                 "amount", "transaction_date"])

    # Add customer_type by joining with customers (needed by monthly_active_users.sql)
    transactions = transactions.merge(
        customers[["customer_id", "customer_type"]],
        on="customer_id"
    ).drop(columns=["order_id_dup"])

    transactions["transaction_date"] = transactions["transaction_date"].astype(str)

    # ── users (funnel) ──────────────────────────
    # 60 days of signups; roughly 70% verify email, 40% make first purchase
    users_rows = []
    uid = 1
    for days_ago in range(0, 60):
        signup_dt  = today - timedelta(days=days_ago)
        daily_signups = 5 + (days_ago % 4)          # 5-8 signups per day
        for _ in range(daily_signups):
            verified  = (uid % 10 != 0)             # ~90% verify email
            purchased = (uid % 3 == 0) and verified  # ~33% of verified purchase
            users_rows.append({
                "user_id":            uid,
                "created_at":         str(signup_dt),
                "email_verified_at":  str(signup_dt + timedelta(days=1)) if verified  else None,
                "first_purchase_at":  str(signup_dt + timedelta(days=3)) if purchased else None,
            })
            uid += 1

    users = pd.DataFrame(users_rows)

    # ── write to DB ─────────────────────────────
    customers.to_sql("customers",    engine, if_exists="replace", index=False)
    transactions.to_sql("transactions", engine, if_exists="replace", index=False)
    users.to_sql("users",            engine, if_exists="replace", index=False)

    print(f"✓ Seeded DB – customers: {len(customers)}, "
          f"transactions: {len(transactions)}, users: {len(users)}")


seed_database(engine)


# ─────────────────────────────────────────────
# Task 4 : Load queries from .sql files
# ─────────────────────────────────────────────

def load_query(query_name: str, queries_dir: str = QUERIES_DIR) -> str:
    """Load SQL query text from a .sql file in the queries directory."""
    filepath = os.path.join(queries_dir, f"{query_name}.sql")
    with open(filepath, "r") as f:
        return f.read()


# Load all three metric queries
mau_query     = load_query("monthly_active_users")
revenue_query = load_query("revenue_by_segment")
funnel_query  = load_query("conversion_funnel")

print("\n✓ Loaded all SQL query files from queries/")

# Execute queries → DataFrames
mau     = pd.read_sql(mau_query,     engine)
revenue = pd.read_sql(revenue_query, engine)
funnel  = pd.read_sql(funnel_query,  engine)

# Display results
print("\n── Monthly Active Users ──────────────────────────")
print(mau.to_string(index=False))

print("\n── Revenue by Segment ───────────────────────────")
print(revenue.to_string(index=False))

print("\n── Conversion Funnel ────────────────────────────")
print(funnel.to_string(index=False))


# ─────────────────────────────────────────────
# Task 5 : Validate metric results
# ─────────────────────────────────────────────

def validate_metrics(
    mau_df: pd.DataFrame,
    revenue_df: pd.DataFrame,
    funnel_df: pd.DataFrame
) -> bool:
    """
    Validate all three metric DataFrames.

    Checks:
      - DataFrames are non-empty
      - No unexpected null values in critical columns
      - Revenue values are strictly positive
      - Conversion percentage is in [0, 100]
      - Logical consistency (order_count > 0, revenue > 0, active_users > 0)

    Returns True when all assertions pass; raises AssertionError otherwise.
    """

    print("\n── Validation ───────────────────────────────────")

    # ── Non-empty ────────────────────────────────
    assert not mau_df.empty,     "MAU result is empty"
    assert not revenue_df.empty, "Revenue result is empty"
    assert not funnel_df.empty,  "Funnel result is empty"
    print("✓ All result sets are non-empty")

    # ── Null checks ──────────────────────────────
    mau_critical     = ["month", "active_users"]
    revenue_critical = ["customer_type", "month", "monthly_revenue",
                        "order_count", "unique_customers"]
    funnel_critical  = ["signup_date", "signups", "conversion_pct"]

    assert mau_df[mau_critical].isnull().sum().sum() == 0, \
        f"MAU has nulls in critical columns: {mau_df[mau_critical].isnull().sum().to_dict()}"
    assert revenue_df[revenue_critical].isnull().sum().sum() == 0, \
        f"Revenue has nulls in critical columns: {revenue_df[revenue_critical].isnull().sum().to_dict()}"
    assert funnel_df[funnel_critical].isnull().sum().sum() == 0, \
        f"Funnel has nulls in critical columns: {funnel_df[funnel_critical].isnull().sum().to_dict()}"
    print("✓ No nulls in critical columns")

    # ── Value ranges ─────────────────────────────
    assert (mau_df["active_users"] > 0).all(), \
        "MAU contains rows with zero active users"
    assert (revenue_df["monthly_revenue"] > 0).all(), \
        "Revenue contains rows with zero or negative revenue"
    assert (funnel_df["conversion_pct"] >= 0).all() and \
           (funnel_df["conversion_pct"] <= 100).all(), \
        "Conversion percentage out of [0, 100] range"
    print("✓ All value ranges are valid")

    # ── Logical consistency ───────────────────────
    assert (revenue_df["order_count"] > 0).all(), \
        "Revenue has rows with zero order count"
    assert (revenue_df["unique_customers"] > 0).all(), \
        "Revenue has rows with zero unique customers"
    assert (revenue_df["revenue_per_customer"] > 0).all(), \
        "Revenue per customer is not positive"
    assert (funnel_df["signups"] > 0).all(), \
        "Funnel has days with zero signups"
    assert (funnel_df["first_purchase"] <= funnel_df["signups"]).all(), \
        "First purchases exceed signups – data inconsistency"
    assert (funnel_df["email_verified"] <= funnel_df["signups"]).all(), \
        "Verified count exceeds signups – data inconsistency"
    print("✓ Logical consistency checks passed")

    print("\n✓ All metrics validated successfully")
    return True


validate_metrics(mau, revenue, funnel)


# ─────────────────────────────────────────────
# Save output report
# ─────────────────────────────────────────────

report = {
    "monthly_active_users": {
        "rows_returned":      len(mau),
        "total_active_users": int(mau["active_users"].sum()),
        "months_covered":     list(mau["month"].astype(str)),
    },
    "revenue_by_segment": {
        "rows_returned":   len(revenue),
        "total_revenue":   round(float(revenue["monthly_revenue"].sum()), 2),
        "segments":        list(revenue["customer_type"].unique()),
    },
    "conversion_funnel": {
        "rows_returned":    len(funnel),
        "total_signups":    int(funnel["signups"].sum()),
        "avg_conversion":   round(float(funnel["conversion_pct"].mean()), 1),
        "min_conversion":   round(float(funnel["conversion_pct"].min()), 1),
        "max_conversion":   round(float(funnel["conversion_pct"].max()), 1),
    },
    "validation": "passed",
}

report_path = os.path.join(OUTPUT_DIR, "sql_metrics_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Report saved to {report_path}")
print("\nDone. All teams query from the same .sql files → one number, one truth.")
