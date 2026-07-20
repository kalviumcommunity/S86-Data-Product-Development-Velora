import os
import pandas as pd
from sqlalchemy import create_engine, inspect

# ----------------------------
# Create sample cleaned dataset
# ----------------------------

df_clean = pd.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "email": [
        "alice@gmail.com",
        "bob@gmail.com",
        "charlie@gmail.com",
        "david@gmail.com",
        "eva@gmail.com"
    ],
    "signup_date": [
        "2024-01-01",
        "2024-01-10",
        "2024-02-15",
        "2024-03-01",
        "2024-03-20"
    ],
    "customer_type": [
        "Enterprise",
        "SMB",
        "Enterprise",
        "Individual",
        "SMB"
    ],
    "lifetime_value": [
        5000,
        1500,
        6500,
        700,
        2000
    ]
})

# ----------------------------
# Task 1
# Database Connection
# ----------------------------

engine = create_engine("sqlite:///analytics.db")

with engine.connect():
    print("✓ Database connection successful")

# ----------------------------
# Task 2
# Load Data
# ----------------------------

df_clean.to_sql(
    "customers_cleaned",
    engine,
    if_exists="replace",
    index=False
)

print("\nTable Loaded")

count = pd.read_sql(
    "SELECT COUNT(*) AS row_count FROM customers_cleaned",
    engine
)

print(count)

# ----------------------------
# Task 3
# Validate Schema
# ----------------------------

print("\nTABLE SCHEMA")

inspector = inspect(engine)

columns = inspector.get_columns("customers_cleaned")

for col in columns:

    print(
        col["name"],
        "-",
        col["type"]
    )

# ----------------------------
# Task 4
# SQL Queries
# ----------------------------

query = """
SELECT *
FROM customers_cleaned
WHERE customer_type='Enterprise'
"""

enterprise = pd.read_sql(query, engine)

print("\nEnterprise Customers")

print(enterprise)

query2 = """
SELECT
customer_type,
COUNT(*) AS total_customers,
AVG(lifetime_value) AS avg_ltv

FROM customers_cleaned

GROUP BY customer_type

ORDER BY avg_ltv DESC
"""

summary = pd.read_sql(query2, engine)

print("\nCustomer Summary")

print(summary)

# ----------------------------
# Task 5
# Reusable Function
# ----------------------------

def load_cleaned_data_to_database(
        df,
        table_name,
        database_path="analytics.db"):

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

    rows = pd.read_sql(
        f"SELECT COUNT(*) AS ct FROM {table_name}",
        engine
    )

    print(
        f"\nLoaded {rows.iloc[0]['ct']} rows into {table_name}"
    )

    return engine

engine = load_cleaned_data_to_database(
    df_clean,
    "customers_cleaned"
)

result = pd.read_sql(
    "SELECT * FROM customers_cleaned LIMIT 10",
    engine
)

print("\nReusable Function Output")

print(result)

# ----------------------------
# Save Output
# ----------------------------

os.makedirs("output", exist_ok=True)

with open(
        "output/database_report.txt",
        "w") as file:

    file.write("Database Integration Completed Successfully\n\n")

    file.write("Rows Loaded:\n")
    file.write(str(count))
    file.write("\n\nCustomer Summary\n")
    file.write(str(summary))

print("\nFiles Created")
print("analytics.db")
print("output/database_report.txt")